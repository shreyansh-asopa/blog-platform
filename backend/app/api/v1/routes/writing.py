from fastapi import APIRouter, Depends

from app.api.deps import (
    AppSettings,
    CurrentUser,
    GrammarCheckerDep,
    LanguageModelDep,
    limit_writing,
)
from app.schemas.writing import (
    CheckRequest,
    GrammarIssueRead,
    GrammarResult,
    SimplifyRequest,
    SimplifyResult,
    ToneRequest,
    ToneResult,
    WritingStatus,
)
from app.services.writing_service import WritingService

router = APIRouter(prefix="/writing", tags=["writing"])


def _service(
    checker: GrammarCheckerDep, model: LanguageModelDep, settings: AppSettings
) -> WritingService:
    return WritingService(checker, model, settings.writing_max_chars)


Service = Depends(_service)


@router.get("/status")
async def writing_status(
    user: CurrentUser, model: LanguageModelDep, settings: AppSettings
) -> WritingStatus:
    """Which checks can run. The AI ones are "no_key" until GEMINI_API_KEY or
    GROQ_API_KEY is set."""
    return WritingStatus(
        grammar="ready",
        tone="no_key" if model.provider is None else "ready",
        ai=model.provider,
        max_chars=settings.writing_max_chars,
    )


@router.post("/grammar", dependencies=[Depends(limit_writing)])
async def check_grammar(
    data: CheckRequest, user: CurrentUser, service: WritingService = Service
) -> GrammarResult:
    """Spelling, grammar, punctuation and style problems, with suggested fixes, plus whole
    sentences corrected by the AI when it's set up.

    Positions are in the text as sent, counted the way JavaScript counts string positions.
    """
    report = await service.grammar(data.text)
    return GrammarResult(
        issues=[
            GrammarIssueRead(
                offset=i.offset,
                length=i.length,
                message=i.message,
                category=i.category,
                replacements=i.replacements,
            )
            for i in report.issues
        ],
        sentences=report.sentences,
        note=report.note,
    )


@router.post("/tone", dependencies=[Depends(limit_writing)])
async def check_tone(
    data: ToneRequest, user: CurrentUser, service: WritingService = Service
) -> ToneResult:
    """How the post sounds, and rewrites that make it sound like `target`."""
    return await service.tone(data.text, data.target)


@router.post("/simplify", dependencies=[Depends(limit_writing)])
async def simplify_sentence(
    data: SimplifyRequest, user: CurrentUser, service: WritingService = Service
) -> SimplifyResult:
    """A shorter, easier version of one sentence."""
    return await service.simplify(data.sentence)
