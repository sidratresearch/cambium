# Configuration File

When `cambium` is run, it will look for a configuration file called `config.yaml` in a folder named `.cambium` in the current directory. The [`--config`](./command-line-options.md#--config) option can also be passed to specify another location.

A Cambium configuration file is a YAML document. The default configuration for your installed version can be seen by running [`cambium --dump-default-config`](./command-line-options.md#--dump-default-config).

## Options

<!-- TableOfContents(section="options") -->

### Input and output control

#### `root_directory`

See [documentation for the CLI option `--root-directory`](./command-line-options.md#--root-directory).

#### `build_directory`

See [documentation for the CLI option `--build-directory`](./command-line-options.md#--build-directory).

#### `paths_to_ignore`

List of paths that will not be touched at all by Cambium. Files matching these paths will not be read, modified, or bundled into the website. The syntax of these entries is akin to a `gitignore`.
In addition to the configurable list of paths, Cambium also has a builtin ignore list, which is combined with the configuration entry. The builtin ignore list covers:

- Hidden files (filenames starting with `.`)
- `__pycache__` files
- Anything which ends in `~` (such files are often created by text editors)

#### `extensions_to_ignore`

In addition to ignoring files by path, files can also be ignored by their extension. This is a list of extensions, where files matching these extensions will be ignored in the same manner as `paths_to_ignore`. Empty by default.

#### `protected_build_paths`

List of paths where Cambium should not write files. This option can be used in the case where some files served on the website do not originate from Cambium, setting those paths as protected ensures that Cambium will exit if a file would be created there. Empty by default.

### About your website

#### `site_name`

The name of the website, as it appears in the tab title (and other locations, dependent on your theme). If not set, Cambium will attempt to use the contents of the first top-level heading in the file that becomes `index.html`. If this is also not found, it will fall back to `Cambium Site`.

#### `domain_name`

The domain where your site will be hosted, empty by default. Should begin with `https://`.

#### `subpath`

The subpath (if any) where your site will be hosted, e.g., if your site will be at `buildwithcambium.org/docs`, then the `domain_name` is `https://buildwithcambium.org` and the `subpath` is `docs`.

### Stages and themes

<!-- Bundled together mostly because of "extensions", which will eventually apply to themes too. It also has effects on macros, but those aren't mentioned in the heading since there's no macro-specific options -->

#### `extensions`

A list of Python packages that Cambium will import. Stages and macros from these packages should be accessible as `package_name.stage_name`.

#### `stages`

The ordered list of stages Cambium will run. See [Configuring Stages](./configuring-stages.md) for additional information on how Cambium uses stages and what each stage does. The default list of stages is:

- `PreviewCSV`
- `IdentifyMetadata`
- `WriteReports`
- `TransformMarkdown`
- `TemplateMarkdown`
- `EnsureIndexPages`
- `PagefindSearch`
- `CheckLinks`

#### `stage_config`

Configuration entries for the stages. See [Configuring Stages](./configuring-stages.md) for additional information.

#### `theme`

The set of templating and styling files to use when building the site. Currently we provide our flagship theme `maple`. Additional themes, and the ability to install and use external themes will be added as Cambium develops. To customize the currently available theme, see [Customizing the Website](./customizing-the-website.md).

#### `theme_config`

Configuration options for the theme, if any. See [Customizing the Website](./customizing-the-website.md#configuration-file) for information on what options are available and how to use them.

### Additional options

#### `max_leaves`

The maximum number of files Cambium can work with. This is not a technical limitation and is intended to provide a warning in the case that Cambium is run in an unintended directory. By default this is 10,000.
