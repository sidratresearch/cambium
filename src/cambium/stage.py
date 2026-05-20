from typing import Any

from .tree import TreeSpan


class Stage:

    def tree_hook(self, tree: TreeSpan) -> None:
        """
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
        """
        Function run on a single leaf, prior to any major transformations

        This function can write to temporary directories
        It can write updated versions of the leaf content (e.g., parse custom markdown
        syntax), or other meta content (e.g., markdown headers)
        """
        raise NotImplementedError()

    def transform(self, leaf_uuid: str, tree: TreeSpan) -> None:
        """
        Function run on a single leaf, applying a  major transformation (md -> html)

        This function can write to temporary directories
        It can write updated versions of the leaf content (like the new HTML),
        or other meta content (e.g., markdown headers). It probably shouldn't be
        writing other meta content, that should be a pre or post hook, but writing
        guardrails for that seems overkill
        """
        raise NotImplementedError()

    def post_hook(self, leaf_uuid: str, tree: TreeSpan) -> None:
        """
        Function run on a single leaf, after any major transformations

        This function can write to and read from temporary directories
        It can write updated versions of the leaf content (e.g., parse custom markdown
        syntax), or other meta content (e.g., markdown headers). It may want to read
        information that was written by this Stage's `pre_hook`
        """
        raise NotImplementedError()


def populating_stage_dict(
    stage_list: list[str], stage_config: dict[str, dict[str, Any]]
) -> dict[str, Stage]:
    """Importing Built-in Stages and compiling all Stages available to Cambium"""

    from . import builtin_stages

    stage_dict = {}

    # Getting all subclasses of Stages
    all_subclasses = Stage.__subclasses__()

    # Adding stages to stage_dict if they're in the stage list:
    for tmp_stage in all_subclasses:
        if tmp_stage.__name__ in stage_list:

            # TODO: validate stage-specific configuration
            # all stages need to define some configuration object (which may be empty)
            # in the input config, not all stages will have defined configuration
            # and there may be configuration define for stages which are not installed
            # pass the validated config to the constructor
            stage_dict[tmp_stage.__name__] = tmp_stage()

    return stage_dict
