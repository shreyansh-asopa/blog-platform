"""Talks to the language model behind the editor's writing help.

Services depend only on the `LanguageModel` interface, as with moderation: Claude by
default (Anthropic's API, needs a key), Ollama for a free model run on this machine (posts
never leave it), "off" to hide the feature, and a fake in tests.
"""

import json
from collections.abc import AsyncIterator
from typing import Any, Literal, Protocol

import httpx2

from app.core.config import Settings

# "ready", or what is missing, so the editor can say how to fix it
AiStatus = Literal["ready", "off", "not_running", "model_missing", "no_key"]


class AiUnavailableError(Exception):
    """The model could not answer (not running, not installed, unusable reply)."""


class LanguageModel(Protocol):
    name: str

    async def status(self) -> AiStatus: ...

    async def complete_json(
        self, system: str, prompt: str, schema: dict[str, Any], *, temperature: float = 0
    ) -> Any:
        """One answer, shaped by a JSON schema, already parsed."""
        ...

    def stream(self, system: str, prompt: str, *, temperature: float = 0.7) -> AsyncIterator[str]:
        """The answer in pieces, as the model writes it."""
        ...


class DisabledModel:
    """AI_PROVIDER=off: the editor hides writing help, and the endpoints say it's off."""

    name = ""

    async def status(self) -> AiStatus:
        return "off"

    async def complete_json(self, *args: Any, **kwargs: Any) -> Any:
        raise AiUnavailableError("AI writing help is turned off on this server")

    async def stream(self, *args: Any, **kwargs: Any) -> AsyncIterator[str]:
        raise AiUnavailableError("AI writing help is turned off on this server")
        yield ""  # makes this a generator, like the real one


class OllamaModel:
    """A model served by Ollama (https://ollama.com), through its chat API:

        POST <url>/api/chat  {"model", "messages", "stream", "format"?, "options"}

    With "stream": true the reply is one JSON object per line, each carrying a piece of
    the text in message.content, until one says "done".
    """

    def __init__(self, client: httpx2.AsyncClient, url: str, model: str, context_tokens: int):
        self._client = client
        self._url = url.rstrip("/")
        self.name = model
        # Ollama's default window is small, and silently cuts off the start of a long post
        self._context = context_tokens

    async def status(self) -> AiStatus:
        # /api/tags lists the models downloaded ("pulled") on this machine
        try:
            response = await self._client.get(f"{self._url}/api/tags", timeout=3)
            response.raise_for_status()
            names = {model["name"] for model in response.json()["models"]}
        except (httpx2.HTTPError, ValueError, KeyError, TypeError):
            return "not_running"
        # "llama3.1" and "llama3.1:latest" are the same model
        found = self.name in names or f"{self.name}:latest" in names
        return "ready" if found else "model_missing"

    def _body(
        self, system: str, prompt: str, *, stream: bool, temperature: float
    ) -> dict[str, Any]:
        return {
            "model": self.name,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "stream": stream,
            "options": {"num_ctx": self._context, "temperature": temperature},
        }

    def _error(self, response: httpx2.Response) -> AiUnavailableError:
        if response.status_code == 404:
            return AiUnavailableError(
                f"The model {self.name} isn't installed. Run: ollama pull {self.name}"
            )
        return AiUnavailableError(f"Ollama said {response.status_code}")

    def _unreachable(self) -> AiUnavailableError:
        return AiUnavailableError(
            "The AI model isn't running. Start Ollama, then try again (see the README)"
        )

    async def complete_json(
        self, system: str, prompt: str, schema: dict[str, Any], *, temperature: float = 0
    ) -> Any:
        body = self._body(system, prompt, stream=False, temperature=temperature)
        # Ollama constrains the output to this schema, so the reply parses as JSON
        body["format"] = schema
        try:
            response = await self._client.post(f"{self._url}/api/chat", json=body)
        except httpx2.TransportError as exc:  # includes timeouts
            raise self._unreachable() from exc
        if response.status_code != 200:
            raise self._error(response)
        try:
            return json.loads(response.json()["message"]["content"])
        except (ValueError, KeyError, TypeError) as exc:
            raise AiUnavailableError("The model's answer wasn't usable, please try again") from exc

    async def stream(
        self, system: str, prompt: str, *, temperature: float = 0.7
    ) -> AsyncIterator[str]:
        body = self._body(system, prompt, stream=True, temperature=temperature)
        try:
            async with self._client.stream("POST", f"{self._url}/api/chat", json=body) as response:
                if response.status_code != 200:
                    await response.aread()
                    raise self._error(response)
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        piece = json.loads(line)
                    except ValueError as exc:
                        raise AiUnavailableError("The model's answer wasn't usable") from exc
                    if error := piece.get("error"):
                        raise AiUnavailableError(f"The model stopped: {error}")
                    if text := piece.get("message", {}).get("content"):
                        yield text
                    if piece.get("done"):
                        return
        except httpx2.TransportError as exc:
            raise self._unreachable() from exc


class ClaudeModel:
    """Claude, through Anthropic's Messages API (https://docs.anthropic.com):

        POST <url>/v1/messages  {"model", "system", "messages", "max_tokens", "stream"?}

    Streamed replies are server-sent events; the text arrives in "content_block_delta"
    events. A JSON answer is asked for as a forced tool call, whose input follows the schema.
    """

    API_VERSION = "2023-06-01"
    # Room for a polished version of the longest post allowed (AI_MAX_CHARS)
    MAX_TOKENS = 8192

    def __init__(self, client: httpx2.AsyncClient, url: str, model: str, api_key: str | None):
        self._client = client
        self._url = url.rstrip("/")
        self.name = model
        self._key = api_key or None

    def _headers(self) -> dict[str, str]:
        return {"x-api-key": self._key or "", "anthropic-version": self.API_VERSION}

    async def status(self) -> AiStatus:
        if not self._key:
            return "no_key"
        # Looking the model up checks the key too, and costs nothing
        try:
            response = await self._client.get(
                f"{self._url}/v1/models/{self.name}", headers=self._headers(), timeout=5
            )
        except httpx2.HTTPError:
            return "not_running"
        if response.status_code in (401, 403):
            return "no_key"
        if response.status_code == 404:
            return "model_missing"
        return "ready" if response.status_code == 200 else "not_running"

    # Temperature is left to Claude's default: newer models don't accept every setting
    def _body(self, system: str, prompt: str) -> dict[str, Any]:
        return {
            "model": self.name,
            "max_tokens": self.MAX_TOKENS,
            "system": system,
            "messages": [{"role": "user", "content": prompt}],
        }

    def _error(self, status_code: int, body: bytes) -> AiUnavailableError:
        if status_code in (401, 403):
            return AiUnavailableError(
                "Claude rejected the API key. Check ANTHROPIC_API_KEY in .env"
            )
        if status_code == 404:
            return AiUnavailableError(f"Claude has no model called {self.name}. Check AI_MODEL")
        if status_code == 429:
            return AiUnavailableError("Claude's rate limit was reached, please wait a minute")
        if status_code >= 500:
            return AiUnavailableError("Claude is busy right now, please try again")
        # 400s explain themselves, for example "Your credit balance is too low"
        try:
            message = json.loads(body)["error"]["message"]
        except (ValueError, KeyError, TypeError):
            message = f"status {status_code}"
        return AiUnavailableError(f"Claude couldn't answer: {message}")

    def _unreachable(self) -> AiUnavailableError:
        return AiUnavailableError("Couldn't reach the Claude API, please try again")

    async def complete_json(
        self, system: str, prompt: str, schema: dict[str, Any], *, temperature: float = 0
    ) -> Any:
        if not self._key:
            raise AiUnavailableError("Set ANTHROPIC_API_KEY in .env to use Claude")
        body = self._body(system, prompt)
        body["tools"] = [
            {"name": "answer", "description": "Give the answer", "input_schema": schema}
        ]
        body["tool_choice"] = {"type": "tool", "name": "answer"}
        try:
            response = await self._client.post(
                f"{self._url}/v1/messages", json=body, headers=self._headers()
            )
        except httpx2.TransportError as exc:  # includes timeouts
            raise self._unreachable() from exc
        if response.status_code != 200:
            raise self._error(response.status_code, response.content)
        try:
            blocks = response.json()["content"]
            return next(b["input"] for b in blocks if b["type"] == "tool_use")
        except (ValueError, KeyError, TypeError, StopIteration) as exc:
            raise AiUnavailableError("The model's answer wasn't usable, please try again") from exc

    async def stream(
        self, system: str, prompt: str, *, temperature: float = 0.7
    ) -> AsyncIterator[str]:
        if not self._key:
            raise AiUnavailableError("Set ANTHROPIC_API_KEY in .env to use Claude")
        body = {**self._body(system, prompt), "stream": True}
        try:
            async with self._client.stream(
                "POST", f"{self._url}/v1/messages", json=body, headers=self._headers()
            ) as response:
                if response.status_code != 200:
                    raise self._error(response.status_code, await response.aread())
                # Only the "data:" lines matter; each names its own event type
                async for line in response.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    try:
                        event = json.loads(line[5:])
                    except ValueError as exc:
                        raise AiUnavailableError("The model's answer wasn't usable") from exc
                    kind = event.get("type")
                    if kind == "content_block_delta" and event["delta"].get("type") == "text_delta":
                        yield event["delta"]["text"]
                    elif kind == "error":
                        message = event.get("error", {}).get("message", "unknown error")
                        raise AiUnavailableError(f"Claude stopped: {message}")
                    elif kind == "message_stop":
                        return
        except httpx2.TransportError as exc:
            raise self._unreachable() from exc


def create_language_model(settings: Settings, client: httpx2.AsyncClient) -> LanguageModel:
    if settings.ai_provider == "off":
        return DisabledModel()
    if settings.ai_provider == "ollama":
        return OllamaModel(
            client, settings.ollama_url, settings.model_name, settings.ai_context_tokens
        )
    return ClaudeModel(
        client, settings.anthropic_url, settings.model_name, settings.anthropic_api_key
    )
