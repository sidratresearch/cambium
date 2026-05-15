from marko import Markdown
from marko.html_renderer import HTMLRenderer
from marko.inline import Link
from typing_extensions import override

from ..stage import Stage
from ..tree import TreeSpan


class CambiumHTMLRenderer(HTMLRenderer):
    @override
    def render_link(self, element: Link) -> str:
        if element.dest.endswith(".md"):
            element.dest = element.dest[: element.dest.rindex(".md")] + ".html"
        return super().render_link(element)


def markdown_to_html(markdown: str) -> str:
    # WARNING: The Markdown class is not thread-safe. Create a new instance for each thread.
    return Markdown(extensions=["gfm"], renderer=CambiumHTMLRenderer).convert(markdown)


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
        if tree.leaves["initial_path"][leaf_uuid].parts[0] == "static":
            return
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
