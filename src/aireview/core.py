import os
import sys
import subprocess
import argparse
import logging
import yaml
import stat
from dataclasses import dataclass
from typing import List, Dict, Protocol, Any, Optional

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
# 3. IMPLEMENTATIONS (PROVIDERS)
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


# --- OPENAI ---
class OpenAIProvider:
    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not set. OpenAI models will fail.")
            self.client = None
            return

        try:
            import openai
            self.client = openai.OpenAI(api_key=self.api_key)
        except ImportError:
            logger.error("Python package 'openai' is missing. Run: pip install openai")
            self.client = None

    def analyze(self, model: str, system_prompt: str, user_content: str) -> str:
        if not self.client:
            return "ERROR: OpenAI client not initialized (missing key or package)."
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


# --- ANTHROPIC (CLAUDE) ---
class AnthropicProvider:
    def __init__(self):
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            logger.warning("ANTHROPIC_API_KEY not set. Claude models will fail.")
            self.client = None
            return

        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=self.api_key)
        except ImportError:
            logger.error("Python package 'anthropic' is missing. Run: pip install anthropic")
            self.client = None

    def analyze(self, model: str, system_prompt: str, user_content: str) -> str:
        if not self.client:
            return "ERROR: Anthropic client not initialized (missing key or package)."
        try:
            logger.info(f"Sending request to Anthropic (Model: {model})...")
            # Claude API treats system prompt as a top-level parameter
            message = self.client.messages.create(
                model=model,
                max_tokens=4000,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_content}
                ]
            )
            return message.content[0].text
        except Exception as e:
            logger.error(f"Anthropic API Error: {e}")
            return f"AI API ERROR: {str(e)}"


# --- GOOGLE (GEMINI) ---
class GeminiProvider:
    def __init__(self):
        self.api_key = os.environ.get("GOOGLE_API_KEY")
        if not self.api_key:
            logger.warning("GOOGLE_API_KEY not set. Gemini models will fail.")
            self.genai = None
            return

        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.genai = genai
        except ImportError:
            logger.error("Python package 'google-generativeai' is missing. Run: pip install google-generativeai")
            self.genai = None

    def analyze(self, model: str, system_prompt: str, user_content: str) -> str:
        if not self.genai:
            return "ERROR: Google GenAI client not initialized (missing key or package)."
        try:
            logger.info(f"Sending request to Google (Model: {model})...")
            # Gemini configuration for system instructions
            model_instance = self.genai.GenerativeModel(
                model_name=model,
                system_instruction=system_prompt
            )
            response = model_instance.generate_content(user_content)
            return response.text
        except Exception as e:
            logger.error(f"Gemini API Error: {e}")
            return f"AI API ERROR: {str(e)}"


# --- UNIVERSAL ROUTER ---
class UniversalAIProvider:
    """Routes requests to the correct provider based on model name."""

    def __init__(self):
        self.openai = OpenAIProvider()
        self.anthropic = AnthropicProvider()
        self.gemini = GeminiProvider()

    def analyze(self, model: str, system_prompt: str, user_content: str) -> str:
        model_lower = model.lower()

        if model_lower.startswith("claude"):
            return self.anthropic.analyze(model, system_prompt, user_content)

        if model_lower.startswith("gemini"):
            return self.gemini.analyze(model, system_prompt, user_content)

        # Default to OpenAI for gpt-* or unknown models
        return self.openai.analyze(model, system_prompt, user_content)


class MockAIProvider:
    def analyze(self, model: str, system_prompt: str, user_content: str) -> str:
        logger.info(f"[DRY-RUN] Routing to provider for model: {model}")
        logger.info(f"[DRY-RUN] Payload size: {len(user_content)} chars")
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
            check = next((c for c in self.config.checks if c.id == check_id), None)
            if not check:
                logger.error(f"Check ID '{check_id}' not found in configuration.")
                return False

            context = self.build_context(check_id)

            if not context.strip():
                logger.warning(f"Context for '{check_id}' is empty. Skipping AI call.")
                return True

            verdict = self.ai.analyze(check.model, check.system_prompt, context)

            print(f"\n--- REPORT: {check_id} ({check.model}) ---")
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
    if not os.path.exists(".git"):
        logger.error("Not a git repository (no .git directory found).")
        sys.exit(1)

    hook_path = os.path.join(".git", "hooks", "pre-push")
    script_path = os.path.abspath(__file__)

    hook_content = f"""#!/bin/sh
# AI Review Pre-Push Hook
echo "🤖 Running AI Pre-Push Review..."
if git log -1 --pretty=%B | grep -q "\\[skip-ai\\]"; then
    echo "⏩ Skipping AI checks..."
    exit 0
fi
"{sys.executable}" "{script_path}" run
if [ $? -ne 0 ]; then
    echo "❌ AI Review Failed. Push aborted."
    exit 1
fi
exit 0
"""
    try:
        with open(hook_path, "w") as f:
            f.write(hook_content)
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
  - id: openai_check
    system_prompt: "Say PASS if good."
    model: gpt-3.5-turbo
    context: [git_diff]

  - id: claude_check
    system_prompt: "Say PASS if good."
    model: claude-3-opus-20240229
    context: [git_diff]

  - id: gemini_check
    system_prompt: "Say PASS if good."
    model: gemini-1.5-pro
    context: [git_diff]
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
    # Custom help formatter to keep newlines in the description/epilog
    parser = argparse.ArgumentParser(
        description="🤖 AI Pre-Push Review Tool\n"
                    "Automated code review using OpenAI, Claude, or Gemini before you push.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES:
  1. Initialize a new configuration file:
     $ aireview init

  2. Install the git pre-push hook (runs automatically on git push):
     $ aireview install

  3. Run all checks manually (using API keys from env):
     $ aireview run

  4. Run a specific check only:
     $ aireview run --check security-audit

  5. Dry-run mode (see what would be sent to AI without paying):
     $ aireview run --dry-run --verbose

  6. Validate your configuration file syntax:
     $ aireview validate

ENVIRONMENT VARIABLES:
  OPENAI_API_KEY      Required for gpt-* models
  ANTHROPIC_API_KEY   Required for claude-* models
  GOOGLE_API_KEY      Required for gemini-* models
"""
    )

    parser.add_argument("command", choices=["run", "init", "validate", "install"],
                        help="Action to perform")
    parser.add_argument("--config", default="ai-checks.yaml",
                        help="Path to config file (default: ai-checks.yaml)")
    parser.add_argument("--check",
                        help="Run a specific check ID only (e.g., 'security-audit')")
    parser.add_argument("--dry-run", action="store_true",
                        help="Simulate execution without calling AI APIs")
    parser.add_argument("--verbose", action="store_true",
                        help="Enable detailed debug logging")

    # Handle no-argument case
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

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
        # Use the Universal Router
        ai_provider = UniversalAIProvider()

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