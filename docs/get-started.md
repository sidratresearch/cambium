# Getting started with Cambium

<!-- TableOfContents(maxdepth=2) -->

## Quickstart

Cambium can be installed from PyPI via pip:

```bash
pip install cambium
```

Navigate to a directory containing some Markdown files. Then, run Cambium:

```bash
cambium
```

You should see some descriptive output and a new directory `_build`, which contains the ready-for-use version of your site. To preview the site, use your favourite live server, or use Python's native HTTP server with:

```bash
python -m http.server -d _build
```

and visit the site in a browser, at [`http://localhost:8000`](http://localhost:8000/).

If your directory had a file named `index.md` or `index.html`, that file will be displayed. Otherwise, if you had a Markdown or HTML file named `readme` or `README`, that file will be rendered to `index.html`. If none of these are present, Cambium creates a blank `index.html`, and you'll need to navigate to a specific URL.

## Built-in features

Cambium includes support for all basic Markdown syntax, some common Markdown extensions, and some custom features on top of that. See the page on [writing content for Cambium](./writing-content.md) for details.

In addition to Markdown processing, by default Cambium builds your website with search, a light and dark theme, and a menu listing all top-level pages.

## Using the development server

Running `cambium --dev` starts Cambium in development server mode. In this mode, Cambium opens an http server in the background, allowing you to view your site in a browser, and watches your files for changes, re-building the site on each change. For details and configuration, see the [Development Server documentation](./command-line-options.md#development-server).

## Configuring Cambium

Cambium's [command line options](./command-line-options.md) can affect the input and output locations and verbosity of Cambium, but for anything that affects the final look and functionality of the website Cambium uses a YAML configuration file. Cambium will automatically apply configuration found in `.cambium/config.yaml` or `.cambium/config.yml`.

Options such as the site name, search configuration, and files to ignore can all be set [in the configuration file](./config-file.md).

## How Cambium works

Cambium runs through a series of phases: a setup section, some main work phases, and a finalization. The setup and finalization are primarily housekeeping and copying files, the actual process of converting Markdown content into a website takes place within the work phases.

Cambium is built from a series of modular ["stages"](./configuring-stages.md). Each stage can optionally process data during each of the work phases, but some are done earlier than others. For example, [`PreviewCSV`](./configuring-stages.md#previewcsv) writes Markdown files early on, which are converted to HTML by [`TransformMarkdown`](./configuring-stages.md#transformmarkdown), and then placed into the theme-provided template by [`TemplateMarkdown`](./configuring-stages.md#templatemarkdown).

Cambium processes all of the files and makes all modifications within a temporary directory. This ensures that under no circumstances is your original content modified. After all of the stages are complete, Cambium copies everything from the temporary location into the build directory.

### Special Directories

Cambium uses some special directory names in order to separate the bulk of the content from special files used for customization. Some of these directories are relevant in the [root](./command-line-options.md#--root-directory) (typically where Cambium is run), and some in the [build](./command-line-options.md#--build-directory) (where Cambium outputs your site).

#### `.cambium/`

If this is present in the root, Cambium will look for specially named files for configuration and customization. Files in here which are *not* specially named (e.g. `.cambium/cofnig.yaml`) will be ignored - they will not be read or copied to the build directory.

#### `static/`

Any files in the root directory within the `static/` subfolder will be copied directly to the build directory following the same path. For example, `static/example.md` will be copied to `_build/static/example.md`, without being transformed into HTML.

Additionally, Cambium may create or relocate other files into `static`. The CSS and JavaScript files which make up your theme will be placed here (typically within subfolders). If you use a [`custom.css`](./customizing-the-website.md#custom-css) file, it will be built to `static/custom.css`.

In addition to theme files, some [stages](./configuring-stages.md) may also need to write files to the build directory. These may be specific styles, or data files (such as a search index). In this case, files will be written to the build directory under `static/_cambium/` in a directory with the same names as the stage.

## What to do if there are issues

If you run into issues with Cambium, there are several steps than can be taken to help diagnose the issue.

1. If you have a configuration file, test if the issue occurs without it.
   - If the problem resolves, try reverting individual configuration entries to their default values to narrow down which value triggers the issue.
2. Check if the issue seems to be caused by a specific file. If so, there may be something about that file which Cambium cannot handle (e.g., macros called with incorrect arguments, or a malformed CSV).
   - Renaming the file to start with a `.` will cause Cambium to ignore it - this can be a good way to verify if one specific file is problematic.
3. Run Cambium with all of its debugging options: `cambium --fail-fast --verbose --show-traceback`. This will cause Cambium to show full debugging output, quit the first time it encounters an error, and produce the full Python traceback.

Issues should be reported on [GitHub {target="_blank"}](https://github.com/sidratresearch/cambium). Include the version being used (`cambium --version`), along with anything found from the above steps. If a specific file or configuration is causing an issue, providing a complete copy of the files will help greatly.
