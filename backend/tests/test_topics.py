import pytest
from fastapi.testclient import TestClient

from tests.test_posts import create_post, publish

POSTS = "/api/v1/posts"
TOPICS = "/api/v1/topics"


@pytest.fixture
def ada(make_user):
    return make_user("ada")


def slugs(post: dict) -> list[str]:
    return [t["slug"] for t in post["topics"]]


def feed(client: TestClient, **params) -> list[str]:
    response = client.get(POSTS, params=params)
    assert response.status_code == 200, response.text
    return [p["title"] for p in response.json()["items"]]


# --- The topic list ---


def test_topics_come_from_the_migration(client: TestClient):
    response = client.get(TOPICS)

    assert response.status_code == 200
    topics = response.json()
    assert [t["slug"] for t in topics][:4] == [
        "ai",
        "genai",
        "machine-learning",
        "data-engineering",
    ]
    assert topics[0] == {
        "slug": "ai",
        "name": "AI",
        "description": "Models, agents and the ideas behind artificial intelligence.",
        "post_count": 0,
    }


def test_post_count_skips_drafts_and_deleted_posts(client: TestClient, ada):
    publish(client, ada, create_post(client, ada, title="Live", topics=["ai"]))
    create_post(client, ada, title="Draft", topics=["ai"])
    gone = publish(client, ada, create_post(client, ada, title="Gone", topics=["ai"]))
    client.delete(f"{POSTS}/{gone['id']}", headers=ada.headers)

    counts = {t["slug"]: t["post_count"] for t in client.get(TOPICS).json()}
    assert counts["ai"] == 1
    assert client.get(f"{TOPICS}/ai").json()["post_count"] == 1


def test_one_topic(client: TestClient):
    response = client.get(f"{TOPICS}/GenAI")

    assert response.status_code == 200
    assert response.json()["name"] == "Generative AI"


def test_unknown_topic_is_404(client: TestClient):
    response = client.get(f"{TOPICS}/astrology")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


# --- Filing posts under topics ---


def test_create_with_topics(client: TestClient, ada):
    post = create_post(client, ada, topics=["genai", "AI", "genai"])

    # Repeats dropped, case ignored, listed in the topics' own order
    assert slugs(post) == ["ai", "genai"]
    assert post["topics"][1] == {"slug": "genai", "name": "Generative AI"}


def test_topics_are_optional(client: TestClient, ada):
    assert create_post(client, ada)["topics"] == []


def test_at_most_three_topics(client: TestClient, ada):
    body = {"title": "T", "content": "C", "topics": ["ai", "genai", "security", "cloud-devops"]}
    response = client.post(POSTS, json=body, headers=ada.headers)

    assert response.status_code == 422


def test_unknown_topics_are_rejected(client: TestClient, ada):
    body = {"title": "T", "content": "C", "topics": ["ai", "astrology"]}
    response = client.post(POSTS, json=body, headers=ada.headers)

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "unknown_topic"
    assert "astrology" in error["message"]


def test_update_replaces_topics(client: TestClient, ada):
    post = create_post(client, ada, topics=["ai"])

    def patch(body: dict) -> dict:
        response = client.patch(f"{POSTS}/{post['id']}", json=body, headers=ada.headers)
        assert response.status_code == 200, response.text
        return response.json()

    assert slugs(patch({"topics": ["security", "web-development"]})) == [
        "web-development",
        "security",
    ]
    # Leaving topics out keeps them
    assert slugs(patch({"title": "Renamed"})) == ["web-development", "security"]
    assert slugs(patch({"topics": []})) == []


def test_topics_cannot_be_null(client: TestClient, ada):
    post = create_post(client, ada)
    response = client.patch(f"{POSTS}/{post['id']}", json={"topics": None}, headers=ada.headers)

    assert response.status_code == 422


def test_topics_show_on_the_post_page(client: TestClient, ada):
    post = publish(client, ada, create_post(client, ada, topics=["data-engineering"]))

    assert slugs(client.get(f"{POSTS}/{post['slug']}").json()) == ["data-engineering"]


# --- Filtering the feed ---


def test_feed_filters_by_topic(client: TestClient, ada):
    publish(client, ada, create_post(client, ada, title="Prompting tips", topics=["genai"]))
    publish(
        client, ada, create_post(client, ada, title="Kafka basics", topics=["data-engineering"])
    )
    publish(
        client,
        ada,
        create_post(client, ada, title="RAG pipelines", topics=["genai", "data-engineering"]),
    )
    create_post(client, ada, title="Draft about GenAI", topics=["genai"])

    assert sorted(feed(client, topic="genai")) == ["Prompting tips", "RAG pipelines"]
    assert sorted(feed(client, topic="DATA-ENGINEERING")) == ["Kafka basics", "RAG pipelines"]
    assert feed(client, topic="security") == []
    assert feed(client, topic="astrology") == []


def test_topic_filter_combines_with_search(client: TestClient, ada):
    publish(client, ada, create_post(client, ada, title="Pipelines for LLMs", topics=["genai"]))
    publish(
        client,
        ada,
        create_post(client, ada, title="Pipelines for Spark", topics=["data-engineering"]),
    )

    assert feed(client, q="pipelines", topic="genai") == ["Pipelines for LLMs"]


# --- Trending ---


def trending(client: TestClient, **params) -> list[str]:
    response = client.get(f"{TOPICS}/trending", params=params)
    assert response.status_code == 200, response.text
    return [t["slug"] for t in response.json()]


def test_trending_ranks_topics_by_recent_likes_and_comments(client: TestClient, ada, make_user):
    grace = make_user("grace")
    publish(client, ada, create_post(client, ada, title="Quiet", topics=["ai"]))
    busy = publish(client, ada, create_post(client, ada, title="Busy", topics=["travel"]))
    some = publish(client, ada, create_post(client, ada, title="Some", topics=["security"]))
    for user in (ada, grace):
        client.put(f"{POSTS}/{busy['id']}/like", headers=user.headers)
    client.post(f"{POSTS}/{busy['id']}/comments", json={"content": "Lovely"}, headers=grace.headers)
    client.put(f"{POSTS}/{some['id']}/like", headers=grace.headers)

    assert trending(client) == ["travel", "security", "ai"]
    assert trending(client, limit=1) == ["travel"]


def test_trending_ignores_old_likes(client: TestClient, ada, monkeypatch):
    from datetime import timedelta

    from app.services import topic_service

    post = publish(client, ada, create_post(client, ada, title="Old news", topics=["travel"]))
    client.put(f"{POSTS}/{post['id']}/like", headers=ada.headers)
    # A zero-length window: the like happened before it started
    monkeypatch.setattr(topic_service, "TRENDING_WINDOW", timedelta(0))

    # With no engagement, the topic with the most posts leads
    assert trending(client)[0] == "travel"
    publish(client, ada, create_post(client, ada, title="A", topics=["ai"]))
    publish(client, ada, create_post(client, ada, title="B", topics=["ai"]))
    assert trending(client)[0] == "ai"


def test_trending_limit_is_bounded(client: TestClient):
    assert client.get(f"{TOPICS}/trending", params={"limit": 0}).status_code == 422
    assert client.get(f"{TOPICS}/trending", params={"limit": 21}).status_code == 422
    assert len(trending(client)) == 3
