from ..md_transform import markdown_to_html
from ..stage import Stage
from ..tree import Leaf, TreeSpan


class TransformMarkdown(Stage):

    def tree_hook(tree: TreeSpan) -> None:
        """
        Update final path and list of transforms for markdown leaves.
        """
        tree.apply_to_leaves(TransformMarkdown._tree_hook_for_leaf)

    # function that reads all files and finds all the links within them
    # can make a mapping of original link href -> uuid of the files -> output file
    # then the marko extension could use that mapping

    def _tree_hook_for_leaf(leaf: Leaf, _: TreeSpan) -> None:
        """
        Update final path and list of transforms for a single leaf, if applicable
        """
        if leaf.latest_path.parts[0] == "static":
            return
        if leaf.latest_path.suffix.lower() != ".md":
            return

        leaf.final_path = leaf.latest_path.with_suffix(".html")
        leaf.transforms.append(TransformMarkdown)

    def transform(leaf: Leaf, working_config) -> None:
        """
        Use Marko to write an HTML version of a markdown leaf.
        """
        output_path = working_config.tmp_dir / leaf.final_path

        markdown = (working_config.tmp_dir / leaf.latest_path).read_text()
        html = markdown_to_html(markdown)

        output_path.write_text(html)
        leaf.latest_path = output_path
