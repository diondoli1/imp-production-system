"""SQLAlchemy models for the IMP CNC prototype."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class Machine(Base):
    __tablename__ = "machines"

    machine_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    machine_name: Mapped[str] = mapped_column(String(100), nullable=False)
    machine_type: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class Operator(Base):
    __tablename__ = "operators"

    operator_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    operator_name: Mapped[str] = mapped_column(String(100), nullable=False)
    pin: Mapped[str] = mapped_column(String(20), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="OPERATOR")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class Job(Base):
    __tablename__ = "jobs"

    job_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    part_name: Mapped[str] = mapped_column(String(120), nullable=False)
    material: Mapped[str] = mapped_column(String(80), nullable=False)
    target_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    drawing_file: Mapped[str] = mapped_column(String(255), nullable=False)
    planned_cycle_time_sec: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    produced_quantity_final: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    scrap_quantity_final: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    completed_by_operator_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("operators.operator_id"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class MachineEvent(Base):
    __tablename__ = "machine_events"

    event_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    machine_id: Mapped[str] = mapped_column(ForeignKey("machines.machine_id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    machine_state: Mapped[str] = mapped_column(String(20), nullable=False)
    job_id: Mapped[Optional[str]] = mapped_column(ForeignKey("jobs.job_id"), nullable=True)
    operator_id: Mapped[Optional[str]] = mapped_column(ForeignKey("operators.operator_id"), nullable=True)
    reason_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class MachineState(Base):
    __tablename__ = "machine_state"

    machine_id: Mapped[str] = mapped_column(ForeignKey("machines.machine_id"), primary_key=True)
    current_state: Mapped[str] = mapped_column(String(20), nullable=False, default="IDLE")
    active_job_id: Mapped[Optional[str]] = mapped_column(ForeignKey("jobs.job_id"), nullable=True)
    active_operator_id: Mapped[Optional[str]] = mapped_column(ForeignKey("operators.operator_id"), nullable=True)
    produced_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    scrap_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_event_id: Mapped[Optional[int]] = mapped_column(ForeignKey("machine_events.event_id"), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class ScrapReport(Base):
    __tablename__ = "scrap_reports"

    scrap_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    machine_id: Mapped[str] = mapped_column(ForeignKey("machines.machine_id"), nullable=False)
    job_id: Mapped[Optional[str]] = mapped_column(ForeignKey("jobs.job_id"), nullable=True)
    operator_id: Mapped[Optional[str]] = mapped_column(ForeignKey("operators.operator_id"), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    reason_code: Mapped[str] = mapped_column(String(50), nullable=False)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class AIReport(Base):
    __tablename__ = "ai_reports"

    report_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    machine_id: Mapped[str] = mapped_column(ForeignKey("machines.machine_id"), nullable=False)
    job_id: Mapped[Optional[str]] = mapped_column(ForeignKey("jobs.job_id"), nullable=True)
    operator_id: Mapped[Optional[str]] = mapped_column(ForeignKey("operators.operator_id"), nullable=True)
    report_type: Mapped[str] = mapped_column(String(50), nullable=False)
    input_reference: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    output_text: Mapped[str] = mapped_column(Text, nullable=False)