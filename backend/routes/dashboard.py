from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.event_engine import EventEngine
from backend.schemas import DashboardSummaryResponse, MachineEventResponse, TimelineSegment

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(db: Session = Depends(get_db)) -> DashboardSummaryResponse:
    payload = EventEngine(db).get_dashboard_summary()
    return DashboardSummaryResponse(**payload)


@router.get("/timeline", response_model=list[TimelineSegment])
def get_dashboard_timeline(db: Session = Depends(get_db)) -> list[TimelineSegment]:
    segments = EventEngine(db).get_timeline_segments()
    return [TimelineSegment(**segment) for segment in segments]


@router.get("/events", response_model=list[MachineEventResponse])
def get_dashboard_events(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[MachineEventResponse]:
    events = EventEngine(db).get_recent_events(limit=limit)
    return [
        MachineEventResponse(
            event_id=event.event_id,
            timestamp=event.timestamp,
            machine_id=event.machine_id,
            event_type=event.event_type,
            machine_state=event.machine_state,
            job_id=event.job_id,
            operator_id=event.operator_id,
            reason_code=event.reason_code,
            details=event.details,
        )
        for event in events
    ]