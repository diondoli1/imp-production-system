"""Deterministic AI analysis engine for Phase 6.

AI is analysis-only and must never control machine behavior.
"""

from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy.orm import Session

from backend.event_engine import EventEngine
from backend.models import AIReport
from backend.schemas import MACHINE_ID


class AIEngine:
    def __init__(self, db: Session):
        self.db = db
        self.event_engine = EventEngine(db)

    def analyze_downtime(self, job_id: str | None, operator_id: str | None, limit: int) -> dict:
        events = self.event_engine.get_recent_events(limit=limit, job_id=job_id, operator_id=operator_id)
        pauses = sum(1 for event in events if event.event_type == "cycle_paused")
        alarms = sum(1 for event in events if event.event_type == "alarm_triggered")
        resumes = sum(1 for event in events if event.event_type == "cycle_resumed")
        clears = sum(1 for event in events if event.event_type == "alarm_cleared")

        output_text = (
            f"Downtime analysis for {MACHINE_ID}: {pauses} pause event(s), {alarms} alarm trigger event(s), "
            f"{resumes} resume event(s), and {clears} alarm clear event(s) in the last {len(events)} event(s)."
        )
        return self._save_report(
            report_type="downtime_analysis",
            output_text=output_text,
            input_reference={"job_id": job_id, "operator_id": operator_id, "limit": limit},
            job_id=job_id,
            operator_id=operator_id,
        )

    def analyze_scrap(self, job_id: str | None, operator_id: str | None, limit: int) -> dict:
        scrap_reports = self.event_engine.get_scrap_reports(limit=limit, job_id=job_id, operator_id=operator_id)
        total_quantity = sum(report.quantity for report in scrap_reports)
        by_reason: dict[str, int] = {}
        for report in scrap_reports:
            by_reason[report.reason_code] = by_reason.get(report.reason_code, 0) + report.quantity

        reason_text = ", ".join(f"{reason}: {qty}" for reason, qty in sorted(by_reason.items())) if by_reason else "none"
        output_text = (
            f"Scrap analysis for {MACHINE_ID}: total scrap quantity is {total_quantity} across "
            f"{len(scrap_reports)} report(s). Reason totals: {reason_text}."
        )
        return self._save_report(
            report_type="scrap_analysis",
            output_text=output_text,
            input_reference={"job_id": job_id, "operator_id": operator_id, "limit": limit},
            job_id=job_id,
            operator_id=operator_id,
        )

    def summarize_production(self, job_id: str | None, operator_id: str | None, limit: int) -> dict:
        state = self.event_engine.get_machine_state()
        events = self.event_engine.get_recent_events(limit=limit, job_id=job_id, operator_id=operator_id)
        completed = sum(1 for event in events if event.event_type == "part_completed")
        scraps = sum(1 for event in events if event.event_type == "scrap_reported")
        alarms = sum(1 for event in events if event.event_type == "alarm_triggered")
        output_text = (
            f"Production summary for {MACHINE_ID}: state={state.current_state}, active_job={state.active_job_id}, "
            f"active_operator={state.active_operator_id}, produced_count={state.produced_count}, "
            f"scrap_count={state.scrap_count}. In the analysis window: {completed} part completion event(s), "
            f"{scraps} scrap event(s), and {alarms} alarm trigger event(s)."
        )
        return self._save_report(
            report_type="production_summary",
            output_text=output_text,
            input_reference={"job_id": job_id, "operator_id": operator_id, "limit": limit},
            job_id=job_id or state.active_job_id,
            operator_id=operator_id or state.active_operator_id,
        )

    def answer_operator_question(
        self,
        question: str,
        job_id: str | None,
        operator_id: str | None,
        limit: int,
    ) -> dict:
        state = self.event_engine.get_machine_state()
        events = self.event_engine.get_recent_events(limit=limit, job_id=job_id, operator_id=operator_id)
        lower = question.lower()
        part_events = sum(1 for event in events if event.event_type == "part_completed")
        alarm_events = sum(1 for event in events if event.event_type == "alarm_triggered")
        scrap_events = sum(1 for event in events if event.event_type == "scrap_reported")

        if "alarm" in lower:
            answer = f"There are {alarm_events} alarm trigger event(s) in the selected analysis window."
        elif "scrap" in lower:
            answer = f"There are {scrap_events} scrap report event(s) in the selected analysis window."
        elif "count" in lower or "part" in lower or "produce" in lower:
            answer = (
                f"Current produced_count is {state.produced_count}. "
                f"There are {part_events} part completion event(s) in the selected analysis window."
            )
        elif "state" in lower:
            answer = f"Current machine state is {state.current_state}."
        elif "operator" in lower:
            answer = f"Current active operator is {state.active_operator_id}."
        else:
            answer = (
                f"Current state is {state.current_state}, active_job={state.active_job_id}, "
                f"active_operator={state.active_operator_id}, produced_count={state.produced_count}, "
                f"scrap_count={state.scrap_count}, events_in_window={len(events)}."
            )

        output_text = f"Question: {question}\nAnswer: {answer}"
        return self._save_report(
            report_type="operator_question",
            output_text=output_text,
            input_reference={
                "question": question,
                "job_id": job_id,
                "operator_id": operator_id,
                "limit": limit,
            },
            job_id=job_id or state.active_job_id,
            operator_id=operator_id or state.active_operator_id,
        )

    def _save_report(
        self,
        report_type: str,
        output_text: str,
        input_reference: dict,
        job_id: str | None,
        operator_id: str | None,
    ) -> dict:
        report = AIReport(
            timestamp=datetime.utcnow(),
            machine_id=MACHINE_ID,
            job_id=job_id,
            operator_id=operator_id,
            report_type=report_type,
            input_reference=json.dumps(input_reference),
            output_text=output_text,
        )
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return {
            "report_id": report.report_id,
            "report_type": report.report_type,
            "machine_id": report.machine_id,
            "job_id": report.job_id,
            "operator_id": report.operator_id,
            "output_text": report.output_text,
            "input_reference": report.input_reference or "{}",
        }
