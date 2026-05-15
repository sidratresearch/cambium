from ..stage import Stage
from ..tree import TreeSpan, Leaf
from ..md_transform import markdown_to_html


class TransformMarkdown(Stage):
    identifier: str = "TransformMarkdown"  # can we use __name__ or something?

    # MR: If we're supporting Py3.11, we probably shouldn't use @override. Also, we should remove @staticmethod decorators
    @staticmethod
    def tree_hook(tree: TreeSpan) -> None:
        """
        Update final path and list of transforms for markdown leaves.
        """
        tree.apply_to_leaves(TransformMarkdown._tree_hook_for_leaf)

    @staticmethod
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

    @staticmethod
    def transform(leaf: Leaf, working_config) -> None:
        """
        Use Marko to write an HTML version of a markdown leaf.
        """
        output_path = working_config["tempdir"].name / leaf.final_path

        markdown = (working_config["tempdir"].name / leaf.latest_path).read_text()
        html = markdown_to_html(markdown)

        output_path.write_text(html)
        leaf.latest_path = output_path
