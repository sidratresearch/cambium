from ..stage import Stage
from ..tree import TreeSpan


class TemplatingMarkdown(Stage):

    def tree_hook(tree: TreeSpan) -> None:
        pass

    def post_hook(tree: TreeSpan) -> None:
        pass
