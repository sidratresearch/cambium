from pathlib import Path

from ..stage import Stage
from ..tree import TreeSpan


class AddPlaceholderIndex(Stage):

    def tree_hook(self, tree: TreeSpan) -> None:
        final_paths = [tree.leaves["final_path"][uuid] for uuid in tree.leaves["uuids"]]

        for directory in [Path(), *tree.directories_in_build]:
            index_file = directory / "index.html"
            if index_file not in final_paths:
                self._create_index_leaf(directory, tree)

    def _create_index_leaf(self, directory: Path, tree: TreeSpan) -> None:
        # TODO: figure out what to do about this
        source_path = Path(".cambium/AddPlaceholderIndex/index.html")

        uuid = tree.add_leaf(directory)
        # not using tree.update_leaf_path because it doesn't make sense here
        tree.leaves["final_path"][uuid] = directory / "index.html"
        tree.leaves["latest_path"][uuid] = source_path

        tree.abs_write_path(uuid).write_text("")
