# Notes on Developing Stages

- `initial_path` should be treated as read-only
- `final_path` should only be changed be tree hooks

## The 'Jobs' of Stage Hooks

- Tree hooks
    - Identify and mark leaves that need future work (e.g., markdown files to transform, directories missing index.html)
    - Create and remove leaves as necessary
    - Update `final_path`
- Pre-hooks
    - Collect information (e.g., metadata), where possible at the pre-hook stage
    - Modify the contents (without major transformation), writing back to `latest_path`
- Transforms
    - Perform major modifications to the file (md->html, jpg->webp)
- Post-hooks
    - Collect any information only available after transformation
    - Perform additional modifications only available after transformation (e.g., Jinja templating)

## Hook Initialization and Finalization

## Other Stage Responsibilities

_Tree hooks should be as lightweight as possible_. Tree hooks may rely on eachother, and so cannot be parallelized stage-wise; but may also add or remove leaves, and so cannot be parallelized leaf-wise either.

### Managing Paths

If stage edits the path of a leaf, it likely needs to do that twice: once in the `tree_hook` to set `final_path`, and once in another hook when the action is being taken, and data is written to an updated `latest_path`.
While a stage can safely assume that the absolute path provided by `TreeSpan.abs_write_path(leaf_uuid)` always contains the most recent copy of the data, assumptions _cannot_ safely be made regarding what the actual path returned will be, because other stages may have modified `latest_path`.

So, when setting `latest_path` in a pre/post/transform hook, a stage needs to apply the change to the current `latest_path`, _not_ to `initial_path` since other changes may have happened causing `latest_path` to not look like `initial_path`.

For example:

1. The tree hook for `URLEncodePaths` sees a file named `cats or dogs.md`, and sets `final_path` to `cats-or-dogs.md`
2. The tree hook for `TransformMarkdown` sees final path `cats-or-dogs.md` and wants to change the extension to `.html`. In order to not revert the changes made by `URLEncodePaths`, the new `final_path` needs to be `final_path.with_suffix(".html")` _not_ `initial_path.with_suffix(".html")`
3. `TreeSpan` copies all initial paths (currently equivalent to latest paths) into the temporary directory
4. The pre-hook for `URLEncodePaths` moves the file from `latest_path="cats or dogs.md"` (accessing the temporary directory copy with `TreeSpan.abs_write_path(leaf_uuid)`) to `cats-or-dogs.md`, and updates `latest_path`.
5. The transform hook for `TransformMarkdown` reads the contents of `latest_path` (`/tmp_dir/cats-or-dogs.md`), updates `latest_path` to have the correct extension, and writes to the new latest path.

Note that some stages create new leaves, which aren't linked to any specific location on the filesystem. Because of this, the `initial_path` of a leaf is _not_ actually guaranteed to exist.

To make path management slightly easier, we have the following `TreeSpan` functions:

- `TreeSpan.add_leaf()`: create a new leaf, requires the initial path, but can optionally accept the latest and final paths as keyword arguments if they are different from the initial. This function will validate the paths.
    - Note that this function does _not_ instantiate the file at latest path. That must be done by the stage.
- `TreeSpan.abs_write_path()`: returns an absolute path to the latest path of a leaf. If a stage is writing files, it should do so to the path provided by this function.
- `TreeSpan.update_path()`: allows updating the latest or final path of a leaf, and validates the new path.
