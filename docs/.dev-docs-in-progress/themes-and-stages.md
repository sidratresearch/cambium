## A theme can

- Provide Jinja templates that directly override root
- Provide static files that directly override root
- Provide additional Jinja templates
- Provide additional static files
- Provide Jinja templates that include or override stage-provided Jinja templates
  - A theme can’t know what stages are turned on/off, so while it can attempt to include stage templates, this could fail if the user doesn't have the relevant stage installed/activated.

## A theme must

- (if overriding relevant Jinja) provide a location for stage-requested CSS and JS files
- (if overriding relevant Jinja) provide a location for dev server files
- Not provide the files `static/css/custom.css` or `static/css/custom.js`

## Themes *should*

- Avoid overriding `static/css/base.css` unless the theme is a ground-up rewrite. The `base.css` included by default is intended to be minimal and unobtrusive. Theme-specific styles should go into `static/css/theme.css`
- *Not* assume the presence of any given stage. While any stage may be installed into the Python environment, there is no guarantee that a stage is enabled in the configuration. Themes should be written to be aware of this.

## A stage can

- Provide a single entrypoint CSS file to Cambium that should be imported in the Jinja
- Provide a single entrypoint JS file to Cambium that should be imported in the Jinja
- Provide any number of static files to be copied into `_build/static/_cambium/<stage name>` (and potentially imported by that entrypoint file)
- Provide “component” Jinja files (`PagefindSearch-searchbar.html.jinja`), and add these to the list of templates searched by Jinja
- Tell the user how to include those components ("create `.cambium/theme/templates/header-right.html.jinja` and put `...` it")
- Write files directly into `_build/static/_cambium/<stage name>` post tree hook
  - e.g. Pagefind's search index

## An external package can

- Provide any number of stages
- Provide any number of themes
