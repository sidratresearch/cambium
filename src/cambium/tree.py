from __future__ import annotations

import os
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

    source_directory: Path
    leaves: deque[Leaf]
    build_directory: Path
    directories_in_build: list[Path]

    def __init__(self, source_directory: Path | None = None) -> None:
        if source_directory is None:
            self.source_directory = Path(os.getcwd())
        else:
            self.source_directory = source_directory
        self.build_directory = self.source_directory / "_build"

        self.config = {
            "ignore": {
                "directories": ["_build/", "__pycache__"],
                "globs": [],
                "filenames": [],
            },
            "pre_hooks": [],  # currently set up to be a list of Hook objects
            "post_hooks": [],  # currently set up to be a list of Hook objects
            "max_leaves": 10000,  # maximum length of leaf deque
            "tempdirs": {"transform": tempfile.TemporaryDirectory()},
        }

        self.directories_in_build = [
            p.relative_to(self.source_directory)
            for p in self._get_directories_in_build(self.source_directory)
        ]

        self.leaves = deque(maxlen=self.config["max_leaves"])
        for directory in self.directories_in_build:
            directory_leaves = self._make_leaves_from_directory(directory)
            if len(self.leaves) + len(directory_leaves) > self.leaves.maxlen:
                raise ValueError("self.leaves will drop items")
            self.leaves.extend(directory_leaves)  # appends each item

        # print("\n".join([str(l.initial_path) for l in self.leaves]))

        # deal w/ ghost index

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
            leaves.append(
                Leaf(
                    initial_path=path,
                    source_directory=self.source_directory,
                    build_directory=self.build_directory,
                    pre_hooks=self.config["pre_hooks"],
                    post_hooks=self.config["post_hooks"],
                )
            )

        return leaves

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
        """
        raise NotImplementedError()

    def transform(self) -> None:
        tempdir_name = self.config["tempdirs"]["transform"].name
        for directory in self.directories_in_build:
            (tempdir_name / directory).mkdir()

        self.apply_to_leaves(transform_markdown_leaf_to_html)
        return

    def apply_post_hooks(self) -> None:
        """
        Iterate through each leaf and apply, in order, the post hooks that it calls for
        """
        raise NotImplementedError()


class Leaf:
    """

    Attributes
    ----------
    initial_path : Path
        Passed during initialization, this stores the absolute path to the original
        version of the file
        Should be read-only
    latest_path : Path
        The absolute path to the most up-to-date version of the file. When a markdown
        file is converted to HTML, the path to a temporary .html file is put here
    final_path : Path
        The absolute path that this Leaf will result in, in the build directory
        Is this read only? or can hooks modify this? - Thinking especially if MD-to-HTML
        is a hook
    final_directory : Path
        Parent directory of final_path
    transform_markdown : bool
        True if this is a markdown file that should be parsed to HTML, false otherwise
    pre_hooks : list[str]
        Ordered list of Hook.identifier that should be applied before running the
        markdown transformation
    post_hooks : list[str]
        Ordered list of Hook.identifier that should be applied after running the
        markdown transformation
    """

    initial_path: Path

    # generated attrs
    latest_path: Path
    final_path: Path
    final_directory: Path
    transform_markdown: bool = False
    pre_hooks: list[str]
    post_hooks: list[str]

    def __init__(
        self,
        initial_path: Path,
        source_directory: Path,
        build_directory: Path,
        pre_hooks: list[Hook],
        post_hooks: list[Hook],
    ) -> None:
        self.initial_path = initial_path
        # print(f"Initializing leaf for {self.initial_path}")

        path_in_build = build_directory / self.initial_path

        # set the final_path depending on the type of file this is
        # TODO: don't do this to files in /static/
        if self.initial_path.suffix == ".md":
            # TODO: choose how to deal with .MD .markdown etc
            self.final_path = path_in_build.with_suffix(".html")
            self.transform_markdown = True
        else:
            self.final_path = path_in_build

        self.final_directory = self.final_path.parent

        # run hook conditional functions to decide if hooks should be run later on
        self.pre_hooks = [
            hook.identifier for hook in pre_hooks if hook.should_hook_run(self)
        ]
        self.post_hooks = [
            hook.identifier for hook in post_hooks if hook.should_hook_run(self)
        ]

        # print(f"\t-> {self.final_path.relative_to(build_directory)}")

        return


class Hook:
    identifier: str = ""

    def should_hook_run(self, leaf: Leaf) -> bool:
        raise NotImplementedError()

    def apply(self, leaf: Leaf, tree: TreeSpan) -> None:
        raise NotImplementedError()


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
