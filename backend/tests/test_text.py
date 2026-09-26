import pytest

from app.core.text import make_excerpt, slugify


@pytest.mark.parametrize(
    ("title", "slug"),
    [
        ("My First Post", "my-first-post"),
        ("  ¡Héllo, Wörld!  ", "hello-world"),
        ("C++ & Rust: 2026", "c-rust-2026"),
        ("---", "post"),
        ("日本語", "post"),
    ],
)
def test_slugify(title, slug):
    assert slugify(title) == slug


def test_slugify_limits_length():
    assert len(slugify("word " * 100)) <= 200
    assert not slugify("word " * 100).endswith("-")


def test_short_content_is_its_own_excerpt():
    assert make_excerpt("Hello,\n\n   world.") == "Hello, world."


def test_long_content_is_cut_at_a_word():
    excerpt = make_excerpt("abcdefghi " * 50)

    assert excerpt.endswith("abcdefghi…")
    assert len(excerpt) <= 201
