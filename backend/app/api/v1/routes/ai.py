from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.deps import AppSettings, CurrentUser, LanguageModelDep, limit_ai
from app.schemas.ai import AiRequest, AiStatusRead, AiWriteRequest, GrammarResult
from app.services.ai_service import AiService

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/status")
async def ai_status(
    user: CurrentUser, model: LanguageModelDep, settings: AppSettings
) -> AiStatusRead:
    """Whether writing help is ready, or what's missing (no API key, Ollama not running...)."""
    return AiStatusRead(
        status=await model.status(),
        provider=settings.ai_provider,
        model=model.name,
        max_chars=settings.ai_max_chars,
    )


@router.post("/grammar", dependencies=[Depends(limit_ai)])
async def check_grammar(
    data: AiRequest, user: CurrentUser, model: LanguageModelDep, settings: AppSettings
) -> GrammarResult:
    """Spelling, grammar and punctuation mistakes, each as exact words from the post and a fix."""
    fixes = await AiService(model, settings.ai_max_chars).grammar(data)
    return GrammarResult(fixes=fixes)


@router.post(
    "/write",
    dependencies=[Depends(limit_ai)],
    response_class=StreamingResponse,
    responses={200: {"content": {"text/plain": {}}}},
)
async def write(
    data: AiWriteRequest, user: CurrentUser, model: LanguageModelDep, settings: AppSettings
) -> StreamingResponse:
    """A polished version of the post, ideas to add, or recommendations, as Markdown.

    Streamed as plain text while the model writes it, so the answer appears word by word.
    """
    pieces = await AiService(model, settings.ai_max_chars).write(data.action, data)
    return StreamingResponse(pieces, media_type="text/plain; charset=utf-8")
