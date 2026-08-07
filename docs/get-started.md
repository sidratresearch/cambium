# Getting started with Cambium

## Installation

Cambium can be installed from PyPi via pip:

```bash
pip install cambium
```

## Your first run

`cd` to a folder containing some markdown files, and run `cambium`. You should see some descriptive output and a new directory called `_build`. `_build` contains the ready-for-use version of your site.

You can preview your site by running `python -m http.server -d _build` to start a web server from the `_build` directory, and visiting the link that Python outputs. If you see a blank page, that may mean that Cambium has created an empty `index.html` file in `_build`. If Cambium finds a pre-existing `index.md`, `readme.md` or `README.md`, it will use that as the homepage, but otherwise it will create a blank one. You can always list out the files in the build directory to see what HTML pages have been created and visit them directly.

## Licensing

The Cambium source is provided under a permissive MIT License. However, Cambium bundles additional files and content distributed under other licenses and copyrights. For example, the default theme uses fonts and icons licensed under the SIL Open Font License and Font Awesome Free License. Where this is the case, these licenses and attendant copyright information are packaged alongside the relevant assets.

## How Cambium works

- there are stages
- one major stage is transformMD which renders markdown documents into HTML with the help of a Jinja template
- Cambium copies your processed files, as well as some of its own additional files into the build directory

## Editing the configuration

Cambium reads the configuration file at `.cambium/config.yaml` if it exists. You can create this file with the default options by running

```bash
mkdir .cambium && cambium --dump-default-config >.cambium/config.yaml
```

## Custom styling

On top of the default style, Cambium loads `_build/static/css/custom.css`.

If `.cambium/theme/static/css/custom.css` exists, this is what will be used. If not, and `static/css/custom.css` exists, it will be used instead (following the usual rules of priority ordering of static files). If neither of these exist, an empty file will be created.

This is done to provide a location for CSS custom to be loaded from without needing to override the Jinja template, and to ensure that said location always exists, even as an empty file, to avoid 404s. This all also applies to `_build/static/js/custom.js`.

To assist in page-specific styling, Cambium applies a unique `id` to the `html` tag on each page.

## Using the development server

Running `cambium --dev` starts Cambium in development server mode. In this mode, Cambium opens an http server in the background, allowing you to view your site in a browser (by default the URL is [http://localhost:8000](http://localhost:8000)), and watches your files for changes, re-building the site on each change.

The port used for the web server, as well as the frequency Cambium checks for file changes are both configurable.

Changes to the configuration file are _not_ applied, and in fact if the configuration file changes, Cambium will exit the dev server to make this clear.

## Advanced customization with Jinja

Cambium uses Jinja templates to organize the rendering of Markdown content into HTML. If you aren't happy with using a pre-built theme, you can override Jinja templates by creating your own in `.cambium/theme/templates`.

We recommend copying an existing template and making modifications rather than starting entirely from scratch. When modifying, be careful to retain elements such as the development server block in `base.html.jinja`.

The Jinja templates can also read in content from files located in `.cambium/jinja_variables`. Files in that directory will have their contents available as Jinja environment variables. In the `default` theme, if a file named `menu` exists in that directory, that will trigger the rendering of a site menu in the header, containing the contents of the `menu`. Markdown files will be parsed into HTML, so it is often convenient to create `menu.md`.

## Pre-built Themes

Cambium comes with the pre-made _maple_ theme. If you would like to use another built-in theme, just change the `theme` entry in your configuration file. Currently only _maple_ and _root_ are available.
Themes can provide static files (CSS, JS, other assets) as well as Jinja templates. Any files not provided will be pulled from the "fallback" `root` theme. Any theme assets can of course be overridden by placing your own files within one of the static folders (see [Custom Styling](#custom-styling)).
