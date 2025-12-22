# File: src/aireview/main.py

import argparse
import sys
import os
import stat
import logging
import textwrap
from .utils import setup_logging, load_environment, check_dependencies
from .services.config_loader import ConfigLoader
from .services.runner import ShellCommandRunner
from .services.providers import ProviderFactory
from .engine import ReviewEngine
from .errors import ConfigError
from .services.debugger import Debugger
from .services.git_inspector import GitInspector

logger = logging.getLogger("aireview")


def install_hook():
    if not os.path.exists(".git"):
        logger.error("Not a git repository.")
        sys.exit(1)

    hook_path = os.path.join(".git", "hooks", "pre-push")
    script_cmd = f"{sys.executable} -m aireview.main"

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

    {script_cmd} run

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


def main():
    # Define examples text
    examples = textwrap.dedent("""
    Examples:
      # Initialize a new config file
      aireview init

      # Install the git pre-push hook
      aireview install

      # Run all checks on currently staged changes (default)
      aireview run

      # Run a specific check only
      aireview run --check sanity_check

      # Run checks on a specific commit (vs its parent)
      aireview run --commit a1b2c3d

      # Debugging: Run without calling AI, dump request to file, and show verbose logs
      aireview run --dry-run --dump --verbose

      # Test AI behavior with a specific file as context (bypass git)
      aireview run --context-file ./test_diff.txt
    """)

    parser = argparse.ArgumentParser(
        description="AI Review Tool - Automated Code Review CLI",
        epilog=examples,
        formatter_class=argparse.RawDescriptionHelpFormatter  # Keeps the formatting of the examples
    )

    # ... (rest of your arguments) ...
    parser.add_argument("command", choices=["run", "init", "install"], help="Action to perform")
    parser.add_argument("--config", default="ai-checks.yaml", help="Path to configuration file")
    parser.add_argument("--check", help="Run only a specific check ID")
    parser.add_argument("--dry-run", action="store_true", help="Simulate execution without calling AI APIs")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    parser.add_argument("--dump", action="store_true", help="Save the full AI request prompt to .aireview/debug/")
    parser.add_argument("--context-file", help="Override context with content from a specific file")
    parser.add_argument("--commit", help="Run checks on a specific commit SHA")
    parser.add_argument("--force", action="store_true", help="Ignore [skip-ai] tags in commit messages")

    args = parser.parse_args()

    setup_logging(args.verbose)
    load_environment()
    check_dependencies()

    if args.command == "install":
        install_hook()
        return

    loader = ConfigLoader()

    if args.command == "init":
        loader.load(args.config)
        logger.info(f"Config initialized: {args.config}")
        return

    # --- LOGIC START ---

    # 1. Determine Git Target (Req 3)
    # If run via hook, env var is set. If run via CLI --commit, we set it.
    target_range = os.environ.get("AI_DIFF_TARGET", "--cached")

    if args.commit:
        # Target the specific commit (changes between parent and commit)
        target_range = f"{args.commit}^..{args.commit}"
        os.environ["AI_DIFF_TARGET"] = target_range
        logger.info(f"Targeting specific commit: {args.commit}")

    # 2. Check Skip Logic (Req 4)
    inspector = GitInspector()
    if not args.force and inspector.should_skip(target_range):
        print("⏭️  Skipping AI Review: '[skip-ai]' found in commit messages.")
        sys.exit(0)

    # 3. Load Manual Context (Req 2)
    manual_context = None
    if args.context_file:
        if not os.path.exists(args.context_file):
            logger.error(f"Context file not found: {args.context_file}")
            sys.exit(1)
        try:
            with open(args.context_file, 'r', encoding='utf-8') as f:
                manual_context = f.read()
        except Exception as e:
            logger.error(f"Failed to read context file: {e}")
            sys.exit(1)

    try:
        config = loader.load(args.config)
    except ConfigError as e:
        logger.critical(f"Configuration Error: {e}")
        sys.exit(1)

    # 4. Setup Services
    provider_factory = ProviderFactory(is_dry_run=args.dry_run)
    runner = ShellCommandRunner()
    debugger = Debugger(enabled=args.dump or args.verbose) # Req 1

    # Inject Debugger
    engine = ReviewEngine(config, runner, provider_factory, debugger)

    checks = [c for c in config.checks if c.id == args.check] if args.check else config.checks

    if not checks:
        logger.error(f"No checks found matching '{args.check}'" if args.check else "No checks defined in config.")
        sys.exit(1)

    print("\n🤖 AI Code Review\n")

    success = True
    for check in checks:
        # Pass manual context if present
        if not engine.run_check(check.id, override_context=manual_context):
            success = False

    if not success:
        print("❌ Review Failed. Please fix the issues above.")
        sys.exit(1)

    print("✅ All checks passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()