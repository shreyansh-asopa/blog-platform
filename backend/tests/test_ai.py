"""AI writing help. The Ollama client runs against a fake server (httpx2.MockTransport)
and the API against a fake model, so no test needs a real model or the network."""

import json
from collections.abc import AsyncIterator
from typing import Any

import httpx2
import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_language_model
from app.core.config import Settings
from app.integrations.ai import (
    AiUnavailableError,
    ClaudeModel,
    DisabledModel,
    OllamaModel,
    create_language_model,
)

AI = "/api/v1/ai"
OLLAMA = "http://ollama.test"
POST = {"title": "My trip", "content": "I has visited Lisbon last year. It were lovely."}


# --- The Ollama client on its own ---


def ollama_with(handler, model: str = "llama3.1:8b") -> tuple[OllamaModel, list[httpx2.Request]]:
    """An OllamaModel whose requests are answered by `handler`; also returns the requests."""
    seen: list[httpx2.Request] = []

    def record(request: httpx2.Request) -> httpx2.Response:
        seen.append(request)
        return handler(request)

    client = httpx2.AsyncClient(transport=httpx2.MockTransport(record))
    return OllamaModel(client, OLLAMA + "/", model, context_tokens=8192), seen


def tags(*names: str) -> httpx2.Response:
    return httpx2.Response(200, json={"models": [{"name": name} for name in names]})


@pytest.mark.anyio
async def test_status_reports_what_is_missing():
    ready, _ = ollama_with(lambda r: tags("llama3.1:8b", "other:1b"))
    assert await ready.status() == "ready"

    # A model named without a tag means ":latest"
    latest, _ = ollama_with(lambda r: tags("gemma3:latest"), model="gemma3")
    assert await latest.status() == "ready"

    missing, _ = ollama_with(lambda r: tags("other:1b"))
    assert await missing.status() == "model_missing"

    def refuse(request):
        raise httpx2.ConnectError("connection refused")

    down, _ = ollama_with(refuse)
    assert await down.status() == "not_running"


@pytest.mark.anyio
async def test_complete_json_sends_the_schema_and_parses_the_answer():
    answer = {"fixes": []}
    model, seen = ollama_with(
        lambda r: httpx2.Response(200, json={"message": {"content": json.dumps(answer)}})
    )

    assert await model.complete_json("sys", "hello", {"type": "object"}) == answer

    body = json.loads(seen[0].read())
    assert str(seen[0].url) == f"{OLLAMA}/api/chat"
    assert body["model"] == "llama3.1:8b"
    assert body["stream"] is False
    assert body["format"] == {"type": "object"}
    assert body["options"] == {"num_ctx": 8192, "temperature": 0}
    assert [m["role"] for m in body["messages"]] == ["system", "user"]


@pytest.mark.anyio
async def test_stream_yields_each_piece_until_done():
    lines = [
        {"message": {"content": "Hello"}, "done": False},
        {"message": {"content": " world"}, "done": False},
        {"message": {"content": ""}, "done": True},
    ]
    body = "\n".join(json.dumps(line) for line in lines) + "\n"
    model, seen = ollama_with(lambda r: httpx2.Response(200, text=body))

    pieces = [piece async for piece in model.stream("sys", "hi")]

    assert pieces == ["Hello", " world"]
    assert json.loads(seen[0].read())["stream"] is True


@pytest.mark.anyio
async def test_missing_model_and_no_server_explain_the_fix():
    missing, _ = ollama_with(lambda r: httpx2.Response(404, json={"error": "model not found"}))
    with pytest.raises(AiUnavailableError, match="ollama pull llama3.1:8b"):
        await missing.complete_json("sys", "hi", {})
    with pytest.raises(AiUnavailableError, match="ollama pull"):
        [piece async for piece in missing.stream("sys", "hi")]

    def refuse(request):
        raise httpx2.ConnectError("connection refused")

    down, _ = ollama_with(refuse)
    with pytest.raises(AiUnavailableError, match="isn't running"):
        await down.complete_json("sys", "hi", {})
    with pytest.raises(AiUnavailableError, match="isn't running"):
        [piece async for piece in down.stream("sys", "hi")]


@pytest.mark.anyio
async def test_an_answer_that_is_not_json_is_an_error():
    model, _ = ollama_with(lambda r: httpx2.Response(200, json={"message": {"content": "oops"}}))
    with pytest.raises(AiUnavailableError, match="wasn't usable"):
        await model.complete_json("sys", "hi", {})


# --- The Claude client on its own ---

CLAUDE = "http://claude.test"


def claude_with(handler, key: str | None = "sk-test") -> tuple[ClaudeModel, list[httpx2.Request]]:
    seen: list[httpx2.Request] = []

    def record(request: httpx2.Request) -> httpx2.Response:
        seen.append(request)
        return handler(request)

    client = httpx2.AsyncClient(transport=httpx2.MockTransport(record))
    return ClaudeModel(client, CLAUDE + "/", "claude-test", api_key=key), seen


def sse(*events: dict) -> str:
    return "".join(f"event: {e['type']}\ndata: {json.dumps(e)}\n\n" for e in events)


@pytest.mark.anyio
async def test_claude_status_checks_the_key_and_model():
    no_key, seen = claude_with(lambda r: httpx2.Response(200), key=None)
    assert await no_key.status() == "no_key"
    assert seen == []  # nothing is sent without a key

    ready, seen = claude_with(lambda r: httpx2.Response(200, json={"id": "claude-test"}))
    assert await ready.status() == "ready"
    assert str(seen[0].url) == f"{CLAUDE}/v1/models/claude-test"
    assert seen[0].headers["x-api-key"] == "sk-test"
    assert seen[0].headers["anthropic-version"] == "2023-06-01"

    rejected, _ = claude_with(lambda r: httpx2.Response(401))
    assert await rejected.status() == "no_key"
    unknown, _ = claude_with(lambda r: httpx2.Response(404))
    assert await unknown.status() == "model_missing"


@pytest.mark.anyio
async def test_claude_json_is_a_forced_tool_call():
    answer = {"fixes": [{"original": "a", "fix": "b", "reason": "c"}]}
    reply = {"content": [{"type": "tool_use", "name": "answer", "input": answer}]}
    model, seen = claude_with(lambda r: httpx2.Response(200, json=reply))

    assert await model.complete_json("sys", "hello", {"type": "object"}) == answer

    body = json.loads(seen[0].read())
    assert str(seen[0].url) == f"{CLAUDE}/v1/messages"
    assert body["model"] == "claude-test"
    assert body["system"] == "sys"
    assert body["messages"] == [{"role": "user", "content": "hello"}]
    assert body["tools"][0]["input_schema"] == {"type": "object"}
    assert body["tool_choice"] == {"type": "tool", "name": "answer"}


@pytest.mark.anyio
async def test_claude_stream_reads_the_text_events():
    events = sse(
        {"type": "message_start", "message": {}},
        {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": "Hi"}},
        {"type": "ping"},
        {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": "!"}},
        {"type": "message_stop"},
    )
    model, seen = claude_with(lambda r: httpx2.Response(200, text=events))

    assert [piece async for piece in model.stream("sys", "hi")] == ["Hi", "!"]
    assert json.loads(seen[0].read())["stream"] is True


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("status", "body", "message"),
    [
        (401, {}, "rejected the API key"),
        (429, {}, "rate limit"),
        (529, {}, "busy"),
        (400, {"error": {"message": "Your credit balance is too low"}}, "credit balance"),
    ],
)
async def test_claude_errors_explain_the_fix(status, body, message):
    model, _ = claude_with(lambda r: httpx2.Response(status, json=body))
    with pytest.raises(AiUnavailableError, match=message):
        await model.complete_json("sys", "hi", {})
    with pytest.raises(AiUnavailableError, match=message):
        [piece async for piece in model.stream("sys", "hi")]


@pytest.mark.anyio
async def test_claude_without_a_key_sends_nothing():
    model, seen = claude_with(lambda r: httpx2.Response(200), key="")
    with pytest.raises(AiUnavailableError, match="ANTHROPIC_API_KEY"):
        await model.complete_json("sys", "hi", {})
    with pytest.raises(AiUnavailableError, match="ANTHROPIC_API_KEY"):
        [piece async for piece in model.stream("sys", "hi")]
    assert seen == []


def test_the_provider_setting_picks_the_model():
    client = httpx2.AsyncClient()
    base = {
        "postgres_user": "u",
        "postgres_password": "p",
        "postgres_db": "d",
        "jwt_secret": "x" * 32,
    }

    claude = create_language_model(Settings(**base, ai_provider="claude"), client)
    assert isinstance(claude, ClaudeModel) and claude.name == "claude-sonnet-5"
    ollama = create_language_model(Settings(**base, ai_provider="ollama"), client)
    assert isinstance(ollama, OllamaModel) and ollama.name == "llama3.1:8b"
    custom = create_language_model(Settings(**base, ai_provider="claude", ai_model="x"), client)
    assert custom.name == "x"
    assert isinstance(
        create_language_model(Settings(**base, ai_provider="off"), client), DisabledModel
    )


# --- The API, with a fake model ---


class FakeModel:
    name = "fake:1b"

    def __init__(self, *, answer: Any = None, pieces: list[str] | None = None, error: bool = False):
        self.answer = answer
        self.pieces = pieces or []
        self.error = error
        self.prompts: list[str] = []

    async def status(self):
        return "ready"

    async def complete_json(self, system, prompt, schema, *, temperature=0):
        self.prompts.append(prompt)
        if self.error:
            raise AiUnavailableError("The AI model isn't running")
        return self.answer

    async def stream(self, system, prompt, *, temperature=0.7) -> AsyncIterator[str]:
        self.prompts.append(prompt)
        if self.error:
            raise AiUnavailableError("The AI model isn't running")
        for piece in self.pieces:
            yield piece


@pytest.fixture
def ada(make_user):
    return make_user("ada")


def use(client: TestClient, model) -> None:
    client.app.dependency_overrides[get_language_model] = lambda: model


def test_writing_help_needs_a_login(client: TestClient):
    assert client.get(f"{AI}/status").status_code == 401
    assert client.post(f"{AI}/grammar", json=POST).status_code == 401
    assert client.post(f"{AI}/write", json={**POST, "action": "polish"}).status_code == 401


def test_status(client: TestClient, ada):
    use(client, FakeModel())
    body = client.get(f"{AI}/status", headers=ada.headers).json()
    assert body["status"] == "ready"
    assert body["model"] == "fake:1b"
    assert body["provider"] in ("claude", "ollama", "off")
    assert body["max_chars"] == 12_000


def test_grammar_keeps_only_fixes_found_in_the_post(client: TestClient, ada):
    fixes = [
        {"original": "I has visited", "fix": "I visited", "reason": "Past simple"},
        {"original": " It were ", "fix": "It was", "reason": "Agreement"},
        # Not in the post, unchanged, and a repeat: all dropped
        {"original": "Porto is great", "fix": "Porto is grand", "reason": "?"},
        {"original": "lovely", "fix": "lovely", "reason": "?"},
        {"original": "I has visited", "fix": "I had visited", "reason": "Repeat"},
    ]
    model = FakeModel(answer={"fixes": fixes})
    use(client, model)

    response = client.post(f"{AI}/grammar", json=POST, headers=ada.headers)

    assert response.status_code == 200, response.text
    assert response.json()["fixes"] == [
        {"original": "I has visited", "fix": "I visited", "reason": "Past simple"},
        {"original": "It were", "fix": "It was", "reason": "Agreement"},
    ]
    # The post goes to the model inside tags, apart from the instructions
    assert "<post>\nI has visited Lisbon" in model.prompts[0]


def test_grammar_answer_in_the_wrong_shape_is_a_503(client: TestClient, ada):
    use(client, FakeModel(answer={"mistakes": "none"}))
    response = client.post(f"{AI}/grammar", json=POST, headers=ada.headers)
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "ai_unavailable"


def test_write_streams_the_answer(client: TestClient, ada):
    use(client, FakeModel(pieces=["## Better", " post", "\n\nText."]))

    response = client.post(f"{AI}/write", json={**POST, "action": "polish"}, headers=ada.headers)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert response.text == "## Better post\n\nText."


@pytest.mark.parametrize("path", ["grammar", "write"])
def test_a_model_that_is_down_is_a_503_with_the_reason(client: TestClient, ada, path):
    use(client, FakeModel(error=True))

    response = client.post(f"{AI}/{path}", json={**POST, "action": "ideas"}, headers=ada.headers)

    assert response.status_code == 503
    assert response.json()["error"] == {
        "code": "ai_unavailable",
        "message": "The AI model isn't running",
        "request_id": response.headers["X-Request-ID"],
    }


def test_turned_off(client: TestClient, ada):
    use(client, DisabledModel())
    assert client.get(f"{AI}/status", headers=ada.headers).json()["status"] == "off"
    assert client.post(f"{AI}/grammar", json=POST, headers=ada.headers).status_code == 503
    write = client.post(f"{AI}/write", json={**POST, "action": "ideas"}, headers=ada.headers)
    assert write.status_code == 503


def test_input_is_checked(client: TestClient, ada):
    use(client, FakeModel(pieces=["ok"]))
    too_long = {"title": "", "content": "word " * 3000}
    response = client.post(f"{AI}/grammar", json=too_long, headers=ada.headers)
    assert response.status_code == 413
    assert "at most 12,000" in response.json()["error"]["message"]

    empty = client.post(f"{AI}/grammar", json={"content": "   "}, headers=ada.headers)
    assert empty.status_code == 422
    unknown = client.post(f"{AI}/write", json={**POST, "action": "translate"}, headers=ada.headers)
    assert unknown.status_code == 422


def test_requests_are_rate_limited(client: TestClient, ada, make_user):
    use(client, FakeModel(pieces=["ok"]))
    body = {**POST, "action": "ideas"}
    for _ in range(6):
        assert client.post(f"{AI}/write", json=body, headers=ada.headers).status_code == 200

    limited = client.post(f"{AI}/write", json=body, headers=ada.headers)
    assert limited.status_code == 429
    assert "Retry-After" in limited.headers
    # Counted per author
    grace = make_user("grace")
    assert client.post(f"{AI}/write", json=body, headers=grace.headers).status_code == 200
