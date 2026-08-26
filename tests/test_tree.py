"""Tests for tree.py."""

from pathlib import Path

import pytest

from cambium import tree
from tests.test_config import default_configuration


def _prepare_filesystem(root_directory: Path, to_create: list[str]) -> None:
    directories_to_create, files_to_create = [], []
    for s in to_create:
        if s.endswith("/"):
            directories_to_create.append(s)
        else:
            files_to_create.append(s)

    for d in directories_to_create:
        (root_directory / d).mkdir(parents=True)
    for f in files_to_create:
        (root_directory / f).parent.mkdir(parents=True, exist_ok=True)
        (root_directory / f).touch()


@pytest.mark.parametrize(
    ("ignore_lists", "create", "expect"),
    [
        # most basic execution
        (None, ["a/1.txt", "2.txt", "b/"], ["a/", "a/1.txt", "2.txt", "b/"]),
        # ignore top-level static/ only
        (
            None,
            ["a/1.txt", "2.txt", "b/", "static/ignored", "c/static/collected"],
            ["a/", "a/1.txt", "2.txt", "b/", "c/", "c/static/", "c/static/collected"],
        ),
        # test default ignores
        (
            default_configuration().ignore_lists,
            [
                ".hidden-file",
                "a/1/.hidden-file",
                ".hidden-directory/",
                "a/1/.hidden-directory/",
                ".hidden-directory/2.txt",
                ".hidden-directory/.hidden-file",
                ".cambium/config.yaml",
                "src/__pycache__/code",
                "a/3.txt",
                "a/3.txt~",
            ],
            ["a/", "a/1/", "src/", "a/3.txt"],
        ),
    ],
)
def test_walk_directory_tree(
    tmp_path: Path,
    ignore_lists: dict[str, list[str]] | None,
    create: list[str],
    expect: list[str],
) -> None:
    """Test file collection and filtering."""
    # prepare filesystem
    root_directory = tmp_path
    _prepare_filesystem(root_directory, create)

    # organize expected results
    expect_directories, expect_files = [], []
    for s in expect:
        if s.endswith("/"):
            expect_directories.append(s[:-1])
        else:
            expect_files.append(s)

    # walk the filesestem
    found_directories_paths, found_files_paths = tree.walk_directory_tree(
        root_directory, ignore_lists
    )

    # compare results
    found_directories = [str(d) for d in found_directories_paths]
    found_files = [str(f) for f in found_files_paths]

    assert sorted(found_files) == sorted(expect_files)
    assert sorted(found_directories) == sorted(expect_directories)
