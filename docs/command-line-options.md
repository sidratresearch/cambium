# Command Line Options

<!-- TableOfContents(maxdepth=3) -->

<!-- Want to keep this in the same order as `cambium --help` -->
## General

### `--dry-run`

Don't process files or build the site - instead, Cambium will output what the file structure of the build directory would be. Note: this feature is currently under-developed, the output is accurate, but poorly formatted.

### `--version`

Print the installed version of Cambium.

### `--install-completion` / `--show-completion`

Show or install completions for your shell.

### `--help`

Display the CLI help message.

## Configuration

### `--config`

Specify the path to a Cambium [configuration file](./config-file.md) - if not given, Cambium will look for `.cambium/config.yaml`.

### `--dump-default-config`

Print the default configuration used by Cambium if no configuration file is present.

### `--root-directory`

This is the source of your website content. By default, the site will be created from the files is the present working directory `--root-directory` is passed, that will be the source of content for the site.

Note that if you run `cambium --root-directory other` without specifying `--config`, Cambium will load the configuration file from the current directory, if any.

Passing a value on the command line overrides the configuration file setting, if present.

### `--build-directory`

The directory to create to place your built website. Defaults to `_build`. Unless given as an absolute path, this will always be relative to the root directory.

Passing a value on the command line overrides the configuration file setting, if present.

## Development Server

### `--dev`

Start Cambium in development server mode. In this mode, Cambium opens an http server in the background, allowing you to view your site in a browser (by default the URL is [http://localhost:8000](http://localhost:8000)), and watches your files for changes, re-building the site on each change.

Changes to the configuration file are _not_ applied, and in fact if the configuration file changes, Cambium will exit the server to make this clear.

### `--port`

Port to use for the development server. Defaults to 8000. No effect when used without `--dev`.

### `--watch-interval`

How often (in seconds) to poll the filesystem for changes when running the development server. Defaults to 0.5. No effect when used without `--dev`.

### `--dev-directory`

Equivalent to `--build-directory`, but for the development server. This directory will be deleted when the server exits. Defaults to `.cambium-dev/`. No effect when used without `--dev`.

## Logging and Output

### `--verbose` / `-v`

Increase the logging level. By default, Cambium outputs log lines which have a level of `INFO` or higher, and thus passing `--verbose` results in Cambium also showing debug output.

If `log_level` is set in the configuration file to something higher than `INFO`, `--verbose` will increase the verbosity one level for every time it is passed.

### `--show-traceback`

Opt-in to showing Python traceback if an error occurs.

### `--fail-fast`

Exit on the first error encountered. When this option is not provided, if Cambium encounters an error while processing files, it will attempt to process the remaining files, before exiting with a description of all errors encountered.

### `--no-ascii`

Hide the Cambium ASCII art shown on startup.
