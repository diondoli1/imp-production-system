from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.ai_engine import AIEngine
from backend.database import get_db
from backend.schemas import AIAnalysisRequest, AIAnalysisResponse, AIQuestionRequest

router = APIRouter(prefix="/api/ai", tags=["ai"])


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
