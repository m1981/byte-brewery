# ==============================================================================
# ARCHITECTURE DECISION RECORD (ADR) - PAYLOAD VISIBILITY
# ==============================================================================
# DECISION:
#   The ReviewEngine must explicitly print the full prompt payload AND request metadata
#   (temperature, max_tokens, etc.) to stdout when running in DEBUG/VERBOSE mode.
# ==============================================================================

import os
import sys
import subprocess
import argparse
import logging
import stat
import json
import re
from dataclasses import dataclass, field
from typing import List, Dict, Protocol, Any, Optional

# ==========================================
# 0. LOGGING & ENV SETUP
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("aireview")

try:
    from dotenv import load_dotenv

    load_dotenv()
    logger.debug("Loaded environment variables from .env")
except ImportError:
    logger.debug("python-dotenv not installed. Skipping .env file loading.")

try:
    import yaml
except ImportError:
    logger.critical("❌ CRITICAL ERROR: PyYAML is missing.")
    sys.exit(1)


# ==========================================
# 1. DOMAIN LAYER
# ==========================================
# ... (No changes to Domain Layer classes: ContextDefinition, PromptDefinition, CheckDefinition, Config) ...
@dataclass
class ContextDefinition:
    id: str
    tag: str
    cmd: str


@dataclass
class PromptDefinition:
    id: str
    text: str


@dataclass
class CheckDefinition:
    id: str
    prompt_id: str
    model: str
    context_ids: List[str]
    max_chars: int = 16000


@dataclass
class Config:
    definitions: Dict[str, ContextDefinition]
    prompts: Dict[str, PromptDefinition]
    checks: List[CheckDefinition]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Config':
        defs = {}
        for d in data.get('definitions', []):
            defs[d['id']] = ContextDefinition(d['id'], d.get('tag', d['id']), d['cmd'])

        prompts = {}
        for p in data.get('prompts', []):
            p_id = p.get('id')
            text = ""
            if 'file' in p:
                try:
                    with open(p['file'], 'r') as f:
                        text = f.read()
                except Exception as e:
                    logger.error(f"Failed to load prompt file '{p['file']}': {e}")
                    text = "ERROR: Prompt file missing."
            else:
                text = p.get('text', '')

            if "JSON" not in text:
                text += "\n\nIMPORTANT: Return your response in raw JSON format: {\"status\": \"PASS\" | \"FAIL\", \"reason\": \"...\"}"

            prompts[p_id] = PromptDefinition(id=p_id, text=text)

        checks = []
        for c in data.get('checks', []):
            prompt_id = c.get('prompt_id')
            if not prompt_id and 'system_prompt' in c:
                virtual_id = f"inline_{c['id']}"
                prompts[virtual_id] = PromptDefinition(virtual_id, c['system_prompt'])
                prompt_id = virtual_id

            if not prompt_id:
                prompt_id = 'basic_reviewer'
                if 'basic_reviewer' not in prompts:
                    prompts['basic_reviewer'] = PromptDefinition('basic_reviewer',
                                                                 "You are a code reviewer. Return JSON: {\"status\": \"PASS\" | \"FAIL\", \"reason\": \"...\"}")

            checks.append(CheckDefinition(
                id=c['id'],
                prompt_id=prompt_id,
                model=c.get('model', 'gpt-3.5-turbo'),
                context_ids=c.get('context', []),
                max_chars=c.get('max_chars', 16000)
            ))
        return cls(definitions=defs, prompts=prompts, checks=checks)


# ==========================================
# 2. INTERFACES & PROVIDERS
# ==========================================

class CommandRunner(Protocol):
    def run(self, command: str) -> str: ...


class AIProvider(Protocol):
    def analyze(self, model: str, full_message: str) -> str: ...

    # NEW: Method to expose configuration details
    def get_metadata(self, model: str) -> Dict[str, Any]: ...


class ShellCommandRunner:
    def run(self, command: str) -> str:
        if not command or not command.strip():
            return ""
        try:
            result = subprocess.run(
                command, shell=True, check=True, capture_output=True, text=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: '{command}' -> {e.stderr}")
            return f"ERROR executing '{command}'"


class OpenAIProvider:
    def __init__(self):
        self.client = None
        if os.environ.get("OPENAI_API_KEY"):
            try:
                import openai
                self.client = openai.OpenAI()
            except ImportError:
                pass

    def get_metadata(self, model: str) -> Dict[str, Any]:
        # Define standard OpenAI params here
        is_json_mode = "gpt-4" in model or "gpt-3.5-turbo-1106" in model
        return {
            "provider": "OpenAI",
            "model": model,
            "temperature": 1.0,  # Default
            "max_tokens": "Model Default (Inf)",
            "response_format": "json_object" if is_json_mode else "text"
        }

    def analyze(self, model: str, full_message: str) -> str:
        if not self.client: return '{"status": "FAIL", "reason": "OpenAI client not ready"}'
        try:
            meta = self.get_metadata(model)
            kwargs = {
                "model": model,
                "messages": [{"role": "user", "content": full_message}],
                "temperature": meta["temperature"]
            }
            if meta["response_format"] == "json_object":
                kwargs["response_format"] = {"type": "json_object"}

            response = self.client.chat.completions.create(**kwargs)
            return response.choices[0].message.content
        except Exception as e:
            return json.dumps({"status": "FAIL", "reason": f"API Error: {str(e)}"})


class UniversalAIProvider:
    def __init__(self):
        self.openai = OpenAIProvider()

    def get_metadata(self, model: str) -> Dict[str, Any]:
        return self.openai.get_metadata(model)

    def analyze(self, model: str, full_message: str) -> str:
        return self.openai.analyze(model, full_message)


class MockAIProvider:
    def get_metadata(self, model: str) -> Dict[str, Any]:
        return {
            "provider": "Mock (Dry Run)",
            "model": model,
            "temperature": 0.0,
            "max_tokens": 4096,
            "response_format": "json_object"
        }

    def analyze(self, model: str, full_message: str) -> str:
        return '{"status": "PASS", "reason": "Dry Run Successful"}'


# ==========================================
# 3. ENGINE (With Detailed Metadata UI)
# ==========================================

class ReviewEngine:
    def __init__(self, config: Config, runner: CommandRunner, ai: AIProvider):
        self.config = config
        self.runner = runner
        self.ai = ai

    def build_context(self, check: CheckDefinition) -> str:
        buffer = []
        total_chars = 0

        for ctx_id in check.context_ids:
            definition = self.config.definitions.get(ctx_id)
            if not definition:
                continue

            output = self.runner.run(definition.cmd)

            if not output or not output.strip():
                logger.debug(f"Context '{ctx_id}' returned empty output. Skipping.")
                continue

            remaining_chars = check.max_chars - total_chars
            if len(output) > remaining_chars:
                logger.warning(f"Truncating output for context '{ctx_id}' (Limit: {check.max_chars})")
                output = output[:remaining_chars] + "\n... [TRUNCATED]"

            total_chars += len(output)
            buffer.append(f"### Context: {definition.tag}\n```text\n{output}\n```\n")

            if total_chars >= check.max_chars:
                break

        return "\n".join(buffer)

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except:
                    pass
            if "FAIL" in response.upper():
                return {"status": "FAIL",
                        "reason": "Could not parse JSON, but keyword FAIL found. Raw: " + response[:50]}
            return {"status": "PASS", "reason": "Could not parse JSON, assumed PASS. Raw: " + response[:50]}

    def _print_debug_info(self, metadata: Dict[str, Any], full_message: str):
        """Prints compact metadata and indented payload."""
        # Compact Metadata Line
        meta_str = " | ".join(f"{k}: {v}" for k, v in metadata.items())
        print(f"\033[90m[DEBUG] {meta_str}\033[0m")  # Grey color if terminal supports it, else just text

        print("")
        # Indent payload with a vertical bar for visual grouping
        for line in full_message.splitlines():
            print(f"  \033[90m│\033[0m {line}")
        print("")

    def run_check(self, check_id: str) -> bool:
        check = next((c for c in self.config.checks if c.id == check_id), None)
        if not check: return False

        # 1. Print Header First (Clear separation)
        print("=" * 80)
        print(f"CHECK: {check_id}")
        print("=" * 80)

        prompt_def = self.config.prompts.get(check.prompt_id)
        context = self.build_context(check)

        if not context.strip():
            print("  ⚠️  Skipped (Empty Context)")
            print("")
            return True

        full_message = f"{prompt_def.text}\n\n{context}"

        # 2. Print Debug Info (Compact)
        if logger.isEnabledFor(logging.DEBUG):
            metadata = self.ai.get_metadata(check.model)
            self._print_debug_info(metadata, full_message)

        # 3. Call AI
        raw_response = self.ai.analyze(check.model, full_message)

        result = self._parse_json_response(raw_response)
        status = result.get("status", "FAIL").upper()
        reason = result.get("reason", "No reason provided")

        # 4. Print Result (Distinct Footer)
        if logger.isEnabledFor(logging.DEBUG):
            print("-" * 80)

        symbol = "✔" if status == "PASS" else "✘"
        # Optional: Add color codes if you want (Green for Pass, Red for Fail)
        print(f"{symbol} {status} | Reason: {reason}")
        print("")

        return status == "PASS"


# ==========================================
# 4. INSTALLATION (GIT HOOK)
# ==========================================
# ... (No changes to install_hook) ...
def install_hook():
    if not os.path.exists(".git"):
        logger.error("Not a git repository.")
        sys.exit(1)

    hook_path = os.path.join(".git", "hooks", "pre-push")
    script_path = os.path.abspath(__file__)

    hook_content = f"""#!/bin/sh
# AI Review Pre-Push Hook
echo "🤖 AI Review: Checking push..."

while read local_ref local_sha remote_ref remote_sha
do
    if [ "$local_sha" = "0000000000000000000000000000000000000000" ]; then
        exit 0
    fi

    if [ "$remote_sha" = "0000000000000000000000000000000000000000" ]; then
        export AI_DIFF_TARGET="origin/main"
    else
        export AI_DIFF_TARGET="$remote_sha..$local_sha"
    fi

    "{sys.executable}" "{script_path}" run

    if [ $? -ne 0 ]; then
        echo "❌ AI Review Failed."
        exit 1
    fi
done

exit 0
"""
    try:
        with open(hook_path, "w") as f:
            f.write(hook_content)
        st = os.stat(hook_path)
        os.chmod(hook_path, st.st_mode | stat.S_IEXEC)
        logger.info(f"✅ Installed pre-push hook at: {hook_path}")
    except Exception as e:
        logger.error(f"Failed to install hook: {e}")
        sys.exit(1)


# ==========================================
# 5. CLI & CONFIG
# ==========================================
# ... (No changes to CLI/Config logic) ...
DEFAULT_CONFIG = """
definitions:
  - id: git_diff
    tag: git_changes
    cmd: "git diff --cached" 
  - id: file_tree
    tag: project_structure
    cmd: "ls -R"

prompts:
  - id: basic_reviewer
    text: "You are a code reviewer. Return JSON: {\\"status\\": \\"PASS\\" | \\"FAIL\\", \\"reason\\": \\"...\\"}"

checks:
  - id: sanity_check
    prompt_id: basic_reviewer
    model: gpt-3.5-turbo
    context: [git_diff]
    max_chars: 16000
"""


def load_config(path: str) -> Config:
    if not os.path.exists(path):
        with open(path, 'w') as f: f.write(DEFAULT_CONFIG)

    with open(path, 'r') as f:
        try:
            data = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            logger.critical(f"❌ Invalid YAML in configuration file '{path}': {e}")
            sys.exit(1)

    return Config.from_dict(data)


def main():
    parser = argparse.ArgumentParser(description="AI Review Tool")
    parser.add_argument("command", choices=["run", "init", "install"], help="Action")
    parser.add_argument("--config", default="ai-checks.yaml")
    parser.add_argument("--check", help="Specific check ID")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without calling AI")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logs")

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    if args.command == "install":
        install_hook()
        return

    if args.command == "init":
        load_config(args.config)
        logger.info(f"Config initialized: {args.config}")
        return

    config = load_config(args.config)

    git_def = config.definitions.get('git_diff')
    if git_def and "--name-only" in git_def.cmd:
        logger.warning("⚠️  Config Warning: 'git_diff' uses '--name-only'. AI cannot see code content.")

    ai_provider = MockAIProvider() if args.dry_run else UniversalAIProvider()
    runner = ShellCommandRunner()
    engine = ReviewEngine(config, runner, ai_provider)

    checks = [c for c in config.checks if c.id == args.check] if args.check else config.checks

    if not checks:
        logger.error(f"No checks found matching '{args.check}'" if args.check else "No checks defined in config.")
        sys.exit(1)

    print("\n🤖 AI Code Review\n")

    success = True
    for check in checks:
        if not engine.run_check(check.id):
            success = False

    if not success:
        print("❌ Review Failed. Please fix the issues above.")
        sys.exit(1)

    print("✅ All checks passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()