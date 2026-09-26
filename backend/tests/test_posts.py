import uuid

import pytest
from fastapi.testclient import TestClient

POSTS = "/api/v1/posts"
MY_POSTS = "/api/v1/me/posts"


@pytest.fixture
def ada(make_user):
    return make_user("ada")


@pytest.fixture
def grace(make_user):
    return make_user("grace")


def create_post(client: TestClient, user, **fields) -> dict:
    body = {"title": "My First Post", "content": "Hello, world."} | fields
    response = client.post(POSTS, json=body, headers=user.headers)
    assert response.status_code == 201, response.text
    return response.json()


def publish(client: TestClient, user, post: dict) -> dict:
    response = client.post(f"{POSTS}/{post['id']}/publish", headers=user.headers)
    assert response.status_code == 200, response.text
    return response.json()


# --- Creating ---


def test_create_makes_a_draft(client: TestClient, ada):
    post = create_post(client, ada)

    assert post["status"] == "draft"
    assert post["slug"] == "my-first-post"
    assert post["excerpt"] == "Hello, world."
    assert post["published_at"] is None
    assert post["author"] == {"id": ada.id, "username": "ada"}


def test_create_requires_login(client: TestClient):
    response = client.post(POSTS, json={"title": "T", "content": "C"})

    assert response.status_code == 401


@pytest.mark.parametrize(
    "bad",
    [{"title": ""}, {"title": "   "}, {"title": "x" * 201}, {"content": ""}],
)
def test_create_validates_input(client: TestClient, ada, bad):
    response = client.post(POSTS, json={"title": "T", "content": "C"} | bad, headers=ada.headers)

    assert response.status_code == 422


def test_slug_is_url_friendly(client: TestClient, ada):
    post = create_post(client, ada, title="  ¡Héllo, Wörld! 2026  ")

    assert post["slug"] == "hello-world-2026"
    assert post["title"] == "¡Héllo, Wörld! 2026"


def test_duplicate_titles_get_distinct_slugs(client: TestClient, ada, grace):
    first = create_post(client, ada)
    second = create_post(client, grace)

    assert first["slug"] == "my-first-post"
    assert second["slug"].startswith("my-first-post-")
    assert second["slug"] != first["slug"]


def test_long_content_gets_a_short_excerpt(client: TestClient, ada):
    post = create_post(client, ada, content="word " * 100)

    assert len(post["excerpt"]) <= 201
    assert post["excerpt"].endswith("…")


def test_custom_excerpt_is_kept(client: TestClient, ada):
    post = create_post(client, ada, excerpt="A teaser")

    assert post["excerpt"] == "A teaser"


# --- Reading ---


def test_drafts_are_hidden_from_everyone_but_the_author(client: TestClient, ada, grace):
    post = create_post(client, ada)
    url = f"{POSTS}/{post['slug']}"

    assert client.get(url).status_code == 404
    assert client.get(url, headers=grace.headers).status_code == 404
    assert client.get(url, headers=ada.headers).status_code == 200


def test_published_post_is_public(client: TestClient, ada):
    post = publish(client, ada, create_post(client, ada))

    response = client.get(f"{POSTS}/{post['slug']}")

    assert response.status_code == 200
    assert response.json()["content"] == "Hello, world."


def test_feed_shows_only_published_posts_newest_first(client: TestClient, ada):
    create_post(client, ada, title="Draft")
    older = publish(client, ada, create_post(client, ada, title="Older"))
    newer = publish(client, ada, create_post(client, ada, title="Newer"))

    body = client.get(POSTS).json()

    assert [p["id"] for p in body["items"]] == [newer["id"], older["id"]]
    assert body["total"] == 2
    # List items leave out the full content to keep responses small
    assert "content" not in body["items"][0]


def test_feed_is_paginated(client: TestClient, ada):
    for i in range(5):
        publish(client, ada, create_post(client, ada, title=f"Post {i}"))

    page_1 = client.get(POSTS, params={"page": 1, "size": 2}).json()
    page_3 = client.get(POSTS, params={"page": 3, "size": 2}).json()

    assert (page_1["total"], page_1["page"], page_1["size"]) == (5, 1, 2)
    assert len(page_1["items"]) == 2
    assert len(page_3["items"]) == 1


@pytest.mark.parametrize("params", [{"page": 0}, {"size": 0}, {"size": 101}])
def test_feed_rejects_bad_page_params(client: TestClient, params):
    assert client.get(POSTS, params=params).status_code == 422


def test_my_posts_include_drafts_and_filter_by_status(client: TestClient, ada, grace):
    create_post(client, ada, title="Draft")
    publish(client, ada, create_post(client, ada, title="Live"))
    create_post(client, grace, title="Not mine")

    everything = client.get(MY_POSTS, headers=ada.headers).json()
    drafts = client.get(MY_POSTS, params={"status": "draft"}, headers=ada.headers).json()

    assert {p["title"] for p in everything["items"]} == {"Draft", "Live"}
    assert [p["title"] for p in drafts["items"]] == ["Draft"]


def test_my_posts_requires_login(client: TestClient):
    assert client.get(MY_POSTS).status_code == 401


# --- Updating ---


def test_author_can_update(client: TestClient, ada):
    post = create_post(client, ada)

    response = client.patch(
        f"{POSTS}/{post['id']}", json={"content": "New body"}, headers=ada.headers
    )

    assert response.status_code == 200
    assert response.json()["content"] == "New body"
    assert response.json()["title"] == "My First Post"
    assert response.json()["updated_at"] > post["updated_at"]


def test_other_users_cannot_update_a_published_post(client: TestClient, ada, grace):
    post = publish(client, ada, create_post(client, ada))

    response = client.patch(
        f"{POSTS}/{post['id']}", json={"title": "Mine now"}, headers=grace.headers
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "permission_denied"


def test_other_users_get_404_for_a_draft(client: TestClient, ada, grace):
    # 404 rather than 403, so drafts can't be discovered by guessing ids
    post = create_post(client, ada)

    response = client.patch(f"{POSTS}/{post['id']}", json={"title": "x"}, headers=grace.headers)

    assert response.status_code == 404


def test_admin_can_update_any_post(client: TestClient, ada, make_user):
    admin = make_user("admin", admin=True)
    post = publish(client, ada, create_post(client, ada))

    response = client.patch(
        f"{POSTS}/{post['id']}", json={"title": "Moderated"}, headers=admin.headers
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Moderated"


def test_renaming_a_draft_updates_its_slug(client: TestClient, ada):
    post = create_post(client, ada)

    updated = client.patch(
        f"{POSTS}/{post['id']}", json={"title": "Better Title"}, headers=ada.headers
    ).json()

    assert updated["slug"] == "better-title"


def test_renaming_a_published_post_keeps_its_slug(client: TestClient, ada):
    post = publish(client, ada, create_post(client, ada))

    updated = client.patch(
        f"{POSTS}/{post['id']}", json={"title": "Better Title"}, headers=ada.headers
    ).json()

    assert updated["slug"] == "my-first-post"


def test_generated_excerpt_follows_content_but_custom_one_stays(client: TestClient, ada):
    generated = create_post(client, ada, title="A")
    custom = create_post(client, ada, title="B", excerpt="Teaser")

    for post in (generated, custom):
        client.patch(f"{POSTS}/{post['id']}", json={"content": "Rewritten"}, headers=ada.headers)

    mine = {p["title"]: p for p in client.get(MY_POSTS, headers=ada.headers).json()["items"]}
    assert mine["A"]["excerpt"] == "Rewritten"
    assert mine["B"]["excerpt"] == "Teaser"


@pytest.mark.parametrize("field", ["title", "content"])
def test_title_and_content_cannot_be_set_to_null(client: TestClient, ada, field):
    post = create_post(client, ada)

    response = client.patch(f"{POSTS}/{post['id']}", json={field: None}, headers=ada.headers)

    assert response.status_code == 422


def test_unknown_or_malformed_ids(client: TestClient, ada):
    assert client.patch(f"{POSTS}/{uuid.uuid4()}", json={}, headers=ada.headers).status_code == 404
    assert client.patch(f"{POSTS}/not-a-uuid", json={}, headers=ada.headers).status_code == 422


# --- Publishing ---


def test_publish_and_unpublish(client: TestClient, ada):
    post = create_post(client, ada)

    published = publish(client, ada, post)
    assert published["status"] == "published"
    assert published["published_at"] is not None
    assert client.get(POSTS).json()["total"] == 1

    unpublished = client.post(f"{POSTS}/{post['id']}/unpublish", headers=ada.headers).json()
    assert unpublished["status"] == "draft"
    assert client.get(POSTS).json()["total"] == 0


def test_republishing_keeps_the_original_publish_date(client: TestClient, ada):
    post = create_post(client, ada)
    first = publish(client, ada, post)
    client.post(f"{POSTS}/{post['id']}/unpublish", headers=ada.headers)

    again = publish(client, ada, post)

    assert again["published_at"] == first["published_at"]


def test_other_users_cannot_publish(client: TestClient, ada, grace):
    post = publish(client, ada, create_post(client, ada))

    response = client.post(f"{POSTS}/{post['id']}/unpublish", headers=grace.headers)

    assert response.status_code == 403


# --- Deleting ---


def test_deleted_post_disappears_everywhere(client: TestClient, ada):
    post = publish(client, ada, create_post(client, ada))

    response = client.delete(f"{POSTS}/{post['id']}", headers=ada.headers)

    assert response.status_code == 204
    assert client.get(f"{POSTS}/{post['slug']}").status_code == 404
    assert client.get(POSTS).json()["total"] == 0
    assert client.get(MY_POSTS, headers=ada.headers).json()["total"] == 0
    assert client.delete(f"{POSTS}/{post['id']}", headers=ada.headers).status_code == 404


def test_slug_of_a_deleted_post_is_not_reused(client: TestClient, ada):
    post = create_post(client, ada)
    client.delete(f"{POSTS}/{post['id']}", headers=ada.headers)

    again = create_post(client, ada)

    assert again["slug"] != post["slug"]


def test_other_users_cannot_delete(client: TestClient, ada, grace):
    post = publish(client, ada, create_post(client, ada))

    response = client.delete(f"{POSTS}/{post['id']}", headers=grace.headers)

    assert response.status_code == 403
    assert client.get(f"{POSTS}/{post['slug']}").status_code == 200


def test_admin_can_delete_any_post(client: TestClient, ada, make_user):
    admin = make_user("admin", admin=True)
    post = publish(client, ada, create_post(client, ada))

    assert client.delete(f"{POSTS}/{post['id']}", headers=admin.headers).status_code == 204
