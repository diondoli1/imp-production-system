from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.event_engine import EventEngine, EventEngineError
from backend.schemas import APIMessage, MACHINE_ID, ScrapCreateRequest

router = APIRouter(prefix="/api/production", tags=["production"])


@router.post("/scrap", response_model=APIMessage)
def report_scrap(payload: ScrapCreateRequest, db: Session = Depends(get_db)) -> APIMessage:
    engine = EventEngine(db)
    try:
        state = engine.record_scrap(
            quantity=payload.quantity,
            reason_code=payload.reason_code,
            note=payload.note,
            operator_id=payload.operator_id,
        )
    except EventEngineError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return APIMessage(
        message="Scrap recorded",
        machine_id=MACHINE_ID,
        data={
            "active_job_id": state.active_job_id,
            "scrap_count": state.scrap_count,
            "current_state": state.current_state,
        },
    )


@router.get("/counts", response_model=APIMessage)
def get_counts(db: Session = Depends(get_db)) -> APIMessage:
    engine = EventEngine(db)
    state = engine.get_machine_state()
    produced_for_job = 0
    if state.active_job_id:
        produced_for_job = engine.get_job_production_count(state.active_job_id)
    return APIMessage(
        message="Production counts",
        machine_id=MACHINE_ID,
        data={
            "active_job_id": state.active_job_id,
            "produced_count_current_state": state.produced_count,
            "produced_count_for_job": produced_for_job,
            "scrap_count": state.scrap_count,
        },
    )
