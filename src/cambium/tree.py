from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from .config import WorkingConfiguration

import os
import shutil
import tempfile
from collections import defaultdict, deque
from pathlib import Path
from typing import Callable

from typing_extensions import override

from cambium.md_transform import markdown_to_html


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

    # These work as class attributes so long as we never have multiple instances of TreeSpan
    root_directory: Path
    leaves: deque[
        Leaf
    ]  # MR: So, I think this is going to be an issue -- now to do any lookups,
    # you need to essentially have the leaf in hand. Perhaps this is a deque of UUIDs and the leaves live in a dictionary
    build_directory: Path
    directories_in_build: list[Path]

    def __init__(self, working_config: WorkingConfiguration) -> None:
        self.working_config = working_config
        self.config = {
            "ignore": {
                "directories": ["_build/", "__pycache__"],
            },
            "stages": [TransformMarkdown, AddPlaceholderIndex],  # list of Stage objects
        }

        self.root_directory = self.working_config.root_dir
        self.build_directory = self.working_config.build_dir

        self.directories_in_build = [
            p.relative_to(self.root_directory)
            for p in self._get_directories_in_build(self.root_directory)
        ]

        self.leaves = deque(maxlen=self.working_config.max_leaves)
        self._add_leaves(self._make_leaves_from_directory(Path(".")))
        for directory in self.directories_in_build:
            directory_leaves = self._make_leaves_from_directory(directory)
            self._add_leaves(directory_leaves)
        self._check_leaf_collisions()

        # TODO: error collection for leaf generation
        # if there are errors in initial leaf generation, raise them now

        # run all tree hooks, passing them the entire tree structure to modify
        # initial leaves have input file = output file
        for stage in self.config["stages"]:
            working_config.stage_dict[stage].tree_hook(self)
            self._check_leaf_collisions()

        # between tree hooks and pre hooks we need to copy all files into a tempdir so that pre-hooks and transformers can all use latest_path as relative to temp dir
        for directory in self.directories_in_build:
            (self.working_config.tmp_dir / directory).mkdir()
        for leaf in self.leaves:
            if leaf.initial_path_mocked:
                continue
            shutil.copy(
                self.root_directory / leaf.initial_path,
                self.working_config.tmp_dir / leaf.initial_path,
            )

    # MR: I don't think this is supposed to be a property
    @property
    def leaves_by_final_directory(self) -> dict[Path, list[Leaf]]:
        result = defaultdict(list)
        for leaf in self.leaves:
            # TODO: do we want to do this by UUID or something so we aren't storing a second copy of every leaf in memory?
            result[leaf.final_directory].append(leaf)

        return result

    def _check_leaf_collisions(self) -> None:
        final_paths = [leaf.final_path for leaf in self.leaves]
        if len(final_paths) > len(set(final_paths)):
            raise ValueError("Collision in leaf output paths")

    def add_leaf(self, leaf: Leaf) -> None:
        self._add_leaves([leaf])
        self._check_leaf_collisions()

    def _add_leaves(self, new_leaves: list[Leaf]) -> None:
        """Extend the `self.leaves` deque, with a guard on maxlen"""
        if len(self.leaves) + len(new_leaves) > self.leaves.maxlen:
            raise ValueError("self.leaves will drop items")
        self.leaves.extend(new_leaves)  # appends each item

    def _get_leaf_files(self, directory: Path) -> list[Path]:
        """
        Get a list of files that can be leaves

        Not sure if this should a TreeSpan method or a separate utility (or staticmethod) fn that gets passed config
        """
        non_hidden = [f for f in directory.glob("[!.]*") if not f.is_dir()]

        keep = []
        for file in non_hidden:
            # filter based on named files to ignore
            ignore_patterns = self.working_config.ignore_lists["files"]
            ignored_by_filename = any(
                [file.match(pattern) for pattern in ignore_patterns]
            )

            # TODO: add glob ignores or other patterns here

            if not ignored_by_filename:
                keep.append(file)

        return keep

    def _make_leaves_from_directory(self, directory: Path) -> list[Leaf]:
        """
        Given a directory, make a Leaf out of every file in that directory

        Not sure if this should a TreeSpan method or a separate utility fn that gets passed config

        This really doesn't need to be a dedicated function
        """
        leaves = []

        # these are all relative to source directory
        directory_files = self._get_leaf_files(directory)

        for path in directory_files:
            leaves.append(Leaf(initial_path=path))

        return leaves

    def _get_directories_in_build(self, parent_directory: Path) -> list[Path]:
        """
        Get a flat list of directories, which includes all (and only) what will be present in _build

        Not sure if this should a TreeSpan method or a separate utility fn (or staticmethod) that gets passed config

        Returns absolute paths (required as it's recursive)
        """
        # get all top level directories that aren't .hidden
        non_hidden = list(parent_directory.glob("[!.]*/"))
        # MR: Deal with this now in the config

        # MR: This should just be a os.walk (to support 3.11)
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

    def apply_to_leaves(self, function: Callable[[Leaf, TreeSpan], None]) -> None:
        """
        Generic method to apply some function across all leaves.
        If we support multithreading for some operations, this is where it will happen
        Which means `function` should be thread-safe
        """
        for leaf in self.leaves:
            function(leaf, self)

    def apply_pre_hooks(self) -> None:
        """
        Iterate through each leaf and apply, in order, the pre hooks that it calls for

        If a pre-hook fails, the remaining pre-hooks for that Leaf should not be run,
        and the status indicators for transform and post-hooks should be set to skip

        If a pre-hook errors, we either
        - raise that error for that leaf immediately, OR
        - collect errors across all leaves, and raise them collectively (maybe better
            for multithreading)
        """
        raise NotImplementedError()

    def transform(self) -> None:
        """
        Iterate through each leaf, applying the Stage transforms it requests
        """
        # TODO: figure out how to work this in with apply_to_leaves
        # maybe each leaf has a method called apply_transforms?
        for leaf in self.leaves:
            for transform_stage in leaf.transforms:
                transform_stage.transform(leaf, self.working_config)

        return

    def apply_post_hooks(self) -> None:
        """
        Iterate through each leaf and apply, in order, the post hooks that it calls for
        """
        raise NotImplementedError()

    def finalize(self) -> None:
        """
        Copy final leaf versions to build, and do any other cleanup
        """

        if self.build_directory.exists():
            shutil.rmtree(self.build_directory)  # TODO: make this configurable?
        self.build_directory.mkdir()

        for directory in self.directories_in_build:
            (self.build_directory / directory).mkdir()

        for leaf in self.leaves:
            shutil.copy(
                self.working_config.tmp_dir / leaf.latest_path,
                self.build_directory / leaf.final_path,
            )


# MR: Truth be told, I'm starting to be unconvinced by leaf -- we should chat about it.
class Leaf:
    """

    Parameters
    ----------
    initial_path : Path
        Read-only attribute that stores the path to the original version of the file, relative to the root_directory
    initial_path_mocked : bool
        Flag indicating that there is no originating file (i.e., that root_directory / initial_path does not exist)
        Don't like this very much, but the other option is to make initial_path optional and deal with that

    Attributes
    ----------
    latest_path : Path
        The path to the most up-to-date version of the file. When a markdown file
        is converted to HTML, the path to a temporary .html file is put here
        WARNING This is relative to the treewide tempdir - which means that all files need to be copied into that tempdir
        Can be modified by hooks
    final_path : Path
        Stores the path to the final version of the file, relative to the build_directory
        Should only be modified by Tree Hooks
    final_directory : Path
        Parent directory of final_path
    pre_hooks : list[[typeStage]]
        Ordered list of Stage.identifier that should be applied before running the
        markdown transformation, populated by tree hooks
        TODO: str vs Stage typing
    transforms : list[[typeStage]]
        Ordered list of major transformations
    post_hooks : list[type[Stage]]
        Ordered list of Stage.identifier that should be applied after running the
        markdown transformation, populated by tree hooks
    """

    def __init__(
        self,
        initial_path: Path,  # relative to root
        initial_path_mocked: bool = False,
    ) -> None:
        self._initial_path: Path = initial_path
        self._initial_path_mocked: bool = initial_path_mocked

        self.latest_path: Path = initial_path
        # TODO: maybe final_path should be read-only and to change it you have to make a new leaf?
        self.final_path: Path = initial_path

        self.pre_hooks: list[type[Stage]] = []
        self.transforms: list[type[Stage]] = []
        self.post_hooks: list[type[Stage]] = []

        # TODO: status attributes for pre_hook, transform, and post_hook "chapters"
        # status can be incomplete, complete, skip, failed

        return

    # MR: No reason for these to be properties. If we don't intend to change the setters or getters, we shouldn't use property
    @property
    def initial_path(self) -> Path:
        """Path of originating file, relative to TreeSpan.root_directory"""
        return self._initial_path

    @property
    def initial_path_mocked(self) -> bool:
        """Whether `Leaf.initial_path` has been "mocked" (doesn't exist)"""
        return self._initial_path_mocked

    @property
    def final_directory(self) -> Path:
        """Parent directory of `Leaf.final_path`"""
        return self.final_path.parent
