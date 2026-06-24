"""Cambium Configuration File Handling."""

from __future__ import annotations

import logging
import re
import tempfile
from pathlib import Path
from typing import Any, Literal, Optional

import yaml
from pydantic import BaseModel

from . import __version__
from .stage import populating_stage_dict

# At runtime of this file the log level has not been set
# So by default, only warnings and errors are shown
logger = logging.getLogger(__name__)


builtin_paths_to_ignore: list[str] = [
    "/.cambium",
    ".*",
    "__pycache__",
]
"""Built-in Cambium Directories to Ignore"""


current_config: Optional[WorkingConfiguration] = None
"""Globally importable reference to the mutable runtime configuration."""


root_directory_type = Optional[str]
build_directory_type = Optional[str]


class CLIConfiguration(BaseModel):
    """Validation for config options that can be set on the command line.

    This class does no processing, only validates types which are later used
    by WorkingConfiguration.
    """

    root_directory: build_directory_type = None
    build_directory: build_directory_type = None
    dev_server: Optional[bool] = False


class FileConfiguration(BaseModel):
    """Cambium Configuration Object.

    Contains all input cambium configuration parameters that can be set in
    the config file.

    This class does no processing, only validates types which are later used
    by WorkingConfiguration.
    """

    root_directory: root_directory_type = "."
    "Root Directory of Content"

    build_directory: build_directory_type = "_build/"
    "Build Directory of Output"

    paths_to_ignore: Optional[list[str]] = []
    "List of Files and Directories to Ignore"

    protected_build_paths: Optional[list[str]] = []
    "List of directories/filenames that should *not* appear in the output directory"

    extensions_to_ignore: Optional[list[str]] = []
    "File Extensions to Ignore"

    logging_level: Optional[
        Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    ] = "INFO"

    stages: Optional[list[str]] = [
        "IdentifyMetadata",
        "TransformMarkdown",
        "EnsureIndexPages",
        "TemplateMarkdown",
        # "URLEncodeFilenames", # remove from default until relative paths are handled
        "PagefindSearch",
        "CheckLinks",
    ]
    "Ordered List of Stages to Use"

    stage_config: Optional[dict[str, dict[str, Any]]] = {}
    "Configuration for specific stages, passed to the Stage constructor"

    max_leaves: Optional[int] = 10_000
    "Maximum Number of Leaves"

    site_name: Optional[str] = "Cambium Site"
    "The Name of the Cambium Site"

    theme: Optional[str] = "default"
    """Builtin Theme to Use"""


class MergedConfiguration(FileConfiguration, CLIConfiguration):
    """Merging of CLI and file config options.

    Used to provide typing to this combination of options for when they are
    passed to the WorkingConfiguration.
    """

    pass


class WorkingConfiguration:
    """The Internal Working Cambium Configuration Object.

    Contains all working configurations parameters, resolved to their appropriate
    location for a Cambium Run
    """

    ignore_lists: dict[str, list[str]] = {
        "extensions": [],
        "globs": [],  # Change this to original: python-ified for better logging?
        "paths": [],
        "names": [],
    }

    input_config: Optional[FileConfiguration] = None

    def __init__(self, input_config: Optional[MergedConfiguration] = None) -> None:

        # Setting Temporary Directory
        self.setup_tmp_dir()

        # Setting Input Configuration if set, otherwise use default:
        if input_config is not None:
            self.input_config = input_config
        else:
            self.input_config = FileConfiguration()

        # Creating Path object for root directory and testing
        self.root_dir = Path(self.input_config.root_directory)
        assert (
            self.root_dir.exists()
        ), f"The specified root directory, {self.root_dir} does not exist"

        # Creating Path object for build directory
        self.build_dir = Path(self.input_config.build_directory)

        # Populating Ignore Lists
        self.populate_ignore_lists()

        # Populate lists of protected paths
        self.protected_build_paths = sort_user_paths(
            self.input_config.protected_build_paths
        )

        # Importing and Compiling Stages
        self.stages = self.input_config.stages
        self.stage_dict = populating_stage_dict(
            self.stages, self.input_config.stage_config, logger
        )

        # Save lists of theme directories
        self.ordered_theme_directories = [
            self.root_dir / ".cambium/theme",
            Path(__file__).parent / f"themes/{self.input_config.theme}",
        ]
        self.stage_theme_directories = {"static": [], "templates": []}

        # Exposing Simple Parameters (that require no additional processing)
        self.max_leaves = self.input_config.max_leaves
        self.logging_level = self.input_config.logging_level
        self.site_name = self.input_config.site_name
        self.dev_server = self.input_config.dev_server

    def __del__(self) -> None:
        """Clean up All Lingering Directories."""
        # Cleaning up temporary directory
        self.tmp_dir_obj.cleanup()

    def __repr__(self) -> str:
        return f"""Cambium Working Configuration:\nTemporary Directory Path: {self.tmp_dir}"""

    def setup_tmp_dir(self) -> None:
        """Create and save references to a temporary directory."""
        self.tmp_dir_obj = tempfile.TemporaryDirectory(prefix="cambium_")
        self.tmp_dir = Path(self.tmp_dir_obj.name)

    def populate_ignore_lists(self) -> None:
        """Combining ignore lists and putting in appropriate dictionary."""
        # Combining Defaults and Input Configuration
        tmp_ignore_set: set[str] = {"/" + str(self.build_dir)}

        global builtin_paths_to_ignore

        for ignore_entry in builtin_paths_to_ignore:
            tmp_ignore_set.add(ignore_entry)

        for ignore_entry in self.input_config.paths_to_ignore:
            tmp_ignore_set.add(ignore_entry)

        sorted_entries = sort_user_paths(tmp_ignore_set)
        self.ignore_lists["globs"] = sorted_entries["globs"]
        self.ignore_lists["paths"] = sorted_entries["paths"]
        self.ignore_lists["names"] = sorted_entries["names"]

        # Adding Extensions to ignore:
        self.ignore_lists["extensions"] = (
            self.ignore_lists["extensions"] + self.input_config.extensions_to_ignore
        )

        # Removing periods if they exist on extensions
        for i, ext_str in enumerate(self.ignore_lists["extensions"]):
            if ext_str.startswith("."):
                self.ignore_lists["extensions"][i] = ext_str[1:]


def initialize_configuration(
    yaml_dict: dict[str, Any], cli_dict: dict[str, Any]
) -> None:
    """Initialize the current configuration for a Cambium run.

    Parameters
    ----------
    yaml_dict : dict[str,Any]
        Dictionary of values read from a config file
    cli_dict : dict[str,Any]
        Dictionary of values passed on the command line
    """
    validated_yaml = FileConfiguration(**yaml_dict)
    validated_cli = CLIConfiguration(**cli_dict)

    # combine the file and cli options, where CLI options are overrides
    merged_validated = {
        **validated_yaml.model_dump(),
        **{k: v for k, v in validated_cli.model_dump().items() if v is not None},
    }
    merged_config = MergedConfiguration(**merged_validated)

    global current_config
    current_config = WorkingConfiguration(merged_config)


def read_input_configuration(
    cli_path_loc: Optional[str | Path] = None,
) -> dict[str, Any]:
    """Read input configuration from a file, if one exists.

    Parameters
    ----------
    cli_path : Optional[str | Path], optional
        Path to config file as provided on the command line, by default None

    Returns
    -------
    dict[str,Any]
        If a config file was found, return a dictionary of config values, otherwise,
        returns an empty dictionary
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
        return {}


def translate_yaml_configuration(config_path: Path) -> dict[str, Any]:
    """Read a YAML config file and return a CambiumConfiguration object.

    Parameters
    ----------
    config_path : Path
        The location of the Cambium YAML configuration file

    Returns
    -------
    dict[str,Any]
        Dictionary of values from the config file
    """
    # Opening and reading yaml config
    logger.debug(f"Reading configuration file {config_path}")
    with config_path.open() as file:
        config_yaml = yaml.safe_load(file)

    # Empty config file
    if config_yaml is None:
        logger.warning(f"Configuration file {config_path} is empty.")
        config_yaml = {}

    if not isinstance(config_yaml, dict):
        errormsg = f"Error parsing configuration file {config_path}. Expected a dictionary/mapping, got '{config_yaml}'."
        logger.error(errormsg)
        raise ValueError(errormsg)

    # Extracting required dictionary parameters from the YAML
    configuration_parameters = FileConfiguration.model_fields.keys()

    input_dict = {}

    for key in configuration_parameters:
        if key in config_yaml:
            input_dict[key] = config_yaml[key]
            del config_yaml[key]

    # Extra configuration keys
    if len(config_yaml) > 0:
        keys = ", ".join(config_yaml.keys())
        logger.warning(f"Unused configuration entries in {config_path}: {keys}")

    return input_dict


def convert_glob_string_to_regex(glob_string: str) -> str:
    """Convert glob string to regex string, escaping appropriate characters."""
    main_segment = re.escape(glob_string).replace("\\*", ".*")

    return "^" + main_segment + "$|\\/" + main_segment + "$"


def dump_default_config() -> None:
    """Print the default configuration in YAML format."""
    # TODO: how are we going to communicate the builtin_paths_to_ignore to the user?

    config_yaml = yaml.safe_dump(FileConfiguration().model_dump())
    header = "\n".join(
        [
            f"# Cambium {__version__} default configuration",
            "# Created with `cambium --dump-default-config`",
        ]
    )

    print(header + "\n\n" + config_yaml)


def sort_user_paths(path_strings: list[str]) -> dict[str, list[str]]:
    """Sort user-provided path strings into globs/paths/names."""
    result = {"globs": [], "paths": [], "names": []}
    for entry in path_strings:

        if entry[-1] == "/":
            entry = entry[:-1]

        if "*" in entry:
            result["globs"].append(convert_glob_string_to_regex(entry))
        elif entry[0] == "/":
            result["paths"].append(entry)
        else:
            result["names"].append(entry)
    return result
