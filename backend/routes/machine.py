from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.event_engine import EventEngine, EventEngineError, InvalidTransitionError
from backend.schemas import APIMessage, CycleRequest, MACHINE_ID, MachineEventResponse, MachineStateResponse

router = APIRouter(prefix="/api/machine", tags=["machine"])


@router.get("/state", response_model=MachineStateResponse)
def get_machine_state(db: Session = Depends(get_db)) -> MachineStateResponse:
    state = EventEngine(db).get_machine_state()
    return MachineStateResponse(
        machine_id=state.machine_id,
        current_state=state.current_state,
        active_job_id=state.active_job_id,
        active_operator_id=state.active_operator_id,
        produced_count=state.produced_count,
        scrap_count=state.scrap_count,
        updated_at=state.updated_at,
    )


@router.get("/events", response_model=list[MachineEventResponse])
def get_machine_events(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[MachineEventResponse]:
    events = EventEngine(db).get_recent_events(limit=limit)
    return [
        MachineEventResponse(
            event_id=event.event_id,
            timestamp=event.timestamp,
            machine_id=event.machine_id,
            event_type=event.event_type,
            machine_state=event.machine_state,
            job_id=event.job_id,
            operator_id=event.operator_id,
            reason_code=event.reason_code,
            details=event.details,
        )
        for event in events
    ]


@router.post("/setup/start", response_model=APIMessage)
def setup_start(payload: CycleRequest, db: Session = Depends(get_db)) -> APIMessage:
    engine = EventEngine(db)
    try:
        state = engine.setup_start(operator_id=payload.operator_id)
    except InvalidTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except EventEngineError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return APIMessage(
        message="Setup started",
        machine_id=MACHINE_ID,
        data={"current_state": state.current_state, "active_job_id": state.active_job_id},
    )


@router.post("/setup/confirm", response_model=APIMessage)
def setup_confirm(payload: CycleRequest, db: Session = Depends(get_db)) -> APIMessage:
    engine = EventEngine(db)
    try:
        state = engine.setup_confirm(operator_id=payload.operator_id)
    except InvalidTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except EventEngineError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return APIMessage(
        message="Setup confirmed",
        machine_id=MACHINE_ID,
        data={"current_state": state.current_state, "active_job_id": state.active_job_id},
    )


@router.post("/cycle/start", response_model=APIMessage)
def cycle_start(payload: CycleRequest, db: Session = Depends(get_db)) -> APIMessage:
    engine = EventEngine(db)
    try:
        state = engine.cycle_start(operator_id=payload.operator_id)
    except InvalidTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except EventEngineError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return APIMessage(
        message="Cycle started",
        machine_id=MACHINE_ID,
        data={"current_state": state.current_state, "active_job_id": state.active_job_id},
    )


@router.post("/cycle/complete", response_model=APIMessage)
def cycle_complete(payload: CycleRequest, db: Session = Depends(get_db)) -> APIMessage:
    engine = EventEngine(db)
    try:
        state = engine.cycle_complete(operator_id=payload.operator_id)
    except InvalidTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except EventEngineError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return APIMessage(
        message="Cycle completed (part counted)",
        machine_id=MACHINE_ID,
        data={
            "current_state": state.current_state,
            "active_job_id": state.active_job_id,
            "produced_count": state.produced_count,
        },
    )
