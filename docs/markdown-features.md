# Markdown in Cambium

Cambium uses the markdown parser [Marko](https://marko-py.readthedocs.io/en/latest/) with it's built-in GitHub flavoured markdown (GFM) extension in order to parse markdown documents and render them as HTML.

The following table shows a list of common markdown features and their support in Cambium. It should be reasonably up to date with respect to the features currently available for use in Cambium. The list of unsupported features is naturally incomplete, but represents a rough approximation of the featureset Cambium may expand to cover.

| Feature                                           | Supported via Marko? | Additional Cambium Features |
| :------------------------------------------------ | -------------------- | :-------------------------- |
| [Thematic breaks][thematic-breaks]                | ✅                   |                             |
| [`#` (ATX) Headings][thematic-breaks]             | ✅                   | Custom attributes           |
| [Underlined (setext) headings][setext-headings]   | ✅                   | Custom attributes           |
| [Indented code blocks][indented-code-blocks]      | ✅                   |                             |
| [Fenced code blocks][fenced-code-blocks]          | ✅                   |                             |
| [HTML blocks][html-blocks]                        | ✅                   |                             |
| [Named links][link-reference-definitions]         | ✅                   |                             |
| [Paragraphs][paragraphs]                          | ✅                   |                             |
| [Block quotes][block-quotes]                      | ✅                   | Custom attributes           |
| [Lists][lists]                                    | ✅                   | Custom attributes           |
| [Inline code spans][code-spans]                   | ✅                   |                             |
| [Italics and bold][emphasis]                      | ✅                   |                             |
| [Links][links]                                    | ✅                   | Links to Markdown documents remain correct after HTML transformation. Previewer stages. Custom attributes. |
| [Images][images]                                  | ✅                   | Wrapped in special `div`. Custom attributes |
| [Autolinks][autolinks]                            | ✅                   |                             |
| [Tables (GFM)][tables]                            | ✅                   | Wrapped in special `div`, sorting JS, custom attributes |
| [Task lists (GFM)][task-list-items]               | ✅                   |                             |
| [Strikethrough (GFM)][strikethrough]              | ✅                   |                             |
| [Expanded autolinks (GFM)][autolinks-gfm]         | ✅                   |                             |
| [Colour pips (GitHub Extra)][colours-gh-extra]    | ❌                   |                             |
| [Emojis (GitHub Extra)][emojis-gh-extra]          | ❌                   |                             |
| [Footnotes (GitHub Extra)][footnotes-gh-extra]    | ❌                   |                             |
| [Alerts/callouts (GitHub Extra)][alerts-gh-extra] | ✅                   |                             |
| [Diagrams (GitHub Extra)][diagrams-gh-extra]      | ❌                   |                             |
| [LaTeX (GitHub Extra)][latex-gh-extra]            | ❌                   |                             |
| [Definition lists (GitLab)][definitions-gl-extra] | ❌                   |                             |
| [Frontmatter (GitLab)][frontmatter-gl-extra]      | ❌                   |                             |

[thematic-breaks]: https://spec.commonmark.org/0.31.2/#thematic-breaks
[atx-headings]: https://spec.commonmark.org/0.31.2/#atx-headings
[setext-headings]: https://spec.commonmark.org/0.31.2/#setext-headings
[indented-code-blocks]: https://spec.commonmark.org/0.31.2/#indented-code-blocks
[fenced-code-blocks]: https://spec.commonmark.org/0.31.2/#fenced-code-blocks
[html-blocks]: https://spec.commonmark.org/0.31.2/#html-blocks
[link-reference-definitions]: https://spec.commonmark.org/0.31.2/#link-reference-definitions
[paragraphs]: https://spec.commonmark.org/0.31.2/#paragraphs
[block-quotes]: https://spec.commonmark.org/0.31.2/#block-quotes
[lists]: https://spec.commonmark.org/0.31.2/#lists
[code-spans]: https://spec.commonmark.org/0.31.2/#code-spans
[emphasis]: https://spec.commonmark.org/0.31.2/#emphasis-and-strong-emphasis
[links]: https://spec.commonmark.org/0.31.2/#links
[images]: https://spec.commonmark.org/0.31.2/#images
[autolinks]: https://spec.commonmark.org/0.31.2/#autolinks
[tables]: https://github.github.com/gfm/#tables-extension-
[task-list-items]: https://github.github.com/gfm/#task-list-items-extension-
[strikethrough]: https://github.github.com/gfm/#strikethrough-extension-
[autolinks-gfm]: https://github.github.com/gfm/#autolinks-extension-
[colours-gh-extra]: https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax#supported-color-models
[emojis-gh-extra]: https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax#using-emojis
[footnotes-gh-extra]: https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax#footnotes
[alerts-gh-extra]: https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax#alerts
[diagrams-gh-extra]: https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams
[latex-gh-extra]: https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/writing-mathematical-expressions
[definitions-gl-extra]: https://docs.gitlab.com/user/markdown/#description-lists
[frontmatter-gl-extra]: https://docs.gitlab.com/user/markdown/#front-matter
