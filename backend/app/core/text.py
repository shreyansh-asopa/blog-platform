import re
import unicodedata

SLUG_MAX_LENGTH = 200
EXCERPT_MAX_LENGTH = 200


def slugify(text: str) -> str:
    """ "¡Héllo, Wörld!" -> "hello-world". Falls back to "post" when nothing is left."""
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")
    return slug[:SLUG_MAX_LENGTH].rstrip("-") or "post"


# Markdown syntax removed before an excerpt is cut, so previews read as plain sentences
_MARKDOWN_RULES = [
    (re.compile(r"^(```|~~~).*?^\1[^\n]*$", re.M | re.S), " "),  # fenced code blocks
    (re.compile(r"!\[([^\]]*)\]\([^)]*\)"), ""),  # images
    (re.compile(r"\[([^\]]+)\]\([^)]*\)"), r"\1"),  # links keep their text
    (re.compile(r"^\s{0,3}(#{1,6}|>+|[-*+]|\d+[.)])\s+", re.M), ""),  # headings, quotes, lists
    (re.compile(r"^\s*\|?[\s:|-]+\|[\s:|-]*$", re.M), " "),  # table separator rows
    (re.compile(r"\|"), " "),  # table cell borders
    (re.compile(r"(\*\*|\*|~~|`)(?=\S)(.+?)(?<=\S)\1"), r"\2"),  # bold, italic, code
    # Underscores only count at word edges, so snake_case_names survive
    (re.compile(r"(?<!\w)(__|_)(?=\S)(.+?)(?<=\S)\1(?!\w)"), r"\2"),
    (re.compile(r"<[^>]+>"), ""),  # raw HTML tags
]


def strip_markdown(content: str) -> str:
    """ "## Hi **there**" -> "Hi there". Good enough for previews, not a full parser."""
    text = content
    for pattern, replacement in _MARKDOWN_RULES:
        text = pattern.sub(replacement, text)
    return text


def make_excerpt(content: str) -> str:
    """The first ~200 characters of the content as plain text, cut at a word boundary."""
    text = " ".join(strip_markdown(content).split())
    if len(text) <= EXCERPT_MAX_LENGTH:
        return text
    cut = text[:EXCERPT_MAX_LENGTH].rsplit(" ", 1)[0]
    return cut + "…"
