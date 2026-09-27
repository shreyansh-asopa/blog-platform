from typing import Annotated, Literal

from pydantic import BaseModel, StringConstraints

from app.integrations.ai import AiStatus

# What the streamed actions do; see the prompts in app/services/ai_service.py
WriteAction = Literal["polish", "ideas", "recommend"]


class AiStatusRead(BaseModel):
    status: AiStatus
    # Where posts go for suggestions: "claude" is Anthropic's API, "ollama" this machine
    provider: Literal["claude", "ollama", "off"]
    model: str
    max_chars: int


class AiRequest(BaseModel):
    """The post as it is in the editor, saved or not. Length is checked against AI_MAX_CHARS."""

    title: Annotated[str, StringConstraints(strip_whitespace=True, max_length=200)] = ""
    content: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class AiWriteRequest(AiRequest):
    action: WriteAction


class GrammarFix(BaseModel):
    # Exact words from the post, so the editor can find and replace them
    original: str
    fix: str
    reason: str


class GrammarResult(BaseModel):
    fixes: list[GrammarFix]
