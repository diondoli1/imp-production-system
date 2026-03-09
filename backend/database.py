"""Database setup and Phase 2 seed initialization."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

load_dotenv()

DEFAULT_DATABASE_PATH = "data/imp_cnc_demo.db"
DATABASE_PATH = os.getenv("DATABASE_PATH", DEFAULT_DATABASE_PATH)

_db_file = Path(DATABASE_PATH)
if not _db_file.is_absolute():
    _db_file = Path.cwd() / _db_file
_db_file.parent.mkdir(parents=True, exist_ok=True)

SQLALCHEMY_DATABASE_URL = f"sqlite:///{_db_file.as_posix()}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    seed_db()


def seed_db() -> None:
    from backend.models import Job, Machine, MachineState, Operator
    from backend.schemas import MACHINE_ID

    session = SessionLocal()
    try:
        machine = session.get(Machine, MACHINE_ID)
        if machine is None:
            session.add(
                Machine(
                    machine_id=MACHINE_ID,
                    machine_name="Haas VF-2",
                    machine_type="CNC_MILL",
                    is_active=True,
                )
            )

        operators = [
            {"operator_id": "OP_001", "operator_name": "Albert", "pin": "1111"},
            {"operator_id": "OP_002", "operator_name": "Ardin", "pin": "2222"},
            {"operator_id": "OP_003", "operator_name": "Demo Operator", "pin": "3333"},
        ]
        for item in operators:
            if session.get(Operator, item["operator_id"]) is None:
                session.add(Operator(**item, is_active=True))

        jobs = [
            {
                "job_id": "JOB_201",
                "part_name": "Support Plate",
                "material": "S355",
                "target_quantity": 10,
                "drawing_file": "/drawings/support_plate.pdf",
                "status": "PENDING",
            },
            {
                "job_id": "JOB_202",
                "part_name": "Mounting Bracket",
                "material": "Aluminum",
                "target_quantity": 8,
                "drawing_file": "/drawings/mounting_bracket.pdf",
                "status": "PENDING",
            },
            {
                "job_id": "JOB_203",
                "part_name": "Machined Shaft",
                "material": "C45",
                "target_quantity": 25,
                "drawing_file": "/drawings/machined_shaft.pdf",
                "status": "PENDING",
            },
        ]
        for item in jobs:
            if session.get(Job, item["job_id"]) is None:
                session.add(Job(**item))

        state = session.get(MachineState, MACHINE_ID)
        if state is None:
            session.add(
                MachineState(
                    machine_id=MACHINE_ID,
                    current_state="IDLE",
                    active_job_id=None,
                    active_operator_id=None,
                    produced_count=0,
                    scrap_count=0,
                    last_event_id=None,
                )
            )

        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
