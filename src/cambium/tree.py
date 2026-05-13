from __future__ import annotations

import os
from dataclasses import InitVar, dataclass
from pathlib import Path


class TreeSpan:
    """
    Create a tree structure
    Be aware of *all* of the files that cambium will touch
    Not care about files/directories that are ignored by builtin or config

    Hold information on what actions need to be taken (on treewide and/or leaf-wide scales)
        Determines these also (transformations, parsing/collecting information, copy static files, templating, etc)
    Populates "ghost" files in output directory for files that we want to exist, even if they aren't in input (index.html)
    Identify what file should be end up at "index.html" in a directory (if no index, turn README into index)

    Have information showing the final output directory structure (iterable)
    Have lookup tables to correlate [input file]->[output file] and vice versa, and [input file]->[output directory]
    Iterators to operate on every leaf (file/directory)

    """

    source_directory: Path
    leaves: list[Leaf]
    build_directory: Path
    directories_in_build: list[Path]

    def __init__(self, source_directory: Path | None = None) -> None:
        if source_directory is None:
            self.source_directory = Path(os.getcwd())
        else:
            self.source_directory = source_directory
        self.build_directory = self.source_directory / "_build"

        self.config = {
            "ignore": {"directories": ["_build/", "__pycache__"], "globs": []}
        }

        self.directories_in_build = [
            p.relative_to(self.source_directory)
            for p in self._get_directories_in_build(self.source_directory)
        ]
        # print(self.directories_in_build)

        self.leaves = []

    def _get_directories_in_build(self, parent_directory: Path) -> list[Path]:
        """
        Get a flat list of directories, which includes all (and only) what will be present in _build

        Not sure if this should a TreeSpan method or a separate utility fn that gets passed config
        """
        # get all top level directories that aren't .hidden
        non_hidden = list(parent_directory.glob("[!.]*/"))

        without_ignores = []
        for directory in non_hidden:

            # filter based on named directories to ignore
            ignore_patterns = self.config["ignore"]["directories"]
            ignored_by_directory = any(
                [directory.match(pattern) for pattern in ignore_patterns]
            )

            # TODO: add glob ignores or other patterns here

            if not ignored_by_directory:
                # save that directory, and any children
                without_ignores.append(directory)
                children = self._get_directories_in_build(directory)
                for child in children:
                    without_ignores.append(child)

        return without_ignores


@dataclass(kw_only=True)
class Leaf:
    initial_path: Path

    # post init attrs - must appear in same order as in the post init call
    source_directory: InitVar[Path]
    build_directory: InitVar[Path]

    # generated attrs
    final_path: Path | None = None
    final_directory: Path | None = None

    def __post_init__(self, source_directory: Path, build_directory: Path) -> None:
        # set the final_path depending on the type of file this is

        # set the final_directory if final_path is set

        return
