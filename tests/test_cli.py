"""Tests for cli/cli.py."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from cambium.cli import cli

runner = CliRunner()


def test_main() -> None:
    """Test the fast-exiting options of `main()`."""
    # fast exits
    result = runner.invoke(cli.app, ["--version"])
    assert result.exit_code == 0

    result = runner.invoke(cli.app, ["--dump-default-config"])
    assert result.exit_code == 0

    result = runner.invoke(cli.app, ["--dry-run"])
    assert result.exit_code == 0


def test_main_long(tmp_path: Path) -> None:
    """Actually run `cambium` on the Cambium repository."""
    # test on the Cambium source
    result = runner.invoke(cli.app, ["--build-directory", tmp_path])
    assert result.exit_code == 0


def test_dry_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that the dry run doesn't create the build dir."""
    monkeypatch.chdir(tmp_path)
    build_directory = "_build"
    cli.main(
        dry_run=True, root_directory=str(tmp_path), build_directory=build_directory
    )
    assert not (tmp_path / build_directory).exists()
