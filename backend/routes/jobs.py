from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.event_engine import EventEngine, EventEngineError
from backend.models import Job
from backend.schemas import APIMessage, JobRead, JobSelectRequest, MACHINE_ID

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
            status=job.status,
        )
        for job in jobs
    ]


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
