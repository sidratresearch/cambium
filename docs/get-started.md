# Getting started with Cambium

## Quickstart - installation and first run

Cambium can be installed from PyPi via pip:

```bash
pip install cambium
```

Navigate to a directory containing some Markdown (`.md`) files.
Then, run Cambium:

```bash
cambium
```

You should see some descriptive output and a new directory `_build`, which
contains the ready-for-use version of your site. To preview the site, run

```bash
python -m http.server -d _build
```

and visit the site in a browser, at [`http://localhost:8000`](http://localhost:8000/).

You can also list the files in the `_build` directory to see which HTML pages have been created, and visit them directly.

Please note if Cambium finds a pre-existing index file from this list, it will
use it as the homepage.

- `index.md`
- `index.html`
- `readme.md`
- `readme.html`
- `README.md`
- `README.html`

If an index page cannot be found, Cambium will create a blank one at
`index.html`.

## What features are built in?

- link to [Writing Content](./writing-content.md)
- alerts, markdown table alignment, table sorting, search previewCSV
- md inside HTML will not be converted

## Using the development server

Running `cambium --dev` starts Cambium in development server mode. In this mode, Cambium opens an http server in the background, allowing you to view your site in a browser (by default the URL is [http://localhost:8000](http://localhost:8000)), and watches your files for changes, re-building the site on each change.

The port used for the web server, as well as the frequency Cambium checks for file changes are both configurable.

Changes to the configuration file are _not_ applied, and in fact if the configuration file changes, Cambium will exit the dev server to make this clear.

## How and where to write a config file

Cambium reads the configuration file at `.cambium/config.yaml` if it exists. You can create this file with the default options by running

```bash
mkdir .cambium && cambium --dump-default-config >.cambium/config.yaml
```

## Basic Configuration options

- root and build directories (can be CLI or file)
- stages (see [Configuring Stages](./configuring-stages.md))
- site name
- theme (see [Customizing the Website](./customizing-the-website.md))

## What is Cambium's philosophy

## What to do if there are issues

- `--fail-fast`, `--verbose`, and `--show-traceback`
- where to report issues

## How Cambium works

- there are stages
- one major stage is transformMD which renders markdown documents into HTML with the help of a Jinja template
- Cambium copies your processed files, as well as some of its own additional files into the build directory

## Status and future outlook

- Why should I trust in future development
- planned features
- "pre-alpha"

## What is Cambium an alternative to?

- migration instructions
