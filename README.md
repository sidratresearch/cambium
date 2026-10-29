<p align="center">
    <a href="https://buildwithcambium.org">
        <!-- Use full path for visibility on PyPI -->
        <img src="https://raw.githubusercontent.com/sidratresearch/cambium/refs/heads/main/docs/assets/CambiumMainLogoVertical.svg" width="200" height="200" alt="Cambium logo">
    </a>
</p>

<h1 align="center">Cambium</h1>
<p align="center">A Light Touch Markdown Static Site Generator</p>
<br />

<div>
    <img src="https://img.shields.io/pypi/status/cambium" alt="Development status: Beta"/>
    <img src="https://img.shields.io/pypi/v/cambium" alt="Currently available on PyPI"/>
    <img src="https://img.shields.io/pypi/pyversions/cambium" alt="List of compatible Python versions"/>
    <img src="https://img.shields.io/pypi/l/cambium" alt="MIT licensed"/>
</div>
<br />

A Python-based static site generator for repositories of organized Markdown pages.

> [!IMPORTANT]
> This package is under active development, and some things are subject to change. See [the documentation](./docs/index.md#status-and-future-outlook) for details on what the development status means for stability.

## Why Use Cambium?

- Do you have a bunch of Markdown files that you'd like to turn into a static site?
- Do you want to create a rapidly-changing wiki, knowledge base or documentation site that can be hosted without worrying about server requirements?
- Do you want to manage your documents using tools you already know and love
- Do you want to store your source files in a Git repository, a directory on Dropbox, OneDrive, or other place that you can just have files?
- Do you want to be able to customize the look-and-feel of your generated site in a simple fashion?
- Do you want to avoid lock-in to a specific site generator?

## Design Principles

Cambium is built on the following design principles:

- You should be able to organize your Markdown documents in whatever way you'd like
- Your Markdown repository should not have to know that it is being used by Cambium
- Cambium-specific features or macros should be clean and obvious in the Markdown
- Cambium should be able to work elegantly on a repository of Markdown documents with no configuration
- Your final deployment destination should not matter

## Installation Instructions

To install Cambium, run:

```sh
pip install cambium
```

## Running Cambium

To run Cambium, in a folder containing Markdown documents, run:

```sh
cambium
```

This will create a `_build` directory, containing the output HTML. The contents of this folder can be uploaded to any web server or displayed locally.

## Creators

<a href="https://www.sidratresearch.com/">
    <!-- Use full path for visibility on PyPI -->
    <img src="https://raw.githubusercontent.com/sidratresearch/cambium/refs/heads/main/docs/assets/SidratLogo.svg" width="150" height="150" alt="Sidrat Research Logo">
</a>

Cambium is a project of [Sidrat Research](https://www.sidratresearch.com).

## Copyright and License

Code and documentation copyright 2026 [Sidrat Research](https://www.sidratresearch.com). Code released under the [MIT License](LICENSE).
