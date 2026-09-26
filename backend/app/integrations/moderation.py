"""Checks comment text before it is published.

Services depend only on the `Moderator` interface, so the implementation can be swapped
without touching them: a word list by default, an HTTP API when one is configured,
and a fake in tests.
"""

import asyncio
import re
from dataclasses import dataclass
from typing import Protocol

import httpx2

from app.core.config import Settings


@dataclass(frozen=True)
class ModerationResult:
    allowed: bool
    reason: str | None = None


class ModerationUnavailableError(Exception):
    """The moderator could not give an answer (timeout, outage, bad response)."""


class Moderator(Protocol):
    async def check(self, text: str) -> ModerationResult: ...


class WordListModerator:
    """Free and offline: rejects text containing any blocked word (whole words, any case)."""

    DEFAULT_BLOCKED_WORDS = frozenset({"casino", "viagra", "idiot", "stupid"})

    def __init__(self, blocked_words: frozenset[str] = DEFAULT_BLOCKED_WORDS):
        self._pattern = re.compile(
            r"\b(" + "|".join(map(re.escape, sorted(blocked_words))) + r")\b", re.IGNORECASE
        )

    async def check(self, text: str) -> ModerationResult:
        if match := self._pattern.search(text):
            return ModerationResult(False, f"contains a blocked word: {match.group(0).lower()}")
        return ModerationResult(True)


class HttpModerator:
    """Asks an external API. Contract:

        POST <url>  {"text": "..."}  ->  200 {"flagged": bool, "reason": str | null}

    Network errors, timeouts and 5xx responses are retried with a growing pause
    (0.2s, 0.4s, ...) because they are often brief. Anything else is not retried.
    """

    def __init__(
        self,
        client: httpx2.AsyncClient,
        url: str,
        *,
        api_key: str | None = None,
        retries: int = 2,
        backoff_seconds: float = 0.2,
    ):
        self._client = client
        self._url = url
        self._headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        self._retries = retries
        self._backoff = backoff_seconds

    async def check(self, text: str) -> ModerationResult:
        for attempt in range(self._retries + 1):
            try:
                response = await self._client.post(
                    self._url, json={"text": text}, headers=self._headers
                )
            except httpx2.TransportError as exc:  # includes timeouts
                error: Exception = exc
            else:
                if response.status_code < 500:
                    return self._parse(response)
                error = ModerationUnavailableError(f"moderation API said {response.status_code}")

            if attempt < self._retries:
                await asyncio.sleep(self._backoff * 2**attempt)

        raise ModerationUnavailableError(f"gave up after {self._retries + 1} attempts") from error

    @staticmethod
    def _parse(response: httpx2.Response) -> ModerationResult:
        try:
            response.raise_for_status()
            body = response.json()
            return ModerationResult(allowed=not body["flagged"], reason=body.get("reason"))
        except (httpx2.HTTPStatusError, ValueError, KeyError, TypeError, AttributeError) as exc:
            raise ModerationUnavailableError(f"unusable moderation response: {exc}") from exc


def create_moderator(settings: Settings, client: httpx2.AsyncClient) -> Moderator:
    if settings.moderation_api_url is None:
        return WordListModerator()
    return HttpModerator(
        client,
        settings.moderation_api_url,
        api_key=settings.moderation_api_key,
        retries=settings.moderation_retries,
    )
