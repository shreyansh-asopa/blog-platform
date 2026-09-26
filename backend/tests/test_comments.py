import logging
import uuid

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_moderator
from app.integrations.moderation import ModerationResult, ModerationUnavailableError

POSTS = "/api/v1/posts"
COMMENTS = "/api/v1/comments"


@pytest.fixture
def ada(make_user):
    return make_user("ada")


@pytest.fixture
def grace(make_user):
    return make_user("grace")


@pytest.fixture
def post(client: TestClient, ada) -> dict:
    """A published post by ada."""
    created = client.post(POSTS, json={"title": "Chatty", "content": "Hi"}, headers=ada.headers)
    return client.post(f"{POSTS}/{created.json()['id']}/publish", headers=ada.headers).json()


def comment(client: TestClient, user, post: dict, content: str = "Great post!"):
    return client.post(
        f"{POSTS}/{post['id']}/comments", json={"content": content}, headers=user.headers
    )


def thread(client: TestClient, post: dict, **params) -> dict:
    return client.get(f"{POSTS}/{post['id']}/comments", params=params).json()


class DownModerator:
    async def check(self, text: str) -> ModerationResult:
        raise ModerationUnavailableError("service is down")


# --- Writing ---


def test_comment_on_a_published_post(client: TestClient, grace, post):
    response = comment(client, grace, post)

    assert response.status_code == 201
    assert response.json()["content"] == "Great post!"
    assert response.json()["author"] == {"id": grace.id, "username": "grace"}
    assert client.get(f"{POSTS}/{post['slug']}").json()["comment_count"] == 1


def test_commenting_requires_login(client: TestClient, post):
    response = client.post(f"{POSTS}/{post['id']}/comments", json={"content": "Hi"})

    assert response.status_code == 401


@pytest.mark.parametrize("content", ["", "   ", "x" * 5001])
def test_comment_text_is_validated(client: TestClient, grace, post, content):
    assert comment(client, grace, post, content).status_code == 422


def test_drafts_and_unknown_posts_cannot_be_commented_on(client: TestClient, ada, grace):
    draft = client.post(POSTS, json={"title": "Draft", "content": "x"}, headers=ada.headers).json()

    assert comment(client, grace, draft).status_code == 404
    assert comment(client, grace, {"id": str(uuid.uuid4())}).status_code == 404


# --- Moderation ---


def test_blocked_words_are_rejected(client: TestClient, grace, post):
    response = comment(client, grace, post, "What an idiot wrote this")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "content_rejected"
    assert thread(client, post)["total"] == 0


def test_comment_is_accepted_when_moderation_is_down(client: TestClient, grace, post, caplog):
    client.app.dependency_overrides[get_moderator] = DownModerator

    with caplog.at_level(logging.WARNING):
        response = comment(client, grace, post, "What an idiot wrote this")

    # Fail open: posted unchecked, and the outage is logged for someone to look at
    assert response.status_code == 201
    assert "Moderation unavailable" in caplog.text


# --- Reading ---


def test_thread_is_public_oldest_first_and_paginated(client: TestClient, ada, grace, post):
    for i in range(3):
        comment(client, grace if i % 2 else ada, post, f"Comment {i}")

    first_page = thread(client, post, size=2)
    last_page = thread(client, post, size=2, page=2)

    assert [c["content"] for c in first_page["items"]] == ["Comment 0", "Comment 1"]
    assert [c["content"] for c in last_page["items"]] == ["Comment 2"]
    assert first_page["total"] == 3


def test_comments_under_a_draft_are_hidden(client: TestClient, ada, grace, post):
    comment(client, grace, post)
    client.post(f"{POSTS}/{post['id']}/unpublish", headers=ada.headers)
    url = f"{POSTS}/{post['id']}/comments"

    assert client.get(url).status_code == 404
    assert client.get(url, headers=grace.headers).status_code == 404
    assert client.get(url, headers=ada.headers).status_code == 200


# --- Deleting ---


def test_author_can_delete_their_comment(client: TestClient, grace, post):
    comment_id = comment(client, grace, post).json()["id"]

    assert client.delete(f"{COMMENTS}/{comment_id}", headers=grace.headers).status_code == 204
    assert thread(client, post)["total"] == 0
    assert client.get(f"{POSTS}/{post['slug']}").json()["comment_count"] == 0
    assert client.delete(f"{COMMENTS}/{comment_id}", headers=grace.headers).status_code == 404


def test_post_author_can_delete_comments_on_their_post(client: TestClient, ada, grace, post):
    comment_id = comment(client, grace, post).json()["id"]

    assert client.delete(f"{COMMENTS}/{comment_id}", headers=ada.headers).status_code == 204


def test_others_cannot_delete_a_comment(client: TestClient, grace, make_user, post):
    comment_id = comment(client, grace, post).json()["id"]

    response = client.delete(f"{COMMENTS}/{comment_id}", headers=make_user("linus").headers)

    assert response.status_code == 403
    assert thread(client, post)["total"] == 1


def test_admin_can_delete_any_comment(client: TestClient, grace, make_user, post):
    comment_id = comment(client, grace, post).json()["id"]
    admin = make_user("admin", admin=True)

    assert client.delete(f"{COMMENTS}/{comment_id}", headers=admin.headers).status_code == 204
