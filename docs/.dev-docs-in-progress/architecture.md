# Cambium Architecture

Cambium has three core components:

- configuration
- tree
- stages

The configuration is what it sounds like. It's parsed and then stored within the tree object, which is the primary controller.

The tree (`TreeSpan`) object keeps track of the configuration, files, tasks to be done, etc. These _tasks_ primarily exist in the form of stages. A `Stage` is a collection of functions to be run on the files handled by Cambium.

## Files and Leaves

In Cambium, we make a best attempt to use "file" to refer to a specific location on the filesystem (e.g., `/home/writer/website/index.md`). Since this _file_ will be touched be Cambium and the contents may be stored in several locations on it's way to the final output path in `_build/`, we refer to that file-at-any-location concept as a _leaf_.So the leaf in this instance has an initial path `/home/writer/website/index.md`, it may have some intermediate paths, and a final path, perhaps `/home/writer/website/_build/index.html`. All of these files/paths belong to the same leaf.

## Stages

A `Stage` is called to operate on either the entire directory tree (via a tree hook) or a single leaf (via a pre-hook, transform, or post-hook).
The tree hook can interact with the list of leaves, adding and removing items as necessary. It also updates the list of hooks to be run on a per-leaf basis.
The remaining hooks are run on single leaves, and should only be reading or writing to that leaf.

## `TreeSpan`

The job of the `TreeSpan` class is to track and act on the directory tree. It is _only_ aware of the files that Cambium will interact with (i.e., not ignored files) and it does _not_ track files in `.cambium/`, `static/`, or `_build/`.

After performing the initial walk of the directory tree, `TreeSpan` stores the relevant paths as leaves.

In order to coordinate the actions that need to be performed on the leaves, the `TreeSpan` also runs the tree hooks for every stage and holds the list of hooks to run on each leaf.

Since it is the tree's job to manage leaves, it contains some helper functions for stages to use when they need to interact with the leaves.
