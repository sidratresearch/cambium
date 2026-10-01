import pytest
from marko.block import HTMLBlock

from cambium.macros.macro_utils import MacroArgs, MacroCommand, MacroKwargs
from cambium.macros.markdown_macro_utils import (
    _get_requested_macro_markdown,
    _parse_macro_params_markdown,
)


@pytest.mark.parametrize(
    ("html", "matches"),
    [
        (
            "<!-- MacroName() -->",
            {"macro_name": "MacroName", "macro_params": "", "macro_action": None},
        ),
        (
            "<!-- MacroName() start -->",
            {"macro_name": "MacroName", "macro_params": "", "macro_action": "start"},
        ),
        (
            "<!-- MacroName() stop-->",
            {"macro_name": "MacroName", "macro_params": "", "macro_action": "stop"},
        ),
        (
            "<!-- MacroName(1, 2, number=3) -->",
            {
                "macro_name": "MacroName",
                "macro_params": "1, 2, number=3",
                "macro_action": None,
            },
        ),
        (
            "<!-- MacroName('x') start -->",
            {"macro_name": "MacroName", "macro_params": "'x'", "macro_action": "start"},
        ),
        ("<!-- Unregistered() -->", None),
        ("<!-- Unregistered() start -->", None),
    ],
)
def test_get_requested_macro_markdown(
    html: str, matches: dict[str, str | None]
) -> None:
    result = _get_requested_macro_markdown(HTMLBlock(html), ["MacroName"])

    if matches is None:
        assert result is None
    else:
        expected = MacroCommand(matches, original_str=html)
        assert result == expected


@pytest.mark.parametrize(
    ("macro_params", "expected_args", "expected_kwargs"),
    [
        # empty
        ("", [], {}),
        # args
        (
            '0, "string", -100_00.0_3, True, "escaped \\" quote", None',
            [0, "string", -100_00.0_3, True, 'escaped " quote', None],
            {},
        ),
        # kwargs
        ("first='string', second=-0.1", [], {"first": "string", "second": -0.1}),
        # args and kwargs
        (
            "'arg', 4, first='string', second=-0.1",
            ["arg", 4],
            {"first": "string", "second": -0.1},
        ),
        # invalid types - unquoted strings
        pytest.param("notBool", None, None, marks=pytest.mark.xfail()),
        # invalid types - list
        pytest.param("[1,2,3]", None, None, marks=pytest.mark.xfail()),
        # invalid types - tuple
        pytest.param("(1,2,3)", None, None, marks=pytest.mark.xfail()),
        # invalid types - dict
        pytest.param("{'a':1}", None, None, marks=pytest.mark.xfail()),
        # invalid types - evaluated
        pytest.param("dict(a=1)", None, None, marks=pytest.mark.xfail()),
        # wrong order
        pytest.param("key=1, 0", None, None, marks=pytest.mark.xfail()),
        # missing commas
        pytest.param("0 1", None, None, marks=pytest.mark.xfail()),
    ],
)
def test_parse_macro_params_markdown(
    macro_params: str, expected_args: MacroArgs, expected_kwargs: MacroKwargs
) -> None:
    macro_command = MacroCommand(
        {"macro_name": "TestMacro", "macro_params": macro_params, "macro_action": None}
    )
    args, kwargs = _parse_macro_params_markdown(macro_command)

    assert args == expected_args
    assert kwargs == expected_kwargs
