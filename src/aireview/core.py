import os
import sys
import subprocess
import argparse
import logging
import yaml
import stat
from dataclasses import dataclass
from typing import List, Dict, Protocol, Any

# ==========================================
# 0. LOGGING SETUP
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("aireview")


# ==========================================
# 1. DOMAIN LAYER
# ==========================================

@dataclass
class ContextDefinition:
    id: str
    tag: str
    cmd: str


@dataclass
class CheckDefinition:
    id: str
    system_prompt: str
    model: str
    context_ids: List[str]


@dataclass
class Config:
    definitions: Dict[str, ContextDefinition]
    checks: List[CheckDefinition]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Config':
        defs = {}
        for d in data.get('definitions', []):
            if 'id' not in d or 'cmd' not in d:
                logger.warning(f"Skipping malformed definition: {d}")
                continue
            defs[d['id']] = ContextDefinition(d['id'], d.get('tag', d['id']), d['cmd'])

        checks = []
        for c in data.get('checks', []):
            if 'id' not in c:
                logger.warning(f"Skipping malformed check: {c}")
                continue
            checks.append(CheckDefinition(
                id=c['id'],
                system_prompt=c.get('system_prompt', 'You are a code reviewer.'),
                model=c.get('model', 'gpt-3.5-turbo'),
                context_ids=c.get('context', [])
            ))
        return cls(definitions=defs, checks=checks)


# ==========================================
# 2. INTERFACES
# ==========================================

class CommandRunner(Protocol):
    def run(self, command: str) -> str: ...


class AIProvider(Protocol):
    def analyze(self, model: str, system_prompt: str, user_content: str) -> str: ...


# ==========================================
# 3. IMPLEMENTATIONS
# ==========================================

class ShellCommandRunner:
    def run(self, command: str) -> str:
        if not command or not command.strip():
            logger.warning("Attempted to run empty command.")
            return ""

        logger.debug(f"Executing shell command: {command}")
        try:
            result = subprocess.run(
                command,
                shell=True,
                check=True,
                capture_output=True,
                text=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() if e.stderr else str(e)
            logger.error(f"Command failed: '{command}' -> {error_msg}")
            return f"ERROR executing '{command}':\n{error_msg}"
        except FileNotFoundError:
            logger.error(f"Shell not found while executing: {command}")
            return "ERROR: Shell environment issue."


class OpenAIProvider:
    def __init__(self, api_key: str):
        try:
            import openai
            self.client = openai.OpenAI(api_key=api_key)
        except ImportError:
            logger.critical("Python package 'openai' is missing. Install it via pip.")
            sys.exit(1)

    def analyze(self, model: str, system_prompt: str, user_content: str) -> str:
        try:
            logger.info(f"Sending request to OpenAI (Model: {model})...")
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API Error: {e}")
            return f"AI API ERROR: {str(e)}"


class MockAIProvider:
    def analyze(self, model: str, system_prompt: str, user_content: str) -> str:
        logger.info(f"[DRY-RUN] Would send {len(user_content)} chars to {model}")
        return "DRY RUN: PASS"


# ==========================================
# 4. ENGINE
# ==========================================

class ReviewEngine:
    def __init__(self, config: Config, runner: CommandRunner, ai: AIProvider):
        self.config = config
        self.runner = runner
        self.ai = ai

    def build_context(self, check_id: str) -> str:
        # Retrieve check definition
        check = next((c for c in self.config.checks if c.id == check_id), None)
        if not check:
            raise ValueError(f"Check ID '{check_id}' not found")

        buffer = []
        logger.info(f"Building context for check: {check_id}")

        for ctx_id in check.context_ids:
            definition = self.config.definitions.get(ctx_id)
            if not definition:
                logger.warning(f"Context '{ctx_id}' referenced in check '{check_id}' but not defined.")
                buffer.append(f"<!-- Warning: Context '{ctx_id}' not defined -->")
                continue

            output = self.runner.run(definition.cmd)
            buffer.append(f"<{definition.tag}>\n{output}\n</{definition.tag}>")

        return "\n".join(buffer)

    def run_check(self, check_id: str) -> bool:
        try:
            # FIX: Retrieve the check object here so it is available for the AI call
            check = next((c for c in self.config.checks if c.id == check_id), None)
            if not check:
                logger.error(f"Check ID '{check_id}' not found in configuration.")
                return False

            context = self.build_context(check_id)

            if not context.strip():
                logger.warning(f"Context for '{check_id}' is empty. Skipping AI call.")
                return True

            verdict = self.ai.analyze(check.model, check.system_prompt, context)

            print(f"\n--- REPORT: {check_id} ---")
            print(verdict)
            print("--------------------------\n")

            if "FAIL" in verdict.upper() and "DRY RUN" not in verdict:
                return False
            return True
        except Exception as e:
            logger.exception(f"Unexpected error running check '{check_id}': {e}")
            return False


# ==========================================
# 5. INSTALLATION LOGIC
# ==========================================

def install_hook():
    """Installs the pre-push hook into the .git directory."""
    if not os.path.exists(".git"):
        logger.error("Not a git repository (no .git directory found).")
        sys.exit(1)

    hook_path = os.path.join(".git", "hooks", "pre-push")

    # Get the absolute path of the current script to ensure the hook finds it
    script_path = os.path.abspath(__file__)

    # The hook script content
    hook_content = f"""#!/bin/sh
# AI Review Pre-Push Hook
# Auto-generated by aireview

echo "🤖 Running AI Pre-Push Review..."

# Check if we should skip
if git log -1 --pretty=%B | grep -q "\\[skip-ai\\]"; then
    echo "⏩ Skipping AI checks..."
    exit 0
fi

# Run the python script
# We use sys.executable to ensure we use the same python interpreter
"{sys.executable}" "{script_path}" run

# Capture exit code
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo "❌ AI Review Failed. Push aborted."
    echo "💡 To bypass, add '[skip-ai]' to your commit message."
    exit 1
fi

exit 0
"""

    try:
        with open(hook_path, "w") as f:
            f.write(hook_content)

        # Make it executable (chmod +x)
        st = os.stat(hook_path)
        os.chmod(hook_path, st.st_mode | stat.S_IEXEC)

        logger.info(f"✅ Successfully installed pre-push hook at: {hook_path}")
    except Exception as e:
        logger.error(f"Failed to install hook: {e}")
        sys.exit(1)


# ==========================================
# 6. CLI
# ==========================================

DEFAULT_CONFIG = """
definitions:
  - id: git_diff
    tag: git_changes
    cmd: "git diff --cached --name-only"
  - id: file_tree
    tag: project_structure
    cmd: "ls -R"

checks:
  - id: sanity_check
    system_prompt: "Say PASS if the code looks okay, FAIL otherwise."
    model: gpt-3.5-turbo
    context:
      - git_diff
      - file_tree
"""


def load_config(path: str) -> Config:
    if not os.path.exists(path):
        logger.info(f"Config file not found at '{path}'. Creating default.")
        try:
            with open(path, 'w') as f:
                f.write(DEFAULT_CONFIG)
        except IOError as e:
            logger.critical(f"Could not write default config to '{path}': {e}")
            sys.exit(1)

    try:
        with open(path, 'r') as f:
            data = yaml.safe_load(f) or {}
        return Config.from_dict(data)
    except yaml.YAMLError as e:
        logger.critical(f"Invalid YAML in '{path}': {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="AI Pre-Push Review Tool")
    parser.add_argument("command", choices=["run", "init", "validate", "install"], help="Command to execute")
    parser.add_argument("--config", default="ai-checks.yaml", help="Path to config file")
    parser.add_argument("--check", help="Run a specific check ID only")
    parser.add_argument("--dry-run", action="store_true", help="Don't call AI API")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logs")

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # --- COMMAND HANDLERS ---

    if args.command == "install":
        install_hook()
        return

    if args.command == "init":
        load_config(args.config)
        logger.info(f"Initialized configuration at {args.config}")
        return

    config = load_config(args.config)

    if args.command == "validate":
        logger.info("Configuration is valid.")
        return

    # --- RUN LOGIC ---

    runner = ShellCommandRunner()

    if args.dry_run:
        ai_provider = MockAIProvider()
    else:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.critical("OPENAI_API_KEY environment variable not set.")
            sys.exit(1)
        ai_provider = OpenAIProvider(api_key)

    engine = ReviewEngine(config, runner, ai_provider)

    checks_to_run = [c for c in config.checks if c.id == args.check] if args.check else config.checks

    if not checks_to_run:
        logger.error(f"No checks found matching '{args.check}'")
        sys.exit(1)

    all_passed = True
    for check in checks_to_run:
        if not engine.run_check(check.id):
            all_passed = False

    if not all_passed:
        logger.error("❌ Some checks failed.")
        sys.exit(1)

    logger.info("✅ All checks passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()