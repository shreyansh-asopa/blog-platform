import re
import unicodedata

SLUG_MAX_LENGTH = 200
EXCERPT_MAX_LENGTH = 200


def slugify(text: str) -> str:
    """ "¡Héllo, Wörld!" -> "hello-world". Falls back to "post" when nothing is left."""
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")
    return slug[:SLUG_MAX_LENGTH].rstrip("-") or "post"


def make_excerpt(content: str) -> str:
    """The first ~200 characters of content, cut at a word boundary."""
    text = " ".join(content.split())
    if len(text) <= EXCERPT_MAX_LENGTH:
        return text
    cut = text[:EXCERPT_MAX_LENGTH].rsplit(" ", 1)[0]
    return cut + "…"
