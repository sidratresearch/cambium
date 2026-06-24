import http.server
import json
import multiprocessing
import time
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

    # Quick-exit options
    if version_option:
        print(f"Cambium {__version__}")
        return
    if dump_config_option:
        config.dump_default_config()
        return

    # Common setup tasks
    make_ascii_art()
    cli_config = {
        "build_directory": build_directory,
        "root_directory": root_directory,
        "dev_server": dev_server,
    }
    setup_config(config_path, cli_config, verbosity_boost)
    treespan = TreeSpan(config.current_config)

    if dry_run:
        skipped_dir = f"{treespan.build_directory}/static/_cambium"
        logger.warning(
            f"Dry run file structure does not include paths within {skipped_dir}"
        )
        print(json.dumps(treespan.filestructure_in_build, indent=2))
        return

    if dev_server:
        logger.info("Running dev server")
        # TODO: consider adding static files, new files to watched files
        # TODO: what happens when files are deleted?
        # TODO: check for config file changes and warn
        # TODO: run the dev server off of a different folder (not _build)

        port = 8001  # make cli option
        start_http_server(port, treespan.build_directory)

        watched_files = get_watched_files(treespan)
        last_checked = time.monotonic()
        build(treespan)
        # add minimum time between checks
        while True:
            treespan.config.reset_tmp_dir()
            current_time = time.monotonic()
            if (last_checked is None) or (current_time - last_checked > 2):
                logger.debug("Checking for file changes.")
                last_checked = current_time
                files_changed, watched_files = check_file_changes(
                    watched_files, treespan
                )
                if files_changed:
                    logger.info("Re-running Cambium")
                    build(treespan)  # do you need to wipe the tmpdir?

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


def get_watched_files(tree: TreeSpan) -> str:
    """Get the state of watched files in some format that can be compared.

    In the future we could hash the contents of files, include static files,
    check for file deletion, watch the files in .cambium, etc.

    This function may change to return an object that can be iterated on
    the file level to support incremental rebuilds.
    """
    return str(
        {
            tree.leaves["initial_path"][leaf_uuid]: (
                tree.root_directory / tree.leaves["initial_path"][leaf_uuid]
            )
            .stat()
            .st_mtime
            for leaf_uuid in sorted(tree.leaves["uuids"])
        }
    )


def check_file_changes(watched_files: str, tree: TreeSpan) -> tuple[bool, str]:
    """Check if any files have changed, compared to `watched_files`."""
    new_file_status = get_watched_files(tree)

    files_changed = watched_files != new_file_status

    return files_changed, new_file_status


def start_http_server(port: int, directory: Path) -> None:
    """Start the simple Python http.server, serving files from `directory`."""

    class CambiumSimpleHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs) -> None:
            super().__init__(*args, directory=directory, **kwargs)

        def log_message(self, format, *args) -> None:
            """Override the default logging which uses sys.stderr.write."""
            formatted = (format % args).translate(self._control_char_table)
            logger.debug(formatted)

    httpd = http.server.HTTPServer(("", port), CambiumSimpleHTTPRequestHandler)

    server = multiprocessing.Process(target=httpd.serve_forever, daemon=True)
    server.start()  # confirmed via htop that this process gets cleaned up on ctrl-c
    logger.info(f"Serving to http://localhost:{port}")


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
