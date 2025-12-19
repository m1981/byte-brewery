# ==============================================================================
# ARCHITECTURE DECISION RECORD (ADR) - PAYLOAD VISIBILITY
# ==============================================================================
# DECISION:
#   The ReviewEngine must explicitly print the full prompt payload AND request metadata
#   (temperature, max_tokens, etc.) to stdout when running in DEBUG/VERBOSE mode.
# ==============================================================================
# ARCHITECTURE DECISION RECORD (ADR) - CONTEXT FEEDBACK
# ==============================================================================
# DECISION:
#   When a context command returns empty output, the tool MUST provide actionable
#   feedback to the user based on the command type.
# ==============================================================================
# ARCHITECTURE DECISION RECORD (ADR) - INTERNAL COMMAND SYNTAX
# ==============================================================================
# DECISION:
#   Internal/Native commands use the 'internal:' URI scheme.
#   NO MAGIC INJECTION: Users must explicitly define these commands in their config.
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

        # 1. Load User Definitions
        for d in data.get('definitions', []):
            # VALIDATION: Check for unknown keys in definitions
            valid_keys = {'id', 'tag', 'cmd'}
            unknown = set(d.keys()) - valid_keys
            if unknown:
                logger.critical(f"❌ Config Error: Definition '{d.get('id', 'unknown')}' has unknown keys: {unknown}. Valid keys are: {valid_keys}")
                sys.exit(1)

            defs[d['id']] = ContextDefinition(d['id'], d.get('tag', d['id']), d['cmd'])

        prompts = {}
        for p in data.get('prompts', []):
            # VALIDATION: Check for unknown keys in prompts
            valid_keys = {'id', 'text', 'file'}
            unknown = set(p.keys()) - valid_keys
            if unknown:
                logger.critical(f"❌ Config Error: Prompt '{p.get('id', 'unknown')}' has unknown keys: {unknown}. Valid keys are: {valid_keys}")
                sys.exit(1)

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
            valid_keys = {'id', 'prompt_id', 'model', 'context', 'max_chars', 'system_prompt'}
            unknown = set(c.keys()) - valid_keys
            if unknown:
                hint = ""
                if 'cmd' in unknown:
                    hint = " (Did you mean 'context'?)"
                logger.critical(f"❌ Config Error: Check '{c.get('id', 'unknown')}' has unknown keys: {unknown}{hint}. Valid keys are: {valid_keys}")
                sys.exit(1)

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

            # Handle String vs List for context
            raw_context = c.get('context', [])
            if isinstance(raw_context, str):
                context_ids = [raw_context]
            else:
                context_ids = raw_context

            checks.append(CheckDefinition(
                id=c['id'],
                prompt_id=prompt_id,
                model=c.get('model', 'gpt-3.5-turbo'),
                context_ids=context_ids,
                max_chars=c.get('max_chars', 16000)
            ))

        # Strict Validation of References
        for check in checks:
            for ctx_id in check.context_ids:
                if ctx_id not in defs:
                    hint = ""
                    if ctx_id.startswith("internal:") or ctx_id.startswith("@"):
                        hint = f" (Did you mean to define a context with cmd: '{ctx_id}'?)"
                    elif ctx_id == "push_diff":
                        hint = " (You must define 'push_diff' in 'definitions' with cmd: 'internal:push_diff')"

                    logger.critical(f"❌ Config Error: Check '{check.id}' references unknown context ID '{ctx_id}'{hint}")
                    sys.exit(1)

        return cls(definitions=defs, prompts=prompts, checks=checks)


# ==========================================
# 2. INTERFACES & PROVIDERS
# ==========================================

# --- NEW: Custom Exception for Command Failures ---
class CommandError(Exception):
    pass

class CommandRunner(Protocol):
    def run(self, command: str) -> str: ...


class AIProvider(Protocol):
    def analyze(self, model: str, full_message: str) -> str: ...

    def get_metadata(self, model: str) -> Dict[str, Any]: ...


class ShellCommandRunner:
    # Registry of valid internal commands
    VALID_INTERNAL_COMMANDS = {"push_diff"}

    def _run_internal_push_diff(self) -> str:
        target = os.environ.get("AI_DIFF_TARGET", "--cached")
        buffer = []

        try:
            diff_cmd = f"git diff {target}"
            diff_output = subprocess.check_output(diff_cmd, shell=True, text=True).strip()

            if not diff_output:
                return ""

            buffer.append(f"=== GIT DIFF ({target}) ===")
            buffer.append(diff_output)
            buffer.append("\n=== FULL FILE CONTEXT ===")

            files_cmd = f"git diff --name-only --diff-filter=d {target}"
            files_output = subprocess.check_output(files_cmd, shell=True, text=True).strip()

            if files_output:
                for filename in files_output.splitlines():
                    if os.path.exists(filename) and os.path.isfile(filename):
                        buffer.append(f"\n--- FILE: {filename} ---")
                        try:
                            with open(filename, 'r', encoding='utf-8', errors='replace') as f:
                                buffer.append(f.read())
                        except Exception as e:
                            buffer.append(f"[Error reading file: {e}]")

            return "\n".join(buffer)

        except subprocess.CalledProcessError as e:
            # Raise exception instead of returning error string
            raise CommandError(f"Internal push_diff failed: {e}")

    def run(self, command: str) -> str:
        if not command: return ""

        # Check for "internal:" prefix
        if command.startswith("internal:"):
            action = command.split(":", 1)[1]

            # Validate against registry
            if action not in self.VALID_INTERNAL_COMMANDS:
                valid_list = ", ".join([f"internal:{c}" for c in self.VALID_INTERNAL_COMMANDS])
                # Raise exception to stop execution
                raise CommandError(f"Unknown internal command 'internal:{action}'. Available commands: {valid_list}")

            if action == "push_diff":
                return self._run_internal_push_diff()

            raise CommandError(f"Unimplemented internal command '{action}'")

        # Fallback to Shell
        try:
            result = subprocess.run(
                command, shell=True, check=True, capture_output=True, text=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            # Raise exception to stop execution
            raise CommandError(f"Command failed: '{command}'\nStderr: {e.stderr}")


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
        is_json_mode = "gpt-4" in model or "gpt-3.5-turbo-1106" in model
        return {
            "provider": "OpenAI",
            "model": model,
            "temperature": 1.0,
            "max_tokens": "Model Default",
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
# 3. ENGINE
# ==========================================

class ReviewEngine:
    def __init__(self, config: Config, runner: CommandRunner, ai: AIProvider):
        self.config = config
        self.runner = runner
        self.ai = ai

    def _get_empty_context_hint(self, cmd: str) -> str:
        """Generates a helpful hint based on the command that returned nothing."""
        if cmd == "internal:push_diff":
            target = os.environ.get("AI_DIFF_TARGET", "--cached")
            if target == "--cached":
                return "No staged changes found. Did you forget to `git add`?"
            return f"No changes found in range: {target}"
        if "git diff" in cmd and "--cached" in cmd:
            return "No staged changes found. Did you forget to `git add`?"
        if "git diff" in cmd:
            return "No changes found in working directory."
        return "Command returned empty output."

    def build_context(self, check: CheckDefinition) -> str:
        buffer = []
        total_chars = 0

        for ctx_id in check.context_ids:
            definition = self.config.definitions.get(ctx_id)

            if not definition:
                logger.error(f"Context ID '{ctx_id}' not found in definitions. Skipping.")
                continue

            # --- UPDATED: Catch CommandError here ---
            try:
                output = self.runner.run(definition.cmd)
            except CommandError as e:
                # Re-raise to stop the check immediately
                raise e

            if not output or not output.strip():
                hint = self._get_empty_context_hint(definition.cmd)
                print(f"  ⚠️  Context '{ctx_id}' is empty. ({hint})")
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
        meta_str = " | ".join(f"{k}: {v}" for k, v in metadata.items())
        print(f"\033[90m[DEBUG] {meta_str}\033[0m")

        print("")
        for line in full_message.splitlines():
            print(f"  \033[90m│\033[0m {line}")
        print("")

    def run_check(self, check_id: str) -> bool:
        check = next((c for c in self.config.checks if c.id == check_id), None)
        if not check: return False

        print("=" * 80)
        print(f"CHECK: {check_id}")
        print("=" * 80)

        prompt_def = self.config.prompts.get(check.prompt_id)

        # --- UPDATED: Catch CommandError from build_context ---
        try:
            context = self.build_context(check)
        except CommandError as e:
            print(f"  ❌ Error gathering context: {e}")
            print("")
            return False # Fail the check immediately

        if not context.strip():
            print("")
            print("  ⏭️  Skipped Check (No context available)")
            print("")
            return True

        full_message = f"{prompt_def.text}\n\n{context}"

        if logger.isEnabledFor(logging.DEBUG):
            metadata = self.ai.get_metadata(check.model)
            self._print_debug_info(metadata, full_message)

        raw_response = self.ai.analyze(check.model, full_message)

        result = self._parse_json_response(raw_response)
        status = result.get("status", "FAIL").upper()
        reason = result.get("reason", "No reason provided")

        if logger.isEnabledFor(logging.DEBUG):
            print("-" * 80)

        symbol = "✔" if status == "PASS" else "✘"
        print(f"{symbol} {status} | Reason: {reason}")
        print("")

        return status == "PASS"


# ==========================================
# 4. INSTALLATION (GIT HOOK)
# ==========================================

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

# Updated Default Config to be EXPLICIT
DEFAULT_CONFIG = """
definitions:
  - id: push_diff
    tag: git_changes
    cmd: "internal:push_diff"
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
    context: [push_diff]
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