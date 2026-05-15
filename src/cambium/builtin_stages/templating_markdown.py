from ..stage import Stage
from ..tree import TreeSpan

import logging

logger = logging.getLogger(__name__)


class TemplatingMarkdown(Stage):

    def tree_hook(tree: TreeSpan) -> None:
        pass

    def post_hook(tree: TreeSpan) -> None:
        pass
