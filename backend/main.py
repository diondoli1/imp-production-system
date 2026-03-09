"""FastAPI entrypoint for the IMP CNC backend (Phase 5)."""

from __future__ import annotations

import os

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from backend import models  # noqa: F401 - ensures models module is loaded before init
from backend.database import SessionLocal, init_db
from backend.routes import ai, dashboard, jobs, machine, operators, production
from backend.schemas import HealthResponse, MACHINE_ID, RootResponse
from backend.websocket.connection_manager import connection_manager

load_dotenv()


def _parse_cors_origins() -> list[str]:
    raw = os.getenv(
        "FRONTEND_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173",
    )
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


app = FastAPI(
    title="IMP CNC Production Tracking Prototype API",
    description="Phase 6 AI analysis module for a single HAAS VF2 machine.",
    version="0.6.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_parse_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(operators.auth_router)
app.include_router(operators.router)
app.include_router(jobs.router)
app.include_router(machine.router)
app.include_router(production.router)
app.include_router(dashboard.router)
app.include_router(ai.router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/", response_model=RootResponse)
def root() -> RootResponse:
    return RootResponse(
        message="IMP CNC backend AI analysis module is running.",
        machine_id=MACHINE_ID,
        phase="Phase 6 - AI Analysis Module",
    )


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    db_status = "ok"
    session = SessionLocal()
    try:
        session.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"
    finally:
        session.close()
    status = "ok" if db_status == "ok" else "degraded"
    return HealthResponse(status=status, machine_id=MACHINE_ID, database=db_status)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await connection_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)