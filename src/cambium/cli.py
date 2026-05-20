from pathlib import Path
from typing import Annotated

import typer

import cambium  # for version

from . import config
from .log import init_logging
from .tree import TreeSpan

logger = init_logging()
app = typer.Typer()


def version_callback(value: bool) -> None:
    if value:
        print(f"Cambium {cambium.__version__}")
        raise typer.Exit


def dump_config_callback(value: bool) -> None:
    if value:
        config.dump_default_config()
        raise typer.Exit


@app.command()
def main(
    config_path: Annotated[
        Path | None,
        typer.Option("--config", "-c", help="Location of Configuration File"),
    ] = None,
    _: Annotated[
        bool | None,
        typer.Option(
            "--version",
            help="Print version info",
            callback=version_callback,
            is_eager=True,
        ),
    ] = None,
    __: Annotated[
        bool | None,
        typer.Option(
            "--dump-default-config",
            help="Dump default configuration info to stdout",
            callback=dump_config_callback,
            is_eager=True,
        ),
    ] = None,
) -> None:

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

    logger.info("Cambium complete!")


def make_ascii_art() -> None:
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
