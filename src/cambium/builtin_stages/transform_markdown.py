from marko import Markdown
from marko.md_renderer import MarkdownRenderer

from ..stage import Stage
from ..tree import TreeSpan
from .utils import markdown_to_html, rewrite_md_links


class TransformMarkdown(Stage):
    changed_links: list[str] = []

    def tree_hook(self, tree: TreeSpan) -> None:
        """
        Update final path and list of transforms for markdown leaves.
        """
        tree.apply_to_leaves(self._tree_hook_for_leaf)

    def _tree_hook_for_leaf(self, leaf_uuid: str, tree: TreeSpan) -> None:
        """
        Update final path and list of transforms for a single leaf, if applicable
        """
        if tree.leaves["latest_path"][leaf_uuid].suffix.lower() != ".md":
            return

        tree.leaves["final_path"][leaf_uuid] = tree.leaves["latest_path"][
            leaf_uuid
        ].with_suffix(".html")
        tree.leaves["hooks"][leaf_uuid]["pre_hooks"].append(TransformMarkdown.__name__)
        tree.leaves["hooks"][leaf_uuid]["transforms"].append(TransformMarkdown.__name__)
        self.changed_links.append(tree.leaves["initial_path"][leaf_uuid])

    def pre_hook(self, leaf_uuid: str, tree: TreeSpan) -> None:
        """Rewrite links to markdown files that will get transformed"""
        latest_path = tree.config.tmp_dir / tree.leaves["latest_path"][leaf_uuid]
        marko_object = Markdown(renderer=MarkdownRenderer)
        document = marko_object.parse(latest_path.read_text())

        document = rewrite_md_links(
            document, tree.leaves["initial_path"][leaf_uuid].parent, self.changed_links
        )
        latest_path.write_text(marko_object.render(document))

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
