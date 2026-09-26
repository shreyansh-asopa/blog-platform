import uuid

import pytest
from fastapi.testclient import TestClient

POSTS = "/api/v1/posts"


@pytest.fixture
def ada(make_user):
    return make_user("ada")


@pytest.fixture
def grace(make_user):
    return make_user("grace")


@pytest.fixture
def post(client: TestClient, ada) -> dict:
    """A published post by ada."""
    created = client.post(POSTS, json={"title": "Likeable", "content": "Hi"}, headers=ada.headers)
    post_id = created.json()["id"]
    return client.post(f"{POSTS}/{post_id}/publish", headers=ada.headers).json()


def like(client: TestClient, user, post: dict):
    return client.put(f"{POSTS}/{post['id']}/like", headers=user.headers)


def unlike(client: TestClient, user, post: dict):
    return client.delete(f"{POSTS}/{post['id']}/like", headers=user.headers)


def test_new_posts_have_no_likes(post):
    assert post["like_count"] == 0


def test_like_and_unlike(client: TestClient, grace, post):
    liked = like(client, grace, post)
    assert liked.status_code == 200
    assert liked.json() == {"post_id": post["id"], "liked": True, "like_count": 1}

    unliked = unlike(client, grace, post)
    assert unliked.status_code == 200
    assert unliked.json() == {"post_id": post["id"], "liked": False, "like_count": 0}


def test_liking_twice_counts_once(client: TestClient, grace, post):
    like(client, grace, post)

    assert like(client, grace, post).json()["like_count"] == 1


def test_unliking_a_post_you_never_liked_is_fine(client: TestClient, grace, post):
    assert unlike(client, grace, post).json()["like_count"] == 0


def test_likes_from_different_users_add_up(client: TestClient, grace, make_user, post):
    like(client, grace, post)
    like(client, make_user("linus"), post)

    assert client.get(f"{POSTS}/{post['slug']}").json()["like_count"] == 2


def test_you_cannot_like_your_own_post(client: TestClient, ada, post):
    response = like(client, ada, post)

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "permission_denied"


def test_liking_requires_login(client: TestClient, post):
    assert client.put(f"{POSTS}/{post['id']}/like").status_code == 401


def test_drafts_deleted_and_unknown_posts_cannot_be_liked(client: TestClient, ada, grace):
    draft = client.post(POSTS, json={"title": "Draft", "content": "x"}, headers=ada.headers).json()
    deleted = client.post(POSTS, json={"title": "Gone", "content": "x"}, headers=ada.headers).json()
    client.post(f"{POSTS}/{deleted['id']}/publish", headers=ada.headers)
    client.delete(f"{POSTS}/{deleted['id']}", headers=ada.headers)

    for target in (draft, deleted, {"id": str(uuid.uuid4())}):
        assert like(client, grace, target).status_code == 404


def test_feed_shows_each_posts_own_count(client: TestClient, ada, grace, post):
    other = client.post(POSTS, json={"title": "Other", "content": "x"}, headers=ada.headers).json()
    client.post(f"{POSTS}/{other['id']}/publish", headers=ada.headers)
    like(client, grace, post)

    counts = {p["title"]: p["like_count"] for p in client.get(POSTS).json()["items"]}

    assert counts == {"Likeable": 1, "Other": 0}


def test_post_page_says_whether_you_liked_it(client: TestClient, ada, grace, post):
    like(client, grace, post)
    url = f"{POSTS}/{post['slug']}"

    assert client.get(url, headers=grace.headers).json()["liked_by_me"] is True
    assert client.get(url, headers=ada.headers).json()["liked_by_me"] is False
    assert client.get(url).json()["liked_by_me"] is False
