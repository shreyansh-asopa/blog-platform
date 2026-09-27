import io

import pytest
from docx import Document
from fastapi.testclient import TestClient

POSTS = "/api/v1/posts"
EXPORT = "/api/v1/me/posts/export"
DOCX_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


@pytest.fixture
def ada(make_user):
    return make_user("ada")


def create_post(client: TestClient, user, title: str, content: str = "Body") -> dict:
    response = client.post(POSTS, json={"title": title, "content": content}, headers=user.headers)
    return response.json()


def docx_text(content: bytes) -> str:
    return "\n".join(p.text for p in Document(io.BytesIO(content)).paragraphs)


def test_export_defaults_to_a_pdf_download(client: TestClient, ada):
    create_post(client, ada, "First post")

    response = client.get(EXPORT, headers=ada.headers)

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["content-disposition"].startswith('attachment; filename="lumen-posts-')
    assert response.headers["content-disposition"].endswith('.pdf"')
    # %PDF is the magic number every PDF reader looks for at the start of the file
    assert response.content.startswith(b"%PDF")


def test_word_export_contains_the_post_title(client: TestClient, ada):
    create_post(client, ada, "My unique title", "Some content, with detail.")

    response = client.get(EXPORT, params={"format": "docx"}, headers=ada.headers)

    assert response.status_code == 200
    assert response.headers["content-type"] == DOCX_TYPE
    assert response.headers["content-disposition"].endswith('.docx"')
    assert "My unique title" in docx_text(response.content)


def test_export_has_all_my_posts(client: TestClient, ada, make_user):
    create_post(client, ada, "Mine, a draft")
    published = create_post(client, ada, "Mine, published")
    client.post(f"{POSTS}/{published['id']}/publish", headers=ada.headers)
    create_post(client, make_user("grace"), "Not mine")

    text = docx_text(client.get(EXPORT, params={"format": "docx"}, headers=ada.headers).content)

    assert "Mine, a draft" in text
    assert "Mine, published" in text
    assert "Not mine" not in text
    assert "Draft, last edited" in text
    assert "Published" in text


def test_export_can_be_filtered_by_status(client: TestClient, ada):
    create_post(client, ada, "Draft only")
    published = create_post(client, ada, "Published only")
    client.post(f"{POSTS}/{published['id']}/publish", headers=ada.headers)

    response = client.get(
        EXPORT, params={"format": "docx", "status": "published"}, headers=ada.headers
    )

    text = docx_text(response.content)
    assert "Published only" in text
    assert "Draft only" not in text
    # The filter shows up in the filename too, e.g. lumen-posts-published-2026-09-27.docx
    assert "lumen-posts-published-" in response.headers["content-disposition"]


def test_export_can_be_filtered_by_search(client: TestClient, ada):
    create_post(client, ada, "About gardening", "Tomatoes and herbs.")
    create_post(client, ada, "About cooking", "Pasta and sauce.")

    text = docx_text(
        client.get(EXPORT, params={"format": "docx", "q": "garden"}, headers=ada.headers).content
    )

    assert "About gardening" in text
    assert "About cooking" not in text


def test_deleted_posts_are_not_exported(client: TestClient, ada):
    post = create_post(client, ada, "Gone")
    client.delete(f"{POSTS}/{post['id']}", headers=ada.headers)

    response = client.get(EXPORT, params={"format": "docx"}, headers=ada.headers)
    assert "Gone" not in docx_text(response.content)


def test_markdown_is_rendered_not_left_as_symbols(client: TestClient, ada):
    content = "# A heading\n\nSome **bold** text and a list:\n\n- one\n- two"
    create_post(client, ada, "Formatted", content)

    text = docx_text(client.get(EXPORT, params={"format": "docx"}, headers=ada.headers).content)

    assert "A heading" in text
    assert "bold" in text
    assert "one" in text and "two" in text


@pytest.mark.parametrize("format", ["pdf", "docx"])
def test_export_never_crashes_on_unicode_or_emoji(client: TestClient, ada, format):
    create_post(client, ada, "Curly “quotes” — em dash", "Body with an emoji 😀 and — dashes.")

    response = client.get(EXPORT, params={"format": format}, headers=ada.headers)

    assert response.status_code == 200


def test_export_requires_login_and_a_known_format(client: TestClient, ada):
    assert client.get(EXPORT).status_code == 401
    assert client.get(EXPORT, params={"format": "csv"}, headers=ada.headers).status_code == 422
    assert client.get(EXPORT, params={"format": "xlsx"}, headers=ada.headers).status_code == 422
