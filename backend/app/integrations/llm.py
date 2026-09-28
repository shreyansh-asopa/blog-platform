"""A language model that answers in JSON, for sentence fixes, the tone check and
simplifying sentences.

Services depend only on the `LanguageModel` interface. The real one is `ChatModel`, which
talks to any OpenAI-style chat API; both free providers offer one: Google Gemini and
Groq (open models). Without a key the model is `DisabledModel`, and those checks
are reported as not set up.
"""

import asyncio
import json
import logging
from typing import Any, Literal, Protocol

import httpx2

from app.core.config import Settings

logger = logging.getLogger(__name__)

Provider = Literal["gemini", "groq"]

# Overloaded (5xx): usually gone within seconds, so the same model is asked again
_BUSY = {500, 502, 503, 504}
# Worth trying the fallback model: retired (404), out of quota (429), or still busy
_TRY_NEXT = {404, 429} | _BUSY


class ModelUnavailableError(Exception):
    """The model gave no usable answer. The message is safe to show to the writer."""


class LanguageModel(Protocol):
    # None when the model isn't set up, so the editor can say so instead of failing
    provider: Provider | None

    async def complete_json(self, system: str, prompt: str) -> Any: ...


class DisabledModel:
    provider = None

    async def complete_json(self, system: str, prompt: str) -> Any:
        raise ModelUnavailableError("The AI checks aren't set up yet")


class ChatModel:
    """Calls POST {url}/chat/completions, asking for a JSON object back.

    Free models are often busy or out of quota. A busy model is asked again after a short
    pause, and a second model can be given to try when the first can't answer.
    """

    def __init__(
        self,
        client: httpx2.AsyncClient,
        url: str,
        *,
        provider: Provider,
        api_key: str,
        model: str,
        fallback: str | None = None,
        retries: int = 2,
        backoff_seconds: float = 1.0,
    ):
        self.provider = provider
        self._client = client
        self._url = url.rstrip("/") + "/chat/completions"
        self._headers = {"Authorization": f"Bearer {api_key}"}
        self._models = [model] if fallback in (None, model) else [model, fallback]
        self._retries = retries
        self._backoff = backoff_seconds

    async def complete_json(self, system: str, prompt: str) -> Any:
        response: httpx2.Response | None = None
        for model in self._models:
            response = await self._ask_model(model, system, prompt)
            # Unreachable (None) is also worth trying the fallback for
            if response is not None and response.status_code not in _TRY_NEXT:
                break

        if response is None:
            raise ModelUnavailableError("Couldn't reach the AI service, please try again")
        if response.status_code != 200:
            raise ModelUnavailableError(_error_message(response.status_code))
        try:
            return json.loads(_unfenced(response.json()["choices"][0]["message"]["content"]))
        except (ValueError, KeyError, IndexError, TypeError, AttributeError) as exc:
            raise ModelUnavailableError("The AI gave an unusable answer, please try again") from exc

    async def _ask_model(self, model: str, system: str, prompt: str) -> httpx2.Response | None:
        """One model's answer, asking again while it's busy. None if it can't be reached."""
        for attempt in range(self._retries + 1):
            try:
                response = await self._post(model, system, prompt)
            except httpx2.TransportError as exc:  # includes timeouts
                logger.warning("%s model %s couldn't be reached: %r", self.provider, model, exc)
                return None
            if response.status_code == 200:
                return response
            logger.warning(
                "%s model %s answered %s (attempt %s): %s",
                self.provider,
                model,
                response.status_code,
                attempt + 1,
                _error_detail(response),
            )
            if response.status_code not in _BUSY or attempt == self._retries:
                return response
            await asyncio.sleep(self._backoff * 2**attempt)
        return response

    async def _post(self, model: str, system: str, prompt: str) -> httpx2.Response:
        body = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        }
        return await self._client.post(self._url, json=body, headers=self._headers)


class FallbackModel:
    """Asks each model in turn until one answers: Gemini first, then Groq."""

    def __init__(self, models: list[LanguageModel]):
        self._models = models
        self.provider = models[0].provider

    async def complete_json(self, system: str, prompt: str) -> Any:
        for model in self._models:
            try:
                return await model.complete_json(system, prompt)
            except ModelUnavailableError as exc:
                error = exc
                logger.warning("%s couldn't answer, trying the next provider", model.provider)
        raise error


def _error_detail(response: httpx2.Response) -> str:
    """The provider's own reason, for the server log. Gemini wraps it in a list."""
    try:
        body = response.json()
        error = (body[0] if isinstance(body, list) else body)["error"]
        return str(error.get("message", error))[:300]
    except (ValueError, KeyError, IndexError, TypeError, AttributeError):
        return response.text[:300]


def _unfenced(content: str) -> str:
    """Models sometimes wrap the JSON in a ```json ... ``` block even when asked not to."""
    content = content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[-1].removesuffix("```")
    return content


def _error_message(status_code: int) -> str:
    if status_code in (401, 403):
        return "The AI service rejected the API key"
    if status_code == 429:
        return "The AI service's free limit is used up for now, please try again later"
    if status_code in (500, 502, 503, 504):
        return "The AI service is busy right now, please try again in a minute"
    return "The AI service isn't working right now, please try again"


def create_language_model(settings: Settings, client: httpx2.AsyncClient) -> LanguageModel:
    models: list[LanguageModel] = []
    if settings.gemini_api_key:
        models.append(
            ChatModel(
                client,
                settings.gemini_url,
                provider="gemini",
                api_key=settings.gemini_api_key,
                model=settings.gemini_model,
                fallback=settings.gemini_fallback_model,
            )
        )
    if settings.groq_api_key:
        models.append(
            ChatModel(
                client,
                settings.groq_url,
                provider="groq",
                api_key=settings.groq_api_key,
                model=settings.groq_model,
                fallback=settings.groq_fallback_model,
            )
        )
    if not models:
        return DisabledModel()
    return models[0] if len(models) == 1 else FallbackModel(models)
