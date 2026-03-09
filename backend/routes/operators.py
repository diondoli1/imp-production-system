from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.event_engine import EventEngine, EventEngineError
from backend.schemas import APIMessage, LoginRequest, MACHINE_ID, OperatorLoginRequest, OperatorLogoutRequest

router = APIRouter(prefix="/api/operators", tags=["operators"])
auth_router = APIRouter(prefix="/api", tags=["auth"])


def _resolve_login_name(operator_name: str | None, name: str | None) -> str:
    login_name = (operator_name or name or "").strip()
    if not login_name:
        raise HTTPException(status_code=422, detail="name is required")
    return login_name


@auth_router.post("/login", response_model=APIMessage)
def app_login(payload: LoginRequest, db: Session = Depends(get_db)) -> APIMessage:
    engine = EventEngine(db)
    login_name = _resolve_login_name(payload.operator_name, payload.name)
    try:
        operator = engine.authenticate_user(login_name, payload.pin)
        state = engine.get_machine_state()
        if operator.role == "OPERATOR":
            operator, state = engine.login_operator(login_name, payload.pin)
    except EventEngineError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    route_hint = "/operator" if operator.role == "OPERATOR" else "/supervisor"
    return APIMessage(
        message="Login successful",
        machine_id=MACHINE_ID,
        data={
            "user_id": operator.operator_id,
            "name": operator.operator_name,
            "operator_id": operator.operator_id,
            "operator_name": operator.operator_name,
            "role": operator.role,
            "redirect_path": route_hint,
            "route_hint": route_hint,
            "current_state": state.current_state,
            "active_job_id": state.active_job_id,
            "produced_count": state.produced_count,
            "scrap_count": state.scrap_count,
        },
    )


@router.post("/login", response_model=APIMessage)
def operator_login(payload: OperatorLoginRequest, db: Session = Depends(get_db)) -> APIMessage:
    engine = EventEngine(db)
    login_name = _resolve_login_name(payload.operator_name, payload.name)
    try:
        operator, state = engine.login_operator(login_name, payload.pin)
    except EventEngineError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return APIMessage(
        message="Operator logged in",
        machine_id=MACHINE_ID,
        data={
            "user_id": operator.operator_id,
            "name": operator.operator_name,
            "operator_id": operator.operator_id,
            "operator_name": operator.operator_name,
            "role": operator.role,
            "current_state": state.current_state,
            "active_job_id": state.active_job_id,
            "produced_count": state.produced_count,
            "scrap_count": state.scrap_count,
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
