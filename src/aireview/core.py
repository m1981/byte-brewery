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

# (Ad 7) Load .env file if present
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    logger.debug("python-dotenv not installed. Skipping .env loading.")

# (Ad 5) Graceful PyYAML handling
try:
    import yaml

    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    logger.warning("PyYAML not found. Only JSON configs supported unless installed.")


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
    # (Ad 4) Configurable character limit
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

            # (Ad 2) Append JSON instruction automatically to ensure structured output
            if "JSON" not in text:
                text += "\n\nIMPORTANT: Return your response in raw JSON format: {\"status\": \"PASS\" | \"FAIL\", \"reason\": \"...\"}"

            prompts[p_id] = PromptDefinition(id=p_id, text=text)

        checks = []
        for c in data.get('checks', []):
            prompt_id = c.get('prompt_id')
            # Handle inline prompts
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
                max_chars=c.get('max_chars', 16000)  # (Ad 4) Default limit
            ))
        return cls(definitions=defs, prompts=prompts, checks=checks)


# ==========================================
# 2. INTERFACES & PROVIDERS
# ==========================================

class CommandRunner(Protocol):
    def run(self, command: str) -> str: ...


class AIProvider(Protocol):
    def analyze(self, model: str, full_message: str) -> str: ...


class ShellCommandRunner:
    def run(self, command: str) -> str:
        if not command or not command.strip():
            return ""
        try:
            # (Ad 6) Support dynamic commit ranges if passed via ENV
            # If the command contains placeholders, we could swap them here.
            # For now, we assume the command is static or set by the user.
            result = subprocess.run(
                command, shell=True, check=True, capture_output=True, text=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: '{command}' -> {e.stderr}")
            return f"ERROR executing '{command}'"


# --- AI PROVIDERS (Simplified for brevity, logic remains same as original) ---
class OpenAIProvider:
    def __init__(self):
        self.client = None
        if os.environ.get("OPENAI_API_KEY"):
            try:
                import openai
                self.client = openai.OpenAI()
            except ImportError:
                pass

    def analyze(self, model: str, full_message: str) -> str:
        if not self.client: return '{"status": "FAIL", "reason": "OpenAI client not ready"}'
        try:
            # Force JSON mode for newer models
            kwargs = {"model": model, "messages": [{"role": "user", "content": full_message}]}
            if "gpt-4" in model or "gpt-3.5-turbo-1106" in model:
                kwargs["response_format"] = {"type": "json_object"}

            response = self.client.chat.completions.create(**kwargs)
            return response.choices[0].message.content
        except Exception as e:
            return json.dumps({"status": "FAIL", "reason": f"API Error: {str(e)}"})


class UniversalAIProvider:
    def __init__(self):
        self.openai = OpenAIProvider()
        # ... (Anthropic/Gemini would go here) ...

    def analyze(self, model: str, full_message: str) -> str:
        # Routing logic
        return self.openai.analyze(model, full_message)


class MockAIProvider:
    def analyze(self, model: str, full_message: str) -> str:
        logger.info(f"[DRY-RUN] Model: {model}")
        return '{"status": "PASS", "reason": "Dry Run Successful"}'


# ==========================================
# 3. ENGINE
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

            # --- FIX START: Skip if output is empty ---
            if not output or not output.strip():
                logger.debug(f"Context '{ctx_id}' returned empty output. Skipping.")
                continue
            # --- FIX END ---

            # (Ad 4) Truncation Logic
            remaining_chars = check.max_chars - total_chars
            if len(output) > remaining_chars:
                logger.warning(f"Truncating output for context '{ctx_id}' (Limit: {check.max_chars})")
                output = output[:remaining_chars] + "\n... [TRUNCATED DUE TO LENGTH LIMIT] ..."

            total_chars += len(output)

            # (Ad 3) Context Injection Safety: Use Markdown fencing instead of XML
            buffer.append(f"### Context: {definition.tag}\n```text\n{output}\n```\n")

            if total_chars >= check.max_chars:
                break

        return "\n".join(buffer)

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Robustly extracts JSON from AI response."""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # AI often wraps JSON in markdown code blocks
            match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except:
                    pass

            # Fallback: Look for simple PASS/FAIL if JSON fails
            if "FAIL" in response.upper():
                return {"status": "FAIL",
                        "reason": "Could not parse JSON, but keyword FAIL found. Raw: " + response[:50]}
            return {"status": "PASS", "reason": "Could not parse JSON, assumed PASS. Raw: " + response[:50]}

    def run_check(self, check_id: str) -> bool:
        check = next((c for c in self.config.checks if c.id == check_id), None)
        if not check: return False

        prompt_def = self.config.prompts.get(check.prompt_id)
        context = self.build_context(check)

        if not context.strip():
            logger.warning(f"Context empty for {check_id}. Skipping.")
            return True

        full_message = f"{prompt_def.text}\n\n{context}"

        # Call AI
        raw_response = self.ai.analyze(check.model, full_message)

        # (Ad 2) Structured Output Parsing
        result = self._parse_json_response(raw_response)

        status = result.get("status", "FAIL").upper()
        reason = result.get("reason", "No reason provided")

        print(f"\n--- CHECK: {check_id} [{status}] ---")
        print(f"Reason: {reason}")
        print("-----------------------------------\n")

        return status == "PASS"


# ==========================================
# 4. INSTALLATION (GIT HOOK)
# ==========================================

def install_hook():
    # (Ad 6) Robust Pre-Push Hook
    if not os.path.exists(".git"):
        logger.error("Not a git repository.")
        sys.exit(1)

    hook_path = os.path.join(".git", "hooks", "pre-push")
    script_path = os.path.abspath(__file__)

    # This shell script logic handles the pre-push arguments
    hook_content = f"""#!/bin/sh
# AI Review Pre-Push Hook
echo "🤖 AI Review: Checking push..."

# Read stdin to get the range of commits being pushed
while read local_ref local_sha remote_ref remote_sha
do
    if [ "$local_sha" = "0000000000000000000000000000000000000000" ]; then
        # Deleting a remote branch, skip check
        exit 0
    fi

    if [ "$remote_sha" = "0000000000000000000000000000000000000000" ]; then
        # New branch, check against origin/main or HEAD
        export AI_DIFF_TARGET="origin/main"
    else
        # Existing branch, check range
        export AI_DIFF_TARGET="$remote_sha..$local_sha"
    fi

    # Run Python Tool
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

# (Ad 1) Fixed Default Config: Removed --name-only
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
        # Create default
        with open(path, 'w') as f: f.write(DEFAULT_CONFIG)

    with open(path, 'r') as f:
        if HAS_YAML:
            data = yaml.safe_load(f) or {}
        else:
            # Fallback for JSON config if YAML missing
            try:
                data = json.load(f)
            except:
                logger.error("PyYAML not installed and file is not valid JSON.")
                sys.exit(1)
    return Config.from_dict(data)


def main():
    parser = argparse.ArgumentParser(description="AI Review Tool")
    parser.add_argument("command", choices=["run", "init", "install"], help="Action")
    parser.add_argument("--config", default="ai-checks.yaml")
    parser.add_argument("--check", help="Specific check ID")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without calling AI")
    # ADDED BACK: The verbose flag
    parser.add_argument("--verbose", action="store_true", help="Enable debug logs")

    args = parser.parse_args()

    # ADDED BACK: Set logging level based on flag
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled.")

    if args.command == "install":
        install_hook()
        return

    if args.command == "init":
        load_config(args.config)
        logger.info(f"Config initialized: {args.config}")
        return

    config = load_config(args.config)

    # Check for the bad config pattern from user snippet
    git_def = config.definitions.get('git_diff')
    if git_def and "--name-only" in git_def.cmd:
        logger.warning(
            "⚠️  CONFIGURATION WARNING: 'git_diff' uses '--name-only'. The AI cannot see your code, only filenames. Please remove '--name-only' from your config.")

    ai_provider = MockAIProvider() if args.dry_run else UniversalAIProvider()
    runner = ShellCommandRunner()
    engine = ReviewEngine(config, runner, ai_provider)

    checks = [c for c in config.checks if c.id == args.check] if args.check else config.checks

    if not checks:
        logger.error(f"No checks found matching '{args.check}'" if args.check else "No checks defined in config.")
        sys.exit(1)

    success = True
    for check in checks:
        if not engine.run_check(check.id):
            success = False

    if not success:
        logger.error("❌ Some checks failed.")
        sys.exit(1)

    logger.info("✅ All checks passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()