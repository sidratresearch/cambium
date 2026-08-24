import json
from pathlib import Path
from typing import Annotated, Any

import typer

from .. import __version__, config
from ..tree import TreeSpan
from .dev_server import run_dev_server
from .log import get_loglevel, init_logging

logger = init_logging()
app = typer.Typer()

CLI_DEFAULTS = {
    "fail_fast": False,
    "build_directory": None,
    "root_directory": None,
    "dev_server": False,
    "dev_server_port": 8000,
    "dev_server_interval": 0.5,
    "dev_server_directory": ".cambium-dev/",
}
"""Default values for the CLI parameters that get passed to `setup_config`.

Stored here so they can also be used in tests."""

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
            help="""Don't process or write output, only determine and output
            the file structure""",
        ),
    ] = False,
    fail_fast: Annotated[
        bool,
        typer.Option(
            "--fail-fast", help="Quit on first error when running stage hooks."
        ),
    ] = CLI_DEFAULTS["fail_fast"],
    config_path: Annotated[
        Path | None,
        typer.Option(
            "--config",
            "-c",
            help="Location of configuration file",
            rich_help_panel="Configuration",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ] = None,
    build_directory: Annotated[
        str | None,
        typer.Option(
            "--build-directory",
            help="Location to build site into, overrides configuration file",
            rich_help_panel="Configuration",
        ),
    ] = CLI_DEFAULTS["build_directory"],
    root_directory: Annotated[
        str | None,
        typer.Option(
            "--root-directory",
            help="Location of input files for Cambium, overrides configuration file",
            rich_help_panel="Configuration",
        ),
    ] = CLI_DEFAULTS["root_directory"],
    no_ascii: Annotated[
        bool, typer.Option("--no-ascii", help="Hide the Cambium ascii art")
    ] = False,
    dev_server: Annotated[
        bool,
        typer.Option(
            "--dev",
            help="Run Cambium in development server mode",
            rich_help_panel="Development Server",
        ),
    ] = CLI_DEFAULTS["dev_server"],
    dev_server_port: Annotated[
        int,
        typer.Option(
            "--port",
            help="Port to host the development server",
            rich_help_panel="Development Server",
        ),
    ] = CLI_DEFAULTS["dev_server_port"],
    dev_server_interval: Annotated[
        float,
        typer.Option(
            "--watch-interval",
            help="Frequency with whech to check the filesystem for changes (seconds)",
            min=0.01,
            rich_help_panel="Development Server",
        ),
    ] = CLI_DEFAULTS["dev_server_interval"],
    dev_directory: Annotated[
        str,
        typer.Option(
            "--dev-directory",
            help="Location to build development-mode site into",
            rich_help_panel="Development Server",
        ),
    ] = CLI_DEFAULTS["dev_server_directory"],
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
            rich_help_panel="Configuration",
        ),
    ] = False,
) -> None:

    # Quick-exit options
    if version_option:
        print(f"Cambium {__version__}")
        return
    if dump_config_option:
        config.dump_default_config()
        return

    if not no_ascii:
        make_ascii_art()

    # Common setup tasks
    cli_config = {
        "build_directory": build_directory,
        "root_directory": root_directory,
        "fail_fast": fail_fast,
        "dev_server": dev_server,
        "dev_server_port": dev_server_port,
        "dev_server_interval": dev_server_interval,
        "dev_server_directory": dev_directory,
    }
    try:
        setup_config(config_path, cli_config, verbosity_boost)
    except AssertionError as e:
        raise typer.BadParameter(str(e))

    treespan = TreeSpan(config.current_config)

    if dry_run:
        skipped_dir = f"{treespan.build_directory}/static/_cambium"
        logger.warning(
            f"Dry run file structure does not include paths within {skipped_dir}"
        )
        print(json.dumps(treespan.filestructure_in_build, indent=2))
        return

    if dev_server:
        run_dev_server(treespan, build, config_path)
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
