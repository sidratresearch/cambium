<p align="center">
<a href="https://github.com/sidratresearch/cambium">
<img src="docs/assets/cambiumlogo.png" width="200" height="200">
</a>
</p>

<h1 align="center">Cambium</h1>
<p align="center">A Light Touch Markdown Static Site Generator</p>
<br />

![Static Badge](https://img.shields.io/badge/status-pre--alpha-orange)
![PyPI - Version](https://img.shields.io/pypi/v/cambium)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/cambium)
![PyPI - License](https://img.shields.io/pypi/l/cambium)

A Python-based static site generator for repositories of organized markdown pages.

**This package is under active development and is pre-alpha. Please use with caution.**

## Why Use Cambium?

- Do you have a bunch of markdown files that you'd like to turn into a static site?
- Do you want to create a rapidly-changing wiki, knowledge base or documentation site that can be hosted without worrying about server requirements?
- Do you want to manage your documents using tools you already know and love
- Do you want to store your source files in a git repository, a directory on Dropbox, OneDrive, or other place that you can just have files?
- Do you want to be able to customize the look-and-feel of your generated site in a simple fashion?
- Do you want to avoid lock-in to a specific site generator?

## Design Principles

Cambium is built on the following design principles:

- You should be able to organize your markdown documents in whatever way you'd like
- Your markdown repository should not have to know that it is being used by Cambium
- Cambium-specific features or macros should be clean and obvious in the markdown
- Cambium should be able to work elegantly on a repository of markdown documents with no configuration
- Your final deployment destination should not matter

## Installation Instructions

To install Cambium, run:

```
pip install cambium
```

## Running Cambium

To run Cambium, in a folder containing Markdown documents, run:

```
cambium
```

This will create a `_build` directory, containing the output HTML. The contents of this folder can be uploaded to any web server or displayed locally.
