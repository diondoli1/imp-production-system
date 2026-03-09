## Implementation Plan

### 0) Repository analysis summary

### Structure inspected
- Backend: FastAPI + SQLAlchemy + SQLite with route modules under `backend/routes/`
- Frontend: React (Vite) under `frontend/src/` with `OperatorPage` and `DashboardPage`
- Docs: change request and snapshot under `docs/`

### Verification against `docs/PROJECT_SNAPSHOT.md`
- Matches:
  - Single-machine scope and fixed machine ID `HAAS_VF2_01`
  - Core backend modules and routes exist
  - SQLite schema mostly matches snapshot tables
  - WebSocket `/ws` exists
  - React shell with operator/dashboard modes exists
- Differences/gaps:
  - Snapshot mentions `.env.example`, but file is not present
  - Frontend calls `/api/ai/placeholder-report`, but backend does not expose it
  - AI engine counts pause/alarm/resume/clear events, but machine routes/event engine do not currently generate all those events
  - No role column on operators; no supervisor login flow
  - No job creation endpoint (`POST /api/jobs`)
  - No completed-jobs-today endpoint
  - No dashboard timeline aggregation endpoint
  - No backend drawing file serving/event endpoint

### Comparison against `docs/CHANGE_REQUEST.md`
- Fully missing or partial:
  - Role-based login + role-based routing
  - Operator UI redesign with control matrix and state-based button gating
  - Real PDF viewer integration and drawing-opened event
  - Supervisor dashboard expansion (KPIs, completed jobs, shift timeline, add job)
  - Job creation from dashboard + new job fields
  - Completed jobs today data panel
  - Shift timeline backend aggregation + frontend visualization
  - AI context expansion (timeline/completed jobs/downtime/scrap/notes)

---

## 1) Exact files that must change

- [backend/models.py](C:/Users/PC/Documents/New project/backend/models.py)
- [backend/schemas.py](C:/Users/PC/Documents/New project/backend/schemas.py)
- [backend/database.py](C:/Users/PC/Documents/New project/backend/database.py)
- [backend/main.py](C:/Users/PC/Documents/New project/backend/main.py)
- [backend/event_engine.py](C:/Users/PC/Documents/New project/backend/event_engine.py)
- [backend/ai_engine.py](C:/Users/PC/Documents/New project/backend/ai_engine.py)
- [backend/routes/operators.py](C:/Users/PC/Documents/New project/backend/routes/operators.py)
- [backend/routes/jobs.py](C:/Users/PC/Documents/New project/backend/routes/jobs.py)
- [backend/routes/machine.py](C:/Users/PC/Documents/New project/backend/routes/machine.py)
- [backend/routes/dashboard.py](C:/Users/PC/Documents/New project/backend/routes/dashboard.py)
- [backend/routes/ai.py](C:/Users/PC/Documents/New project/backend/routes/ai.py)
- [frontend/package.json](C:/Users/PC/Documents/New project/frontend/package.json)
- [frontend/package-lock.json](C:/Users/PC/Documents/New project/frontend/package-lock.json)
- [frontend/src/main.jsx](C:/Users/PC/Documents/New project/frontend/src/main.jsx)
- [frontend/src/App.jsx](C:/Users/PC/Documents/New project/frontend/src/App.jsx)
- [frontend/src/constants.js](C:/Users/PC/Documents/New project/frontend/src/constants.js)
- [frontend/src/services/api.js](C:/Users/PC/Documents/New project/frontend/src/services/api.js)
- [frontend/src/services/ws.js](C:/Users/PC/Documents/New project/frontend/src/services/ws.js)
- [frontend/src/pages/OperatorPage.jsx](C:/Users/PC/Documents/New project/frontend/src/pages/OperatorPage.jsx)
- [frontend/src/pages/DashboardPage.jsx](C:/Users/PC/Documents/New project/frontend/src/pages/DashboardPage.jsx)
- [frontend/src/components/MachineStatusBadge.jsx](C:/Users/PC/Documents/New project/frontend/src/components/MachineStatusBadge.jsx)
- [frontend/src/index.css](C:/Users/PC/Documents/New project/frontend/src/index.css)

---

## 2) New files to create

- [frontend/src/pages/LoginPage.jsx](C:/Users/PC/Documents/New project/frontend/src/pages/LoginPage.jsx)
- [frontend/src/components/MachinePanel.jsx](C:/Users/PC/Documents/New project/frontend/src/components/MachinePanel.jsx)
- [frontend/src/components/MachineControls.jsx](C:/Users/PC/Documents/New project/frontend/src/components/MachineControls.jsx)
- [frontend/src/components/JobCard.jsx](C:/Users/PC/Documents/New project/frontend/src/components/JobCard.jsx)
- [frontend/src/components/JobSelector.jsx](C:/Users/PC/Documents/New project/frontend/src/components/JobSelector.jsx)
- [frontend/src/components/PdfViewer.jsx](C:/Users/PC/Documents/New project/frontend/src/components/PdfViewer.jsx)
- [frontend/src/components/NotesPanel.jsx](C:/Users/PC/Documents/New project/frontend/src/components/NotesPanel.jsx)
- [frontend/src/components/ScrapPanel.jsx](C:/Users/PC/Documents/New project/frontend/src/components/ScrapPanel.jsx)
- [frontend/src/components/KpiCards.jsx](C:/Users/PC/Documents/New project/frontend/src/components/KpiCards.jsx)
- [frontend/src/components/MachineStatusCard.jsx](C:/Users/PC/Documents/New project/frontend/src/components/MachineStatusCard.jsx)
- [frontend/src/components/CompletedJobsToday.jsx](C:/Users/PC/Documents/New project/frontend/src/components/CompletedJobsToday.jsx)
- [frontend/src/components/AddJobForm.jsx](C:/Users/PC/Documents/New project/frontend/src/components/AddJobForm.jsx)
- [frontend/src/components/ShiftTimeline.jsx](C:/Users/PC/Documents/New project/frontend/src/components/ShiftTimeline.jsx)
- [frontend/src/components/AiInsightsPanel.jsx](C:/Users/PC/Documents/New project/frontend/src/components/AiInsightsPanel.jsx)

---

## 3) Phase-by-phase execution plan

## Phase 1 — database and backend foundations

- Files to modify:
  - `backend/models.py`, `backend/schemas.py`, `backend/database.py`, `backend/routes/operators.py`, `backend/routes/jobs.py`, `backend/routes/dashboard.py`, `backend/main.py`
- New files to create:
  - none required in backend for this phase
- Endpoints affected:
  - Add `POST /api/login` (keep `/api/operators/login` for compatibility)
  - Add `POST /api/jobs`
  - Add `GET /api/jobs/completed/today` (initial query contract)
  - Add `GET /api/dashboard/timeline` (initial response contract)
  - Keep existing endpoints unchanged
- Database changes:
  - `operators.role TEXT NOT NULL DEFAULT 'OPERATOR'`
  - `jobs.planned_cycle_time_sec INTEGER`
  - `jobs.completed_at DATETIME`
  - `jobs.produced_quantity_final INTEGER`
  - `jobs.scrap_quantity_final INTEGER`
  - `jobs.completed_by_operator_id TEXT`
  - Startup-safe SQLite migration logic in `database.py` (non-destructive, additive)
- Frontend components/pages affected:
  - none in this phase (backend contract first)
- Risks/dependencies:
  - SQLite ALTER behavior and existing DB compatibility
  - Need strict default role assignment for seeded users (including supervisor seed)

## Phase 2 — backend logic updates

- Files to modify:
  - `backend/event_engine.py`, `backend/routes/machine.py`, `backend/routes/jobs.py`, `backend/routes/dashboard.py`, `backend/routes/production.py`, `backend/ai_engine.py`, `backend/schemas.py`
- New files to create:
  - none required
- Endpoints affected:
  - Extend machine control endpoints to support requested controls (pause/resume/alarm/reset/finish) while preserving current setup/cycle endpoints
  - `POST /api/jobs` finalized behavior
  - `GET /api/jobs/completed/today` finalized aggregation
  - `GET /api/dashboard/summary` enriched output
  - `GET /api/dashboard/timeline` timeline segments from events
  - Drawing-open event endpoint support (or machine route action) for `drawing_opened`
- Database changes:
  - No new columns beyond Phase 1
  - Persist completion data into new `jobs` fields on job-finish flow
- Frontend components/pages affected:
  - API contract consumers only (implementation in Phase 3)
- Risks/dependencies:
  - Event/state transition integrity (EventEngine remains central validator)
  - Backward compatibility of existing API response shapes
  - Timeline accuracy depends on clean event ordering/timestamps

## Phase 3 — frontend integration

- Files to modify:
  - `frontend/src/main.jsx`, `frontend/src/App.jsx`, `frontend/src/services/api.js`, `frontend/src/services/ws.js`, `frontend/src/pages/OperatorPage.jsx`, `frontend/src/pages/DashboardPage.jsx`, `frontend/src/components/MachineStatusBadge.jsx`, `frontend/src/index.css`, `frontend/package.json`, `frontend/package-lock.json`
- New files to create:
  - `LoginPage.jsx`, `MachinePanel.jsx`, `MachineControls.jsx`, `JobCard.jsx`, `JobSelector.jsx`, `PdfViewer.jsx`, `NotesPanel.jsx`, `ScrapPanel.jsx`, `KpiCards.jsx`, `MachineStatusCard.jsx`, `CompletedJobsToday.jsx`, `AddJobForm.jsx`, `ShiftTimeline.jsx`, `AiInsightsPanel.jsx`
- Endpoints affected:
  - Consume `POST /api/login`
  - Consume `POST /api/jobs`, `GET /api/jobs`, `GET /api/jobs/completed/today`
  - Consume `GET /api/dashboard/summary`, `GET /api/dashboard/timeline`
  - Consume machine control endpoints and drawing-open event endpoint
  - Continue consuming `/ws`
- Database changes:
  - none
- Frontend components/pages affected:
  - New routes `/login`, `/operator`, `/supervisor`
  - Operator page rebuilt into two-column machine/work layout
  - Supervisor dashboard expanded with KPIs, timeline, completed jobs, add-job form, AI insights
  - PDF drawing viewer embedded with navigation/zoom/fit-width
- Risks/dependencies:
  - Route migration without breaking current app boot path
  - PDF viewer dependency + browser compatibility
  - Button enable/disable logic must mirror backend state machine exactly

## Phase 4 — AI improvements

- Files to modify:
  - `backend/ai_engine.py`, `backend/routes/ai.py`, `backend/schemas.py`, `frontend/src/components/AiInsightsPanel.jsx`, `frontend/src/services/api.js`
- New files to create:
  - none beyond Phase 3 AI panel
- Endpoints affected:
  - Existing AI endpoints remain and gain richer analysis context:
    - `POST /api/ai/downtime-analysis`
    - `POST /api/ai/scrap-analysis`
    - `POST /api/ai/summary`
    - `POST /api/ai/question`
- Database changes:
  - none required; continue persisting to `ai_reports`
- Frontend components/pages affected:
  - `AiInsightsPanel` and supervisor dashboard AI section
- Risks/dependencies:
  - Must remain analysis-only; no AI-triggered machine writes
  - “Operator notes” insight depends on what note data is persisted in backend events

## Phase 5 — cleanup and testing

- Files to modify:
  - `README.md`, `frontend/README.md`, `ws_test.py` (and any existing test harness files if present)
- New files to create:
  - `backend/tests/test_api_flows.py`
  - `backend/tests/test_event_engine_transitions.py`
  - `frontend/src/components/__tests__/` test files for critical UI flows (if test stack is added)
- Endpoints affected:
  - Validate all existing + new endpoints, especially backward-compatible legacy ones
- Database changes:
  - Migration validation against fresh DB and existing DB
- Frontend components/pages affected:
  - Final UX polish for login/operator/supervisor flows and responsive behavior
- Risks/dependencies:
  - No existing formal test suite baseline
  - Must verify demo scenarios end-to-end with single machine `HAAS_VF2_01`
  - Ensure no autonomous simulator behavior and no architecture drift
