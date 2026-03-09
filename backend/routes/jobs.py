from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.event_engine import EventEngine, EventEngineError
from backend.models import Job
from backend.schemas import (
    APIMessage,
    CompletedJobRow,
    CompletedJobsTodayResponse,
    JobCreateRequest,
    JobRead,
    JobSelectRequest,
    MACHINE_ID,
)

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("", response_model=list[JobRead])
def list_jobs(db: Session = Depends(get_db)) -> list[JobRead]:
    jobs = db.query(Job).order_by(Job.created_at.asc()).all()
    return [
        JobRead(
            job_id=job.job_id,
            part_name=job.part_name,
            material=job.material,
            target_quantity=job.target_quantity,
            drawing_file=job.drawing_file,
            planned_cycle_time_sec=job.planned_cycle_time_sec,
            status=job.status,
            completed_at=job.completed_at,
            produced_quantity_final=job.produced_quantity_final,
            scrap_quantity_final=job.scrap_quantity_final,
            completed_by_operator_id=job.completed_by_operator_id,
        )
        for job in jobs
    ]


@router.post("", response_model=APIMessage)
def create_job(payload: JobCreateRequest, db: Session = Depends(get_db)) -> APIMessage:
    engine = EventEngine(db)
    try:
        job = engine.create_job(
            part_name=payload.part_name,
            material=payload.material,
            target_quantity=payload.target_quantity,
            drawing_file=payload.drawing_file,
            planned_cycle_time_sec=payload.planned_cycle_time_sec,
        )
    except EventEngineError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return APIMessage(
        message="Job created",
        machine_id=MACHINE_ID,
        data={
            "job_id": job.job_id,
            "part_name": job.part_name,
            "status": job.status,
        },
    )


@router.get("/completed/today", response_model=CompletedJobsTodayResponse)
def completed_jobs_today(db: Session = Depends(get_db)) -> CompletedJobsTodayResponse:
    payload = EventEngine(db).get_completed_jobs_today()
    rows = [CompletedJobRow(**item) for item in payload["jobs"]]
    return CompletedJobsTodayResponse(
        machine_id=payload["machine_id"],
        jobs_completed_today=payload["jobs_completed_today"],
        parts_produced_today=payload["parts_produced_today"],
        scrap_today=payload["scrap_today"],
        jobs=rows,
    )


@router.post("/select", response_model=APIMessage)
def select_job(payload: JobSelectRequest, db: Session = Depends(get_db)) -> APIMessage:
    engine = EventEngine(db)
    try:
        state = engine.select_job(job_id=payload.job_id, operator_id=payload.operator_id)
    except EventEngineError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return APIMessage(
        message="Job selected",
        machine_id=MACHINE_ID,
        data={
            "job_id": state.active_job_id,
            "current_state": state.current_state,
            "produced_count": state.produced_count,
            "scrap_count": state.scrap_count,
        },
    )