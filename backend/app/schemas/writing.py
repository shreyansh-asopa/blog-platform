from typing import Annotated, Literal

from pydantic import BaseModel, StringConstraints

from app.integrations.grammar import Category
from app.integrations.llm import Provider

# Not stripped: the grammar check's positions must match the text the browser sent.
# The upper limit is a setting (writing_max_chars), checked in the service
CheckText = Annotated[str, StringConstraints(min_length=1)]
ToneTarget = Literal["professional", "friendly", "confident", "casual"]


class WritingStatus(BaseModel):
    grammar: Literal["ready"]
    # "no_key" until GEMINI_API_KEY or GROQ_API_KEY is set. Sentence fixes and
    # simplifying use the same model
    tone: Literal["ready", "no_key"]
    # Which AI the text is sent to, so the editor can say so
    ai: Provider | None
    max_chars: int


class CheckRequest(BaseModel):
    text: CheckText


class GrammarIssueRead(BaseModel):
    offset: int
    length: int
    message: str
    category: Category
    replacements: list[str]


class ToneRequest(BaseModel):
    text: CheckText
    target: ToneTarget


class Suggestion(BaseModel):
    original: str
    fix: str
    reason: str = ""


class GrammarResult(BaseModel):
    # Word-level mistakes (LanguageTool)
    issues: list[GrammarIssueRead]
    # Whole sentences rewritten to be correct (the AI; empty when it isn't set up)
    sentences: list[Suggestion]
    # Set when one of the two checkers failed but the other answered
    note: str | None = None


class ToneResult(BaseModel):
    tone: str
    explanation: str
    suggestions: list[Suggestion]


class SimplifyRequest(BaseModel):
    sentence: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)
    ]


class SimplifyResult(BaseModel):
    fix: str
