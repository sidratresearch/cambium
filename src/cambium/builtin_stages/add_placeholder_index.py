from pathlib import Path

from ..stage import Stage
from ..tree import TreeSpan


# initial path is directory
# initial path is file that lead to the cause of the output
class AddPlaceholderIndex(Stage):

    def tree_hook(self, tree: TreeSpan) -> None:
        final_paths = [tree.leaves["final_path"][uuid] for uuid in tree.leaves["uuids"]]

        for directory in [Path("."), *tree.directories_in_build]:
            index_file = directory / "index.html"
            if index_file not in final_paths:
                self._create_index_leaf(directory, tree)

    def _create_index_leaf(self, directory: Path, tree: TreeSpan) -> None:
        # TODO: figure out what to do about this
        initial_path = Path(f".cambium/AddPlaceholderIndex/index.html")
        source_file = tree.config.tmp_dir / initial_path
        source_file.parent.mkdir(parents=True, exist_ok=True)
        source_file.write_text("")

        uuid = tree.add_leaf(directory)
        tree.leaves["final_path"][uuid] = directory / "index.html"
        tree.leaves["latest_path"][uuid] = source_file
