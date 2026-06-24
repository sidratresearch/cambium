import http.server
import json
import multiprocessing
import time
from pathlib import Path
from typing import Annotated, Any

import typer

from . import __version__, config
from .log import get_loglevel, init_logging
from .tree import TreeSpan, walk_directory_tree

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
        typer.Option(
            "--dev",
            help="Run Cambium in development server mode",
            rich_help_panel="Development Server",
        ),
    ] = False,
    dev_server_port: Annotated[
        int,
        typer.Option(
            "--port",
            help="Port to host the development server",
            rich_help_panel="Development Server",
        ),
    ] = 8000,
    dev_server_interval: Annotated[
        float,
        typer.Option(
            "--watch-interval",
            help="Frequency with whech to check the filesystem for changes (seconds)",
            min=0.01,
            rich_help_panel="Development Server",
        ),
    ] = 0.5,
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
        "dev_server_port": dev_server_port,
        "dev_server_interval": dev_server_interval,
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
        run_dev_server(treespan)
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
    _, paths = walk_directory_tree(tree)

    return str({path: path.stat().st_mtime for path in sorted(paths)})


def check_file_changes(watched_files: str, tree: TreeSpan) -> tuple[bool, str]:
    """Check if any files have changed, compared to `watched_files`."""
    new_file_status = get_watched_files(tree)

    files_changed = watched_files != new_file_status

    return files_changed, new_file_status


def start_http_server(port: int, directory: Path) -> multiprocessing.Process:
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

    return server


def run_dev_server(tree: TreeSpan) -> None:
    """Run Cambium in development server mode.

    Sets up a list of files to watch, and re-runs Cambium whenever any of
    those files changes. Also backgrounds an http server so the results can
    be seen on localhost, and includes an auto-reload script in the HTML of
    any templated markdown files.
    """
    logger.info("Running Cambium in dev server mode, use CTRL-c to quit")
    # TODO: consider adding static files
    # TODO: check for config file changes and warn
    # TODO: run the dev server off of a different folder (not _build)

    server_process = start_http_server(
        tree.config.dev_server_port, tree.build_directory
    )

    try:
        watched_files = get_watched_files(tree)
        last_checked = time.monotonic()
        build(tree)
        logger.info(
            f"Checking for changes every {tree.config.dev_server_interval} seconds."
        )

        while True:
            current_time = time.monotonic()
            if current_time - last_checked > tree.config.dev_server_interval:
                logger.debug("Checking for file changes.")
                last_checked = current_time
                files_changed, watched_files = check_file_changes(watched_files, tree)
                if files_changed:
                    tree.config.tmp_dir_obj.cleanup()  # clean up old tree
                    tree = TreeSpan(config.current_config)  # make new tree
                    logger.info("Re-running Cambium")
                    build(tree)
    except KeyboardInterrupt:
        logger.info("Closing dev server")
        server_process.terminate()  # prints "Process Process-1" to sys.stderr


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
