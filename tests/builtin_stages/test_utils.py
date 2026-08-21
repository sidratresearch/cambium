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
    ("markdown", "expected"),
    [
        # preceding comments
        (
            "<!-- {#custom-header-id} -->\n## Header with a custom ID",
            '<h2 id="custom-header-id">Header with a custom ID</h2>\n',
        ),
        (
            "<!-- {#blockquote-1 .my-quotes} -->\n> This blockquote has\n> both an ID and a class\n",
            '<blockquote id="blockquote-1" class="my-quotes">\n<p>This blockquote has\nboth an ID and a class</p>\n</blockquote>\n',
        ),
        (
            '<!-- {title="Hover title" inert data-first-letter="G"} -->\n### Generic attributes',
            '<h3 id="generic-attributes" inert title="Hover title" data-first-letter="G">Generic attributes</h3>\n',
        ),
        (
            "<!-- {#3-list} -->\n3. list starting at 3",
            '<ol id="3-list" start="3">\n<li>list starting at 3</li>\n</ol>\n',
        ),
        (
            '<!-- {data-sortable="false"} -->\n| C1  | C2  |\n| --- | --- |\n| A   | B   |\n| C   | D   |',
            '<div class="cambium-table-holder"><table data-sortable="false">\n<thead>\n<tr>\n<th>C1</th>\n<th>C2</th>\n</tr>\n</thead>\n<tbody>\n<tr>\n<td>A</td>\n<td>B</td>\n</tr>\n<tr>\n<td>C</td>\n<td>D</td>\n</tr>\n</tbody></table></div>',
        ),
        # inline for links
        (
            "[link with class {.bookmark}](https://buildwithcambium.com)",
            '<p><a class="bookmark" href="https://buildwithcambium.com">link with class</a></p>\n',
        ),
        (
            "[*em link with class* {.bookmark}](https://buildwithcambium.com)",
            '<p><a class="bookmark" href="https://buildwithcambium.com"><em>em link with class</em></a></p>\n',
        ),
        (
            "[*em link no class {.bookmark}*](https://buildwithcambium.com)",
            '<p><a href="https://buildwithcambium.com"><em>em link no class {.bookmark}</em></a></p>\n',
        ),
        (
            "[{#link-id}](https://buildwithcambium.com)",
            '<p><a id="link-id" href="https://buildwithcambium.com"></a></p>\n',
        ),
        # inline for images
        (
            "![alt text {.image-with-alt .png}](fake.png)",
            '<p><div class="cambium-img-holder"><img class="image-with-alt png" src="fake.png" alt="alt text" /></div></p>\n',
        ),
    ],
)
def test_markdown_to_html(markdown: str, expected: str) -> None:
    """Verify the output of `markdown_to_html`."""

    assert markdown_to_html(markdown, heading_id_prefix="") == expected
