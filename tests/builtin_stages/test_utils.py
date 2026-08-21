from pathlib import Path

import pytest

from cambium.builtin_stages.utils import (
    ElementAttributeSet,
    markdown_to_html,
    parse_comment,
)


@pytest.mark.parametrize(
    ("comment_string", "expected"),
    [
        ("not-attr-comment", None),
        ("not attr comment", None),
        ("not {attr} comment", None),
        ("{not attr} comment", None),
        ("{not attr comment", None),
        ("not attr comment}", None),
        ("{#id-to-use}", ElementAttributeSet(id="id-to-use")),
        ("{.class-to-use}", ElementAttributeSet(classes=["class-to-use"])),
        ("{.class-1 .class-2}", ElementAttributeSet(classes=["class-1", "class-2"])),
        ("{#id .class}", ElementAttributeSet(id="id", classes=["class"])),
        ("{hidden}", ElementAttributeSet(simple_attrs=["hidden"])),
        ("{no-quote=head}", ElementAttributeSet(keyval_attrs=[("no-quote", "head")])),
        (
            '{aria-label="head"}',
            ElementAttributeSet(keyval_attrs=[("aria-label", '"head"')]),
        ),
        (
            '{key="val" hidden}',
            ElementAttributeSet(
                simple_attrs=["hidden"], keyval_attrs=[("key", '"val"')]
            ),
        ),
        (
            '{key=".val-looks-like-class"}',
            ElementAttributeSet(keyval_attrs=[("key", '".val-looks-like-class"')]),
        ),
        # invalid or questionable HTML, do we block?
        ("{#id-with-.}", ElementAttributeSet(id="id-with-.")),
        (
            "{.0-number-starts-class}",
            ElementAttributeSet(classes=["0-number-starts-class"]),
        ),
        (
            "{.-hyphen-starts-class}",
            ElementAttributeSet(classes=["-hyphen-starts-class"]),
        ),
        pytest.param("{#id-1 #id-2}", None, marks=pytest.mark.xfail(reason="2 IDs")),
    ],
)
def test_parse_comment(
    comment_string: str, expected: ElementAttributeSet | None
) -> None:
    """Verify the parsing of comments which add HTML attributes."""
    result = parse_comment(comment_string)
    assert result == expected


@pytest.mark.parametrize(
    ("markdown_filename", "html_filename"),
    [
        ("markdown-with-attrs.md", "markdown-with-attrs.html"),
    ],
)
def test_markdown_to_html(markdown_filename: str, html_filename: str) -> None:
    """Verify the output of `markdown_to_html` by using known input and output files."""
    data_dir = Path("tests/test_cases")
    markdown_string = (data_dir / markdown_filename).read_text()
    html_string = (data_dir / html_filename).read_text()

    assert markdown_to_html(markdown_string, heading_id_prefix="") == html_string
