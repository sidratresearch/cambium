# Getting started with Cambium

## Installation

Cambium can be installed from PyPi via pip:

```bash
pip install cambium
```

## Your first run

`cd` to a folder containing some markdown files, and run `cambium`. You should see some descriptive output and a new directory called `_build`. `_build` contains the ready-for-use version of your site.

You can preview your site by running `python -m http.server -d _build` to start a web server from the `_build` directory, and visiting the link that Python outputs. If you see a blank page, that may mean that Cambium has created an empty `index.html` file in `_build`. If Cambium finds a pre-existing `index.md`, `readme.md` or `README.md`, it will use that as the homepage, but otherwise it will create a blank one. You can always list out the files in the build directory to see what HTML pages have been created and visit them directly.

## How Cambium works

- there are stages
- one major stage is transformMD which renders markdown documents into HTML with the help of a Jinja template
- Cambium copies your processed files, as well as some of its own additional files into the build directory

## Editing the configuration

Cambium reads the configuration file at `.cambium/config.yaml` if it exists. You can create this file with the default options by running

```bash
mkdir .cambium && cambium --dump-default-config > .cambium/config.yaml
```

## Custom styling

On top of the default style, Cambium loads `_build/static/css/custom.css`.

If `static/css/custom.css` exists, this is what will be used. If not, and `.cambium/theme/static/css/custom.css` exists, it will be used instead (following the usual rules of priority ordering of static files). If neither of these exist, an empty file will be created.

This is done to provide a location for CSS custom to be loaded from without needing to override the Jinja template, and to ensure that said location always exists, even as an empty file, to avoid 404s.

## Using the development server

## Advanced customization with Jinja
