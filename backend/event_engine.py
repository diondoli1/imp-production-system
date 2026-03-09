"""Core event/state engine for Phase 2."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta

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

PAUSE_REASON_CODES = {
    "TOOL_CHANGE",
    "INSPECTION",
    "DRAWING_REVIEW",
    "MATERIAL_CHECK",
    "WAITING_INSTRUCTIONS",
    "OPERATOR_BREAK",
}

ALARM_REASON_CODES = {
    "TOOL_WEAR",
    "PROGRAM_STOP",
    "FIXTURE_ISSUE",
    "DIMENSION_CHECK",
    "UNKNOWN_FAULT",
}

SCRAP_REASON_CODES = {
    "DIMENSION_OUT",
    "SURFACE_DEFECT",
    "WRONG_SETUP",
    "TOOL_MARK",
    "OPERATOR_ERROR",
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

    def authenticate_user(self, operator_name: str, pin: str) -> Operator:
        stmt = select(Operator).where(
            Operator.operator_name == operator_name,
            Operator.pin == pin,
            Operator.is_active.is_(True),
        )
        operator = self.db.scalar(stmt)
        if operator is None:
            raise EventEngineError("Invalid credentials")
        return operator

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

    def create_job(
        self,
        part_name: str,
        material: str,
        target_quantity: int,
        drawing_file: str,
        planned_cycle_time_sec: int | None,
    ) -> Job:
        if target_quantity <= 0:
            raise EventEngineError("target_quantity must be > 0")

        next_job_id = self._next_job_id()
        job = Job(
            job_id=next_job_id,
            part_name=part_name,
            material=material,
            target_quantity=target_quantity,
            drawing_file=drawing_file,
            planned_cycle_time_sec=planned_cycle_time_sec,
            status="PENDING",
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def get_completed_jobs_today(self) -> dict:
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow_start = today_start + timedelta(days=1)

        stmt = (
            select(Job)
            .where(
                Job.completed_at.is_not(None),
                Job.completed_at >= today_start,
                Job.completed_at < tomorrow_start,
            )
            .order_by(Job.completed_at.desc())
        )
        jobs = list(self.db.scalars(stmt))

        rows: list[dict] = []
        for job in jobs:
            operator_name = None
            if job.completed_by_operator_id:
                operator = self.db.get(Operator, job.completed_by_operator_id)
                if operator is not None:
                    operator_name = operator.operator_name
            rows.append(
                {
                    "completed_at": job.completed_at,
                    "job_id": job.job_id,
                    "part_name": job.part_name,
                    "produced_quantity_final": int(job.produced_quantity_final or 0),
                    "scrap_quantity_final": int(job.scrap_quantity_final or 0),
                    "completed_by_operator_id": job.completed_by_operator_id,
                    "completed_by_operator_name": operator_name,
                }
            )

        return {
            "machine_id": MACHINE_ID,
            "jobs_completed_today": len(rows),
            "parts_produced_today": sum(item["produced_quantity_final"] for item in rows),
            "scrap_today": sum(item["scrap_quantity_final"] for item in rows),
            "jobs": rows,
        }

    def get_timeline_segments(self) -> list[dict]:
        events = list(
            self.db.scalars(
                select(MachineEvent)
                .where(MachineEvent.machine_id == MACHINE_ID)
                .order_by(MachineEvent.timestamp.asc(), MachineEvent.event_id.asc())
            )
        )
        if not events:
            return []

        segments: list[dict] = []
        current_state = events[0].machine_state
        segment_start = events[0].timestamp
        segment_reason = events[0].reason_code

        for event in events[1:]:
            if event.machine_state != current_state:
                end = event.timestamp
                duration_sec = max(0, int((end - segment_start).total_seconds()))
                segments.append(
                    {
                        "state": current_state,
                        "start": segment_start,
                        "end": end,
                        "duration_sec": duration_sec,
                        "reason_code": segment_reason,
                    }
                )
                current_state = event.machine_state
                segment_start = event.timestamp
                segment_reason = event.reason_code

        now = datetime.utcnow()
        duration_sec = max(0, int((now - segment_start).total_seconds()))
        segments.append(
            {
                "state": current_state,
                "start": segment_start,
                "end": now,
                "duration_sec": duration_sec,
                "reason_code": segment_reason,
            }
        )
        return segments

    def get_job_production_count(self, job_id: str) -> int:
        stmt = select(func.count(MachineEvent.event_id)).where(
            MachineEvent.machine_id == MACHINE_ID,
            MachineEvent.job_id == job_id,
            MachineEvent.event_type == "part_completed",
        )
        return int(self.db.scalar(stmt) or 0)

    def login_operator(self, operator_name: str, pin: str) -> tuple[Operator, MachineState]:
        operator = self.authenticate_user(operator_name, pin)

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
        state.active_operator_id = operator_id or state.active_operator_id
        state.produced_count = 0
        state.scrap_count = 0
        state.updated_at = datetime.utcnow()

        job.status = "ACTIVE"
        event = self._create_event(
            event_type="job_selected",
            machine_state=state.current_state,
            job_id=job_id,
            operator_id=state.active_operator_id,
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

    def open_drawing(self, job_id: str, operator_id: str | None = None) -> Job:
        job = self.db.get(Job, job_id)
        if job is None:
            raise EventEngineError(f"Unknown job_id: {job_id}")

        state = self.ensure_machine_state()
        state.active_operator_id = operator_id or state.active_operator_id
        state.updated_at = datetime.utcnow()
        event = self._create_event(
            event_type="drawing_opened",
            machine_state=state.current_state,
            job_id=job.job_id,
            operator_id=state.active_operator_id,
            details={"drawing_file": job.drawing_file},
        )
        self.db.commit()
        self._broadcast_event_created(event)
        return job

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
        state = self.ensure_machine_state()
        if not state.active_job_id:
            raise EventEngineError("No active job selected")
        return self._transition(
            event_type="cycle_started",
            target_state="RUNNING",
            operator_id=operator_id,
        )

    def cycle_pause(
        self,
        reason_code: str,
        operator_id: str | None = None,
        note: str | None = None,
    ) -> MachineState:
        validated_reason = self._validate_reason_code(
            reason_code=reason_code,
            allowed_codes=PAUSE_REASON_CODES,
            context="pause",
            required=True,
        )
        return self._transition(
            event_type="cycle_paused",
            target_state="PAUSED",
            operator_id=operator_id,
            reason_code=validated_reason,
            details={"note": note} if note else None,
        )

    def cycle_resume(
        self,
        operator_id: str | None = None,
        reason_code: str | None = None,
        note: str | None = None,
    ) -> MachineState:
        validated_reason = self._validate_reason_code(
            reason_code=reason_code,
            allowed_codes=PAUSE_REASON_CODES,
            context="resume",
            required=False,
        )
        return self._transition(
            event_type="cycle_resumed",
            target_state="RUNNING",
            operator_id=operator_id,
            reason_code=validated_reason,
            details={"note": note} if note else None,
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

    def alarm_trigger(
        self,
        reason_code: str,
        operator_id: str | None = None,
        note: str | None = None,
    ) -> MachineState:
        validated_reason = self._validate_reason_code(
            reason_code=reason_code,
            allowed_codes=ALARM_REASON_CODES,
            context="alarm",
            required=True,
        )
        return self._transition(
            event_type="alarm_triggered",
            target_state="ALARM",
            operator_id=operator_id,
            reason_code=validated_reason,
            details={"note": note} if note else None,
        )

    def alarm_clear(
        self,
        operator_id: str | None = None,
        reason_code: str | None = None,
        note: str | None = None,
    ) -> MachineState:
        validated_reason = self._validate_reason_code(
            reason_code=reason_code,
            allowed_codes=ALARM_REASON_CODES,
            context="alarm_clear",
            required=False,
        )
        return self._transition(
            event_type="alarm_cleared",
            target_state="READY",
            operator_id=operator_id,
            reason_code=validated_reason,
            details={"note": note} if note else None,
        )

    def add_note(
        self,
        note: str,
        operator_id: str | None = None,
        reason_code: str | None = None,
    ) -> MachineState:
        cleaned_note = note.strip()
        if not cleaned_note:
            raise EventEngineError("Note must not be empty")

        state = self.ensure_machine_state()
        if not state.active_job_id:
            raise EventEngineError("No active job selected")

        state.active_operator_id = operator_id or state.active_operator_id
        state.updated_at = datetime.utcnow()
        event = self._create_event(
            event_type="note_added",
            machine_state=state.current_state,
            job_id=state.active_job_id,
            operator_id=state.active_operator_id,
            reason_code=self._normalize_reason_code(reason_code),
            details={"note": cleaned_note},
        )
        self.db.commit()
        self.db.refresh(state)
        self._broadcast_event_created(event)
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

        validated_reason = self._validate_reason_code(
            reason_code=reason_code,
            allowed_codes=SCRAP_REASON_CODES,
            context="scrap",
            required=True,
        )

        state = self.ensure_machine_state()
        if not state.active_job_id:
            raise EventEngineError("No active job selected")

        previous_scrap = state.scrap_count
        scrap = ScrapReport(
            machine_id=MACHINE_ID,
            job_id=state.active_job_id,
            operator_id=operator_id or state.active_operator_id,
            quantity=quantity,
            reason_code=validated_reason,
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
            reason_code=validated_reason,
            details={"quantity": quantity, "note": note},
        )
        self.db.commit()
        self.db.refresh(state)
        self._broadcast_event_created(event)
        if previous_scrap != state.scrap_count:
            self._broadcast_scrap_count(state)
        return state

    def finish_job(self, operator_id: str | None = None, note: str | None = None) -> tuple[MachineState, Job]:
        state = self.ensure_machine_state()
        if not state.active_job_id:
            raise EventEngineError("No active job selected")

        self._assert_transition(state.current_state, "COMPLETED")
        completed_job_id = state.active_job_id
        job = self.db.get(Job, completed_job_id)
        if job is None:
            raise EventEngineError(f"Unknown job_id: {completed_job_id}")

        previous_produced = state.produced_count
        previous_scrap = state.scrap_count

        state.current_state = "COMPLETED"
        state.active_operator_id = operator_id or state.active_operator_id
        state.updated_at = datetime.utcnow()
        finished_event = self._create_event(
            event_type="job_finished",
            machine_state="COMPLETED",
            job_id=completed_job_id,
            operator_id=state.active_operator_id,
            details={
                "note": note,
                "produced_quantity_final": previous_produced,
                "scrap_quantity_final": previous_scrap,
            },
        )

        job.status = "COMPLETED"
        job.completed_at = datetime.utcnow()
        job.produced_quantity_final = previous_produced
        job.scrap_quantity_final = previous_scrap
        job.completed_by_operator_id = state.active_operator_id

        self._schedule_broadcast(
            {
                "type": "machine_state_updated",
                "machine_id": state.machine_id,
                "current_state": "COMPLETED",
                "active_job_id": completed_job_id,
                "active_operator_id": state.active_operator_id,
                "produced_count": previous_produced,
                "scrap_count": previous_scrap,
                "updated_at": state.updated_at.isoformat(),
            }
        )

        self._assert_transition("COMPLETED", "IDLE")
        state.current_state = "IDLE"
        state.active_job_id = None
        state.produced_count = 0
        state.scrap_count = 0
        state.updated_at = datetime.utcnow()
        reset_event = self._create_event(
            event_type="machine_reset_to_idle",
            machine_state="IDLE",
            job_id=None,
            operator_id=state.active_operator_id,
            details={"previous_job_id": completed_job_id},
        )

        self.db.commit()
        self.db.refresh(state)
        self.db.refresh(job)

        self._broadcast_event_created(finished_event)
        self._broadcast_event_created(reset_event)
        self._broadcast_machine_state(state)
        if previous_produced != state.produced_count:
            self._broadcast_produced_count(state)
        if previous_scrap != state.scrap_count:
            self._broadcast_scrap_count(state)

        return state, job

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
        self._assert_transition(previous_state, target_state)

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

    def _next_job_id(self) -> str:
        existing_ids = list(self.db.scalars(select(Job.job_id)))
        max_numeric = 200
        for job_id in existing_ids:
            if not job_id.startswith("JOB_"):
                continue
            suffix = job_id.split("JOB_", 1)[1]
            if suffix.isdigit():
                max_numeric = max(max_numeric, int(suffix))
        return f"JOB_{max_numeric + 1}"

    def _assert_transition(self, current_state: str, target_state: str) -> None:
        allowed = VALID_TRANSITIONS.get(current_state, set())
        if target_state not in allowed:
            raise InvalidTransitionError(f"Invalid transition {current_state} -> {target_state}")

    def _normalize_reason_code(self, reason_code: str | None) -> str | None:
        if reason_code is None:
            return None
        normalized = reason_code.strip().upper()
        return normalized if normalized else None

    def _validate_reason_code(
        self,
        reason_code: str | None,
        allowed_codes: set[str],
        context: str,
        required: bool,
    ) -> str | None:
        normalized = self._normalize_reason_code(reason_code)
        if normalized is None:
            if required:
                raise EventEngineError(f"{context} reason_code is required")
            return None
        if normalized not in allowed_codes:
            allowed_values = ", ".join(sorted(allowed_codes))
            raise EventEngineError(f"Invalid {context} reason_code '{normalized}'. Allowed: {allowed_values}")
        return normalized

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