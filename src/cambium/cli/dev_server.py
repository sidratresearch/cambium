"""Functions for running Cambium in development server mode."""

import functools
import http.server
import logging
import multiprocessing
import shutil
import sys
import time
from collections.abc import Callable
from pathlib import Path

import typer

from .. import config
from ..tree import TreeSpan
from ..utils import walk_directory_tree

logger = logging.getLogger(__name__)


def run_dev_server(
    tree: TreeSpan, build: Callable[[TreeSpan], None], config_path: Path | None
) -> None:
    """Run Cambium in development server mode.

    Sets up a list of files to watch, and re-runs Cambium whenever any of
    those files changes. Also backgrounds an http server so the results can
    be seen on localhost, and includes an auto-reload script in the HTML of
    any templated markdown files.
    """
    logger.info("Running Cambium in dev server mode, use CTRL-c to quit")

    server_process = start_http_server(
        tree.config.dev_server_port, tree.build_directory
    )
    check_server_process(server_process)

    try:
        watched_files = get_watched_files(tree)
        last_checked = time.monotonic()
        check_server_process(server_process)
        build(tree)
        logger.info(
            f"Checking for changes every {tree.config.dev_server_interval} seconds."
        )

        while True:
            current_time = time.monotonic()
            if current_time - last_checked > tree.config.dev_server_interval:
                check_server_process(server_process)
                logger.debug("Checking for file changes.")
                last_checked = current_time
                files_changed, watched_files, config_changed = check_file_changes(
                    watched_files, tree, config_path
                )
                if config_changed:
                    logger.warning("Config file changed, closing dev server")
                    raise typer.Exit()

                if files_changed:
                    tree.config.tmp_dir_obj.cleanup()  # clean up old tree
                    tree.config.setup_tmp_dir()  # start a new tmpdir
                    tree = TreeSpan(config.current_config)  # make new tree
                    logger.info("Re-running Cambium")
                    build(tree)
    except Exception as e:
        logger.info("Closing dev server and deleting development files")
        shutil.rmtree(tree.build_directory)
        server_process.terminate()  # prints "Process Process-1" to sys.stderr
        if not isinstance(e, KeyboardInterrupt):
            logger.error(e)
            raise e


# --------------------------------------------------------------------#
#                       web server definitions                        #
# --------------------------------------------------------------------#


class CambiumSimpleHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):

    def log_message(self, format, *args) -> None:
        """Override the default logging which uses sys.stderr.write."""
        formatted = (format % args).translate(self._control_char_table)
        logger.debug(formatted)


def serve_forever(port: int, directory: Path) -> None:
    """Picklable function which starts an http server."""
    handler = functools.partial(CambiumSimpleHTTPRequestHandler, directory=directory)
    try:
        httpd = http.server.HTTPServer(("", port), handler)
    except OSError as e:
        logger.error(f"An error occurred starting the HTTP server on port {port}: {e}")
        sys.exit(1)  # caught by `check_server_process`

    httpd.serve_forever()


def start_http_server(port: int, directory: Path) -> multiprocessing.Process:
    """Start the simple Python http.server, serving files from `directory`."""
    server = multiprocessing.Process(
        target=serve_forever, args=([port, directory]), daemon=True
    )
    server.start()  # confirmed via htop that this process gets cleaned up on ctrl-c
    logger.info(f"Serving to http://localhost:{port}")

    return server


def check_server_process(server_process: multiprocessing.Process) -> None:
    """Exit if the HTTP server has closed."""
    if server_process.exitcode == 1:
        raise typer.Exit


# --------------------------------------------------------------------#
#                      file watching functions                        #
# --------------------------------------------------------------------#


def check_file_changes(
    watched_files: str, tree: TreeSpan, config_path: Path | None
) -> tuple[bool, str, bool]:
    """Check if any files have changed, compared to `watched_files`."""
    new_file_status = get_watched_files(tree)

    files_changed = str(watched_files) != str(new_file_status)

    config_path = (
        config_path
        if config_path is not None
        else tree.root_directory / config.config_default_path
    )
    config_previous = watched_files.get(config_path, None)
    config_current = new_file_status.get(config_path, None)

    config_changed = config_previous != config_current

    return files_changed, new_file_status, config_changed


def get_watched_files(tree: TreeSpan) -> str:
    """Get the state of watched files in some format that can be compared.

    In the future we could hash the contents of files, include static files,
    check for file deletion, watch the files in .cambium, etc.

    This function may change to return an object that can be iterated on
    the file level to support incremental rebuilds.
    """
    _, paths = walk_directory_tree(tree.root_directory, tree.config.ignore_lists)
    for other_dir in [
        tree.root_directory / "static",
        tree.root_directory / ".cambium",
    ]:
        if other_dir.exists():
            _, static_paths = walk_directory_tree(other_dir, None)
            paths = paths + [other_dir / p for p in static_paths]

    return {path: path.stat().st_mtime for path in sorted(paths)}
