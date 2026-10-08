# Customizing the Website

## Global (non-specific) theme options

These options exist regardless of which theme you have picked. Most of the customization options live inside the '.cambium' folder.

### Setting Site Title and Theme

To set the title of your Cambium site:

- Create a '.cambium/config.yaml' file if it does not already exist
- Add the following line to the file: `site_name: [Insert site name here]`

By default, if you have not set your site name in the config file, Cambium will use the `h1` title in your home page (i.e. 'index.md' or 'README.md').

### Controlling Menu Content

Cambium will automatically put all your pages into the menu. To customize what shows up in the menu, you need to create a 'menu.md' file in the '.cambium' folder. Cambium will then use only the contents of this file to populate the menu. It will not do any conversion on the contents of the 'menu.md' file, so a list of file names will not work as menu links. Follow the guidelines below for formatting the links in your 'menu.md' file:

- All links need to be formatted as markdown links (e.g. `index.html` or `[Home](index.html)`)
- Links should point to the final html versions of your files, so they should end in '.html', not '.md'. as Cambium will not do any conversion on the contents of your 'menu.md' file
- Links should be put in an unorderd list

Here's an example of 'menu.md' file contents:

```
	- [Home](index.html)
	- [A folder](folder/index.html)
	- [Page two](page_two.html)
```

### Copyright (Footer) Text

To change the default copyright text that Cambium displays in the footers, create a file called 'footer_text.md' in the '.cambium' folder. The file should contain whatever text or content you want to be in the center of the footer on your website, and you can make use of Markdown styling options (i.e., making the text a link) to format it as you like.

### Overriding CSS Variables

To override any of the Cambium CSS variables provided:

- Create a file called 'custom.css' and put it in the `.cambium/` folder (you can also put it in `static/` instead).
- Inside that file, write out the variables you want to replace inside a `:root{}` pseudo-class tag. For example, to set the primary colour to white when in dark mode, your file would look like this:

  ```
  :root{
  --cambium-primary-colour-dark: #000000;
  }
  ```

### Common CSS Variables

#### Colours

The most commonly changed CSS variables are the colours. There are light and dark versions for each colour (for use in light and dark mode, respectively).

| Description                                                                                                            | Variables                                                                                       | Maple Value                                                                                                                                    |
| ---------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| Primary colour, used for the main accents                                                                              | `--cambium-primary-colour-light`<br/> `--cambium-primary-colour-dark`                           | `indianred`<br/>`#cba6a6`                                                                                                                      |
| Secondary colour, used mainly as a hover colour                                                                        | `--cambium-secondary-colour-light`<br/> `--cambium-secondary-colour-dark`                       | `oklch(from var(--cambium-primary-colour-light) 45% calc(c * 1.1) h)`<br/>`oklch(from var(--cambium-primary-colour-dark) 85% calc(c * 0.8) h)` |
| Background colour, used for all page backgrounds                                                                       | `--cambium-background-colour-light`<br/> `--cambium-background-colour-dark`                     | `white`<br/>`#1a1a1a`                                                                                                                          |
| Alternate background colour, used in places where a subtle difference from the main background is needed (i.e. tables) | `--cambium-alternate-background-colour-light`<br/> `--cambium-alternate-background-colour-dark` | `rgb(230, 230, 230)`<br/>`#333333`                                                                                                             |
| Font colour                                                                                                            | `--cambium-font-colour-light`<br/> `--cambium-font-colour-dark`                                 | `black`<br/>`#f9f9f9`                                                                                                                          |
| Secondary font colour, used for places where the font should be less prominent                                         | `--cambium-secondary-font-colour-light`<br/> `--cambium-secondary-font-colour-dark`             | `#595959`<br/>`#a9a9a9`                                                                                                                        |
| Border colour                                                                                                          | `--cambium-border-colour-light`<br/> `--cambium-border-colour-dark`                             |                                                                                                                                                |

#### Font

The font used across your Cambium website is set by the following variables. If you want to use a different font, [MDN's styling fundamentals](https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Text_styling/Fundamentals#font_families) has a list of commonly available fonts and how to use them. To use font families outside of this list, you will have to import the font inside your 'custom.css' file (see [MDN's tutorial on font families](https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Text_styling/Web_fonts#adding_your_own_web_fonts) for more information on how to go about this).

| Description                                                                                     | Variables                         | Maple Value                    |
| ----------------------------------------------------------------------------------------------- | --------------------------------- | ------------------------------ |
| Font size for main body text. Font sizes for mobile and template are calculated from this value | `--cambium-font-size`             | 16pt                           |
| The font family                                                                                 | `--cambium-font-family`           | "Source Sans 3 VF", sans-serif |
| The font weight, or how thick the font is                                                       | `--cambium-font-weight`           | 400                            |
| Monospace font family, used for code                                                            | `--cambium-monospace-font-family` | "Intel One Mono VF", monospace |
