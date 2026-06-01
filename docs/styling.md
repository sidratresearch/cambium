On top of the default style, Cambium loads `_build/static/css/custom.css`.

If `static/css/custom.css` exists, this is what will be used. If not, and `.cambium/theme/static/css/custom.css` exists, it will be used instead (following the usual rules of priority ordering of static files). If neither of these exist, an empty file will be created.

This is done to provide a location for CSS custom to be loaded from without needing to override the Jinja template, and to ensure that said location always exists, even as an empty file, to avoid 404s.
