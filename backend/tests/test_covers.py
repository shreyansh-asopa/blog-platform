from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.integrations.storage import LocalStorage, detect_image_type

POSTS = "/api/v1/posts"

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 100
WEBP = b"RIFF\x00\x00\x00\x00WEBPVP8 " + b"\x00" * 100


@pytest.fixture
def ada(make_user):
    return make_user("ada")


@pytest.fixture
def post(client: TestClient, ada) -> dict:
    """A published post by ada."""
    created = client.post(POSTS, json={"title": "Pretty", "content": "Hi"}, headers=ada.headers)
    return client.post(f"{POSTS}/{created.json()['id']}/publish", headers=ada.headers).json()


def upload(client: TestClient, user, post: dict, data: bytes = PNG, name: str = "cover.png"):
    return client.post(
        f"{POSTS}/{post['id']}/cover",
        files={"file": (name, data, "image/png")},
        headers=user.headers if user else None,
    )


def file_on_disk(client: TestClient, url: str) -> Path:
    return client.app.state.settings.upload_dir / url.removeprefix("/uploads/")


# --- Uploading ---


@pytest.mark.parametrize(("data", "extension"), [(PNG, "png"), (JPEG, "jpg"), (WEBP, "webp")])
def test_author_uploads_a_cover(client: TestClient, ada, post, data, extension):
    response = upload(client, ada, post, data)

    assert response.status_code == 200
    url = response.json()["cover_image"]
    assert url.startswith("/uploads/covers/") and url.endswith(f".{extension}")
    # Served back byte for byte, and shown on the post
    assert client.get(url).content == data
    assert client.get(f"{POSTS}/{post['slug']}").json()["cover_image"] == url


def test_file_names_are_random_not_the_uploaders(client: TestClient, ada, post):
    url = upload(client, ada, post, name="../../app/main.png").json()["cover_image"]

    assert "main" not in url and ".." not in url


def test_replacing_a_cover_deletes_the_old_file(client: TestClient, ada, post):
    old = upload(client, ada, post).json()["cover_image"]

    new = upload(client, ada, post, JPEG).json()["cover_image"]

    assert new != old
    assert not file_on_disk(client, old).exists()
    assert file_on_disk(client, new).exists()


# --- Rejected files ---


def test_only_real_images_are_accepted(client: TestClient, ada, post):
    # Named .png and labelled image/png, but the bytes say otherwise
    response = upload(client, ada, post, b"<script>alert(1)</script>", name="evil.png")

    assert response.status_code == 415
    assert response.json()["error"]["code"] == "unsupported_file_type"


def test_files_over_the_limit_are_rejected(client: TestClient, ada, post):
    too_big = PNG + b"\x00" * (5 * 1024 * 1024)

    response = upload(client, ada, post, too_big)

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "file_too_large"
    assert client.get(f"{POSTS}/{post['slug']}").json()["cover_image"] is None


def test_a_file_is_required(client: TestClient, ada, post):
    assert client.post(f"{POSTS}/{post['id']}/cover", headers=ada.headers).status_code == 422


# --- Who may change a cover ---


def test_only_the_author_or_an_admin_can_change_a_cover(client: TestClient, make_user, post):
    assert upload(client, None, post).status_code == 401
    assert upload(client, make_user("grace"), post).status_code == 403


def test_admin_changing_a_cover_is_audited(client: TestClient, make_user, ada, post):
    admin = make_user("root", admin=True)

    assert upload(client, admin, post).status_code == 200

    [entry] = client.get("/api/v1/admin/audit-logs", headers=admin.headers).json()["items"]
    assert entry["action"] == "post.updated"
    assert entry["details"] == {"fields": ["cover_image"], "author_id": ada.id}


# --- Removing ---


def test_removing_a_cover_deletes_the_file(client: TestClient, ada, post):
    url = upload(client, ada, post).json()["cover_image"]

    response = client.delete(f"{POSTS}/{post['id']}/cover", headers=ada.headers)

    assert response.status_code == 200
    assert response.json()["cover_image"] is None
    assert not file_on_disk(client, url).exists()
    # Removing again is harmless
    assert client.delete(f"{POSTS}/{post['id']}/cover", headers=ada.headers).status_code == 200


# --- The storage itself ---


def test_detect_image_type():
    assert detect_image_type(PNG) == "png"
    assert detect_image_type(JPEG) == "jpg"
    assert detect_image_type(WEBP) == "webp"
    assert detect_image_type(b"GIF89a") is None
    assert detect_image_type(b"") is None


@pytest.mark.anyio
async def test_storage_never_deletes_outside_its_folder(tmp_path: Path):
    outside = tmp_path / "secret.txt"
    outside.write_text("keep me")
    storage = LocalStorage(tmp_path / "uploads")

    await storage.delete("/uploads/../secret.txt")
    await storage.delete("/somewhere/else.png")

    assert outside.exists()
