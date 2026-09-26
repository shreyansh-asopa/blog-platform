import csv
import io

import pytest
from fastapi.testclient import TestClient

from app.services.export_service import COLUMNS, safe_cell

POSTS = "/api/v1/posts"
EXPORT = "/api/v1/me/posts/export"


@pytest.fixture
def ada(make_user):
    return make_user("ada")


def create_post(client: TestClient, user, title: str, content: str = "Body") -> dict:
    response = client.post(POSTS, json={"title": title, "content": content}, headers=user.headers)
    return response.json()


def export(client: TestClient, user, **params) -> list[dict]:
    response = client.get(EXPORT, params=params, headers=user.headers)
    assert response.status_code == 200, response.text
    return list(csv.DictReader(io.StringIO(response.content.decode("utf-8-sig"))))


def test_export_is_a_csv_download(client: TestClient, ada):
    response = client.get(EXPORT, headers=ada.headers)

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert response.headers["content-disposition"].startswith('attachment; filename="lumen-posts-')
    # Starts with the UTF-8 marker Excel looks for, then the header row
    assert response.content.startswith("﻿".encode())
    assert response.content.decode("utf-8-sig").splitlines() == [",".join(COLUMNS)]


def test_export_has_all_my_posts_oldest_first(client: TestClient, ada, make_user):
    first = create_post(client, ada, "First", "Line one\nline two, with a comma")
    second = create_post(client, ada, "Zweiter Beitrag ü")
    client.post(f"{POSTS}/{second['id']}/publish", headers=ada.headers)
    create_post(client, make_user("grace"), "Not mine")

    rows = export(client, ada)

    assert [r["title"] for r in rows] == ["First", "Zweiter Beitrag ü"]
    # Newlines and commas inside a field survive the round trip
    assert rows[0]["content"] == "Line one\nline two, with a comma"
    assert rows[0]["id"] == first["id"]
    assert [r["status"] for r in rows] == ["draft", "published"]
    assert rows[0]["published_at"] == ""
    assert rows[1]["like_count"] == "0"


def test_export_can_be_filtered_by_status(client: TestClient, ada):
    create_post(client, ada, "Draft")
    published = create_post(client, ada, "Published")
    client.post(f"{POSTS}/{published['id']}/publish", headers=ada.headers)

    assert [r["title"] for r in export(client, ada, status="published")] == ["Published"]


def test_deleted_posts_are_not_exported(client: TestClient, ada):
    post = create_post(client, ada, "Gone")
    client.delete(f"{POSTS}/{post['id']}", headers=ada.headers)

    assert export(client, ada) == []


def test_formulas_are_exported_as_plain_text(client: TestClient, ada):
    create_post(client, ada, '=HYPERLINK("http://evil.example","Click")')

    assert export(client, ada)[0]["title"] == '\'=HYPERLINK("http://evil.example","Click")'


def test_export_requires_login_and_a_known_format(client: TestClient, ada):
    assert client.get(EXPORT).status_code == 401
    assert client.get(EXPORT, params={"format": "xlsx"}, headers=ada.headers).status_code == 422


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("Hello", "Hello"),
        ("=1+1", "'=1+1"),
        ("+1", "'+1"),
        ("-1", "'-1"),
        ("@SUM(A1)", "'@SUM(A1)"),
        (None, ""),
        (3, "3"),
    ],
)
def test_safe_cell(value, expected):
    assert safe_cell(value) == expected
