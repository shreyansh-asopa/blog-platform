"""Turns Markdown into a small block structure the PDF and Word exporters both render.

Not a full CommonMark renderer: just enough structure (headings, paragraphs, bold,
italic, inline code, lists and fenced code blocks) for a readable document. A link
keeps its visible text but not its URL — exported files are read, not browsed.
"""

from dataclasses import dataclass

from markdown_it import MarkdownIt
from markdown_it.token import Token

_parser = MarkdownIt("commonmark")


@dataclass(frozen=True)
class Run:
    """A stretch of inline text with one combination of styles."""

    text: str
    bold: bool = False
    italic: bool = False
    code: bool = False


@dataclass(frozen=True)
class Heading:
    level: int  # 1-6, from "#" to "######"
    runs: list[Run]


@dataclass(frozen=True)
class Paragraph:
    runs: list[Run]


@dataclass(frozen=True)
class ListBlock:
    ordered: bool
    items: list[list[Run]]


@dataclass(frozen=True)
class CodeBlock:
    text: str


Block = Heading | Paragraph | ListBlock | CodeBlock


def parse_blocks(content: str) -> list[Block]:
    """Markdown source -> a flat list of blocks, in reading order."""
    tokens = _parser.parse(content)
    return _blocks(tokens, 0, len(tokens))[0]


def _inline_runs(token: Token) -> list[Run]:
    """The runs inside one "inline" token, e.g. a paragraph or list item's text."""
    runs: list[Run] = []
    bold = italic = False
    for child in token.children or []:
        if child.type == "text":
            runs.append(Run(child.content, bold, italic))
        elif child.type == "code_inline":
            runs.append(Run(child.content, bold, italic, code=True))
        elif child.type == "softbreak":
            runs.append(Run(" ", bold, italic))
        elif child.type == "hardbreak":
            runs.append(Run("\n", bold, italic))
        elif child.type == "strong_open":
            bold = True
        elif child.type == "strong_close":
            bold = False
        elif child.type == "em_open":
            italic = True
        elif child.type == "em_close":
            italic = False
        # link_open/link_close/image carry no text of their own: the link's label is
        # still made of "text" tokens above, so it survives with the URL dropped
    return [run for run in runs if run.text]


def _blocks(tokens: list[Token], start: int, end: int) -> tuple[list[Block], int]:
    """Block-level tokens from `start` up to (not including) `end`."""
    blocks: list[Block] = []
    i = start
    while i < end:
        token = tokens[i]
        if token.type == "heading_open":
            blocks.append(Heading(int(token.tag[1]), _inline_runs(tokens[i + 1])))
            i += 3  # heading_open, inline, heading_close
        elif token.type == "paragraph_open":
            blocks.append(Paragraph(_inline_runs(tokens[i + 1])))
            i += 3  # paragraph_open, inline, paragraph_close
        elif token.type == "fence" or token.type == "code_block":
            blocks.append(CodeBlock(token.content.rstrip("\n")))
            i += 1
        elif token.type in ("bullet_list_open", "ordered_list_open"):
            items, i = _list_items(tokens, i + 1)
            blocks.append(ListBlock(ordered=token.type == "ordered_list_open", items=items))
        elif token.nesting == 1:
            # An opening tag this parser doesn't render as its own block (e.g. a
            # blockquote): skip past it, but keep reading what's nested inside it
            depth = 1
            j = i + 1
            while depth:
                depth += tokens[j].nesting
                j += 1
            inner, _ = _blocks(tokens, i + 1, j - 1)
            blocks.extend(inner)
            i = j
        else:
            i += 1
    return blocks, i


def _list_items(tokens: list[Token], i: int) -> tuple[list[list[Run]], int]:
    items: list[list[Run]] = []
    while i < len(tokens) and tokens[i].type == "list_item_open":
        i += 1
        runs: list[Run] = []
        while tokens[i].type != "list_item_close":
            if tokens[i].type == "paragraph_open":
                runs.extend(_inline_runs(tokens[i + 1]))
                i += 3
            else:
                i += 1
        items.append(runs)
        i += 1  # past list_item_close
    return items, i + 1  # past bullet_list_close / ordered_list_close
