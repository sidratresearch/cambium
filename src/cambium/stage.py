from .tree import TreeSpan, Leaf


# TODO: it's technically correct to have Stage inherit from ABC and decorate tree_hook
# as @abstractmethod, but I'm not convinced it's worth it
# MR: Yeah, these _are_ going to be Abstract methods, but in reality, we should decorate a lot less in general
class Stage:
    identifier: str = ""

    # MR: Is there a reason we're making all of these static methods? In general, they should likely be just normal methods.
    @staticmethod
    def tree_hook(tree: TreeSpan) -> None:
        """
        Function to run which can modify the tree structure, adding and removing
        leaves and directories

        Function should also modify each leaf to add itself to the list of pre-hooks,
        transforms, and post-hooks as necessary

        Because tree hooks don't edit the contents of any file, they should not modify leaf.latest_path

        the tree_hook method is required because it is the function that registers the Stage into the pre/transform/post hooks for a leaf, and therefore if the tree_hook is not run, nothing else will be either
        """
        raise NotImplementedError()
        # MR: Base methods should probably not raise anything, so that we don't run into needing to capture exceptions

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


def populating_stage_dict(stage_list: list[str]) -> dict[str, Stage]:
    """Importing Built-in Stages and compiling all Stages available to Cambium"""

    from . import builtin_stages

    stage_dict = {}

    # Getting all subclasses of Stages
    all_subclasses = Stage.__subclasses__()

    # Adding stages to stage_dict if they're in the stage list:
    for tmp_stage in all_subclasses:
        if tmp_stage.__name__ in stage_list:
            stage_dict[tmp_stage.__name__] = tmp_stage()

    return stage_dict
