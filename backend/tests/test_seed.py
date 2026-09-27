import asyncio

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.seed import seed
from app.seed_data import POSTS


def test_seed_loads_everything_once(client: TestClient, settings: Settings, tmp_path, capsys):
    # `client` empties the tables first; uploads go to a temporary folder
    settings = settings.model_copy(update={"upload_dir": tmp_path})

    asyncio.run(seed(settings))
    asyncio.run(seed(settings))

    assert "nothing to do" in capsys.readouterr().out
    feed = client.get("/api/v1/posts", params={"size": 100}).json()
    assert feed["total"] == len(POSTS)
    for post in feed["items"]:
        assert post["topics"], post["title"]
        assert post["cover_image"].startswith("/uploads/covers/")
    assert len(list((tmp_path / "covers").iterdir())) == len(POSTS)

    counts = {t["slug"]: t["post_count"] for t in client.get("/api/v1/topics").json()}
    # Every topic has something to explore
    assert all(counts.values()), counts
