from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.ai_engine import AIEngine, AIEngineError
from backend.database import get_db
from backend.schemas import (
    AIAnalysisRequest,
    AIAnalysisResponse,
    AIQuestionRequest,
    ReasonSuggestRequest,
    ReasonSuggestResponse,
)

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/reason-suggest", response_model=ReasonSuggestResponse)
def reason_suggest(payload: ReasonSuggestRequest, db: Session = Depends(get_db)) -> ReasonSuggestResponse:
    try:
        result = AIEngine(db).suggest_reason_from_note(
            note=payload.note,
            reason_group=payload.reason_group,
            job_id=payload.job_id,
            operator_id=payload.operator_id,
        )
    except AIEngineError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ReasonSuggestResponse(**result)


@router.post("/downtime-analysis", response_model=AIAnalysisResponse)
def downtime_analysis(payload: AIAnalysisRequest, db: Session = Depends(get_db)) -> AIAnalysisResponse:
    result = AIEngine(db).analyze_downtime(
        job_id=payload.job_id,
        operator_id=payload.operator_id,
        limit=payload.limit,
    )
    return AIAnalysisResponse(**result)


@router.post("/scrap-analysis", response_model=AIAnalysisResponse)
def scrap_analysis(payload: AIAnalysisRequest, db: Session = Depends(get_db)) -> AIAnalysisResponse:
    result = AIEngine(db).analyze_scrap(
        job_id=payload.job_id,
        operator_id=payload.operator_id,
        limit=payload.limit,
    )
    return AIAnalysisResponse(**result)


@router.post("/summary", response_model=AIAnalysisResponse)
def summary(payload: AIAnalysisRequest, db: Session = Depends(get_db)) -> AIAnalysisResponse:
    result = AIEngine(db).summarize_production(
        job_id=payload.job_id,
        operator_id=payload.operator_id,
        limit=payload.limit,
    )
    return AIAnalysisResponse(**result)


@router.post("/question", response_model=AIAnalysisResponse)
def question(payload: AIQuestionRequest, db: Session = Depends(get_db)) -> AIAnalysisResponse:
    result = AIEngine(db).answer_operator_question(
        question=payload.question,
        job_id=payload.job_id,
        operator_id=payload.operator_id,
        limit=payload.limit,
    )
    return AIAnalysisResponse(**result)
