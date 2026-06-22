import json
from pathlib import Path
from typing import Annotated

import typer

from . import __version__, config
from .log import get_loglevel, init_logging
from .tree import TreeSpan

logger = init_logging()
app = typer.Typer()

# --------------------------------------------------------------------#
#                      Subcommand-style options                       #
# --------------------------------------------------------------------#


def version_callback(value: bool) -> None:
    if value:
        print(f"Cambium {__version__}")
        raise typer.Exit


version_option = Annotated[
    bool | None,
    typer.Option(
        "--version",
        help="Print version info",
        callback=version_callback,
        is_eager=True,
    ),
]


def dump_config_callback(value: bool) -> None:
    if value:
        config.dump_default_config()
        raise typer.Exit


dump_config_option = Annotated[
    bool | None,
    typer.Option(
        "--dump-default-config",
        help="Dump default configuration info to stdout",
        callback=dump_config_callback,
        is_eager=True,
    ),
]


def dev_callback(value: bool) -> None:
    if value:
        print("Running dev server")


dev_option = Annotated[
    bool | None,
    typer.Option(
        "--dev", help="Run Cambium in development server mode", callback=dev_callback
    ),
]


# --------------------------------------------------------------------#
#                           Main function                             #
# --------------------------------------------------------------------#


@app.command()
def main(
    verbosity_boost: Annotated[
        int,
        typer.Option(
            "--verbose",
            "-v",
            help="Increase verbosity (repeatable)",
            count=True,
        ),
    ] = 0,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help="Don't process or write output, only determine and output the file structure",
        ),
    ] = False,
    config_path: Annotated[
        Path | None,
        typer.Option(
            "--config",
            "-c",
            help="Location of Configuration File",
            rich_help_panel="Configuration",
        ),
    ] = None,
    build_directory: Annotated[
        str | None,
        typer.Option(
            "--build-directory",
            help="Location to build site into, overrides configuration file",
            rich_help_panel="Configuration",
        ),
    ] = None,
    root_directory: Annotated[
        str | None,
        typer.Option(
            "--root-directory",
            help="Location of input files for Cambium, overrides configuration file",
            rich_help_panel="Configuration",
        ),
    ] = None,
    # subcommands
    _: version_option = None,
    __: dump_config_option = None,
    ___: dev_option = None,
) -> None:

    make_ascii_art()

    yaml_config = config.read_input_configuration(config_path)
    cli_config = {"build_directory": build_directory, "root_directory": root_directory}
    config.initialize_configuration(yaml_config, cli_config)

    logger.setLevel(get_loglevel(config.current_config.logging_level, verbosity_boost))
    logger.info("Logger is setup")

    if dev_option:
        config.current_config.dev_server = True

    treespan = TreeSpan(config.current_config)

    if dry_run:
        logger.warning(
            f"Dry run file structure does not include paths within {treespan.build_directory}/static/_cambium"
        )
        print(json.dumps(treespan.filestructure_in_build, indent=2))
        return

    treespan.prepare_tree()
    treespan.apply_pre_hooks()
    treespan.transform()
    treespan.apply_post_hooks()
    treespan.finalize()

    logger.info("Cambium complete!")


def make_ascii_art() -> None:
    ascii_art = f"""
^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^

  ░██████                             ░██        ░██
 ░██   ░██                            ░██
░██         ░██████   ░█████████████  ░████████  ░██░██    ░██ ░█████████████
░██              ░██  ░██   ░██   ░██ ░██    ░██ ░██░██    ░██ ░██   ░██   ░██
░██         ░███████  ░██   ░██   ░██ ░██    ░██ ░██░██    ░██ ░██   ░██   ░██
 ░██   ░██ ░██   ░██  ░██   ░██   ░██ ░███   ░██ ░██░██   ░███ ░██   ░██   ░██
  ░██████   ░█████░██ ░██   ░██   ░██ ░██░█████  ░██ ░█████░██ ░██   ░██   ░██


            Version: {__version__}

^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^
    """

    print(ascii_art)
