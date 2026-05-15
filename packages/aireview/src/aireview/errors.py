class CommandError(Exception):
    """Raised when a shell or internal command fails."""
    pass

class ConfigError(Exception):
    """Raised when configuration validation fails."""
    pass