# Writing content for Cambium

As a Markdown-focused project, most of the content written for a Cambium website should likely be in Markdown format. Exactly which features are included in a given Markdown tool varies wildly - Cambium aims to incorporate a "common sense" set of features. Under the hood we use the CommonMark compliant parser [Marko](https://marko-py.readthedocs.io/en/latest/), along with its builtin GitHub Flavoured Markdown (GFM) extension.

 For the cases where additional control is needed, Markdown documents can contain blocks of HTML. Cambium passes these HTML blocks through unchanged, so your output exactly matches your input.

Cambium will also work with HTML files, copying them directly to the build directory along with your images and other assets. For webpages where complex design is needed, this is typically the best option.

However, there are cases where a middle ground between Markdown and HTML is desired, for which Cambium has implemented some special features.

<!-- TableOfContents(maxdepth=3) -->

## Heading Anchors

Like GitHub and GitLab (among others), Cambium automatically adds `id` attributes to headings. This allows you to link directly to specific sections of your page.
We aim to produce the same ids as other systems, so that links will work regardless of whether your Markdown is rendered by Cambium or another service.

## Wrapped Images and Tables

Cambium automatically wraps tables and images in `div` tags with a special class. This allows for improved default styling that can be opted out of as-needed by writing the HTML for your content directly within the Markdown.

Since this is intended to style full-width elements, images which appear to be inline (i.e., embedded within text, rather than surrounded by blank lines) will not be wrapped.

## Custom Markup

Cambium's custom markup allows you to add HTML classes and attributes to arbitrary blocks of content, without embedding the entire block in HTML. This markup is intended to be as invisible as possible when documents are rendered outside of Cambium.

The custom markup comes in two flavours: inline and block. Both use the same syntax for adding classes (`.class-name`, similar to a CSS selector) and attributes (`attribute-name` or `key=value`).
If an attribute is specified multiple times, only the first declaration will be used.

>[!NOTE]
> Cambium does not enforce correctness or validate the custom markup being used, this has the potential to result in incorrect HTML.

### Inline Markup

Inline markup can be applied only to images and links, in both cases the markup is denoted with in curly braces at the end of the descriptive text.

An image defined as:

```md
![Descriptive alt text {.img-class .img-class-2 width="300"}](image.jpg)
```

will produce the following HTML:

```HTML
<img
  src="image.jpg"
  alt="Descriptive alt text"
  class="img-class img-class-2"
  width="300"
/>
```

Links are similarly handled:

```md
[The Cambium Project {.external inert target="_blank"}](https://buildwithcambium.org)
```

becomes:

```HTML
<a
  href="https://buildwithcambium.org"
  class="external"
  inert
  target="_blank"
>
  The Cambium Project
</a>
```

### Block Markup

Attributes can also be applied to certain block elements: headings, lists, block quotes, tables, images, and code blocks. In these cases, the markup is embedded in an HTML comment directly before the element.

#### Headings, Lists, and Quotes

The following Markdown example:

```md
<!-- {.special-heading} -->
## This heading is special

<!-- {.ingredients data-dietary="vegetarian"} -->
- celery
- carrots
- eggs

<!-- {.alert .alert-note} -->
> Custom Alert
>
> This quote uses Cambium's alert classes to get the styling of a note alert, but a custom heading.
```

renders to:

```HTML
<h2 id="this-heading-is-special" class="special-heading">
  This heading is special
</h2>
<ul class="ingredients" data-dietary="vegetarian">
  <li>celery</li>
  <li>carrots</li>
  <li>eggs</li>
</ul>
<blockquote class="alert alert-note">
    <p>Custom Alert</p>
    <p>This quote uses Cambium's alert classes to get the styling of a note alert, but a custom heading.</p>
</blockquote>
```

#### Images and Tables

The markup applied to the table and image blocks goes directly to the `table` and `img` tags, within the special Cambium wrappers.

The following Markdown example:

```md
<!-- {id="network-table"} -->
| IP Address  | Hostname |
| ----------- | -------- |
| 192.168.0.1 | desktop  |
| 192.168.0.2 | server   |
| 192.168.0.3 | nas      |

<!-- {style="max-width: 100px;"} -->
![Image description](./image.jpg)
```

renders to:

```HTML
<div class="cambium-table-holder">
  <table id="network-table">
    <thead>
      <tr>
        <th>IP Address</th>
        <th>Hostname</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>192.168.0.1</td>
        <td>desktop</td>
      </tr>
      <tr>
        <td>192.168.0.2</td>
        <td>server</td>
      </tr>
      <tr>
        <td>192.168.0.3</td>
        <td>nas</td>
      </tr>
    </tbody>
  </table>
</div>
<div class="cambium-img-holder">
  <img style="max-width: 100px;" src="./image.jpg" alt="Image description" />
</div>
```

#### Code Blocks

Cambium only supports custom markup on fenced code blocks (those using triple backticks or tildes). For these, the markup goes on the same line as the opening code fence, after a language declaration (if any).

The markup attributes will be applied to the inner `code` tag, along with any `language-` class.

With a specified language:

````md
```python {.python-examples}
print("Hello world!")
```
````

becomes:

```html
<pre>
    <code class="python-examples language-python">print("Hello world!")</code>
</pre>
```

Markup is still applied without a language declaration:

````md
```{data-no-language}
Just some pre-formatted text in a code tag.
```
````

becomes:

```html
<pre>
    <code data-no-language>Just some pre-formatted text in a code tag.</code>
</pre>
```

## Macros

Cambium provides a "macros" feature, where Python functions can be called from within your Markdown document. These macros are called via HTML comments, so operate at the block level only - a macro cannot be called in the middle of a paragraph.

Macros can take parameters, as well as consume part of the document as content to be modified.

To call a macro, call it like a function in an HTML comment:

```md
<!-- MyMacro() -->
```

Arguments are passed as Python code, with separating commas:

```md
<!-- MyMacro(2, "maximum", block_style=True) -->
```

Only simple Python datatypes are valid for use in macro parameters: compound types such as lists, tuples, and dicts cannot be used.

To pass a segment of your document to the macro, use the `start` and `stop` keywords (include parameters in the start call if relevanst):

```md
<!-- MyMacro() start -->
The macro will recieve this as plain text.
<!-- MyMacro() stop -->
```

Macros that receive content will get it as the original Markdown text, not transformed to HTML. Any macro calls which are inside this content will *not* be executed.

### Builtin macros

#### `CambiumLink`

A minimal example of a macro - inserts a link to the Cambium website.

Markdown:

```md
<!-- CambiumLink() -->
```

HTML:

```html
<a href="https://buildwithcambium.org">Cambium</a>
```

#### `CaptionedImage`

Creates a `figure` element.

Markdown:

```md
<!-- CaptionedImage("image.png", alt="Descriptive text") start -->
Caption for the image.
<!-- CaptionedImage() stop -->
```

HTML:

```html
<div class="cambium-img-holder">
    <figure>
        <img src="image.png" alt="Descriptive text">
        <figcaption>Caption for the image.</figcaption>
    </figure>
</div>
```

#### `TableOfContents`

Creates a table of contents for headings on the current page, rendered as a `nav` tag containing a nested list of `ul` tags, each with a `toc-level-[LEVEL]` class indicating the heading level.

Markdown:

```md
<!-- TableOfContents() -->

## First H2

### First H3

### Second H3

## Second H2

## Third H2
```

HTML (omitting the heading tags):

```html
<nav class="cambium-table-of-contents">
  <ul class="toc-level-2">
    <li><a href="#first-h2">First H2</a></li>
    <ul class="toc-level-3">
      <li><a href="#first-h3">First H3</a></li>
      <li><a href="#second-h3">Second H3</a></li>
    <li><a href="#second-h2">Second H2</a></li>
    <li><a href="#third-h2">Third H2</a></li>
  </ul>
</nav>
```

Takes the following keyword arguments:

- `mindepth` - default 2, the lowest heading level to include.
- `maxdepth` - default 6, the highest heading level to include.
- `section` - if passed, this must be the `id` of a heading in the current page, the rendered ToC will only include headings within that part of the document. Modifying the previous example:

    ```md
    <!-- TableOfContents(section="first-h2") -->

    ## First H2

    ### First H3

    ### Second H3

    ## Second H2

    ## Third H2
    ```

    now renders:

    ```html
    <nav class="cambium-table-of-contents">
      <ul class="toc-level-3">
        <li><a href="#first-h3">First H3</a></li>
        <li><a href="#second">Second H3</a></li>
      </ul>
    </nav>
    ```

- `inline` - if `True`, the `nav` tag will also include a `cambium-inline-table-of-contents` class.

### Using non-builtin macros

In order to be available to Cambium, the package providing a macro must be included in the `extensions` key of the configuration file:

```yaml
extensions:
  - package_with_macros
```

Then, with the macro importable at `package_with_macros.CustomMacro`, that import syntax is used to call the macro:

```md
<!-- package_with_macros.CustomMacro() -->
```
