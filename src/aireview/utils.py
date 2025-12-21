import logging
import sys

logger = logging.getLogger("aireview")

def setup_logging(verbose: bool = False):
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S"
    )

def load_environment():
    try:
        from dotenv import load_dotenv
        load_dotenv()
        logger.debug("Loaded environment variables from .env")
    except ImportError:
        logger.debug("python-dotenv not installed. Skipping .env file loading.")

def check_dependencies():
    try:
        import yaml
    except ImportError:
        logger.critical("❌ CRITICAL ERROR: PyYAML is missing.")
        sys.exit(1)