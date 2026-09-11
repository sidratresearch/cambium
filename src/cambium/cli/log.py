"""
Configure logging for Cambium.

Within Cambium `init_logging` function is only called in `cli.py`
However if it gets used in other packages we may want to move it to utils?

Worth noting that other external packages that use logging (e.g. astropy) use their
own log configuration (or lack thereof)
"""

import logging
import warnings
from typing import Any, TypeVar

from rich.console import ConsoleRenderable
from rich.logging import RichHandler
from rich.text import Text


class CambiumHandler(RichHandler):
    """Customizations to the Rich log handler which colourizes output."""

    def get_level_text(self, record: logging.LogRecord) -> Text:
        """Get the formatted text to show for the log level."""
        level_name = record.levelname
        return Text.styled(level_name, f"logging.level.{level_name.lower()}")

    def render_message(
        self, record: logging.LogRecord, message: str
    ) -> ConsoleRenderable:
        """Create a Text object to display from a log message."""
        message_text = super().render_message(record, message)

        # add the source module
        module = Text.styled(f" [{record.name}]", style="bright_black")
        return message_text + module


def init_logging(package: str) -> logging.Logger:
    """Function to call once, returns the top-level Cambium logger.

    Module-specific loggers are children of this logger
    For this to work, the first logger needs to be set up with the name "cambium"
    Then, all modules (which have names "cambium.<<something>>") will inherit
    configuration
    """
    handler = CambiumHandler(show_path=False, show_time=False)

    root_logger = logging.getLogger(package)
    root_logger.addHandler(handler)

    # also capture and format `warnings.warn()` calls
    # these should not be used in Cambium, but may be used by dependencies
    logging.captureWarnings(True)
    warnings.formatwarning = formatwarning
    warnings_logger = logging.getLogger("py.warnings")
    warnings_logger.addHandler(handler)

    return root_logger


def formatwarning(
    message: UserWarning | Any,
    _: type[TypeVar("Category", bound=Exception)],
    filename: str,
    lineno: int,
    __: str | None = None,
) -> str:
    """Override default formatwarning function to play better with our log format.

    Unused args are "category" (class of warning) and "line" (actual line of code)
    https://docs.python.org/3/library/warnings.html#warnings.formatwarning
    """
    return f"{message!s} (warning thrown by {filename}:{lineno})"


def get_loglevel(level_str: str, verbosity_count: int) -> int:
    """Get a numeric log level combining config file and CLI values."""
    config_level: int = logging.getLevelNamesMapping()[level_str]

    if verbosity_count == 0:
        return config_level

    adjustment = -10 * verbosity_count
    new_level = config_level + adjustment
    return max(10, new_level)
