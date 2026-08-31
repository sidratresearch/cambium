"""Definition and helper functions for the abstract Stage class."""

import importlib
import logging
from pathlib import Path
from typing import Any, Literal

from click import ClickException, UsageError
from pydantic import BaseModel, ValidationError

from .tree import TreeSpan

"""
When adding a new built-in stage, add it to builtin_stages/__init__.py,
and add documentation to docs/builtin_stages.md

In general if you're adding a new stage
- overwrite __init__ if you:
    - have a stage config (also write a model class),
    - need to set required stages/runs_before/runs_after, or
    - need to store data in instance variables (prior to the tree_hook)
- overwrite tree_hook()
- overwrite any of pre_hook(), transform(), post_hook()
- overwrite the initialize and finalize functions for each hook as needed
"""


class StageConfig(BaseModel, extra="forbid"):
    """The default stage config is empty, and it is an error to provide entries."""

    ...


class Stage:
    """Base class for Cambium stages.

    A `Stage` is a set of functions that do the heavy lifting of Cambium. Stages are
    requested in the configuration, and run by the `TreeSpan` object. See developer
    documentation for additional information on how stages should be structured
    and used.
    """

    def __init__(self, config_dict: dict[str, Any]) -> None:
        self.config = StageConfig.model_validate(config_dict)
        """Validated configuration"""

        self.requires: list[str] = []
        """Other stages that must also be present, unordered"""

        self.runs_after: list[str] = []
        """Names of any stages which, if present, should come *earlier* in
        the list than this one"""

        self.runs_before: list[str] = []
        """Names of any stages which, if present, should come *later* in
        the list than this one"""

    # Private Utility Functions

    def _register_hook(
        self,
        leaf_uuid: str,
        tree: TreeSpan,
        hook_type: Literal["pre_hooks", "post_hooks", "transforms"],
    ) -> None:
        """Add this stage to the list of hooks for a given leaf."""
        tree.leaves["hooks"][leaf_uuid][hook_type].append(self.__class__.__name__)

    def _set_css_include(self, path: Path, leaf_uuid: str, tree: TreeSpan) -> None:
        """Set a path to a CSS file which will be imported as a stylesheet.

        The path should be given relative to the stage's `static` directory.
        """
        stage_name = self.__class__.__name__
        path_from_build = f"static/_cambium/{stage_name}" / path
        tree.leaves["metadata"][leaf_uuid].stage_metadata[stage_name][
            "cambium_css"
        ] = path_from_build

    def _set_js_include(self, path: Path, leaf_uuid: str, tree: TreeSpan) -> None:
        """Set a path to a JS file which will be imported as a module.

        The path should be given relative to the stage's `static` directory.
        """
        stage_name = self.__class__.__name__
        path_from_build = f"static/_cambium/{stage_name}" / path
        tree.leaves["metadata"][leaf_uuid].stage_metadata[stage_name][
            "cambium_js"
        ] = path_from_build

    def _set_leaf_metadata(
        self, metadata_name: str, metadata_value: Any, leaf_uuid: str, tree: TreeSpan
    ) -> None:
        """Helper function to set stage-specific metadata."""
        tree.leaves["metadata"][leaf_uuid].stage_metadata[self.__class__.__name__][
            metadata_name
        ] = metadata_value

    def _get_leaf_metadata(
        self,
        metadata_name: str,
        leaf_uuid: str,
        tree: TreeSpan,
        metadata_provider: str | None = None,
    ) -> Any:
        """Helper function to fetch metadata for a leaf.

        By default this function searches the metadata associated with this stage,
        passing `metadata_provider = "cambium"` accesses Cambium-provided metadata

        `metadata_provider` can also be passed the (string) class name of another
        stage, to access metadata set by another stage
        """
        leaf_metadata = tree.leaves["metadata"][leaf_uuid]

        if metadata_provider == "cambium":
            # accessing default metadata
            return getattr(leaf_metadata, metadata_name)

        if metadata_provider is None:
            # accessing own metadata
            metadata_provider = self.__class__.__name__

        return leaf_metadata.stage_metadata[metadata_provider][metadata_name]

    def add_leaf(
        self,
        initial_path: Path,
        tree: TreeSpan,
        final_path: Path | None = None,
    ) -> str:
        """Add a new leaf to the tree.

        Note that if you're doing this while iterating through
        tree.leaves["uuids"] you will likely encounter "RuntimeError: deque
        mutated during iteration". If you *don't* want to iterate over
        the new leaves, you can freeze the deque before iteration by doing
        `for leaf_uuid in list(tree.leaves["uuids"])`. If you *do* want to
        include the new leaves, use a while loop instead.
        """
        if final_path is None:
            final_path = initial_path

        prefixed_initial_path = (
            tree.config.stage_leaf_prefix / self.__class__.__name__ / initial_path
        )
        return tree._add_leaf(prefixed_initial_path, final_path=final_path)

    # --------------------------------------------------------------------#
    #                             Tree Hook                               #
    # --------------------------------------------------------------------#

    def tree_hook(self, tree: TreeSpan) -> None:
        """Required "setup" function for a Stage.

        Function to run which can modify the tree structure, adding and removing
        leaves and directories

        Function should also modify each leaf to add itself to the list of pre-hooks,
        transforms, and post-hooks as necessary

        Because tree hooks don't edit the contents of any file, they should not
        modify leaf.latest_path

        the tree_hook method is required because it is the function that registers
        the Stage into the pre/transform/post hooks for a leaf, and therefore if
        the tree_hook is not run, nothing else will be either
        """
        raise NotImplementedError()

    # --------------------------------------------------------------------#
    #                              Pre-Hook                               #
    # --------------------------------------------------------------------#

    def pre_hook_initialize(self, tree: TreeSpan) -> None:
        """Function to run once, prior to running the pre-hook over all leaves."""
        pass

    def pre_hook(self, leaf_uuid: str, tree: TreeSpan) -> None:
        """Function run on a single leaf, prior to any major transformations.

        This function can write to temporary directories
        It can write updated versions of the leaf content (e.g., parse custom markdown
        syntax), or other meta content (e.g., markdown headers)
        """
        raise NotImplementedError("pre_hook is not defined on this stage")

    def pre_hook_finalize(self, tree: TreeSpan) -> None:
        """Function called after the pre-hook is run on all leaves."""
        pass

    # --------------------------------------------------------------------#
    #                           Transform Hook                            #
    # --------------------------------------------------------------------#

    def transform_initialize(self, tree: TreeSpan) -> None:
        """Function to run once, prior to running the transform over all leaves."""
        pass

    def transform(self, leaf_uuid: str, tree: TreeSpan) -> None:
        """Function run on a single leaf, applying a major transformation (md -> html).

        This function can write to temporary directories
        It can write updated versions of the leaf content (like the new HTML),
        or other meta content (e.g., markdown headers). It probably shouldn't be
        writing other meta content, that should be a pre or post hook, but writing
        guardrails for that seems overkill
        """
        raise NotImplementedError("transform is not defined on this stage")

    def transform_finalize(self, tree: TreeSpan) -> None:
        """Function called after the transform is run on all leaves."""
        pass

    # --------------------------------------------------------------------#
    #                             Post-Hook                               #
    # --------------------------------------------------------------------#

    def post_hook_initialize(self, tree: TreeSpan) -> None:
        """Function to run once, prior to running the post-hook over all leaves."""
        pass

    def post_hook(self, leaf_uuid: str, tree: TreeSpan) -> None:
        """Function run on a single leaf, after any major transformations.

        This function can write to and read from temporary directories
        It can write updated versions of the leaf content (e.g., parse custom markdown
        syntax), or other meta content (e.g., markdown headers). It may want to read
        information that was written by this Stage's `pre_hook`
        """
        raise NotImplementedError("post_hook is not defined on this stage")

    def post_hook_finalize(self, tree: TreeSpan) -> None:
        """Function called after the post-hook is run on all leaves."""
        pass


def populate_stage_dict(
    stage_list: list[str],
    stage_config: dict[str, dict[str, Any]],
    logger: logging.Logger,
) -> dict[str, Stage]:
    """Importing Built-in Stages and compiling all Stages available to Cambium.

    Raises AssertionError if requested stages are missing, and ValidationError
    if the stage configuration is incorrect.
    """
    # TODO: AssertionErrors raised here and below raise a typer.BadParameter, which prints "Invalid value"
    # Should consider doing some custom errors or something?

    from . import builtin_stages  # noqa: F401

    for i, stage_name in enumerate(stage_list):
        if stage_name in builtin_stages.__all__:
            continue

        if "." in stage_name:
            import_string, new_name = stage_name.rsplit(".", maxsplit=1)
            stage_list[i] = new_name
            try:
                # test importing the stage
                _ = getattr(importlib.import_module(import_string), new_name)
            except AttributeError as e:
                raise ClickException(
                    f"Error importing requested stage {stage_name}: {e}"
                )

        else:
            raise UsageError(
                f"Requested stage `{stage_name}` is not a Cambium builtin. "
                f"If this is an external stage, try `<package name>.{stage_name}`."
            )

    stage_dict: dict[str, Stage] = {}

    # Getting all subclasses of Stages
    all_subclasses = Stage.__subclasses__()

    # Adding stages to stage_dict if they're in the stage list:
    for tmp_stage in all_subclasses:
        if tmp_stage.__name__ in stage_list:

            try:
                if tmp_stage.__name__ in stage_config:
                    initialized_stage = tmp_stage(stage_config[tmp_stage.__name__])
                else:
                    initialized_stage = tmp_stage({})
            except ValidationError as e:
                # TODO: see what traceback looks like here
                logger.error(
                    f"Error validating configuration for stage `{tmp_stage.__name__}`"
                )
                raise e

            stage_dict[tmp_stage.__name__] = initialized_stage

    # error if any stages requested in the config are missing
    for requested in stage_list:
        assert requested in stage_dict, f"Requested stage `{requested}` was not found."

    # re-order the dictionary to match the user-provided list
    stage_dict = {name: stage_dict[name] for name in stage_list}

    verify_stage_dict(stage_dict)

    return stage_dict


def verify_stage_dict(stage_dict: dict[str, Stage]) -> None:
    """Verify stage dependencies and ordering.

    Raises AssertionError if there are issues.
    """
    # ensure that any stages with dependencies are satisfied
    for name, instance in stage_dict.items():
        for required_stage in instance.requires:
            assert (
                required_stage in stage_dict
            ), f"Stage `{name}` requires stage `{required_stage}` which is not in config"

    # ensure ordering requirements are met
    stage_order = list(stage_dict.keys())
    for i, (name, instance) in enumerate(stage_dict.items()):

        for before in instance.runs_after:
            if before in stage_order:
                before_index = stage_order.index(before)
                assert (
                    before_index < i
                ), f"Stage {name} needs to be after {before} in the stage list"

        for after in instance.runs_before:
            if after in stage_order:
                after_index = stage_order.index(after)
                assert (
                    after_index > i
                ), f"{name} needs to be before {after} in the stage list"
