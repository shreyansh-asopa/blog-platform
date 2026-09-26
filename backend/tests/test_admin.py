import asyncio
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.db.session import create_engine

POSTS = "/api/v1/posts"
ADMIN = "/api/v1/admin"


@pytest.fixture
def admin(make_user):
    return make_user("root", admin=True)


@pytest.fixture
def ada(make_user):
    return make_user("ada")


@pytest.fixture
def grace(make_user):
    return make_user("grace")


def set_role(client: TestClient, actor, target, role: str):
    return client.patch(
        f"{ADMIN}/users/{target.id}/role", json={"role": role}, headers=actor.headers
    )


def audit_log(client: TestClient, admin, **params) -> list[dict]:
    response = client.get(f"{ADMIN}/audit-logs", params=params, headers=admin.headers)
    assert response.status_code == 200, response.text
    return response.json()["items"]


def published_post(client: TestClient, user) -> dict:
    post = client.post(POSTS, json={"title": "Post", "content": "Body"}, headers=user.headers)
    return client.post(f"{POSTS}/{post.json()['id']}/publish", headers=user.headers).json()


# --- Who may use the admin endpoints ---


def test_admin_endpoints_are_for_admins_only(client: TestClient, ada, grace):
    assert set_role(client, ada, grace, "admin").status_code == 403
    assert client.get(f"{ADMIN}/audit-logs", headers=ada.headers).status_code == 403
    assert client.get(f"{ADMIN}/audit-logs").status_code == 401


# --- Changing roles ---


def test_promoting_a_user_takes_effect_immediately(client: TestClient, admin, ada, grace):
    post = published_post(client, grace)

    response = set_role(client, admin, ada, "admin")

    assert response.status_code == 200
    assert response.json()["role"] == "admin"
    # The token was issued before the promotion, and it already carries admin powers
    edit = client.patch(f"{POSTS}/{post['id']}", json={"title": "Edited"}, headers=ada.headers)
    assert edit.status_code == 200


def test_demoting_an_admin_takes_effect_immediately(client: TestClient, admin, make_user):
    other_admin = make_user("second", admin=True)

    set_role(client, admin, other_admin, "user")

    # Their token still says "admin", but the database is what counts
    response = client.get(f"{ADMIN}/audit-logs", headers=other_admin.headers)
    assert response.status_code == 403


def test_role_changes_are_recorded(client: TestClient, admin, ada):
    set_role(client, admin, ada, "admin")

    [entry] = audit_log(client, admin)

    assert entry["action"] == "user.role_changed"
    assert entry["actor"] == {"id": admin.id, "username": "root"}
    assert (entry["entity_type"], entry["entity_id"]) == ("user", ada.id)
    assert entry["details"] == {"username": "ada", "from": "user", "to": "admin"}


def test_setting_the_same_role_records_nothing(client: TestClient, admin, ada):
    assert set_role(client, admin, ada, "user").status_code == 200

    assert audit_log(client, admin) == []


def test_admins_cannot_change_their_own_role(client: TestClient, admin):
    # Otherwise the last admin could lock everyone out
    assert set_role(client, admin, admin, "user").status_code == 403


def test_unknown_user_and_invalid_role(client: TestClient, admin, ada):
    unknown = client.patch(
        f"{ADMIN}/users/{uuid.uuid4()}/role", json={"role": "admin"}, headers=admin.headers
    )

    assert unknown.status_code == 404
    assert set_role(client, admin, ada, "superuser").status_code == 422


# --- What gets recorded ---


def test_authors_editing_their_own_posts_is_not_recorded(client: TestClient, admin, ada):
    post = published_post(client, ada)
    client.patch(f"{POSTS}/{post['id']}", json={"title": "Mine"}, headers=ada.headers)
    client.post(f"{POSTS}/{post['id']}/unpublish", headers=ada.headers)

    assert audit_log(client, admin) == []


def test_admin_changes_to_others_posts_are_recorded(client: TestClient, admin, ada):
    post = published_post(client, ada)

    client.patch(
        f"{POSTS}/{post['id']}", json={"title": "Fixed", "content": "x"}, headers=admin.headers
    )
    client.post(f"{POSTS}/{post['id']}/unpublish", headers=admin.headers)

    unpublished, updated = audit_log(client, admin)
    assert updated["action"] == "post.updated"
    assert updated["details"] == {"fields": ["content", "title"], "author_id": ada.id}
    assert unpublished["action"] == "post.unpublished"


def test_every_delete_is_recorded(client: TestClient, admin, ada, grace):
    post = published_post(client, ada)
    comment = client.post(
        f"{POSTS}/{post['id']}/comments", json={"content": "Hi"}, headers=grace.headers
    ).json()

    client.delete(f"/api/v1/comments/{comment['id']}", headers=grace.headers)
    client.delete(f"{POSTS}/{post['id']}", headers=ada.headers)

    post_deleted, comment_deleted = audit_log(client, admin)
    assert post_deleted["action"] == "post.deleted"
    assert post_deleted["details"] == {"title": "Post", "author_id": ada.id}
    assert comment_deleted["action"] == "comment.deleted"
    assert comment_deleted["actor"]["username"] == "grace"
    assert comment_deleted["details"] == {"post_id": post["id"], "author_id": grace.id}


# --- Reading the log ---


def test_log_is_newest_first_filterable_and_paginated(client: TestClient, admin, ada, grace):
    set_role(client, admin, ada, "admin")
    set_role(client, admin, grace, "admin")
    client.delete(f"{POSTS}/{published_post(client, grace)['id']}", headers=ada.headers)

    assert [e["action"] for e in audit_log(client, admin)] == [
        "post.deleted",
        "user.role_changed",
        "user.role_changed",
    ]
    assert len(audit_log(client, admin, action="user.role_changed")) == 2
    assert [e["actor"]["username"] for e in audit_log(client, admin, actor_id=ada.id)] == ["ada"]
    assert len(audit_log(client, admin, size=1, page=3)) == 1


def test_log_outlives_the_user_who_acted(client: TestClient, admin, ada, grace, settings):
    set_role(client, admin, ada, "admin")
    client.delete(f"{POSTS}/{published_post(client, grace)['id']}", headers=ada.headers)

    asyncio.run(_delete_user(settings, "ada"))

    entry = audit_log(client, admin, action="post.deleted")[0]
    assert entry["actor"] is None
    assert entry["details"]["title"] == "Post"


async def _delete_user(settings, username: str) -> None:
    engine = create_engine(settings)
    async with engine.begin() as conn:
        await conn.execute(text("DELETE FROM users WHERE username = :u"), {"u": username})
    await engine.dispose()
