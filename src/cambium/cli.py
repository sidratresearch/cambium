import logging
from pathlib import Path
from typing import Annotated

import typer

import cambium
from cambium import config
from cambium.tree import TreeSpan

logger = logging.getLogger("CambiumLogger")
handler = logging.StreamHandler()
formatter = logging.Formatter("%(levelname)s: %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


app = typer.Typer()


@app.command()
def main(
    config_path: Annotated[
        Path | None,
        typer.Option("--config", "-c", help="Location of Configuration File"),
    ] = None,
):

    make_ascii_art()

    config_params = config.read_input_configuration(config_path)
    config.initialize_configuration(config_params)

    logger.setLevel(config.current_config.logging_level)
    logger.info("Logger is setup")

    treespan = TreeSpan(config.current_config)
    treespan.transform()
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
