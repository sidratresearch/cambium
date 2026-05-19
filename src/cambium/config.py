"""Cambium Configuration File Handling"""

from __future__ import annotations

import logging
import re
import tempfile
from pathlib import Path
from typing import Any, Literal, Optional

import yaml
from pydantic import BaseModel

from .stage import populating_stage_dict

logger = logging.getLogger(__name__)


builtin_paths_to_ignore: list[str] = [
    "/.cambium",
    "/_build",
    ".*",
    "__pycache__",
]
"""Built-in Cambium Directories to Ignore"""


current_config: Optional[WorkingConfiguration] = None


class CambiumConfiguration(BaseModel):
    """Cambium Configuration Object

    Contains all input cambium configuration parameters

    """

    root_directory: Optional[str] = "."
    "Root Directory of Content"

    build_directory: Optional[str] = "_build/"
    "Build Directory of Output"

    paths_to_ignore: Optional[list[str]] = []
    "List of Files and Directories to Ignore"

    extensions_to_ignore: Optional[list[str]] = []
    "File Extensions to Ignore"

    logging_level: Optional[
        Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    ] = "INFO"

    stages: Optional[list[str]] = [
        "IdentifyMetadata",
        "TransformMarkdown",
        "AddPlaceholderIndex",
        "TemplateMarkdown",
    ]
    "Ordered List of Stages to Use"

    stage_config: Optional[dict[str, dict[str, Any]]] = {}
    "Configuration for specific stages, passed to the Stage constructor"

    max_leaves: Optional[int] = 10_000
    "Maximum Number of Leaves"

    site_name: Optional[str] = "Cambium Site"
    "The Name of the Cambium Site"


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
        "names": [],
    }

    input_config: Optional[CambiumConfiguration] = None

    def __init__(self, input_config: Optional[CambiumConfiguration] = None):

        # Setting Temporary Directory
        self.tmp_dir_obj = tempfile.TemporaryDirectory(prefix="cambium_")
        self.tmp_dir = Path(self.tmp_dir_obj.name)

        # Setting Input Configuration if set, otherwise use default:
        if input_config is not None:
            self.input_config = input_config
        else:
            self.input_config = default_config

        # Populating Ignore Lists
        self.populate_ignore_lists()

        # Creating Path object for root directory and testing
        self.root_dir = Path(self.input_config.root_directory)
        assert (
            self.root_dir.exists()
        ), f"The specified root directory, {self.root_dir} does not exist"

        # Creating Path object for build directory
        self.build_dir = Path(self.input_config.build_directory)

        # Importing and Compiling Stages
        self.stages = self.input_config.stages
        self.stage_dict = populating_stage_dict(
            self.stages, self.input_config.stage_config
        )

        # Exposing Simple Parameters (that require no additional processing)
        self.max_leaves = self.input_config.max_leaves
        self.logging_level = self.input_config.logging_level
        self.site_name = self.input_config.site_name

        self.ordered_theme_directories = [
            self.root_dir / ".cambium/theme",
            Path(__file__).parent / "themes/default",
        ]

    def __del__(self):
        """Clean up All Lingering Directories"""

        # Cleaning up temporary directory
        self.tmp_dir_obj.cleanup()

    def __repr__(self):
        return f"""Cambium Working Configuration:\nTemporary Directory Path: {self.tmp_dir}"""

    def populate_ignore_lists(self):
        """Combining ignore lists and putting in appropriate dictionary"""

        # Combining Defaults and Input Configuration
        tmp_ignore_set: set[str] = set()

        global builtin_paths_to_ignore

        for ignore_entry in builtin_paths_to_ignore:
            tmp_ignore_set.add(ignore_entry)

        for ignore_entry in self.input_config.paths_to_ignore:
            tmp_ignore_set.add(ignore_entry)

        # Sorting through ignorable entries and removing trailing slash (if exists):
        for ignore_entry in tmp_ignore_set:

            if ignore_entry[-1] == "/":
                ignore_entry = ignore_entry[:-1]

            if "*" in ignore_entry:
                self.ignore_lists["globs"].append(
                    convert_glob_string_to_regex(ignore_entry)
                )
            elif ignore_entry[0] == "/":
                self.ignore_lists["paths"].append(ignore_entry)
            else:
                self.ignore_lists["names"].append(ignore_entry)

        # Adding Extensions to ignore:
        self.ignore_lists["extensions"] = (
            self.ignore_lists["extensions"] + self.input_config.extensions_to_ignore
        )

        # Removing periods if they exist on extensions
        for i, ext_str in enumerate(self.ignore_lists["extensions"]):
            if ext_str.startswith("."):
                self.ignore_lists["extensions"][i] = ext_str[1:]


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


def read_input_configuration(
    cli_path_loc: Optional[str | Path] = None,
) -> Optional[CambiumConfiguration]:
    """Attempt to read input configuration from either command line argument or
    expected default location, and return to

    Parameters
    ----------
    cli_path : Optional[str | Path], optional
        Path to config file as provided on the command line, by default None

    Returns
    -------
    Optional[CambiumConfiguration]
        If a config file was found, return a CambiumConfiguration object
    """

    config_default_path = Path(".cambium/config.yaml")

    # Attempting to read CLI provided config
    if cli_path_loc is not None:
        cli_path = Path(cli_path_loc)
        assert (
            cli_path.exists()
        ), f"Provided configuration file location {cli_path_loc} does not exist"

        return translate_yaml_configuration(cli_path)

    # Attempting to read default config path

    if config_default_path.exists():
        return translate_yaml_configuration(config_default_path)
    else:
        return None


def translate_yaml_configuration(config_path: Path) -> CambiumConfiguration:
    """Reads a YAML Configuration and Populates a CambiumConfiguration with
    the appropriate parameters

    Parameters
    ----------
    config_path : Path
        The location of the Cambium YAML configuration file

    Returns
    -------
    CambiumConfiguration
        The interpreted Cambium configuration object
    """

    # Opening and reading yaml config
    with open(config_path, "r") as file:
        config_yaml = yaml.safe_load(file)

    # Extracting required dictionary parameters from the YAML
    configuration_parameters = CambiumConfiguration.model_fields.keys()

    input_dict = {}

    for key in configuration_parameters:
        if key in config_yaml:
            input_dict[key] = config_yaml[key]

    # Creating the CambiumConfiguration object:
    return CambiumConfiguration(**input_dict)


def convert_glob_string_to_regex(glob_string: str) -> str:
    """Convert glob string to regex string, escaping appropriate characters"""

    main_segment = re.escape(glob_string).replace("\*", ".*")

    return "^" + main_segment + "$|\/" + main_segment + "$"
