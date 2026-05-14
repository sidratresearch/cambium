import typer
from typing import Annotated
from pathlib import Path
from cambium import config
from cambium.tree import TreeSpan

app = typer.Typer()


@app.command()
def main(
    config_path: Annotated[
        Path | None,
        typer.Option("--config", "-c", help="Location of Configuration File"),
    ] = None,
):

    config_params = config.read_input_configuration(config_path)
    config.initialize_configuration(config_params)

    treespan = TreeSpan()
    treespan.transform()
    treespan.finalize()
