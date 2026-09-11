# Error Handling

Unless the `--show-traceback` flag is active, the final exception raised to the user should always be `click.ClickException` or `typer.BadParameter` as these result in clean error messages.

Within stages, all errors should end up being caught by the `TreeSpan` (which transforms them into `CambiumError`s, adding some additional information in the process). The `cli` module then transforms `CambiumError`s into `ClickException`s.
