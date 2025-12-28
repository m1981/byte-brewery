# File: src/aireview/utils.py

import logging
import sys
import os

logger = logging.getLogger("aireview")


def setup_logging(verbose: bool = False):
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S"
    )


def load_environment():
    """
    Loads environment variables from .env file.
    Crucial for Git Hooks which don't inherit shell profiles.
    """
    env_path = os.path.join(os.getcwd(), ".env")
    env_exists = os.path.exists(env_path)

    try:
        from dotenv import load_dotenv

        # Force load from current directory
        if env_exists:
            load_dotenv(env_path, override=True)
            logger.debug(f"Loaded .env from: {env_path}")
        else:
            # Try generic load (looks in parent dirs)
            load_dotenv()

    except ImportError:
        if env_exists:
            logger.warning("⚠️  .env file found but 'python-dotenv' is not installed.")
            logger.warning("   Run: pipx inject byte-brewery python-dotenv")
        else:
            logger.debug("python-dotenv not installed and no .env found.")

    # Debugging: Print status of keys (Redacted)
    _debug_key_status("ANTHROPIC_API_KEY")
    _debug_key_status("OPENAI_API_KEY")
    _debug_key_status("GOOGLE_API_KEY")


def _debug_key_status(key: str):
    val = os.environ.get(key)
    if val:
        masked = val[:4] + "..." + val[-4:] if len(val) > 8 else "****"
        logger.debug(f"🔑 Found {key}: {masked}")
    else:
        logger.debug(f"❌ Missing {key}")


def check_dependencies():
    try:
        import yaml
    except ImportError:
        logger.critical("❌ CRITICAL ERROR: PyYAML is missing.")
        sys.exit(1)