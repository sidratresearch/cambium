import logging
from pathlib import Path
from typing import Annotated

import typer

import cambium  # for version

from . import config
from .tree import TreeSpan

logger = logging.getLogger("CambiumLogger")
handler = logging.StreamHandler()
formatter = logging.Formatter("%(levelname)s: %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

app = typer.Typer()


def version_callback(value: bool) -> None:
    if value:
        print(f"Cambium {cambium.__version__}")
        raise typer.Exit


@app.command()
def main(
    config_path: Annotated[
        Path | None,
        typer.Option("--config", "-c", help="Location of Configuration File"),
    ] = None,
    _: Annotated[
        bool | None,
        typer.Option("--version", callback=version_callback, is_eager=True),
    ] = None,
):

    make_ascii_art()

    config_params = config.read_input_configuration(config_path)
    config.initialize_configuration(config_params)

    logger.setLevel(config.current_config.logging_level)
    logger.info("Logger is setup")

    treespan = TreeSpan(config.current_config)
    treespan.apply_pre_hooks()
    treespan.transform()
    treespan.apply_post_hooks()
    treespan.finalize()


def make_ascii_art():
    ascii_art = f"""
^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^^v^v^v^v^v^v^v^v^v^

  ░██████                             ░██        ░██
 ░██   ░██                            ░██
░██         ░██████   ░█████████████  ░████████  ░██░██    ░██ ░█████████████
░██              ░██  ░██   ░██   ░██ ░██    ░██ ░██░██    ░██ ░██   ░██   ░██
░██         ░███████  ░██   ░██   ░██ ░██    ░██ ░██░██    ░██ ░██   ░██   ░██
 ░██   ░██ ░██   ░██  ░██   ░██   ░██ ░███   ░██ ░██░██   ░███ ░██   ░██   ░██
  ░██████   ░█████░██ ░██   ░██   ░██ ░██░█████  ░██ ░█████░██ ░██   ░██   ░██


            Version: {cambium.__version__}

^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^^v^v^v^v^v^v^v^v^v^
    """

    print(ascii_art)
