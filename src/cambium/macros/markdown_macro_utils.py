"""Function to run macros during TransformMarkdown."""

import ast
import copy
import functools
import re

from marko import block
from marko.element import Element

from ..tree import TreeSpan
from .macro_utils import (
    MACRO_ACTIONS,
    MacroArgs,
    MacroCommand,
    MacroKwargs,
    MacroParam,
    _apply_macros,
)


def apply_markdown_macros(
    document: block.Document,
    leaf_uuid: str,
    tree: TreeSpan,
    original_text: str,
) -> block.Document:
    """Apply macros to a markdown document."""
    new_document = copy.deepcopy(document)
    new_document.children = _apply_macros(
        document.children,
        leaf_uuid,
        tree,
        get_requested_macro=_get_requested_macro_markdown,
        parse_macro_params=_parse_macro_params_markdown,
        unwrap_content=functools.partial(_unwrap_content_markdown, original_text),
        wrap_result=_wrap_result_markdown,
    )
    return new_document


def _get_requested_macro_markdown(
    element: Element, macro_names: list[str]
) -> MacroCommand | None:
    """Check which (if any) macro was called."""
    if not isinstance(element, block.HTMLBlock):
        return

    comment_start, comment_end = "<!--+", "-+->"
    macro_names_group = "(?P<macro_name>" + "|".join(macro_names) + ")"
    brackets_group = r"\((?P<macro_params>.*)\)"
    action_group = "(?P<macro_action>" + "|".join(MACRO_ACTIONS) + ")?"
    any_whitepace = r"\s*"

    full_regex = (
        comment_start
        + any_whitepace
        + macro_names_group
        + brackets_group
        + any_whitepace
        + action_group
        + any_whitepace
        + comment_end
    )

    original_str = element.body.strip()
    match = re.fullmatch(full_regex, original_str)

    if match is None:
        return

    return MacroCommand(match.groupdict(), original_str=original_str)


def _parse_macro_params_markdown(macro: MacroCommand) -> tuple[MacroArgs, MacroKwargs]:
    """Parse the parameters of a macro call."""
    param_string = f"{macro['macro_name']}({macro['macro_params']})"

    # may throw syntax errors
    ast_call = ast.parse(param_string, mode="eval").body

    # _type_check_param may throw RuntimeErrors
    args = [_type_check_param(arg) for arg in ast_call.args]
    kwargs = {kw.arg: _type_check_param(kw.value) for kw in ast_call.keywords}

    return args, kwargs


def _type_check_param(param: ast.expr) -> MacroParam:
    if isinstance(param, ast.Name):
        raise RuntimeError(
            f"Argument {param.id} is undefined, wrap in quotes to pass a string."
        )

    if isinstance(param, ast.Call):
        raise RuntimeError(
            "Macro arguments cannot be evaluated, pass in literal/constant values."
        )

    value = ast.literal_eval(param)

    if not isinstance(value, MacroParam):
        raise RuntimeError(
            f"{ast.unparse(param)} has an invalid type for a macro parameter."
        )

    return value


def _unwrap_content_markdown(full_text: str, macro_content: list[Element]) -> str:
    """Convert Marko Elements back into the original markdown."""
    string_content = ""
    for element in macro_content:
        string_content += full_text[element.source_span[0] : element.source_span[1]]

    return string_content


def _wrap_result_markdown(result: str) -> block.HTMLBlock:
    """Convert a macro result into a Marko Element."""
    return block.HTMLBlock(lines=result)
