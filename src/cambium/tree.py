from __future__ import annotations

import os
import shutil
import tempfile
from collections import deque
from pathlib import Path
from typing import Callable

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

    root_directory: Path
    leaves: deque[Leaf]
    build_directory: Path
    directories_in_build: list[Path]

    def __init__(self) -> None:

        self.config = {
            "ignore": {
                "directories": ["_build/", "__pycache__"],
                "globs": [],
                "filenames": [],
            },
            "max_leaves": 10000,  # maximum length of leaf deque
            "tempdir": tempfile.TemporaryDirectory(),
            "stages": [TransformMarkdown],  # list of Stage objects
            "root_directory": Path(os.getcwd()),  # absolute path to the input directory
        }

        self.root_directory = self.config["root_directory"]  # for now, speedy access
        self.build_directory = self.root_directory / "_build"

        self.directories_in_build = [
            p.relative_to(self.root_directory)
            for p in self._get_directories_in_build(self.root_directory)
        ]

        self.leaves = deque(maxlen=self.config["max_leaves"])
        self._add_leaves(self._make_leaves_from_directory(Path(".")))
        for directory in self.directories_in_build:
            directory_leaves = self._make_leaves_from_directory(directory)
            self._add_leaves(directory_leaves)

        # TODO: error collection for leaf generation
        # if there are errors in inital leaf generation, raise them now

        # run all tree hooks, passing them the entire tree structure to modify
        # initial leaves have input file = output file
        for stage in self.config["stages"]:
            if not stage.has_tree_hook:
                continue
            stage.tree_hook(self)

        # markdown to html tree hook changes output file path/extension where necessary
        # then ghost index.html tree hook

        # between tree hooks and pre hooks we need to copy all files into a tempdir so that pre-hooks and transformers can all use latest_path as relative to temp dir
        for directory in self.directories_in_build:
            (self.config["tempdir"].name / directory).mkdir()
        for leaf in self.leaves:
            shutil.copy(
                self.root_directory / leaf.initial_path,
                self.config["tempdir"].name / leaf.initial_path,
            )

    def _add_leaves(self, new_leaves: list[Leaf]) -> None:
        """Extend the `self.leaves` deque, with a guard on maxlen"""
        if len(self.leaves) + len(new_leaves) > self.leaves.maxlen:
            raise ValueError("self.leaves will drop items")
        self.leaves.extend(new_leaves)  # appends each item

    def _get_files(self, directory: Path) -> list[Path]:
        """
        Get a list of files that can be leaves

        Not sure if this should a TreeSpan method or a separate utility fn that gets passed config
        """
        non_hidden = [f for f in directory.glob("[!.]*") if not f.is_dir()]

        keep = []
        for file in non_hidden:
            # filter based on named files to ignore
            ignore_patterns = self.config["ignore"]["filenames"]
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
        """
        leaves = []

        # these are all relative to source directory
        directory_files = self._get_files(directory)

        for path in directory_files:
            leaves.append(Leaf(initial_path=path))

        return leaves

    def _get_directories_in_build(self, parent_directory: Path) -> list[Path]:
        """
        Get a flat list of directories, which includes all (and only) what will be present in _build

        Not sure if this should a TreeSpan method or a separate utility fn that gets passed config

        Returns absolute paths
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
                transform_stage.transform(leaf, self.config)

        # self.apply_to_leaves(transform_markdown_leaf_to_html)
        return

    def apply_post_hooks(self) -> None:
        """
        Iterate through each leaf and apply, in order, the post hooks that it calls for
        """
        raise NotImplementedError()


class Leaf:
    """

    Parameters
    ----------
    initial_path : Path
        Read-only attribute that stores the path to the original version of the file, relative to the root_directory

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
    pre_hooks : list[Stage]
        Ordered list of Stage.identifier that should be applied before running the
        markdown transformation, populated by tree hooks
        TODO: str vs Stage typing
    transforms : list[Stage]
        Ordered list of major transformations
    post_hooks : list[Stage]
        Ordered list of Stage.identifier that should be applied after running the
        markdown transformation, populated by tree hooks
    """

    def __init__(
        self,
        initial_path: Path,  # relative to root
    ) -> None:
        self.initial_path: Path = initial_path
        self.latest_path: Path = initial_path
        self.final_path: Path = initial_path

        self.pre_hooks: list[Stage] = []
        self.transforms: list[Stage] = []
        self.post_hooks: list[Stage] = []

        # TODO: status attributes for pre_hook, transform, and post_hook "chapters"
        # status can be incomplete, complete, skip, failed

        return

    @property
    def final_directory(self) -> Path:
        return self.final_path.parent


# TODO: should this class be decorated as abstract or something?
class Stage:
    identifier: str = ""
    has_tree_hook: bool = False
    has_pre_hook: bool = False
    has_transform: bool = False
    has_post_hook: bool = False

    def should_hook_run(self, leaf: Leaf) -> bool:
        raise NotImplementedError()

    @staticmethod
    def tree_hook(tree: TreeSpan) -> None:
        """
        Function to run which can modify the tree structure, adding and removing
        leaves and directories

        Function should also modify each leaf to add itself to the list of pre-hooks,
        transforms, and post-hooks as necessary

        Because tree hooks don't edit the contents of any file, they should not modify leaf.latest_path
        """
        raise NotImplementedError()

    @staticmethod
    def pre_hook(leaf: Leaf) -> None:
        """
        Function run on a single leaf, prior to any major transformations

        This function can write to temporary directories
        It can write updated versions of the leaf content (e.g., parse custom markdown
        syntax), or other meta content (e.g., markdown headers)
        """
        raise NotImplementedError()

    @staticmethod
    def transform(leaf: Leaf, working_config) -> None:
        """
        Function run on a single leaf, applying a  major transformation (md -> html)

        This function can write to temporary directories
        It can write updated versions of the leaf content (like the new HTML),
        or other meta content (e.g., markdown headers). It probably shouldn't be
        writing other meta content, that should be a pre or post hook, but writing
        guardrails for that seems overkill
        """
        raise NotImplementedError()

    @staticmethod
    def post_hook(leaf: Leaf) -> None:
        """
        Function run on a single leaf, after any major transformations

        This function can write to and read from temporary directories
        It can write updated versions of the leaf content (e.g., parse custom markdown
        syntax), or other meta content (e.g., markdown headers). It may want to read
        information that was written by this Stage's `pre_hook`
        """
        raise NotImplementedError()


class TransformMarkdown(Stage):
    identifier = "TransformMarkdown"  # can we use __name__ or something?
    has_tree_hook = True
    has_transform = True

    @staticmethod
    def tree_hook(tree: TreeSpan) -> None:
        # TODO: could refactor this to use tree.apply_to_leaves
        for leaf in tree.leaves:
            print(leaf.initial_path, leaf.transforms)
            if leaf.latest_path.parts[0] == "static":
                continue
            if leaf.latest_path.suffix.lower() != ".md":
                continue

            leaf.final_path = leaf.latest_path.with_suffix(".html")
            leaf.transforms.append(TransformMarkdown)

    @staticmethod
    def transform(leaf: Leaf, working_config) -> None:
        output_path = working_config["tempdir"].name / leaf.final_path

        markdown = (working_config["tempdir"].name / leaf.latest_path).read_text()
        html = markdown_to_html(markdown)

        output_path.write_text(html)
        leaf.latest_path = output_path  # TODO: confirm that updating references like this works as expected
        print(output_path)


def transform_markdown_leaf_to_html(leaf: Leaf, tree: TreeSpan) -> None:
    """
    Function to read a markdown leaf and write transformed HTML to a temp file
    """
    if not leaf.transform_markdown:
        return

    output_path = tree.config["tempdirs"][
        "transform"
    ].name / leaf.final_path.relative_to(tree.build_directory)

    markdown = leaf.latest_path.read_text()
    html = markdown_to_html(markdown)

    output_path.write_text(html)
    leaf.latest_path = output_path  # TODO: confirm that updating references like this works as expected
