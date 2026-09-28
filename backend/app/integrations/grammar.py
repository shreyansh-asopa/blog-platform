"""Finds spelling, grammar and punctuation mistakes in a post.

Services depend only on the `GrammarChecker` interface. The real one is LanguageTool
(https://languagetool.org), whose public API is free and needs no key; tests use a fake.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

import httpx2

from app.core.config import Settings

logger = logging.getLogger(__name__)

Category = Literal["spelling", "grammar", "punctuation", "style"]


@dataclass(frozen=True)
class GrammarIssue:
    # Where the mistake is in the checked text, counted in UTF-16 code units the way
    # JavaScript counts string positions, so the browser can use them as they are
    offset: int
    length: int
    message: str
    category: Category
    replacements: list[str] = field(default_factory=list)


class GrammarUnavailableError(Exception):
    """The checker could not give an answer (timeout, outage, bad response)."""


class GrammarChecker(Protocol):
    async def check(self, text: str) -> list[GrammarIssue]: ...


class LanguageToolChecker:
    """Calls LanguageTool's /v2/check. Network errors, timeouts and 5xx responses are
    retried with a growing pause; anything else is not."""

    MAX_REPLACEMENTS = 3

    def __init__(
        self,
        client: httpx2.AsyncClient,
        url: str,
        *,
        language: str = "en-US",
        retries: int = 1,
        backoff_seconds: float = 0.5,
    ):
        self._client = client
        self._url = url.rstrip("/") + "/v2/check"
        self._language = language
        self._retries = retries
        self._backoff = backoff_seconds

    async def check(self, text: str) -> list[GrammarIssue]:
        for attempt in range(self._retries + 1):
            try:
                response = await self._client.post(
                    self._url, data={"text": text, "language": self._language}
                )
            except httpx2.TransportError as exc:  # includes timeouts
                error: Exception = exc
            else:
                if response.status_code < 500:
                    return self._parse(response)
                error = GrammarUnavailableError(f"LanguageTool said {response.status_code}")

            logger.warning("LanguageTool attempt %s failed: %r", attempt + 1, error)
            if attempt < self._retries:
                await asyncio.sleep(self._backoff * 2**attempt)

        raise GrammarUnavailableError(f"gave up after {self._retries + 1} attempts") from error

    @classmethod
    def _parse(cls, response: httpx2.Response) -> list[GrammarIssue]:
        try:
            response.raise_for_status()
            return [cls._issue(match) for match in response.json()["matches"]]
        except (httpx2.HTTPStatusError, ValueError, KeyError, TypeError, AttributeError) as exc:
            logger.warning("LanguageTool answered %s: %r", response.status_code, exc)
            raise GrammarUnavailableError(f"unusable LanguageTool response: {exc}") from exc

    @classmethod
    def _issue(cls, match: dict[str, Any]) -> GrammarIssue:
        rule = match.get("rule") or {}
        return GrammarIssue(
            offset=int(match["offset"]),
            length=int(match["length"]),
            message=str(match["message"]),
            category=_category(rule.get("issueType"), (rule.get("category") or {}).get("id")),
            replacements=[
                str(r["value"]) for r in match.get("replacements", [])[: cls.MAX_REPLACEMENTS]
            ],
        )


_PUNCTUATION = {"PUNCTUATION", "TYPOGRAPHY"}
_STYLE_TYPES = {"style", "register", "locale-violation"}
_STYLE_CATEGORIES = {"STYLE", "REDUNDANCY", "PLAIN_ENGLISH", "COLLOQUIALISMS"}


def _category(issue_type: str | None, category_id: str | None) -> Category:
    """Sorts LanguageTool's many rule types into the four groups the editor shows.

    The category decides first: LanguageTool also calls mix-ups like "their is" or
    "a apple" misspellings, but writers think of those as grammar.
    """
    if category_id == "TYPOS":
        return "spelling"
    if category_id in _PUNCTUATION or issue_type == "typographical":
        return "punctuation"
    if issue_type in _STYLE_TYPES or category_id in _STYLE_CATEGORIES:
        return "style"
    if issue_type == "misspelling" and category_id is None:
        return "spelling"
    return "grammar"


def create_grammar_checker(settings: Settings, client: httpx2.AsyncClient) -> GrammarChecker:
    return LanguageToolChecker(
        client,
        settings.languagetool_url,
        language=settings.languagetool_language,
        retries=settings.writing_retries,
    )
