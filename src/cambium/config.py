"""Cambium Configuration File Handling"""

from __future__ import annotations
from typing import Optional, Annotated
from pathlib import Path
import tempfile

from pydantic import BaseModel, FilePath

builtin_paths_to_ignore: list[str] = [".cambium/", "_build/", ".*", "static/"]
"""Built-in Cambium Directories to Ignore"""

current_config: Optional[WorkingConfiguration] = None


class CambiumConfiguration(BaseModel):
    """Cambium Configuration Object

    Contains all input cambium configuration parameters

    """

    root_directory: Optional[str] = "."
    "Root Directory of Content"

    paths_to_ignore: Optional[list[str]] = []
    "List of Files and Directories to Ignore"

    extensions_to_ignore: Optional[list[str]] = []
    "File Extensions to Ignore"

    stages: Optional[list[str]] = ["md_transform"]
    "Ordered List of Stages to Use"

    max_leaves: Optional[int] = 10_000
    "Maximum Number of Leaves"


default_config = CambiumConfiguration()


class WorkingConfiguration(object):
    """The Internal Working Cambium Configuration Object

    Contains all working configurations parameters, resolved to their appropriate location for
    a Cambium Run

    """

    ignore_lists: dict[str, list[str]] = {
        "extensions": [],
        "globs": [],
        "paths": [],
        "files": [],
    }

    input_config: Optional[CambiumConfiguration] = None

    def __init__(self, input_config: Optional[CambiumConfiguration] = None):

        # Setting Temporary Directory
        self.tmp_dir = tempfile.TemporaryDirectory(prefix="cambium_")
        self.tmp_dir_path = Path(self.tmp_dir.name)

        # Setting Input Configuration if set, otherwise use default:
        if input_config is not None:
            self.input_config = input_config
        else:
            self.input_config = default_config

        # Populating Ignore Lists
        self.populate_ignore_lists()

    def __del__(self):
        """Clean up All Lingering Directories"""

        # Cleaning up temporary directory
        self.tmp_dir.cleanup()

    def __repr__(self):
        return f"""Cambium Working Configuration:\nTemporary Directory Path: {self.tmp_dir_path}"""

    def populate_ignore_lists(self):
        """Combining ignore lists and putting in appropriate dictionary"""

        # Combining Defaults and Input Configuration
        tmp_ignore_set: set[str] = set()

        global builtin_paths_to_ignore

        for ignore_entry in builtin_paths_to_ignore:
            tmp_ignore_set.add(ignore_entry)

        for ignore_entry in self.input_config.paths_to_ignore:
            tmp_ignore_set.add(ignore_entry)

        # Sorting through ignorable entries:
        for ignore_entry in tmp_ignore_set:
            if "*" in ignore_entry:
                self.ignore_lists["globs"].append(ignore_entry)
            elif ignore_entry[-1] == "/":
                self.ignore_lists["paths"].append(ignore_entry)
            else:
                self.ignore_lists["files"].append(ignore_entry)

        # Adding Extensions to ignore:
        self.ignore_lists["extensions"] = (
            self.ignore_lists["extensions"] + self.input_config.extensions_to_ignore
        )


def initialize_configuration(
    input_configuration: Optional[CambiumConfiguration] = None,
):
    """Initialize the current configuration for a Cambium run

    Parameters
    ----------
    input_configuration : Optional[CambiumConfiguration], optional
        The input cambium configuration, by default None
    """

    global current_config
    current_config = WorkingConfiguration(input_configuration)
