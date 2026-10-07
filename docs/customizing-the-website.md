# Customizing the Website

## Global (non-specific) theme options

These options exist regardless of which theme you have picked. Most of the customization options live inside the '.cambium' folder.

### Setting Site Title and Theme

To set the title of your Cambium site:

    - Create the '.cambium/config.yaml' file if it does not already exist
    - Add the following line to the file: `site_name: [Insert site name here]`

By default, if you have not set your site name in the config file, Cambium will use the `h1` title in your home page (i.e. 'index.md' or 'README.md').

### Controlling Menu Content

Cambium will automatically put all your pages into the menu. To customize what shows up in the menu, you need to create a 'menu.md' file in the '.cambium' folder. Cambium will then use the contents of this file to populate the menu. A list of file names will not work as menu links. In order for the file to create the menu links properly, follow the guidelines below: - Links should be formatted as such (i.e. [Home](index.html)) - Links should end in '.html', not '.md', as Cambium will not do any conversion on the contents of your 'menu.md' file

Example 'menu.md' file contents:

```
	- [Home](index.html)
	- [A folder](folder/index.html)
	- [Page two](page_two.html)
```

### Copyright (Footer) Text

To change the default copyright text that Cambium displays in the footers, create a file called 'footer_text.md' in the '.cambium' folder. We recommend creating it as a Markdown file, but any text file should work. The file should only contain whatever you want in the footer, and you can make use of Markdown styling options (i.e., making the text a link).

### Overriding CSS Variables

To override any of the Cambium CSS variables provided: - Create a file called 'custom.css' and put it in the '.cambium/' folder (you can also put it in `static/` instead). - Inside that file, write out the variables you want to replace inside a `:root{}` pseudo-class tag. For example, to set the primary colour to white:

```
:root{
--cambium-primary-colour-light: #000000;
}
```

### Common CSS Variables

#### Colours

The most commonly changed CSS variables are the colours. There are light and dark versions for each colour (for light and dark mode, respectively).

| Description                                                                                                            | Variables                                                                                  | Maple Value |
| ---------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ | ----------- |
| Primary colour, used for the main accents                                                                              | `--cambium-primary-colour-light` `--cambium-primary-colour-dark`                           |             |
| Secondary colour, used mainly as a hover colour                                                                        | `--cambium-secondary-colour-light` `--cambium-secondary-colour-dark`                       |             |
| Background colour, used for all page backgrounds                                                                       | `--cambium-background-colour-light` `--cambium-background-colour-dark`                     |             |
| Alternate background colour, used in places where a subtle difference from the main background is needed (i.e. tables) | `--cambium-alternate-background-colour-light` `--cambium-alternate-background-colour-dark` |             |
| Font colour                                                                                                            | `--cambium-font-colour-light` `--cambium-font-colour-dark`                                 |             |
| Secondary font colour, used for places where the font should be less prominent                                         | `--cambium-secondary-font-colour-light` `--cambium-secondary-font-colour-dark`             |             |
| Border colour                                                                                                          | `--cambium-border-colour-light` `--cambium-border-colour-dark`                             |             |

#### Font

To use different font families, you may also have to import the font inside your 'custom.css' file.

[May want to change wording to note that some common fonts (what can be expected to be pre-installed) don't actually need to be imported, may or may not want to give detail on what importin means, or link to the relevant source within cambium]
TODO: add in links to these pages for more info on this? - Fundamental text and font styling - Learn web development | MDN - Web fonts - Learn web development | MDN

| Description                                                                                      | Variables                         | Maple Value                    |
| ------------------------------------------------------------------------------------------------ | --------------------------------- | ------------------------------ |
| Font size for main body text. Font sizes for mobile and template are calculated from this value. | `--cambium-font-size`             | 16pt                           |
| The font family                                                                                  | `--cambium-font-family`           | "Source Sans 3 VF", sans-serif |
| The font weight                                                                                  | `   --cambium-font-weight`        | 400                            |
| Monospace font family, for code                                                                  | `--cambium-monospace-font-family` | "Intel One Mono VF", monospace |
