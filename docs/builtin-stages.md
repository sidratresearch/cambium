Documentation for the stages built into the core Cambium package.

Is this where we want to put documentation on stage config options?

- CheckLinks
- EnsureIndexPages
  - Creates `index.html` files in all non-static folders. This prevents someone from seeing the complete listing of files in a given folder (as they will instead be served the blank `index.html` page).
  - Also (optionally) moves files which would be served at `README.html` to instead become `index.html`. Redirect pages will be created from the original endpoint.
- IdentifyMetadata
- PagefindSearch
- PreviewCSV
- Sitemap
- TemplateMarkdown
- TransformMarkdown
- URLEncodeFilenames
- WriteReports
