"""Where uploaded files are kept.

`Storage` is the interface the rest of the app uses. `LocalStorage` writes to a folder
(a Docker volume in production) that the app serves at /uploads. Moving to S3 later
means writing an S3Storage with the same three methods; nothing else changes.
"""

import asyncio
import logging
import uuid
from pathlib import Path
from typing import Protocol

logger = logging.getLogger(__name__)

# What a file is, judged by its first bytes ("magic numbers"). The filename and the
# Content-Type header are chosen by the uploader, so neither can be trusted
_SIGNATURES = {
    "jpg": lambda head: head.startswith(b"\xff\xd8\xff"),
    "png": lambda head: head.startswith(b"\x89PNG\r\n\x1a\n"),
    "webp": lambda head: head[:4] == b"RIFF" and head[8:12] == b"WEBP",
}


def detect_image_type(data: bytes) -> str | None:
    """The file extension for a JPEG, PNG or WebP image, or None for anything else."""
    return next((ext for ext, matches in _SIGNATURES.items() if matches(data[:12])), None)


class Storage(Protocol):
    async def save(self, folder: str, data: bytes, extension: str) -> str:
        """Stores the file under a new random name and returns its public URL."""
        ...

    async def delete(self, url: str) -> None:
        """Removes a file saved earlier. A file that is already gone is not an error."""
        ...


class LocalStorage:
    def __init__(self, root: Path, base_url: str = "/uploads"):
        self.root = root
        self.base_url = base_url.rstrip("/")

    async def save(self, folder: str, data: bytes, extension: str) -> str:
        # A random name: uploaders can't overwrite each other's files or pick paths
        # like "../../app/main.py", and names reveal nothing about the post
        key = f"{folder}/{uuid.uuid4().hex}.{extension}"
        # Disk writes block, so they run in a worker thread to keep the server responsive
        await asyncio.to_thread(self._write, self.root / key, data)
        return f"{self.base_url}/{key}"

    async def delete(self, url: str) -> None:
        path = self._path_for(url)
        if path is not None:
            await asyncio.to_thread(path.unlink, missing_ok=True)

    @staticmethod
    def _write(path: Path, data: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def _path_for(self, url: str) -> Path | None:
        """The file behind one of our URLs, or None if the URL isn't ours."""
        prefix = f"{self.base_url}/"
        if not url.startswith(prefix):
            return None
        path = (self.root / url.removeprefix(prefix)).resolve()
        # Never touch anything outside the uploads folder, whatever the URL says
        if not path.is_relative_to(self.root.resolve()):
            logger.warning("Refusing to delete %s: outside the uploads folder", url)
            return None
        return path
