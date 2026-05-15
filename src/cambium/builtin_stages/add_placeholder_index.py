from pathlib import Path

from ..stage import Stage
from ..tree import Leaf, TreeSpan


class AddPlaceholderIndex(Stage):
    identifier = "AddPlaceholderIndex"

    @staticmethod
    def tree_hook(tree: TreeSpan) -> None:
        leaves_by_final_directory = tree.leaves_by_final_directory

        for directory in [Path("."), *tree.directories_in_build]:
            # get list of leaves that will output to that directory
            leaves = leaves_by_final_directory[directory]
            leaf_filenames = [leaf.final_path.name for leaf in leaves]

            if "index.html" not in leaf_filenames:
                AddPlaceholderIndex._create_index_leaf(directory, tree)

    @staticmethod
    def _create_index_leaf(directory: Path, tree: TreeSpan) -> None:
        # TODO: figure out what to do about this
        initial_path = Path(f".cambium/{AddPlaceholderIndex.identifier}/index.html")
        source_file = tree.working_config.tmp_dir / initial_path
        source_file.parent.mkdir(parents=True, exist_ok=True)
        source_file.write_text("")

        index_leaf = Leaf(initial_path=initial_path, initial_path_mocked=True)
        index_leaf.latest_path = source_file
        index_leaf.final_path = directory / "index.html"

        tree.add_leaf(index_leaf)
