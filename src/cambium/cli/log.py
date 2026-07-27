"""
Configure logging for Cambium.

The `init_logging` function is only called in `cli.py`
"""

import logging


def init_logging() -> logging.Logger:
    """Function to call once, returns the top-level Cambium logger.

    Module-specific loggers are children of this logger
    For this to work, the first logger needs to be set up with the name "cambium"
    Then, all modules (which have names "cambium.<<something>>") will inherit
    configuration
    """
    root_logger = logging.getLogger("cambium")
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(levelname)s: %(message)s [%(name)s]")
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    return root_logger


def get_loglevel(level_str: str, verbosity_count: int) -> int:
    """Get a numeric log level combining config file and CLI values."""
    config_level: int = logging.getLevelNamesMapping()[level_str]

    if verbosity_count == 0:
        return config_level

    adjustment = -10 * verbosity_count
    new_level = config_level + adjustment
    return max(10, new_level)
