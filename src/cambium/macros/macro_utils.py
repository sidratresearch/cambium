"""Types and generic function for using macros in Cambium."""

import logging
from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable
from enum import StrEnum
from typing import TypeVar

from typing_extensions import (
    TypedDict,  # import from typing in 3.12 https://pydantic.dev/docs/validation/latest/errors/usage_errors/#typed-dict-version
)

from ..tree import TreeSpan

logger = logging.getLogger(__name__)

T = TypeVar("T")
"""Generic class type, can be removed for Python 3.12."""


class MacroAction(StrEnum):
    """Types of action commands that can be included after a macro call."""

    start = "start"
    stop = "stop"


MACRO_ACTIONS = [e.value for e in MacroAction]

# types for parameters passed to macros
MacroParam = str | bytes | int | float | complex | bool | None
MacroArgs = list[MacroParam]
MacroKwargs = dict[str, MacroParam]


class Macro(ABC):
    """Abstract base class for macros."""

    @classmethod
    @abstractmethod
    def apply(
        cls,
        leaf_uuid: str,
        tree: TreeSpan,
        content: str | None = None,
        args: MacroArgs = [],
        kwargs: MacroKwargs = {},
    ) -> str:
        """Applies a macro."""
        raise NotImplementedError


class MacroCommand(TypedDict):
    """Partially parsed macro call (parameters are not yet handled)."""

    macro_name: str
    macro_params: str | None
    macro_action: MacroAction | None
    original_str: str


def _apply_macros(
    elements: Iterable[T],
    leaf_uuid: str,
    tree: TreeSpan,
    get_requested_macro: Callable[[T, list[str]], MacroCommand | None],
    parse_macro_params: Callable[[T], tuple[MacroArgs, MacroKwargs]],
    unwrap_content: Callable[[list[T]], str],
    wrap_result: Callable[[str], T],
    registered_macros: dict[str, Macro],
) -> Iterable[T]:
    """Generic (non-language-specific) function to apply macros to content.

    Iterates through some set of `elements`. When an element is found to be
    a macro (as per `get_requested_macro`), that element is replaced by the
    result of calling the macro.
    """
    new_elements = []

    element_indexes = list(range(len(elements)))

    for i in element_indexes:
        element = elements[i]

        # check if this element is a macro command, and if so, get the details
        requested_macro = get_requested_macro(element, registered_macros.keys())

        if requested_macro is None:
            new_elements.append(element)
            continue

        # grab the actual class definition from the macro name
        macro_class = registered_macros[requested_macro["macro_name"]]

        # parse the macro command into args and kwargs
        try:
            args, kwargs = parse_macro_params(requested_macro)
        except Exception as e:
            raise RuntimeError(
                f"Error parsing macro command {requested_macro['original_str']}: {e}"
            )

        content = None
        if requested_macro["macro_action"] == "start":
            # if the command is a start command, iterate through elements
            # until we find the end all of the intervening elements will get
            # passed to the macro, and removed from global iteration
            content_elements = []
            stop_found = False
            for k in [j for j in element_indexes if j > i]:
                # transfer this element from "check if it's a macro"
                # to "this is macro content"
                element_indexes.remove(k)
                content_elements.append(elements[k])

                # check if it's the stop item
                rqm = get_requested_macro(elements[k], registered_macros.keys())
                if rqm is None:
                    continue
                if rqm["macro_name"] != requested_macro["macro_name"]:
                    continue
                if rqm["macro_action"] != "stop":
                    continue

                # it *is* the stop
                stop_found = True
                content_elements.pop()  # don't pass the stop as content for the macro

                # ignoring any params passed to the stop command
                stop_pars = rqm["macro_params"]
                if stop_pars is not None and len(stop_pars.strip()) > 0:
                    logger.warning(
                        f"Parameters {stop_pars}  will be ignored in `stop` command for {rqm['macro_name']}"
                    )

                # don't search more elements
                break

            if not stop_found:
                start = requested_macro["original_str"]
                raise RuntimeError(f"Missing `stop` command for macro call {start}.")

            content = unwrap_content(content_elements)

        try:
            macro_result = macro_class.apply(
                leaf_uuid, tree, content=content, args=args, kwargs=kwargs
            )
        except Exception as e:
            raise RuntimeError(
                f"Error executing macro call {requested_macro['original_str']}: {e}"
            )

        new_elements.append(wrap_result(macro_result))

    return new_elements
