from ..stage import Stage
from ..tree import TreeSpan
from .utils import markdown_to_html


class TransformMarkdown(Stage):

    def tree_hook(self, tree: TreeSpan) -> None:
        """
        Update final path and list of transforms for markdown leaves.
        """
        tree.apply_to_leaves(self._tree_hook_for_leaf)

    # TODO:
    # function that reads all files and finds all the links within them
    # can make a mapping of original link href -> uuid of the files -> output file
    # then the marko extension could use that mapping

    def _tree_hook_for_leaf(self, leaf_uuid: str, tree: TreeSpan) -> None:
        """
        Update final path and list of transforms for a single leaf, if applicable
        """
        if tree.leaves["latest_path"][leaf_uuid].suffix.lower() != ".md":
            return

        tree.leaves["final_path"][leaf_uuid] = tree.leaves["latest_path"][
            leaf_uuid
        ].with_suffix(".html")
        tree.leaves["hooks"][leaf_uuid]["transforms"].append(TransformMarkdown.__name__)

    def transform(self, leaf_uuid: str, tree: TreeSpan) -> None:
        """
        Use Marko to write an HTML version of a markdown leaf.
        """
        output_path = tree.config.tmp_dir / tree.leaves["final_path"][leaf_uuid]

        markdown = (
            tree.config.tmp_dir / tree.leaves["latest_path"][leaf_uuid]
        ).read_text()
        html = markdown_to_html(markdown)

        output_path.write_text(html)
        tree.leaves["latest_path"][leaf_uuid] = output_path
