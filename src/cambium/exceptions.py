"""Custom exception for Cambium."""

import sys


class CambiumError(Exception):
    """Custom exception type for Cambium.

    Enriches the message with additional information.
    """

    def __init__(self, location: str, cause: Exception | None = None) -> None:
        self.location = location
        if cause is not None:
            self.__context__ = cause

    def get_suggestion(self) -> str | None:
        """Add troubleshooting info to the exception.

        This function is intended to centralize the adding of information to exceptions
        raised lower in the stack. Rather than looking at every error at the point
        of raising, we check all errors during the conversion to a CambiumError,
        and enrich the message here.
        """
        if (
            isinstance(self.__context__, UnicodeDecodeError)
            and sys.platform == "win32"
            and not sys.flags.utf8_mode
        ):
            return "Set the environment variable PYTHONUTF8 to `1` and try again."

    def get_notes(self) -> str | None:
        """Include `Exception.add_note()` context in main message."""
        if (
            hasattr(self.__context__, "__notes__")
            and len(self.__context__.__notes__) > 0
        ):
            return ". ".join(self.__context__.__notes__)

    def __str__(self) -> str:

        # could show exception type with type(self.__context__).__name__
        string = f"Error {self.location}"

        prev_message = str(self.__context__)
        if len(prev_message) > 0:
            string = f"{string}: {prev_message}"

        notes = self.get_notes()
        if notes is not None:
            string = f"{string}. {notes}"

        suggestion = self.get_suggestion()
        if suggestion is not None:
            string = f"{string}. {suggestion}"

        return string
