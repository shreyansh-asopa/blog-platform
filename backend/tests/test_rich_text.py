"""Posts written in the rich-text editor: stored as cleaned HTML, shown safely."""

import pytest
from fastapi.testclient import TestClient

from app.core.html import clean_html, html_to_text
from app.core.text import make_excerpt
from tests.test_posts import POSTS, create_post, publish


@pytest.fixture
def ada(make_user):
    return make_user("ada")


def create_html(client: TestClient, user, content: str, **fields) -> dict:
    return create_post(client, user, content=content, content_format="html", **fields)


def test_markdown_is_still_the_default(client: TestClient, ada):
    post = create_post(client, ada)
    assert post["content_format"] == "markdown"
    assert post["content"] == "Hello, world."


def test_editor_formatting_survives(client: TestClient, ada):
    content = (
        '<h2 style="text-align: center">Title</h2>'
        '<p style="text-align: right"><span style="color: #dc2626; font-size: 20px; '
        'font-family: Georgia, serif">Red</span> <strong>bold</strong> <em>it</em> '
        "<u>under</u> <s>gone</s></p>"
        "<ul><li>one</li></ul><ol><li>two</li></ol><blockquote><p>q</p></blockquote>"
        "<pre><code>x = 1</code></pre><hr>"
        '<table><tbody><tr><th colspan="2">h</th></tr><tr><td>a</td><td>b</td></tr></tbody></table>'
    )
    post = create_html(client, ada, content)
    assert post["content_format"] == "html"
    # The cleaner rewrites style="color: red" as style="color:red"; nothing else changes
    assert post["content"].replace(" ", "") == content.replace(" ", "")


@pytest.mark.parametrize(
    ("dirty", "clean"),
    [
        ("<p>Hi<script>alert(1)</script></p>", "<p>Hi</p>"),
        ('<p onclick="steal()">Hi</p>', "<p>Hi</p>"),
        ('<p><a href="javascript:alert(1)">x</a></p>', '<p><a rel="noopener noreferrer">x</a></p>'),
        (
            '<p><a href="https://x.dev">x</a></p>',
            '<p><a href="https://x.dev" rel="noopener noreferrer">x</a></p>',
        ),
        (
            '<p><span style="color: red; position: fixed; background: url(x)">Hi</span></p>',
            '<p><span style="color:red">Hi</span></p>',
        ),
        ('<p>Hi</p><iframe src="https://evil.dev"></iframe>', "<p>Hi</p>"),
        ('<img src="x" onerror="steal()"><p>Hi</p>', "<p>Hi</p>"),
        ("<style>body{display:none}</style><p>Hi</p>", "<p>Hi</p>"),
    ],
)
def test_clean_html_removes_anything_dangerous(dirty, clean):
    assert clean_html(dirty) == clean


def test_saved_html_is_cleaned(client: TestClient, ada):
    post = create_html(client, ada, '<p onclick="x()">Safe<script>alert(1)</script></p>')
    assert post["content"] == "<p>Safe</p>"


def test_html_with_no_text_is_refused(client: TestClient, ada):
    body = {"title": "Empty", "content": "<script>x()</script><p></p>", "content_format": "html"}
    response = client.post(POSTS, json=body, headers=ada.headers)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "empty_content"


def test_html_excerpt_is_plain_text(client: TestClient, ada):
    post = create_html(client, ada, "<h2>Intro</h2><p>Fish &amp; <strong>chips</strong></p>")
    assert post["excerpt"] == "Intro Fish & chips"


def test_switching_a_post_to_html_updates_its_excerpt(client: TestClient, ada):
    post = create_post(client, ada, content="## Old *words*")
    assert post["excerpt"] == "Old words"
    body = {"content": "<p>New <em>words</em></p>", "content_format": "html"}
    response = client.patch(f"{POSTS}/{post['id']}", json=body, headers=ada.headers)
    assert response.status_code == 200, response.text
    assert response.json()["content_format"] == "html"
    assert response.json()["excerpt"] == "New words"


def test_changing_only_the_format_cleans_the_content(client: TestClient, ada):
    post = create_post(client, ada, content="<p onclick='x()'>Hi</p>")
    body = {"content_format": "html"}
    response = client.patch(f"{POSTS}/{post['id']}", json=body, headers=ada.headers)
    assert response.json()["content"] == "<p>Hi</p>"


def test_content_format_cannot_be_null(client: TestClient, ada):
    post = create_post(client, ada)
    response = client.patch(
        f"{POSTS}/{post['id']}", json={"content_format": None}, headers=ada.headers
    )
    assert response.status_code == 422


def test_search_matches_words_not_tags(client: TestClient, ada):
    content = '<p><span style="color: red">Lighthouse</span> keepers</p>'
    publish(client, ada, create_html(client, ada, content, title="Coastal life"))

    def found(q: str) -> list[str]:
        return [p["title"] for p in client.get(POSTS, params={"q": q}).json()["items"]]

    assert found("lighthouse") == ["Coastal life"]
    assert found("span") == []
    assert found("color") == []


def test_html_to_text():
    assert html_to_text("<p>a</p><p>b<br>c</p><ul><li>d</li></ul>").split() == list("abcd")
    assert make_excerpt("<p>x</p>", html=True) == "x"
