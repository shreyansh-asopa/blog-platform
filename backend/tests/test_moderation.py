"""The moderation clients on their own. The HTTP one runs against a fake server
(httpx2.MockTransport), so these tests never touch the network."""

import httpx2
import pytest

from app.integrations.moderation import (
    HttpModerator,
    ModerationResult,
    ModerationUnavailableError,
    WordListModerator,
)

pytestmark = pytest.mark.anyio

URL = "https://moderation.example/check"


async def test_word_list_blocks_whole_words_in_any_case():
    moderator = WordListModerator(frozenset({"spam"}))

    assert (await moderator.check("Buy SPAM now")).allowed is False
    assert (await moderator.check("Nice post!")).allowed is True
    # Part of a longer word is fine
    assert (await moderator.check("spammy")).allowed is True


def moderator_with(handler, retries: int = 2) -> tuple[HttpModerator, list[httpx2.Request]]:
    """An HttpModerator whose requests are answered by `handler`; also returns the requests."""
    seen: list[httpx2.Request] = []

    def record(request: httpx2.Request) -> httpx2.Response:
        seen.append(request)
        return handler(request)

    client = httpx2.AsyncClient(transport=httpx2.MockTransport(record))
    moderator = HttpModerator(client, URL, api_key="k", retries=retries, backoff_seconds=0)
    return moderator, seen


async def test_http_moderator_sends_text_and_reads_the_verdict():
    moderator, seen = moderator_with(
        lambda r: httpx2.Response(200, json={"flagged": True, "reason": "insult"})
    )

    result = await moderator.check("hello")

    assert result == ModerationResult(allowed=False, reason="insult")
    assert seen[0].headers["Authorization"] == "Bearer k"
    assert seen[0].read() == b'{"text":"hello"}'


async def test_server_errors_are_retried():
    answers = iter([httpx2.Response(503), httpx2.Response(200, json={"flagged": False})])
    moderator, seen = moderator_with(lambda r: next(answers))

    assert (await moderator.check("hi")).allowed is True
    assert len(seen) == 2


async def test_timeouts_are_retried_then_give_up():
    def time_out(request):
        raise httpx2.ReadTimeout("too slow", request=request)

    moderator, seen = moderator_with(time_out, retries=2)

    with pytest.raises(ModerationUnavailableError):
        await moderator.check("hi")
    assert len(seen) == 3  # the first try plus 2 retries


@pytest.mark.parametrize(
    "response",
    [
        httpx2.Response(401),  # wrong API key: retrying won't help
        httpx2.Response(200, text="not json"),
        httpx2.Response(200, json={"unexpected": "shape"}),
    ],
)
async def test_unusable_answers_are_not_retried(response):
    moderator, seen = moderator_with(lambda r: response)

    with pytest.raises(ModerationUnavailableError):
        await moderator.check("hi")
    assert len(seen) == 1
