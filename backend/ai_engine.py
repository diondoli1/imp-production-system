"""Deterministic AI analysis engine for Phase 6.

AI is analysis-only and must never control machine behavior.
"""

from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime
from urllib import error as url_error
from urllib import request as url_request

from sqlalchemy.orm import Session

from backend.event_engine import ALARM_REASON_CODES, PAUSE_REASON_CODES, SCRAP_REASON_CODES, EventEngine
from backend.models import AIReport
from backend.schemas import MACHINE_ID
from backend.websocket.connection_manager import connection_manager

REASON_GROUP_CODES = {
    "PAUSE": sorted(PAUSE_REASON_CODES),
    "ALARM": sorted(ALARM_REASON_CODES),
    "SCRAP": sorted(SCRAP_REASON_CODES),
}


class AIEngineError(Exception):
    pass


class AIEngine:
    def __init__(self, db: Session):
        self.db = db
        self.event_engine = EventEngine(db)
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini").strip() or "gpt-4.1-mini"

    def suggest_reason_from_note(
        self,
        note: str,
        reason_group: str,
        job_id: str | None,
        operator_id: str | None,
    ) -> dict:
        cleaned_note = note.strip()
        if not cleaned_note:
            raise AIEngineError("note must not be empty")

        normalized_group = reason_group.strip().upper()
        allowed_codes = REASON_GROUP_CODES.get(normalized_group)
        if allowed_codes is None:
            raise AIEngineError("reason_group must be one of: PAUSE, ALARM, SCRAP")

        openai_code, openai_explanation = self._suggest_reason_with_openai(
            note=cleaned_note,
            reason_group=normalized_group,
            allowed_codes=allowed_codes,
        )

        source = "fallback"
        if openai_code:
            suggested_reason_code = openai_code
            explanation = openai_explanation or "Reason suggested by OpenAI."
            source = "openai"
        else:
            suggested_reason_code, explanation = self._fallback_reason_suggestion(
                note=cleaned_note,
                reason_group=normalized_group,
            )

        state = self.event_engine.get_machine_state()
        effective_job_id = job_id or state.active_job_id
        effective_operator_id = operator_id or state.active_operator_id

        report_payload = {
            "reason_group": normalized_group,
            "suggested_reason_code": suggested_reason_code,
            "explanation": explanation,
            "source": source,
        }
        saved = self._save_report(
            report_type="reason_suggest",
            output_text=json.dumps(report_payload),
            input_reference={
                "note": cleaned_note,
                "reason_group": normalized_group,
                "allowed_reason_codes": allowed_codes,
                "source": source,
                "openai_key_present": bool(self.openai_api_key),
            },
            job_id=effective_job_id,
            operator_id=effective_operator_id,
        )

        return {
            "report_id": saved["report_id"],
            "machine_id": saved["machine_id"],
            "job_id": saved["job_id"],
            "operator_id": saved["operator_id"],
            "reason_group": normalized_group,
            "suggested_reason_code": suggested_reason_code,
            "explanation": explanation,
            "source": source,
        }

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

    def _fallback_reason_suggestion(self, note: str, reason_group: str) -> tuple[str, str]:
        lower = note.lower()
        if reason_group == "ALARM":
            if "wear" in lower or "vibration" in lower or "insert" in lower:
                return "TOOL_WEAR", "Detected tooling wear/vibration keywords in note."
            if "fixture" in lower or "clamp" in lower:
                return "FIXTURE_ISSUE", "Detected fixture/clamp keywords in note."
            if "program" in lower or "stop" in lower:
                return "PROGRAM_STOP", "Detected program stop keywords in note."
            if "dimension" in lower or "tolerance" in lower:
                return "DIMENSION_CHECK", "Detected dimension/tolerance keywords in note."
            return "UNKNOWN_FAULT", "No direct alarm keyword match; using UNKNOWN_FAULT fallback."

        if reason_group == "PAUSE":
            if "tool" in lower:
                return "TOOL_CHANGE", "Detected tool-related keyword in note."
            if "inspect" in lower or "check" in lower:
                return "INSPECTION", "Detected inspection/check keyword in note."
            if "drawing" in lower:
                return "DRAWING_REVIEW", "Detected drawing keyword in note."
            if "material" in lower:
                return "MATERIAL_CHECK", "Detected material keyword in note."
            if "instruction" in lower or "wait" in lower:
                return "WAITING_INSTRUCTIONS", "Detected waiting/instructions keyword in note."
            if "break" in lower:
                return "OPERATOR_BREAK", "Detected break keyword in note."
            return "INSPECTION", "No direct pause keyword match; using INSPECTION fallback."

        if "dimension" in lower or "tolerance" in lower:
            return "DIMENSION_OUT", "Detected dimension/tolerance keyword in note."
        if "surface" in lower:
            return "SURFACE_DEFECT", "Detected surface keyword in note."
        if "setup" in lower:
            return "WRONG_SETUP", "Detected setup keyword in note."
        if "mark" in lower or "scratch" in lower:
            return "TOOL_MARK", "Detected tool-mark keyword in note."
        if "operator" in lower:
            return "OPERATOR_ERROR", "Detected operator keyword in note."
        return "DIMENSION_OUT", "No direct scrap keyword match; using DIMENSION_OUT fallback."

    def _suggest_reason_with_openai(
        self,
        note: str,
        reason_group: str,
        allowed_codes: list[str],
    ) -> tuple[str | None, str | None]:
        if not self.openai_api_key:
            return None, None

        system_prompt = (
            "You are assisting a CNC production tracking prototype. "
            "Choose exactly one reason code from the allowed list. "
            "Return JSON with keys suggested_reason_code and explanation."
        )
        user_prompt = (
            f"Reason group: {reason_group}\n"
            f"Allowed reason codes: {', '.join(allowed_codes)}\n"
            f"Operator note: {note}\n"
            "Rules: output only one allowed code."
        )
        response_text = self._call_openai_text(system_prompt=system_prompt, user_prompt=user_prompt)
        if not response_text:
            return None, None

        try:
            parsed = json.loads(response_text)
            code = str(parsed.get("suggested_reason_code", "")).strip().upper()
            explanation = str(parsed.get("explanation", "")).strip()
            if code in allowed_codes:
                return code, explanation or "Reason suggested by OpenAI."
        except Exception:
            pass

        for code in allowed_codes:
            if code in response_text.upper():
                return code, "Reason extracted from OpenAI response text."

        return None, None

    def _call_openai_text(self, system_prompt: str, user_prompt: str) -> str | None:
        payload = {
            "model": self.openai_model,
            "input": [
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": system_prompt}],
                },
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": user_prompt}],
                },
            ],
            "temperature": 0,
            "max_output_tokens": 200,
        }
        request_data = json.dumps(payload).encode("utf-8")
        request_obj = url_request.Request(
            "https://api.openai.com/v1/responses",
            data=request_data,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json",
            },
        )

        try:
            with url_request.urlopen(request_obj, timeout=20) as response:
                response_body = json.loads(response.read().decode("utf-8"))
        except (url_error.URLError, TimeoutError, json.JSONDecodeError, ValueError):
            return None

        direct_text = response_body.get("output_text")
        if isinstance(direct_text, str) and direct_text.strip():
            return direct_text.strip()

        output_items = response_body.get("output", [])
        if not isinstance(output_items, list):
            return None
        for item in output_items:
            contents = item.get("content", []) if isinstance(item, dict) else []
            if not isinstance(contents, list):
                continue
            for content in contents:
                if not isinstance(content, dict):
                    continue
                if content.get("type") in {"output_text", "text"}:
                    text_value = content.get("text")
                    if isinstance(text_value, str) and text_value.strip():
                        return text_value.strip()
        return None

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

        payload = {
            "report_id": report.report_id,
            "report_type": report.report_type,
            "machine_id": report.machine_id,
            "job_id": report.job_id,
            "operator_id": report.operator_id,
            "output_text": report.output_text,
            "input_reference": report.input_reference or "{}",
        }
        self._broadcast_ai_report(report)
        return payload

    def _broadcast_ai_report(self, report: AIReport) -> None:
        payload = {
            "type": "ai_report_created",
            "machine_id": report.machine_id,
            "report": {
                "report_id": report.report_id,
                "timestamp": report.timestamp.isoformat(),
                "report_type": report.report_type,
                "machine_id": report.machine_id,
                "job_id": report.job_id,
                "operator_id": report.operator_id,
                "input_reference": self._decode_input_reference(report.input_reference),
                "output_text": report.output_text,
            },
        }
        self._schedule_broadcast(payload)

    def _schedule_broadcast(self, payload: dict) -> None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(connection_manager.broadcast_json(payload))
            return
        loop.create_task(connection_manager.broadcast_json(payload))

    @staticmethod
    def _decode_input_reference(input_reference: str | None) -> dict | str | None:
        if input_reference is None:
            return None
        try:
            return json.loads(input_reference)
        except Exception:
            return input_reference
