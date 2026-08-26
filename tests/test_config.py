"""Tests for config.py."""

from copy import deepcopy
from pathlib import Path

import pytest

from cambium import config
from cambium.builtin_stages.utils import path_matches_patterns
from cambium.cli import cli


def default_configuration() -> None:
    """Return a copy of the default configuration object."""
    yaml_config = config.FileConfiguration().model_dump()
    config.initialize_configuration(yaml_config, cli.CLI_DEFAULTS)
    return deepcopy(config.current_config)


def test_default_config() -> None:
    """Ensure that the default configuration is valid."""
    default_configuration()


@pytest.mark.parametrize(
    ("filename", "contents"),
    [
        ("empty", ""),
        ("json", "{'one':True}"),
        pytest.param(
            "not_yaml",
            "logging_level = INFO",
            marks=pytest.mark.xfail(reason="Invalid YAML parses as a string"),
        ),
        pytest.param(
            "bad_input",
            "logging_level: nothing",
            marks=pytest.mark.xfail(reason="Invalid value for config item"),
        ),
    ],
)
def test_bad_config_file(tmp_path: Path, filename: str, contents: str) -> None:
    """Test config file parsing."""
    config_file = tmp_path / filename
    config_file.write_text(contents)
    config_dict = config.translate_yaml_configuration(config_file)
    config.initialize_configuration(config_dict, cli.CLI_DEFAULTS)


def test_merge_config(tmp_path: Path) -> None:
    """Tests regarding CLI configuration precedence."""
    yaml_config = {"root_directory": "./unused"}
    cli_config = {"root_directory": str(tmp_path), "build_directory": None}

    config.initialize_configuration(yaml_config, {**cli.CLI_DEFAULTS, **cli_config})

    assert str(config.current_config.root_dir) == cli_config["root_directory"]

    assert config.current_config.build_dir is not None


def test_root_build(tmp_path: Path) -> None:
    """Tests related to the root and build directories."""
    config_path = None

    verbosity = 0

    # build directory always returns absolute
    cli_build = "../../_build/"
    cli.setup_config(
        config_path, {**cli.CLI_DEFAULTS, "build_directory": cli_build}, verbosity
    )
    assert config.current_config.build_dir.is_absolute()
    # when given relative, build should be relative to root
    expected_build = (config.current_config.root_dir / cli_build).resolve()
    assert config.current_config.build_dir == expected_build

    # root directory does not exist
    with pytest.raises(AssertionError):
        cli.setup_config(
            config_path,
            {**cli.CLI_DEFAULTS, "root_directory": str(tmp_path / "nonexistent")},
            verbosity,
        )

    # build directory is the same as unspecified root
    with pytest.raises(AssertionError):
        cli.setup_config(
            config_path, {**cli.CLI_DEFAULTS, "build_directory": "."}, verbosity
        )

    # build directory is the same as specified root
    with pytest.raises(AssertionError):
        cli.setup_config(
            config_path,
            {
                **cli.CLI_DEFAULTS,
                "root_directory": str(tmp_path),
                "build_directory": str(tmp_path),
            },
            verbosity,
        )


# TODO: move to test_cli.py?
def test_dry_run(tmp_path: Path) -> None:
    """Test that the dry run doesn't create the build dir."""
    build_directory = "_build"
    cli.main(
        dry_run=True, root_directory=str(tmp_path), build_directory=build_directory
    )
    assert not (tmp_path / build_directory).exists()


@pytest.mark.parametrize(
    ("pattern_str", "path_expected"),
    [
        ("bar.txt", [("bar.txt", True), ("foo/bar.txt", True)]),
        ("/bar.txt", [("bar.txt", True), ("foo/bar.txt", False)]),
        (
            "foo/bar.txt",
            [
                ("bar.txt", False),
                ("foo/bar.txt", True),
                ("baz/foo/bar.txt", False),
                ("foo/baz/bar.txt", False),
            ],
        ),
    ],
)
def test_path_matching(pattern_str: str, path_expected: list[tuple[str, bool]]) -> None:
    sorted_patterns = config.sort_user_paths([pattern_str])

    for path_str, match_expected in path_expected:
        assert (
            path_matches_patterns(Path(path_str), sorted_patterns) == match_expected
        ), f"{pattern_str=} {path_str=} {match_expected=}"
