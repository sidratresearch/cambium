from __future__ import annotations

import re
import typing
from uuid import uuid4

if typing.TYPE_CHECKING:
    from .config import WorkingConfiguration

import os
import shutil
from collections import deque
from pathlib import Path
from typing import Callable


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

    build_directory: Path
    directories_in_build: list[Path] = []

    def __init__(self, working_config: WorkingConfiguration) -> None:
        self.config = working_config

        self.root_directory = self.config.root_dir
        self.build_directory = self.config.build_dir

        self.leaves = {
            # dictionary doesn't need to ever shrink, so long as existing entries are up-to-date
            "uuids": deque(maxlen=self.config.max_leaves),
            # never iterate over these
            "initial_path": {},
            "latest_path": {},
            "final_path": {},
            "hooks": {},
        }
        self._walk_directory_tree()

        # TODO: error collection for leaf generation
        # if there are errors in initial leaf generation, raise them now

        # run all tree hooks, passing them the entire tree structure to modify
        # initial leaves have input file = output file
        for stage in self.config.stages:
            working_config.stage_dict[stage].tree_hook(self)
            self._check_leaf_collisions()

        # between tree hooks and pre hooks we need to copy all files into a tempdir so that pre-hooks and transformers can all use latest_path as relative to temp dir
        for directory in self.directories_in_build:
            (self.config.tmp_dir / directory).mkdir()
        for leaf_uuid in self.leaves["uuids"]:
            initial_path = self.leaves["initial_path"][leaf_uuid]
            if not (self.root_directory / initial_path).is_file():
                continue
            shutil.copy(
                self.root_directory / initial_path,
                self.config.tmp_dir / initial_path,
            )

    def _walk_directory_tree(self) -> None:
        """
        Walks the tree and populates the list of directories that are cared about, as well as saving initial copies of information regarding files we care about
        """

        for current_root, directories, files in os.walk(
            self.root_directory, topdown=True
        ):
            # current_root: string starting with ./ (except on first loop, where it's ".")
            # directories: list of strings, not ending with /
            # files: list of strings

            # filter by absolute path
            for absolute_ignore in self.config.ignore_lists["paths"]:
                matcher = f".{absolute_ignore}"  # add the leading dot
                for d in directories:
                    if f"{current_root}/{d}" == matcher:
                        directories.remove(d)
                for f in files:
                    if f"{current_root}/{f}" == matcher:
                        files.remove(f)

            # filter by name
            for name in self.config.ignore_lists["names"]:
                if name in directories:
                    directories.remove(name)
                if name in files:
                    files.remove(name)

            # filter by glob
            for pattern in self.config.ignore_lists["globs"]:
                for d in directories:
                    full_path = f"{current_root}/{d}".removeprefix("./")
                    if re.match(pattern, full_path) is not None:
                        directories.remove(d)
                for f in files:
                    full_path = f"{current_root}/{f}".removeprefix("./")
                    if re.match(pattern, full_path) is not None:
                        files.remove(f)

            # filter files by ext
            for extension in self.config.ignore_lists["extensions"]:
                for f in files:
                    if f.endswith(f".{extension}"):
                        files.remove(f)

            # save dirs to list
            for d in directories:
                self.directories_in_build.append(
                    Path(f"{current_root}/{d}".removeprefix("./"))
                )

            # assign UUIDs to files
            for f in files:
                path = Path(f"{current_root}/{f}".removeprefix("./"))
                self.add_leaf(path)

    def _check_leaf_collisions(self) -> None:
        final_paths = [self.leaves["final_path"][uuid] for uuid in self.leaves["uuids"]]
        if len(final_paths) > len(set(final_paths)):
            raise ValueError("Collision in leaf output paths")

    def add_leaf(self, initial_path: Path) -> str:
        if len(self.leaves["uuids"]) == self.leaves["uuids"].maxlen:
            raise ValueError("self.leaves will drop items")

        uuid = str(uuid4())
        self.leaves["uuids"].append(uuid)
        self.leaves["initial_path"][uuid] = initial_path
        self.leaves["latest_path"][uuid] = initial_path
        self.leaves["final_path"][uuid] = initial_path
        self.leaves["hooks"][uuid] = {
            "pre_hooks": [],
            "transforms": [],
            "post_hooks": [],
        }
        return uuid

    def apply_to_leaves(self, function: Callable[[str, TreeSpan], None]) -> None:
        """
        Generic method to apply some function across all leaves.
        If we support multithreading for some operations, this is where it will happen
        Which means `function` should be thread-safe
        """
        for leaf_uuid in self.leaves["uuids"]:
            function(leaf_uuid, self)

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
        return

    def transform(self) -> None:
        """
        Iterate through each leaf, applying the Stage transforms it requests
        """
        # TODO: figure out how to work this in with apply_to_leaves
        # maybe each leaf has a method called apply_transforms?
        for leaf_uuid in self.leaves["uuids"]:
            transforms = self.leaves["hooks"][leaf_uuid]["transforms"]
            for transform_stage in transforms:
                transform_stage.transform(leaf_uuid, self)

        return

    def apply_post_hooks(self) -> None:
        """
        Iterate through each leaf and apply, in order, the post hooks that it calls for
        """
        return

    def finalize(self) -> None:
        """
        Copy final leaf versions to build, and do any other cleanup
        """

        if self.build_directory.exists():
            shutil.rmtree(self.build_directory)  # TODO: make this configurable?
        self.build_directory.mkdir()

        for directory in self.directories_in_build:
            (self.build_directory / directory).mkdir()

        for leaf_uuid in self.leaves["uuids"]:
            shutil.copy(
                self.config.tmp_dir / self.leaves["latest_path"][leaf_uuid],
                self.build_directory / self.leaves["final_path"][leaf_uuid],
            )
