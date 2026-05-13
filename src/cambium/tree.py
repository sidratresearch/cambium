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

    def __init__(self, source_directory: Path | None = None) -> None:
        if source_directory is None:
            self.source_directory = Path(os.getcwd())
        else:
            self.source_directory = source_directory
        self.build_directory = self.source_directory / "_build"

        leaf_paths = get_leaf_paths(self.source_directory)
        self.leaves = [
            Leaf(
                initial_path=path,
                source_directory=self.source_directory,
                build_directory=self.build_directory,
            )
            for path in leaf_paths
        ]

def get_leaf_paths(directory: Path) -> list[Path]:
    """Recursively searches `directory` and returns a list of all filepaths that
    cambium should be aware of

    Parameters
    ----------
    directory : Path


    Returns
    -------
    list[Path]
    """
    paths = []
    for child in directory.iterdir():
        # TODO: add tests for this, and make extensible
        if (child.name == "_build") and (child.is_dir()):
            continue
        if child.name.startswith(".") and not child.name == ".cambium":
            continue

        if child.is_dir():
            for subchild in get_leaf_paths(child):
                paths.append(subchild)
        else:
            paths.append(child)

    return paths


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
