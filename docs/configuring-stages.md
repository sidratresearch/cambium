# Stages

Cambium converts your documents into a website by running a series of "stages". Each stage has a specific purpose and may affect all files, or only a subset. Cambium runs these stages (each of which may have multiple parts, called "hooks") in the order specified by your configuration.
This list of enabled stages can be found in your configuration file, and the default list can be seen with `cambium --dump-default-config`.

<!-- TableOfContents(maxdepth=2) -->

## Controlling stages

- The list of active stages is controlled by the configuration file `.cambium/config.yaml`. Stages which are named in the config file are enabled, and the order in which they are listed is the order in which they will be run (subject to restrictions imposed by the stages themselves, see LINK Stage Interdependency for more detail).
- Config docs link to this
- How do I set configuration options for stages?
  - Config docs link to this
  - Within the `stage_config` entry in the configuration file, the name of each stage can be used as a key to a table of values with the options for that stage. EXAMPLE CODE
  - Stages can be disabled (removed from the list of stages), but remain in the `stage_config` with no issue.

## Builtin Stages

The builtin stages are listed below along with their purpose and configuration options (if any).

<!-- TableOfContents(section="builtin-stages", maxdepth=3) -->

### `CheckLinks`

`CheckLinks` verifies that links in Markdown and HTML documents point to valid endpoints on the site. External links (http, mailto, etc.) are not validated. Links that point to unknown files will result in warnings.

#### Configuration

- `links_to_ignore` is a list of strings where if a link matches any of those strings, the validity of the link will not be checked. Ideal if a page will be added to the output after running Cambium. Empty by default.

### `EnsureIndexPages`

`EnsureIndexPages` adds blank "index.html" pages to folders which don't have them. This prevents anyone from seeing the list of files present in the folder. Additionally, it can redirect "README.html" files to instead be located at "index.html".

#### Configuration

- `useable_as_index` is a list of strings which name files that can be redirected to become `index.html`. By default this includes `README.html` and `readme.html`, which will capture Markdown READMEs that have been converted to HTML by `TransformMarkdown`.

### `IdentifyMetadata`

`IdentifyMetadata` is a utility stage that collects information such as page titles, lists of headings, etc. for use by other stages. It is non-configurable and should always be present.

### `PagefindSearch`

[Pagefind](https://pagefind.app/) is a search engine for static sites. Enabling this stage runs the search indexer on all of the built webpages, and bundles the search index and required JavaScript into the built site. Note that the search bar will not appear unless your theme supports it. [Link to themes?]

#### Configuration

- `exclude_selectors`, `force_language`, `include_characters`, `keep_index_url`, `root_selector`, `write_playground` are all [as documented by Pagefind](https://pagefind.app/docs/config-options/).
- `include_characters` defaults to including `.` and `_`, so that searches for text such as "cambium.builtin_stages" will be performed as-is.
- If not set, `write_playground` will be set such that the Pagefind playground is written to `static/_cambium/PagefindSearch/playground` if you are running the dev server. Set this to `True` to always create the playground, or `False` to never create it.

### `PreviewCSV`

`PreviewCSV` builds "preview" pages for all CSV files in the directory. A preview page embeds the CSV content as an HTML table, and includes a download link to the actual file. Additionally, any Markdown files which link to CSVs will now link to the preview page instead.

#### Configuration

- `enable_paths` and `disable_paths` allow you to customize which files have previews created. Both are lists of strings in the same format as [LINK to config]. By default, all CSV files are enabled.
- `max_preview_rows` is the number of rows from a CSV to embed into the HTML table. The default value `None` embeds all rows.

### `Sitemap`

`Sitemap` generates a `sitemap.xml` in the top-level of your site. It requires that the `domain_name` option be set in your configuration. (Link)

### `TemplateMarkdown`

`TemplateMarkdown` places your Markdown content inside the template provided by your theme. Generally this will be run alongside `TransformMarkdown` to convert basic Markdown documents into an HTML website. `TemplateMarkdown` does not provide any of the styling or layout of the webpage, as that is all handled by the theme.

### `TransformMarkdown`

`TransformMarkdown` converts Markdown documents into HTML. This is also where Cambium-specific markup features (e.g., LINKS) are applied, and links between Markdown files are updated to point to the resulting HTML files.

#### Configuration

- `enable_paths` and `disable_paths` allow you to customize which files are converted from Markdown to HTML. Both are lists of strings in the same format as [LINK to config]. By default, all Markdown files are enabled.

### `WriteReports`

`WriteReports` creates special "report" pages that can provide additional information about the site. These are similar to "Special" pages on MediaWiki. Currently the only report available is HTML Pages, which lists and links to all of the HTML pages in the site.

#### Configuration

- `reports` is a list of the reports to include. Currently the only available report is `html_pages`.
- `report_directory` is where in the output directory the reports will go. Defaults to `_cambium-reports/`.
- `dev_only` indicates whether report pages should only be built when running the development server. Defaults to `False` which will build reports for both the development server, and the final build.

## How do I install, use, and configure additional stages?

- Anything loaded from an external package needs to be imported by Cambium, via the `extensions` key in the configuration. The stage can then be loaded by adding the entry `package_name.stage_name` to the stages list (assuming the stage can be directly imported from the package)
- When configuring external stages, the entry in `stage_config` should use the same `package_name.stage_name` structure as in the list of stages.
- EXAMPLE YAML as in cambium-astro

## Stage interdependency

- Stages may "require" other stages, which simply means that the dependency must also be present. For example, `TransformMarkdown` requires the `IdentifyMetadata` stage (as `IdentifyMetadata` finds all of the links that `TransformMarkdown` will need to update).
- Some stages also need to run in specific orders. For example, if `TemplateMarkdown` and `CheckLinks` are both enabled, then `TemplateMarkdown` needs to be listed first, as enforced by its `runs_before` attribute.
