"""Cambium Configuration File Handling"""

from __future__ import annotations
from typing import Optional, Annotated
from pathlib import Path

from pydantic import BaseModel, FilePath

builtin_directories_to_ignore: list[str] = [".cambium", "_build", ".*", "static"]
"""Built-in Cambium Directories to Ignore"""


class CambiumConfiguration(BaseModel):
    """Cambium Configuration Object

    Contains all input cambium configuration parameters

    """

    root_directory: Optional[FilePath] = None
    "Root Directory of Content"

    paths_to_ignore: Optional[list[str]] = None
    "List of Files and Directories to Ignore"

    extensions_to_ignore: Optional[list[str]] = None
    "File Extensions to Ignore"


class WorkingConfiguration(object):
    """The Internal Working Cambrium Configuration Object

    Contains all working configurations parameters, resolved to their appropriate location for
    a Cambium Run

    """

    def __init__(self):
        pass
