import pytest
from fastapi.testclient import TestClient

from tests.test_posts import create_post, publish

POSTS = "/api/v1/posts"
USERS = "/api/v1/users"


@pytest.fixture
def ada(make_user):
    return make_user("ada")


@pytest.fixture
def grace(make_user):
    return make_user("grace")


def search(client: TestClient, **params) -> dict:
    response = client.get(POSTS, params=params)
    assert response.status_code == 200, response.text
    return response.json()


def titles(page: dict) -> list[str]:
    return [p["title"] for p in page["items"]]


# --- Search ---


def test_search_matches_title_and_content(client: TestClient, ada):
    publish(client, ada, create_post(client, ada, title="Python tips", content="Some tricks."))
    publish(client, ada, create_post(client, ada, title="Cooking", content="I cook with python."))
    publish(client, ada, create_post(client, ada, title="Gardening", content="Tomatoes."))

    page = search(client, q="python")

    assert page["total"] == 2
    # A match in the title ranks above one in the body
    assert titles(page) == ["Python tips", "Cooking"]


def test_search_ignores_case_and_word_endings(client: TestClient, ada):
    publish(client, ada, create_post(client, ada, title="Running a marathon", content="Hard."))

    assert titles(search(client, q="RUNS")) == ["Running a marathon"]


def test_search_supports_phrases_and_exclusions(client: TestClient, ada):
    publish(client, ada, create_post(client, ada, title="Fast cars", content="Red and fast."))
    publish(client, ada, create_post(client, ada, title="Cars are fast", content="Blue."))

    assert titles(search(client, q='"fast cars"')) == ["Fast cars"]
    assert titles(search(client, q="cars -red")) == ["Cars are fast"]


def test_search_skips_drafts_and_deleted_posts(client: TestClient, ada):
    create_post(client, ada, title="Secret draft about rust")
    gone = publish(client, ada, create_post(client, ada, title="Deleted rust post"))
    client.delete(f"{POSTS}/{gone['id']}", headers=ada.headers)

    assert search(client, q="rust")["total"] == 0


def test_search_follows_edits(client: TestClient, ada):
    post = publish(client, ada, create_post(client, ada, title="Old title"))
    client.patch(f"{POSTS}/{post['id']}", json={"title": "Brand new title"}, headers=ada.headers)

    # Postgres recomputes the search column on update; nothing in the app has to
    assert search(client, q="brand")["total"] == 1
    assert search(client, q="old")["total"] == 0


@pytest.mark.parametrize("q", ["", "   ", "the", "!!! & | :*", "'"])
def test_odd_searches_never_fail(client: TestClient, ada, q):
    publish(client, ada, create_post(client, ada))

    # Blank means the plain feed; filler words or punctuation alone match nothing
    page = search(client, q=q)
    assert page["total"] == (1 if not q.strip() else 0)


def test_search_is_limited_to_200_characters(client: TestClient):
    response = client.get(POSTS, params={"q": "x" * 201})

    assert response.status_code == 422


# --- Filtering by author ---


def test_author_filter(client: TestClient, ada, grace):
    publish(client, ada, create_post(client, ada, title="By Ada about space"))
    publish(client, grace, create_post(client, grace, title="By Grace about space"))
    create_post(client, grace, title="Grace's draft")

    assert titles(search(client, author="grace")) == ["By Grace about space"]
    assert titles(search(client, author="grace", q="space")) == ["By Grace about space"]
    assert search(client, author="nobody")["total"] == 0


# --- Public profiles ---


def test_profile_shows_published_post_count(client: TestClient, ada):
    publish(client, ada, create_post(client, ada, title="One"))
    publish(client, ada, create_post(client, ada, title="Two"))
    create_post(client, ada, title="Draft")

    response = client.get(f"{USERS}/ada")

    assert response.status_code == 200
    body = response.json()
    assert body["username"] == "ada"
    assert body["post_count"] == 2
    # Public: no email, role or anything else private
    assert set(body) == {"id", "username", "created_at", "post_count"}


def test_profile_of_unknown_user_is_404(client: TestClient):
    response = client.get(f"{USERS}/nobody")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_me_still_means_the_logged_in_user(client: TestClient, ada):
    response = client.get(f"{USERS}/me", headers=ada.headers)

    assert response.json()["email"] == "ada@example.com"
