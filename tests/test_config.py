"""Tests for config.py."""

from pathlib import Path

import pytest

from cambium import config


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
