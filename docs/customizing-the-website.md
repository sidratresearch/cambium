# Customizing the Website

Cambium is designed to make good-looking websites by default, as well as have several levels of customization, which make small tweaks easy and entirely custom designs possible. This page covers the options you have for customizing the design of your website.

<!-- TableOfContents(maxdepth=3) -->

## Configuration File Options

A few options for website design are present in the [configuration file](./config-file.md#theme). The `theme` entry allows you to select the all-in-one package to use as a starting point, and beyond that, there is the `theme_config` key. The [`site_name`](./config-file.md#site_name) is also used by the theme.

<!-- Ignoring the `maple` key of `theme_config` for now, since we don't have any entries there, or support external themes yet -->

`theme_config` allows for simple theme configuration, without creating any additional files. Currently it can have the key `default_colour_mode` which defines whether the website should default to dark or light mode. If `default_colour_mode` is not set, the default colourscheme is chosen by the theme designer.

An example snippet of a configuration file might be:

```yaml
site_name: Cambium Documentation

theme: maple

theme_config:
  default_colour_mode: dark
```

## Reusable Content

Cambium can read specially named files as custom pieces of re-usable content. These files are located in the `.cambium/` folder, and are identified by the file name - without the extension.

### Site Menu

Cambium will automatically generate a list of links that can be used as a menu. All pages in the top level of your website (`/page-name.html`), and index pages of the next level down (`/directory-name/index.html`) will be included. Your theme may choose how and where to display the menu items.

If you would like to customize which pages are visible in the menu (or re-arrange the pages that are there), you can create a file in `.cambium/` with the name `menu`.
If this file has a `.md` extension, Cambium will turn the contents into HTML before displaying it. Otherwise, the contents will be used directly in your website. This means that if you would like a very customized menu, you can create `.cambium/menu.html` and populate it however you like.

> [!NOTE]
> When creating custom menu files, always use absolute links (starting with `/`) rather than relative links.

An example `menu.md` might be:

```md
- [Home](/index.html)
- [Get Started](/get-started.html)
- [Configuration File](/config-file.html)
- [PyPi](https://pypi.org/project/cambium/)
```

### Favicon

Cambium provides a default favicon of the Cambium logo. To replace it, place your own image (must have the extension `.png`) at `static/images/favicon.png`. To use other filetypes see [Advanced Customization](#advanced-customization).

### Footer Content

By default, Cambium generates some text that can be used as a copyright line, with the copyright symbol, site name, and current year. Maple displays this text in both the page footer and at the bottom of the site menu.

This text can be replaced in the same manner as the site menu with a `.cambium/footer_content` file. Like the menu, you can use any file extension, but `.md` will signal to Cambium to convert the contents to HTML, allowing for simple use of formatting and links.

## Custom CSS

Cambium allows you to create additional CSS files which can add to or override the styling provided by your theme. If either of `static/custom.css` or `.cambium/custom.css` is present, Cambium will place it in the build directory at `static/custom.css`, and load it on every page.

To override the Cambium CSS variables, define your preferred versions inside the `:root` pseudo-class. For example, to set the primary colour to white when in dark mode:

```css
:root {
  --cambium-primary-colour-dark: #000000;
}
```

### Combining CSS Files

If you would like to use multiple CSS files, we recommend combining them with the [`@import` rule {target="_blank"}](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@import). Keep in mind that from the `.cambium/` folder, only `custom.css` will be copied to the build directory. Therefore, for this case, we recommend writing all of your CSS files in `static/`, and using relative imports from there.

### Cambium CSS Variables

Cambium and its themes define many CSS variables to ensure consistent styling and make customization easy. These are prefixed with either `--cambium-` or `--cw-`, to differentiate them from any variables you may wish to use separately.

The most useful CSS variables are listed below, along with their default values in the Maple theme.

#### Colours

The most commonly changed CSS variables are the colours. There are light and dark versions for each colour (for use in light and dark mode, respectively).

| Description                                                                                                            | Variables                                                                                       | Maple Value |
| :--------------------------------------------------------------------------------------------------------------------- | :---------------------------------------------------------------------------------------------- | :---------- |
| Primary colour, used for the main accents                                                                              | `--cambium-primary-colour-light`<br/> `--cambium-primary-colour-dark`                           | `indianred`<br/>`#cba6a6` |
| Secondary colour, used mainly as a hover colour                                                                        | `--cambium-secondary-colour-light`<br/> `--cambium-secondary-colour-dark`                       | `oklch(from var(--cambium-primary-colour-light) 45% calc(c * 1.1) h)`<br/>`oklch(from var(--cambium-primary-colour-dark) 85% calc(c * 0.8) h)` |
| Background colour, used for all page backgrounds                                                                       | `--cambium-background-colour-light`<br/> `--cambium-background-colour-dark`                     | `white`<br/>`#1a1a1a` |
| Alternate background colour, used in places where a subtle difference from the main background is needed (i.e. tables) | `--cambium-alternate-background-colour-light`<br/> `--cambium-alternate-background-colour-dark` | `rgb(230, 230, 230)`<br/>`#333333` |
| Font colour                                                                                                            | `--cambium-font-colour-light`<br/> `--cambium-font-colour-dark`                                 | `black`<br/>`#f9f9f9` |
| Secondary font colour, used for places where the font should be less prominent                                         | `--cambium-secondary-font-colour-light`<br/> `--cambium-secondary-font-colour-dark`             | `#595959`<br/>`#a9a9a9` |
| Border colour                                                                                                          | `--cambium-border-colour-light`<br/> `--cambium-border-colour-dark`                             |             |

#### Font

The font used across your Cambium website is set by the following variables. If you want to use a different font, [MDN's styling fundamentals {target="_blank"}](https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Text_styling/Fundamentals#font_families) has a list of commonly available fonts and how to use them. To use font families outside of this list, you will have to import the font inside your `custom.css` file (see [MDN's tutorial on font families {target="_blank"}](https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Text_styling/Web_fonts#adding_your_own_web_fonts) for more information on how to go about this).

| Description                                                                                     | Variables                         | Maple Value |
| :---------------------------------------------------------------------------------------------- | :-------------------------------- | :---------- |
| Font size for main body text. Font sizes for mobile and template are calculated from this value | `--cambium-font-size`             | 16pt        |
| The font family                                                                                 | `--cambium-font-family`           | "Source Sans 3 VF", sans-serif |
| The font weight, or how thick the font is                                                       | `--cambium-font-weight`           | 400         |
| Monospace font family, used for code                                                            | `--cambium-monospace-font-family` | "Intel One Mono VF", monospace |

## Advanced Customization

In some cases, you may wish to replace some of the files used by a theme in their entirety. This may include the CSS, JavaScript, image assets, or Jinja templates used to generate HTML. In this case, you can create the folder `.cambium/theme/`.

For non-template files, Cambium will copy anything from the directories `.cambium/theme/static/` and `static/` into the build directory under `static/`. If you include files which would overwrite ones provided by the theme, your files will always take precedence. This is the same principle as is used with the [favicon](#favicon).

If this theme directory contains a subfolder `templates/`, files there will override the Jinja templates provided by Cambium, assuming matching names. For example, the file `.cambium/theme/templates/footer.html.jinja` would be called in place of the `footer.html.jinja` provided by Maple.
To use a non-png file as a favicon, you would create `.cambium/theme/templates/favicon.html.jinja`, overriding the Cambium core template, and include your own `link` tag. You will need to use either an absolute link to the file, or the Jinja variable `relative_path_modifier`, which is calculated for each individual page on your site.

For example, to use an SVG favicon located at `assets/favicon.svg`, your template would contain:

```html
<link
  rel="icon"
  type="image/svg+xml"
  href="{{ relative_path_modifier }}assets/favicon.svg"
/>
```
