"""Schemas used by backend foundation and Phase 2 production engine."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

MACHINE_ID = "HAAS_VF2_01"


class RootResponse(BaseModel):
    message: str
    machine_id: str
    phase: str


class HealthResponse(BaseModel):
    status: str
    machine_id: str
    database: str


class JobRead(BaseModel):
    job_id: str
    part_name: str
    material: str
    target_quantity: int
    drawing_file: str
    planned_cycle_time_sec: int | None = None
    status: str
    completed_at: datetime | None = None
    produced_quantity_final: int | None = None
    scrap_quantity_final: int | None = None
    completed_by_operator_id: str | None = None


class JobCreateRequest(BaseModel):
    part_name: str
    material: str
    target_quantity: int = Field(ge=1)
    drawing_file: str
    planned_cycle_time_sec: int | None = Field(default=None, ge=1)


class JobSelectRequest(BaseModel):
    job_id: str
    operator_id: str | None = None


class JobFinishRequest(BaseModel):
    operator_id: str | None = None
    note: str | None = None


class MachineStateResponse(BaseModel):
    machine_id: str
    current_state: str
    active_job_id: str | None
    active_operator_id: str | None
    produced_count: int
    scrap_count: int
    updated_at: datetime


class MachineEventResponse(BaseModel):
    event_id: int
    timestamp: datetime
    machine_id: str
    event_type: str
    machine_state: str
    job_id: str | None
    operator_id: str | None
    reason_code: str | None
    details: str | None


class CycleRequest(BaseModel):
    operator_id: str | None = None


class MachineActionRequest(BaseModel):
    operator_id: str | None = None
    reason_code: str | None = None
    note: str | None = None


class ScrapCreateRequest(BaseModel):
    quantity: int = Field(ge=1)
    reason_code: str
    note: str | None = None
    operator_id: str | None = None


class NoteCreateRequest(BaseModel):
    note: str = Field(min_length=1)
    operator_id: str | None = None
    reason_code: str | None = None


class APIMessage(BaseModel):
    message: str
    machine_id: str = MACHINE_ID
    data: dict[str, Any] | None = None


class OperatorLoginRequest(BaseModel):
    operator_name: str | None = None
    name: str | None = None
    pin: str


class OperatorLogoutRequest(BaseModel):
    operator_id: str


class LoginRequest(BaseModel):
    operator_name: str | None = None
    name: str | None = None
    pin: str


class DashboardSummaryResponse(BaseModel):
    machine_id: str
    current_state: str
    active_job_id: str | None
    active_job_name: str | None
    active_job_material: str | None = None
    active_job_target_quantity: int | None = None
    active_operator_id: str | None
    active_operator_name: str | None
    produced_count: int
    scrap_count: int
    jobs_completed_today: int = 0
    parts_produced_today: int = 0
    scrap_today: int = 0
    last_event_id: int | None
    updated_at: datetime


class CompletedJobRow(BaseModel):
    completed_at: datetime
    completed_time: datetime | None = None
    job_id: str
    job_name: str | None = None
    part_name: str
    produced_quantity_final: int
    produced: int | None = None
    scrap_quantity_final: int
    scrap: int | None = None
    completed_by_operator_id: str | None
    completed_by_operator_name: str | None
    operator_name: str | None = None


class CompletedJobsTodayResponse(BaseModel):
    machine_id: str
    jobs_completed_today: int
    parts_produced_today: int
    scrap_today: int
    jobs: list[CompletedJobRow]


class TimelineSegment(BaseModel):
    machine_id: str = MACHINE_ID
    state: str
    start: datetime
    end: datetime
    duration_sec: int
    reason_code: str | None = None


class ReasonSuggestRequest(BaseModel):
    note: str = Field(min_length=1)
    reason_group: Literal["PAUSE", "ALARM", "SCRAP"] = "ALARM"
    job_id: str | None = None
    operator_id: str | None = None


class ReasonSuggestResponse(BaseModel):
    report_id: int
    machine_id: str
    job_id: str | None
    operator_id: str | None
    reason_group: str
    suggested_reason_code: str
    explanation: str
    source: str


class AIAnalysisRequest(BaseModel):
    job_id: str | None = None
    operator_id: str | None = None
    limit: int = Field(default=100, ge=1, le=500)


class AIQuestionRequest(BaseModel):
    question: str
    job_id: str | None = None
    operator_id: str | None = None
    limit: int = Field(default=100, ge=1, le=500)


class AIAnalysisResponse(BaseModel):
    report_id: int
    report_type: str
    machine_id: str
    job_id: str | None
    operator_id: str | None
    output_text: str
    input_reference: str
