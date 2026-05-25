import logging
from typing import Any

from pydantic import BaseModel, ValidationError

from .tree import TreeSpan

"""
When adding a new built-in stage, add it to builtin_stages/__init__.py

In general if you're adding a new stage
- overwrite __init__ if you:
    - have a stage config (also write a model class),
    - need to set required stages, or
    - need to store data in instance variables
- overwrite tree_hook()
- overwrite any of pre_hook(), transform(), post_hook()
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

    # Private Utility Functions

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

    # Functions called by TreeSpan

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

    def pre_hook(self, leaf_uuid: str, tree: TreeSpan) -> None:
        """Function run on a single leaf, prior to any major transformations.

        This function can write to temporary directories
        It can write updated versions of the leaf content (e.g., parse custom markdown
        syntax), or other meta content (e.g., markdown headers)
        """
        raise NotImplementedError()

    def transform(self, leaf_uuid: str, tree: TreeSpan) -> None:
        """Function run on a single leaf, applying a major transformation (md -> html).

        This function can write to temporary directories
        It can write updated versions of the leaf content (like the new HTML),
        or other meta content (e.g., markdown headers). It probably shouldn't be
        writing other meta content, that should be a pre or post hook, but writing
        guardrails for that seems overkill
        """
        raise NotImplementedError()

    def post_hook(self, leaf_uuid: str, tree: TreeSpan) -> None:
        """Function run on a single leaf, after any major transformations.

        This function can write to and read from temporary directories
        It can write updated versions of the leaf content (e.g., parse custom markdown
        syntax), or other meta content (e.g., markdown headers). It may want to read
        information that was written by this Stage's `pre_hook`
        """
        raise NotImplementedError()


def populating_stage_dict(
    stage_list: list[str],
    stage_config: dict[str, dict[str, Any]],
    logger: logging.Logger,
) -> dict[str, Stage]:
    """Importing Built-in Stages and compiling all Stages available to Cambium."""
    from . import builtin_stages  # noqa: F401

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
                logger.error(
                    f"Error validating configuration for stage `{tmp_stage.__name__}`"
                )
                raise e

            stage_dict[tmp_stage.__name__] = initialized_stage

    # error if any stages requested in the config are missing
    for requested in stage_list:
        if requested not in stage_dict:
            raise ValueError(f"Requested stage `{requested}` was not found.")

    # ensure that any stages with dependencies are satisfied
    for i, (name, instance) in enumerate(stage_dict.items()):
        for required_stage in instance.requires:
            if required_stage not in stage_dict:
                raise ValueError(
                    f"Stage `{name}` requires stage `{required_stage}` which is not requested in config"
                )

    return stage_dict
