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
