"""Core event/state engine for Phase 2."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.models import Job, MachineEvent, MachineState, Operator, ScrapReport
from backend.schemas import MACHINE_ID
from backend.websocket.connection_manager import connection_manager

MACHINE_STATES = {
    "OFFLINE",
    "IDLE",
    "SETUP",
    "READY",
    "RUNNING",
    "PAUSED",
    "ALARM",
    "COMPLETED",
}

VALID_TRANSITIONS = {
    "OFFLINE": {"IDLE"},
    "IDLE": {"SETUP"},
    "SETUP": {"READY"},
    "READY": {"RUNNING"},
    "RUNNING": {"PAUSED", "ALARM", "COMPLETED"},
    "PAUSED": {"RUNNING"},
    "ALARM": {"READY"},
    "COMPLETED": {"IDLE"},
}


class EventEngineError(Exception):
    pass


class InvalidTransitionError(EventEngineError):
    pass


class EventEngine:
    def __init__(self, db: Session):
        self.db = db

    def ensure_machine_state(self) -> MachineState:
        state = self.db.get(MachineState, MACHINE_ID)
        if state is None:
            state = MachineState(
                machine_id=MACHINE_ID,
                current_state="IDLE",
                active_job_id=None,
                active_operator_id=None,
                produced_count=0,
                scrap_count=0,
                last_event_id=None,
            )
            self.db.add(state)
            self.db.flush()
        return state

    def get_machine_state(self) -> MachineState:
        return self.ensure_machine_state()

    def get_recent_events(
        self,
        limit: int = 50,
        job_id: str | None = None,
        operator_id: str | None = None,
    ) -> list[MachineEvent]:
        stmt = select(MachineEvent).where(MachineEvent.machine_id == MACHINE_ID)
        if job_id:
            stmt = stmt.where(MachineEvent.job_id == job_id)
        if operator_id:
            stmt = stmt.where(MachineEvent.operator_id == operator_id)
        stmt = stmt.order_by(MachineEvent.event_id.desc()).limit(limit)
        return list(self.db.scalars(stmt))

    def get_scrap_reports(
        self,
        limit: int = 100,
        job_id: str | None = None,
        operator_id: str | None = None,
    ) -> list[ScrapReport]:
        stmt = select(ScrapReport).where(ScrapReport.machine_id == MACHINE_ID)
        if job_id:
            stmt = stmt.where(ScrapReport.job_id == job_id)
        if operator_id:
            stmt = stmt.where(ScrapReport.operator_id == operator_id)
        stmt = stmt.order_by(ScrapReport.scrap_id.desc()).limit(limit)
        return list(self.db.scalars(stmt))

    def get_dashboard_summary(self) -> dict:
        state = self.ensure_machine_state()
        active_job_name = None
        active_operator_name = None

        if state.active_job_id:
            job = self.db.get(Job, state.active_job_id)
            if job is not None:
                active_job_name = job.part_name

        if state.active_operator_id:
            operator = self.db.get(Operator, state.active_operator_id)
            if operator is not None:
                active_operator_name = operator.operator_name

        return {
            "machine_id": state.machine_id,
            "current_state": state.current_state,
            "active_job_id": state.active_job_id,
            "active_job_name": active_job_name,
            "active_operator_id": state.active_operator_id,
            "active_operator_name": active_operator_name,
            "produced_count": state.produced_count,
            "scrap_count": state.scrap_count,
            "last_event_id": state.last_event_id,
            "updated_at": state.updated_at,
        }

    def get_job_production_count(self, job_id: str) -> int:
        stmt = select(func.count(MachineEvent.event_id)).where(
            MachineEvent.machine_id == MACHINE_ID,
            MachineEvent.job_id == job_id,
            MachineEvent.event_type == "part_completed",
        )
        return int(self.db.scalar(stmt) or 0)

    def login_operator(self, operator_name: str, pin: str) -> tuple[Operator, MachineState]:
        stmt = select(Operator).where(
            Operator.operator_name == operator_name,
            Operator.pin == pin,
            Operator.is_active.is_(True),
        )
        operator = self.db.scalar(stmt)
        if operator is None:
            raise EventEngineError("Invalid operator credentials")

        state = self.ensure_machine_state()
        state.active_operator_id = operator.operator_id
        state.updated_at = datetime.utcnow()
        event = self._create_event(
            event_type="operator_logged_in",
            machine_state=state.current_state,
            job_id=state.active_job_id,
            operator_id=operator.operator_id,
            details={"operator_name": operator.operator_name},
        )
        self.db.commit()
        self.db.refresh(state)
        self._broadcast_event_created(event)
        return operator, state

    def logout_operator(self, operator_id: str) -> MachineState:
        operator = self.db.get(Operator, operator_id)
        if operator is None or not operator.is_active:
            raise EventEngineError(f"Unknown or inactive operator_id: {operator_id}")

        state = self.ensure_machine_state()
        if state.active_operator_id != operator_id:
            raise EventEngineError("Operator is not currently active on this machine")

        event = self._create_event(
            event_type="operator_logged_out",
            machine_state=state.current_state,
            job_id=state.active_job_id,
            operator_id=operator_id,
            details={"operator_name": operator.operator_name},
        )
        state.active_operator_id = None
        state.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(state)
        self._broadcast_event_created(event)
        return state

    def select_job(self, job_id: str, operator_id: str | None = None) -> MachineState:
        job = self.db.get(Job, job_id)
        if job is None:
            raise EventEngineError(f"Unknown job_id: {job_id}")

        state = self.ensure_machine_state()
        if state.active_job_id and state.active_job_id != job_id:
            previous_job = self.db.get(Job, state.active_job_id)
            if previous_job is not None and previous_job.status == "ACTIVE":
                previous_job.status = "PENDING"

        previous_produced = state.produced_count
        previous_scrap = state.scrap_count
        state.active_job_id = job_id
        state.active_operator_id = operator_id
        state.produced_count = 0
        state.scrap_count = 0
        state.updated_at = datetime.utcnow()

        job.status = "ACTIVE"
        event = self._create_event(
            event_type="job_selected",
            machine_state=state.current_state,
            job_id=job_id,
            operator_id=operator_id,
            details={"message": "Job selected"},
        )
        self.db.commit()
        self.db.refresh(state)
        self._broadcast_event_created(event)
        if previous_produced != state.produced_count:
            self._broadcast_produced_count(state)
        if previous_scrap != state.scrap_count:
            self._broadcast_scrap_count(state)
        return state

    def setup_start(self, operator_id: str | None = None) -> MachineState:
        return self._transition(
            event_type="setup_started",
            target_state="SETUP",
            operator_id=operator_id,
        )

    def setup_confirm(self, operator_id: str | None = None) -> MachineState:
        return self._transition(
            event_type="setup_confirmed",
            target_state="READY",
            operator_id=operator_id,
        )

    def cycle_start(self, operator_id: str | None = None) -> MachineState:
        return self._transition(
            event_type="cycle_started",
            target_state="RUNNING",
            operator_id=operator_id,
        )

    def cycle_complete(self, operator_id: str | None = None) -> MachineState:
        state = self.ensure_machine_state()
        if state.current_state != "RUNNING":
            raise InvalidTransitionError("part_completed is only valid while RUNNING")
        if not state.active_job_id:
            raise EventEngineError("No active job selected")

        previous_produced = state.produced_count
        state.produced_count += 1
        state.active_operator_id = operator_id or state.active_operator_id
        state.updated_at = datetime.utcnow()
        event = self._create_event(
            event_type="part_completed",
            machine_state=state.current_state,
            job_id=state.active_job_id,
            operator_id=state.active_operator_id,
            details={"produced_count": state.produced_count},
        )
        self.db.commit()
        self.db.refresh(state)
        self._broadcast_event_created(event)
        if previous_produced != state.produced_count:
            self._broadcast_produced_count(state)
        return state

    def record_scrap(
        self,
        quantity: int,
        reason_code: str,
        note: str | None = None,
        operator_id: str | None = None,
    ) -> MachineState:
        if quantity <= 0:
            raise EventEngineError("Scrap quantity must be > 0")

        state = self.ensure_machine_state()
        if not state.active_job_id:
            raise EventEngineError("No active job selected")

        previous_scrap = state.scrap_count
        scrap = ScrapReport(
            machine_id=MACHINE_ID,
            job_id=state.active_job_id,
            operator_id=operator_id or state.active_operator_id,
            quantity=quantity,
            reason_code=reason_code,
            note=note,
        )
        self.db.add(scrap)

        state.scrap_count += quantity
        state.active_operator_id = operator_id or state.active_operator_id
        state.updated_at = datetime.utcnow()
        event = self._create_event(
            event_type="scrap_reported",
            machine_state=state.current_state,
            job_id=state.active_job_id,
            operator_id=state.active_operator_id,
            reason_code=reason_code,
            details={"quantity": quantity, "note": note},
        )
        self.db.commit()
        self.db.refresh(state)
        self._broadcast_event_created(event)
        if previous_scrap != state.scrap_count:
            self._broadcast_scrap_count(state)
        return state

    def _transition(
        self,
        event_type: str,
        target_state: str,
        operator_id: str | None = None,
        reason_code: str | None = None,
        details: dict | None = None,
    ) -> MachineState:
        if target_state not in MACHINE_STATES:
            raise EventEngineError(f"Unknown machine state: {target_state}")

        state = self.ensure_machine_state()
        previous_state = state.current_state
        allowed = VALID_TRANSITIONS.get(state.current_state, set())
        if target_state not in allowed:
            raise InvalidTransitionError(f"Invalid transition {state.current_state} -> {target_state}")

        state.current_state = target_state
        state.active_operator_id = operator_id or state.active_operator_id
        state.updated_at = datetime.utcnow()

        event = self._create_event(
            event_type=event_type,
            machine_state=state.current_state,
            job_id=state.active_job_id,
            operator_id=state.active_operator_id,
            reason_code=reason_code,
            details=details,
        )
        self.db.commit()
        self.db.refresh(state)
        self._broadcast_event_created(event)
        if previous_state != state.current_state:
            self._broadcast_machine_state(state)
        return state

    def _create_event(
        self,
        event_type: str,
        machine_state: str,
        job_id: str | None = None,
        operator_id: str | None = None,
        reason_code: str | None = None,
        details: dict | None = None,
    ) -> MachineEvent:
        state = self.ensure_machine_state()
        event = MachineEvent(
            machine_id=MACHINE_ID,
            event_type=event_type,
            machine_state=machine_state,
            job_id=job_id,
            operator_id=operator_id,
            reason_code=reason_code,
            details=json.dumps(details) if details is not None else None,
        )
        self.db.add(event)
        self.db.flush()
        state.last_event_id = event.event_id
        state.updated_at = datetime.utcnow()
        return event

    def _broadcast_machine_state(self, state: MachineState) -> None:
        self._schedule_broadcast(
            {
                "type": "machine_state_updated",
                "machine_id": state.machine_id,
                "current_state": state.current_state,
                "active_job_id": state.active_job_id,
                "active_operator_id": state.active_operator_id,
                "produced_count": state.produced_count,
                "scrap_count": state.scrap_count,
                "updated_at": state.updated_at.isoformat(),
            }
        )

    def _broadcast_event_created(self, event: MachineEvent) -> None:
        self._schedule_broadcast(
            {
                "type": "event_created",
                "machine_id": event.machine_id,
                "event": {
                    "event_id": event.event_id,
                    "timestamp": event.timestamp.isoformat(),
                    "event_type": event.event_type,
                    "machine_state": event.machine_state,
                    "job_id": event.job_id,
                    "operator_id": event.operator_id,
                    "reason_code": event.reason_code,
                    "details": self._decode_event_details(event.details),
                },
            }
        )

    def _broadcast_produced_count(self, state: MachineState) -> None:
        self._schedule_broadcast(
            {
                "type": "production_count_updated",
                "machine_id": state.machine_id,
                "active_job_id": state.active_job_id,
                "produced_count": state.produced_count,
                "updated_at": state.updated_at.isoformat(),
            }
        )

    def _broadcast_scrap_count(self, state: MachineState) -> None:
        self._schedule_broadcast(
            {
                "type": "scrap_count_updated",
                "machine_id": state.machine_id,
                "active_job_id": state.active_job_id,
                "scrap_count": state.scrap_count,
                "updated_at": state.updated_at.isoformat(),
            }
        )

    def _schedule_broadcast(self, payload: dict) -> None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(connection_manager.broadcast_json(payload))
            return
        loop.create_task(connection_manager.broadcast_json(payload))

    @staticmethod
    def _decode_event_details(details: str | None) -> dict | str | None:
        if details is None:
            return None
        try:
            return json.loads(details)
        except Exception:
            return details
