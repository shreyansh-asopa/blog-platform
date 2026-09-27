"""Cleaning the HTML that the rich-text editor sends, so a post can't attack its readers.

Anything not on these lists is removed: <script>, onclick= handlers, javascript: links,
iframes, and style properties other than the four the editor's toolbar sets.
"""

import html
import re

import nh3

# Everything the editor's toolbar can produce, and nothing more
ALLOWED_TAGS = {
    "p", "h2", "h3", "strong", "em", "u", "s", "a",
    "ul", "ol", "li", "blockquote", "pre", "code", "br", "hr", "span",
    "table", "thead", "tbody", "tr", "th", "td",
}  # fmt: skip
_STYLED = {"span", "p", "h2", "h3", "li"}
ALLOWED_ATTRIBUTES = (
    {"a": {"href"}}
    | {tag: {"style"} for tag in _STYLED}
    | {cell: {"colspan", "rowspan"} for cell in ("th", "td")}
)
# Colour, size and font come from the toolbar's text style; alignment from its align buttons
ALLOWED_STYLES = {"color", "font-size", "font-family", "text-align"}


def clean_html(content: str) -> str:
    """Keeps the editor's formatting and drops everything else."""
    return nh3.clean(
        content,
        tags=ALLOWED_TAGS,
        # Script and style bodies are removed along with their tags, not left as text
        clean_content_tags={"script", "style"},
        attributes=ALLOWED_ATTRIBUTES,
        url_schemes={"http", "https", "mailto"},
        filter_style_properties=ALLOWED_STYLES,
    )


_BLOCK_END = re.compile(r"</(p|h2|h3|li|blockquote|pre|th|td)>|<br\s*/?>|<hr\s*/?>", re.I)
_TAG = re.compile(r"<[^>]+>")


def html_to_text(content: str) -> str:
    """ "<p>Hi <b>there</b></p><p>&amp; more</p>" -> "Hi there & more"."""
    text = _BLOCK_END.sub(" ", content)
    return html.unescape(_TAG.sub("", text))
