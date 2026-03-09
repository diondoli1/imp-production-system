# PROJECT_SNAPSHOT

## 1. Project Overview

### What the software currently does
This repository contains a single-machine CNC production tracking prototype for machine `HAAS_VF2_01`.

Current implemented behavior:
- Tracks machine state transitions (`IDLE`, `SETUP`, `READY`, `RUNNING`, etc.).
- Logs machine/operator/job events into an event table.
- Tracks operator login/logout and active operator assignment.
- Tracks job selection and active job assignment.
- Tracks produced and scrap counts through backend logic.
- Exposes dashboard endpoints for state + event history.
- Exposes AI analysis endpoints (deterministic analysis) and persists AI reports.
- Exposes WebSocket `/ws` for live backend event/count/state push updates.
- Provides a React frontend shell with Operator and Supervisor Dashboard modes.

### Main purpose of the system
To demonstrate a practical, local, event-driven CNC production tracking workflow with backend-as-source-of-truth behavior, real-time updates, and analysis-only AI support.

---

## 2. Tech Stack

- Backend framework: FastAPI (Python)
- Frontend framework: React (Vite dev server)
- Database type: SQLite (via SQLAlchemy ORM)
- Realtime system: native WebSocket endpoint (`/ws`) with a simple connection manager

---

## 3. Folder Structure

Top-level structure (current):

```text
imp_cnc_demo/
  backend/
    main.py
    database.py
    models.py
    schemas.py
    event_engine.py
    ai_engine.py
    simulator.py
    routes/
      operators.py
      jobs.py
      machine.py
      production.py
      dashboard.py
      ai.py
    websocket/
      connection_manager.py
  frontend/
    index.html
    package.json
    README.md
    src/
      main.jsx
      App.jsx
      index.css
      constants.js
      pages/
      components/
      services/
  data/
  docs/
    source/
  AGENTS.md
  README.md
  requirements.txt
  .env.example
  ws_test.py
```

Notes:
- `database/` and `scripts/` directories are not present in the current repository snapshot.
- `backend/ai`, `backend/api`, `backend/database` (directory), `backend/services`, `backend/simulator` (directory) exist as scaffold folders but are not primary runtime modules in current code paths.

---

## 4. Database Schema

Database engine: SQLite

### `machines`
- `machine_id` (PK)
- `machine_name`
- `machine_type`
- `is_active`
- `created_at`

### `operators`
- `operator_id` (PK)
- `operator_name`
- `pin`
- `is_active`
- `created_at`

### `jobs`
- `job_id` (PK)
- `part_name`
- `material`
- `target_quantity`
- `drawing_file`
- `status`
- `created_at`

### `machine_events`
- `event_id` (PK, autoincrement)
- `timestamp`
- `machine_id` (FK -> `machines.machine_id`)
- `event_type`
- `machine_state`
- `job_id` (FK -> `jobs.job_id`, nullable)
- `operator_id` (FK -> `operators.operator_id`, nullable)
- `reason_code` (nullable)
- `details` (JSON-as-text, nullable)

### `machine_state`
- `machine_id` (PK, FK -> `machines.machine_id`)
- `current_state`
- `active_job_id` (FK -> `jobs.job_id`, nullable)
- `active_operator_id` (FK -> `operators.operator_id`, nullable)
- `produced_count`
- `scrap_count`
- `last_event_id` (FK -> `machine_events.event_id`, nullable)
- `updated_at`

### `scrap_reports`
- `scrap_id` (PK, autoincrement)
- `timestamp`
- `machine_id` (FK -> `machines.machine_id`)
- `job_id` (FK -> `jobs.job_id`, nullable)
- `operator_id` (FK -> `operators.operator_id`, nullable)
- `quantity`
- `reason_code`
- `note` (nullable)

### `ai_reports`
- `report_id` (PK, autoincrement)
- `timestamp`
- `machine_id` (FK -> `machines.machine_id`)
- `job_id` (FK -> `jobs.job_id`, nullable)
- `operator_id` (FK -> `operators.operator_id`, nullable)
- `report_type`
- `input_reference` (nullable)
- `output_text`

### Relationships summary
- One machine row (`HAAS_VF2_01`) is the central parent for events/state/scrap/AI reports.
- Events, scrap, and AI reports can optionally reference job/operator records.
- `machine_state` tracks current live pointers (`active_job_id`, `active_operator_id`) plus counters.

---

## 5. Backend Architecture

### Main services/modules
- `backend/main.py`: FastAPI app bootstrapping, CORS, startup DB init, route registration, `/ws`.
- `backend/database.py`: SQLAlchemy engine/session/base and seed-on-start logic.
- `backend/models.py`: ORM models for all runtime tables.
- `backend/event_engine.py`: core state transition + event creation service, count updates, dashboard/AI query helpers, WebSocket broadcast hooks.
- `backend/ai_engine.py`: deterministic analysis service; writes AI outputs to `ai_reports`.
- `backend/websocket/connection_manager.py`: active WebSocket connection management and JSON broadcasting.

### Routes/endpoints (current)

Core:
- `GET /`
- `GET /health`
- `GET /ws` (WebSocket upgrade endpoint)

Operators:
- `POST /api/operators/login`
- `POST /api/operators/logout`

Jobs:
- `GET /api/jobs`
- `POST /api/jobs/select`

Machine:
- `GET /api/machine/state`
- `GET /api/machine/events`
- `POST /api/machine/setup/start`
- `POST /api/machine/setup/confirm`
- `POST /api/machine/cycle/start`
- `POST /api/machine/cycle/complete`

Production:
- `POST /api/production/scrap`
- `GET /api/production/counts`

Dashboard:
- `GET /api/dashboard/summary`
- `GET /api/dashboard/events`

AI:
- `POST /api/ai/downtime-analysis`
- `POST /api/ai/scrap-analysis`
- `POST /api/ai/summary`
- `POST /api/ai/question`

### Background jobs
- None as independent workers/cron jobs.
- WebSocket broadcasting is executed inline after backend state/event commits.

### Event systems
- Event log table: `machine_events`.
- Current-state table: `machine_state`.
- Event engine emits WebSocket payloads for:
  - `event_created`
  - `machine_state_updated`
  - `production_count_updated`
  - `scrap_count_updated`

---

## 6. Frontend Architecture

### Main pages
- `OperatorPage.jsx`
- `DashboardPage.jsx`

### Main components
- `ModeSwitch.jsx`
- `MachineStatusBadge.jsx`
- `EventTimeline.jsx`
- `Panel.jsx`

### Dashboards
- Supervisor dashboard page includes:
  - machine status panel
  - production metrics panel
  - event timeline panel
  - runtime metrics panel
  - AI insight panel

### State management
- React local state (`useState`) in `App.jsx` for:
  - current mode
  - machine state snapshot
  - job list
  - event list
  - operator session
  - WebSocket connection status
- Data fetch and mutation through `services/api.js`.
- Live updates through `services/ws.js`.

---

## 7. Data Flow

Primary flow:

1. UI sends action to API (`fetch` in frontend service layer).
2. API route calls `EventEngine` / `AIEngine`.
3. Engine reads/writes SQLite via SQLAlchemy session.
4. On state/event/count change, backend emits WebSocket payloads.
5. Frontend WebSocket client receives payload and updates local UI state.
6. UI reflects updated machine status, metrics, and timeline.

AI flow:

1. UI calls AI endpoint (`/api/ai/...`) with optional filters.
2. `AIEngine` reads event/state/scrap history via backend services.
3. AI output text is generated deterministically.
4. Output is saved to `ai_reports`.
5. Response returns report metadata + generated text.

---

## 8. Current Features

- Single machine identity fixed to `HAAS_VF2_01`.
- Database bootstrap + seed on startup.
- Operator login/logout.
- Job listing and selection.
- Setup/cycle state transition actions.
- Part completion and produced count tracking.
- Scrap reporting and scrap count tracking.
- Dashboard summary and event timeline APIs.
- WebSocket live update endpoint and broadcasts.
- Deterministic AI analysis endpoints:
  - downtime analysis
  - scrap analysis
  - production summary
  - operator Q/A
- Frontend shell with two modes:
  - Operator Interface
  - Supervisor Dashboard

---

## 9. Known Limitations

- Prototype scope only; no real CNC integration.
- No multi-machine support.
- No frontend auth/session persistence beyond in-memory page state.
- No advanced error UI/notification system on frontend.
- Operator notes panel in frontend is currently UI-shell behavior; no dedicated backend notes endpoint wired in current frontend flow.
- Frontend AI button currently references a placeholder-style API call path (`getAIPlaceholder`) that does not match current AI analysis endpoints and should be aligned.
- No separate test suite documented in this snapshot.
- No deployment packaging/containerization.

---

## 10. Deployment / Runtime Setup

### Backend runtime
- Command: `uvicorn backend.main:app --reload`
- Default API URL: `http://127.0.0.1:8000`
- Health endpoint: `/health`

### Frontend runtime
- Directory: `frontend/`
- Commands:
  - `npm install`
  - `npm run dev`
- Default Vite URL: `http://127.0.0.1:5173` (or localhost equivalent)

### Ports and network assumptions
- Backend: `8000`
- Frontend: `5173` (Vite dev)
- WebSocket: `ws://127.0.0.1:8000/ws`
- Intended local office-PC + tablet LAN demo model.

### Environment/config assumptions
- SQLite DB path from `DATABASE_PATH` (defaults to `data/imp_cnc_demo.db`).
- CORS origins from `FRONTEND_ORIGINS`.
- Single-machine fixed ID used throughout backend/frontend constants: `HAAS_VF2_01`.
