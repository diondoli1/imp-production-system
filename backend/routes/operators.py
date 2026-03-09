from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.event_engine import EventEngine, EventEngineError
from backend.schemas import APIMessage, MACHINE_ID, OperatorLoginRequest, OperatorLogoutRequest

router = APIRouter(prefix="/api/operators", tags=["operators"])


@router.post("/login", response_model=APIMessage)
def operator_login(payload: OperatorLoginRequest, db: Session = Depends(get_db)) -> APIMessage:
    engine = EventEngine(db)
    try:
        operator, state = engine.login_operator(payload.operator_name, payload.pin)
    except EventEngineError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return APIMessage(
        message="Operator logged in",
        machine_id=MACHINE_ID,
        data={
            "operator_id": operator.operator_id,
            "operator_name": operator.operator_name,
            "current_state": state.current_state,
            "active_job_id": state.active_job_id,
        },
    )


@router.post("/logout", response_model=APIMessage)
def operator_logout(payload: OperatorLogoutRequest, db: Session = Depends(get_db)) -> APIMessage:
    engine = EventEngine(db)
    try:
        state = engine.logout_operator(payload.operator_id)
    except EventEngineError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return APIMessage(
        message="Operator logged out",
        machine_id=MACHINE_ID,
        data={
            "operator_id": payload.operator_id,
            "current_state": state.current_state,
            "active_job_id": state.active_job_id,
            "active_operator_id": state.active_operator_id,
        },
    )
