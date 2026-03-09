# IMP CNC Production Tracking Prototype

Single-machine CNC production tracking prototype for a HAAS VF2 demo cell.

Fixed machine ID:
`HAAS_VF2_01`

## Non-negotiable constraints

- Single-machine scope only.
- Backend is source of truth.
- AI is analysis-only.
- AI never controls machine behavior.
- Simulator behavior is operator-triggered only.

## Tech stack

- Backend: FastAPI + SQLite + SQLAlchemy
- Frontend: React + Vite
- Realtime: WebSocket (`/ws`)
- AI layer: deterministic analysis + optional OpenAI-backed reason suggestion

## Current capabilities

- Role-based login (`OPERATOR`, `SUPERVISOR`)
- Operator workflow:
  - job selection
  - drawing open event + embedded PDF viewer
  - setup/start/pause/resume/alarm/clear/part-complete/finish controls
  - notes + scrap reporting
- Supervisor workflow:
  - machine status and active context
  - KPI cards
  - completed jobs table
  - add-job form
  - shift timeline
  - AI insight actions
- Event-driven backend with machine state persistence
- WebSocket broadcasts for machine, events, counts, and AI reports

## Repository layout

```text
backend/
frontend/
docs/
requirements.txt
ws_test.py
.env.example
```

## Quick start

### 1) Backend

```bash
pip install -r requirements.txt
copy .env.example .env
uvicorn backend.main:app --reload
```

Backend URL:
`http://127.0.0.1:8000`

Health check:
`http://127.0.0.1:8000/health`

### 2) Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend default URL (Vite):
`http://127.0.0.1:5173`

## Demo credentials

- Operator: `Albert` / `1111`
- Operator: `Ardin` / `2222`
- Operator: `Demo Operator` / `3333`
- Supervisor: `Valdrin` / `4444`

## Drawing files

Served by backend static route:
- `/drawings/support_plate.pdf`
- `/drawings/mounting_bracket.pdf`
- `/drawings/machined_shaft.pdf`

Opening a drawing via API logs a `drawing_opened` event.

## API overview

### Auth / Operators
- `POST /api/login`
- `POST /api/operators/login`
- `POST /api/operators/logout`

### Jobs
- `GET /api/jobs`
- `POST /api/jobs`
- `POST /api/jobs/select`
- `POST /api/jobs/finish`
- `GET /api/jobs/{job_id}/drawing`
- `GET /api/jobs/completed/today`

### Machine
- `GET /api/machine/state`
- `GET /api/machine/events?limit=50`
- `POST /api/machine/setup/start`
- `POST /api/machine/setup/confirm`
- `POST /api/machine/cycle/start`
- `POST /api/machine/cycle/pause`
- `POST /api/machine/cycle/resume`
- `POST /api/machine/cycle/complete`
- `POST /api/machine/alarm/trigger`
- `POST /api/machine/alarm/clear`

### Production
- `POST /api/production/note`
- `POST /api/production/scrap`
- `GET /api/production/counts`

### Dashboard
- `GET /api/dashboard/summary`
- `GET /api/dashboard/events?limit=50`
- `GET /api/dashboard/timeline`

### AI (analysis-only)
- `POST /api/ai/reason-suggest`
- `POST /api/ai/summary`
- `POST /api/ai/downtime-analysis`
- `POST /api/ai/scrap-analysis`
- `POST /api/ai/question`

## WebSocket contract

Endpoint:
`ws://127.0.0.1:8000/ws`

Broadcast message types:
- `machine_state_updated`
- `event_created`
- `production_count_updated`
- `scrap_count_updated`
- `ai_report_created`

## WebSocket smoke script

`ws_test.py` now triggers `POST /api/ai/summary` and waits for `ai_report_created`.

Run:

```bash
python ws_test.py
```

Expected output includes:
- `trigger_status=200`
- one or more websocket payloads
- `ai_report_created_report_id=<id>`

## Phase 8 demo checklist

See:
`docs/PHASE8_DEMO_CHECKLIST.md`

Includes:
- pre-demo readiness checklist
- Scenario 1 validation (normal production)
- Scenario 2 validation (interrupted production)
- presentation order
- constraint compliance checks

## Validation commands used during development

```bash
python -m compileall backend
python -c "import backend.main as m; print('import-ok', m.app.title)"
cd frontend && npm run build
```
