import json
from pathlib import Path
from typing import Annotated, Any

import typer

from . import __version__, config
from .log import get_loglevel, init_logging
from .tree import TreeSpan

logger = init_logging()
app = typer.Typer()

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
    dev_server: Annotated[
        bool,
        typer.Option("--dev", help="Run Cambium in development server mode"),
    ] = False,
    # subcommands
    version_option: Annotated[
        bool,
        typer.Option(
            "--version",
            help="Print version info",
        ),
    ] = False,
    dump_config_option: Annotated[
        bool,
        typer.Option(
            "--dump-default-config",
            help="Dump default configuration info to stdout",
        ),
    ] = False,
) -> None:

    ## Quick-exit options
    if version_option:
        print(f"Cambium {__version__}")
        return
    if dump_config_option:
        config.dump_default_config()
        return

    make_ascii_art()

    cli_config = {
        "build_directory": build_directory,
        "root_directory": root_directory,
        "dev_server": dev_server,
    }
    setup_config(config_path, cli_config, verbosity_boost)

    treespan = TreeSpan(config.current_config)

    if dry_run:
        logger.warning(
            f"Dry run file structure does not include paths within {treespan.build_directory}/static/_cambium"
        )
        print(json.dumps(treespan.filestructure_in_build, indent=2))
        return

    if dev_server:
        logger.info("Running dev server")
        # get list of files to watch: regular cambium, static files, skip cambium ignores

        # run build
        # start http server

        # check for file modifications, and re-run build

        # TODO: wipe _build so the reload js doesn't end up in prod
        # or run the dev server off of a different folder

        # TODO: how do we handle config changes?
        return

    build(treespan)

    logger.info("Cambium complete!")


def setup_config(
    config_path: Path | None, cli_config: dict[str, Any], verbosity_boost: int
) -> None:
    """Process file and command-line configuration, and set up logger."""
    yaml_config = config.read_input_configuration(config_path)
    config.initialize_configuration(yaml_config, cli_config)

    logger.setLevel(get_loglevel(config.current_config.logging_level, verbosity_boost))
    logger.info("Logger is setup")


def build(treespan: TreeSpan) -> None:
    """Run all of the Cambium TreeSpan functions."""
    treespan.prepare_tree()
    treespan.apply_pre_hooks()
    treespan.transform()
    treespan.apply_post_hooks()
    treespan.finalize()


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
