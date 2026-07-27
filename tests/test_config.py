"""Tests for config.py."""

from pathlib import Path

import pytest

from cambium import cli, config


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

    config_file = tmp_path / filename
    config_file.write_text(contents)
    config_dict = config.translate_yaml_configuration(config_file)
    config.initialize_configuration(config_dict, {})


def test_merge_config(tmp_path: Path) -> None:
    yaml_config = {"root_directory": "./unused"}
    cli_config = {"root_directory": str(tmp_path), "build_directory": None}

    config.initialize_configuration(yaml_config, cli_config)

    assert str(config.current_config.root_dir) == cli_config["root_directory"]

    assert config.current_config.build_dir is not None


def test_root_build(tmp_path: Path) -> None:
    """Tests related to the root and build directories."""
    config_path = None
    min_cli_config = {
        "dev_server": False,
        "dev_server_port": 8000,
        "dev_server_interval": 1,
    }
    verbosity = 0

    # build directory always returns absolute
    cli_build = "../../_build/"
    cli.setup_config(
        config_path, {"build_directory": cli_build, **min_cli_config}, verbosity
    )
    assert config.current_config.build_dir.is_absolute()
    # when given relative, build should be relative to root
    expected_build = (config.current_config.root_dir / cli_build).resolve()
    assert config.current_config.build_dir == expected_build

    # root directory does not exist
    with pytest.raises(AssertionError):
        cli.setup_config(
            config_path,
            {"root_directory": str(tmp_path / "nonexistent"), **min_cli_config},
            verbosity,
        )

    # build directory is the same as unspecified root
    with pytest.raises(AssertionError):
        cli.setup_config(
            config_path, {"build_directory": ".", **min_cli_config}, verbosity
        )

    # build directory is the same as specified root
    with pytest.raises(AssertionError):
        cli.setup_config(
            config_path,
            {
                "root_directory": str(tmp_path),
                "build_directory": str(tmp_path),
                **min_cli_config,
            },
            verbosity,
        )
