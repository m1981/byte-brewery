import argparse
import sys
import os
import stat
import logging
from .utils import setup_logging, load_environment, check_dependencies
from .services.config_loader import ConfigLoader
from .services.runner import ShellCommandRunner
from .services.providers import ProviderFactory
from .engine import ReviewEngine

logger = logging.getLogger("aireview")


class AIProviderRouter:
    """Adapts the Factory to the AIProvider protocol expected by the Engine."""

    def __init__(self, factory: ProviderFactory):
        self.factory = factory

    def analyze(self, model: str, msg: str) -> str:
        return self.factory.get_provider(model).analyze(model, msg)

    def get_metadata(self, model: str) -> dict:
        return self.factory.get_provider(model).get_metadata(model)


def install_hook():
    if not os.path.exists(".git"):
        logger.error("Not a git repository.")
        sys.exit(1)

    hook_path = os.path.join(".git", "hooks", "pre-push")
    # Point to the module execution
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
    parser = argparse.ArgumentParser(description="AI Review Tool")
    parser.add_argument("command", choices=["run", "init", "install"], help="Action")
    parser.add_argument("--config", default="ai-checks.yaml")
    parser.add_argument("--check", help="Specific check ID")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without calling AI")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logs")

    args = parser.parse_args()

    setup_logging(args.verbose)
    load_environment()
    check_dependencies()

    if args.command == "install":
        install_hook()
        return

    # 1. Load Config (SRP: ConfigLoader)
    loader = ConfigLoader()
    if args.command == "init":
        loader.load(args.config)  # Just to trigger default creation
        logger.info(f"Config initialized: {args.config}")
        return

    config = loader.load(args.config)

    # Check for bad config pattern (Legacy warning)
    git_def = config.definitions.get('git_diff')
    if git_def and "--name-only" in git_def.cmd:
        logger.warning("⚠️  Config Warning: 'git_diff' uses '--name-only'. AI cannot see code content.")

    # 2. Setup Services (OCP: Factory)
    provider_factory = ProviderFactory(is_dry_run=args.dry_run)
    ai_router = AIProviderRouter(provider_factory)
    runner = ShellCommandRunner()

    engine = ReviewEngine(config, runner, ai_router)

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