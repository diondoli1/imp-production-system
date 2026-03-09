# IMP CNC Prototype - Full Current Delta (As of 2026-03-09)

## 1) Purpose of this document

This document captures the current real implementation state of the repository versus the official source-of-truth documents, so a new Codex agent can continue work with minimal ambiguity.

Date captured: 2026-03-09
Workspace: C:\Users\PC\Documents\New project
Branch at capture: codex/github-checkpoint-automation (ca83be8)

---

## 2) Source-of-truth baseline used for delta

Per AGENTS.md, the following documents were used in required order:

1. `docs/source/03_TECHNICAL_DESIGN_FULL.md` (ultimate source of truth)
2. `docs/source/02_BUILD_RULES.md`
3. `docs/source/07_IMPLEMENTATION_SEQUENCE.md`
4. `docs/source/05_CODEX_PROMPT_SEQUENCE.md`
5. `docs/source/09_RUNTIME_AND_REPOSITORY_SPEC.md`
6. `docs/source/01_PROJECT_BRIEF.md`
7. `docs/source/08_DEMO_DATA_AND_SCENARIOS.md`

---

## 3) High-level status summary

Current implementation is between Phase 6 and Phase 7, with:

- Backend foundation present and substantial.
- Data model present and seeded.
- Event engine present but simulator-control coverage incomplete.
- WebSocket path present, but AI broadcast contract incomplete.
- AI analysis endpoints present, but not aligned to full Phase 6 spec.
- Frontend shell present with Operator and Dashboard modes, but not fully wired to backend capabilities.
- Final demo prep (Phase 8) not completed.

Core architecture constraints are currently respected:

- Single-machine scope preserved.
- Machine ID `HAAS_VF2_01` preserved in backend and frontend constants.
- Backend remains source of truth.
- AI remains analysis-only (no machine control paths observed).
- Simulator is non-autonomous (currently placeholder/manual behavior).

---

## 4) Repository and runtime snapshot

## Current top-level layout (actual)

- `.git/`
- `.github/`
- `backend/`
- `docs/`
- `frontend/`
- `AGENTS.md`
- `README.md`
- `requirements.txt`
- `ws_test.py`

## Notable structure deltas from runtime spec target

- `data/` directory is not currently present in repo root (it is created at runtime by DB init path logic).
- `.env.example` is missing.
- `database/schema.sql`, `data/demo_jobs.json`, `data/demo_operators.json` are not present.

## Git state at capture

- Current branch: `codex/github-checkpoint-automation`
- HEAD: `ca83be8`
- Working tree: dirty (multiple backend source edits and pycache binary changes; one untracked doc file).

---

## 5) Phase-by-phase delta (Implementation Sequence)

## Phase 1 - Backend foundation

Status: Mostly complete

Implemented:

- FastAPI app setup and startup DB init.
- CORS setup for local frontend origins.
- Route registration for operator/jobs/machine/production/dashboard/ai modules.
- Root endpoint `/`.
- Health endpoint `/health`.
- `requirements.txt`.
- Root `README.md`.

Missing/incomplete:

- `.env.example` required by Phase 1 deliverables is missing.

---

## Phase 2 - Database models and seed data

Status: Complete plus extensions

Implemented:

- Core tables implemented:
  - `machines`
  - `operators`
  - `jobs`
  - `machine_events`
  - `machine_state`
  - `scrap_reports`
  - `ai_reports`
- Seed data includes:
  - machine `HAAS_VF2_01`
  - operators `OP_001`, `OP_002`, `OP_003` (with PINs)
  - jobs `JOB_201`, `JOB_202`, `JOB_203` with drawing paths
- Additional schema fields implemented via startup migration logic:
  - `operators.role`
  - `jobs.planned_cycle_time_sec`
  - `jobs.completed_at`
  - `jobs.produced_quantity_final`
  - `jobs.scrap_quantity_final`
  - `jobs.completed_by_operator_id`

Notes:

- A supervisor seed (`SUP_001`, `Valdrin`) exists as an extension beyond baseline demo operator list.

---

## Phase 3 - Event engine

Status: Partially complete (core present, control coverage incomplete)

Implemented:

- EventEngine service with event creation and machine state persistence.
- Transition validation using explicit transition map.
- Counter updates:
  - produced count on `part_completed`
  - scrap count on `scrap_reported`
- Helper queries:
  - current machine state
  - recent events
  - scrap reports
  - dashboard summary
  - completed jobs today aggregation
  - timeline segment aggregation
  - per-job production count

Delta/gaps:

- Event engine methods for key flow events are missing at route level:
  - `cycle_paused`
  - `cycle_resumed`
  - `alarm_triggered`
  - `alarm_cleared`
  - `job_finished` complete flow (COMPLETED -> IDLE)
  - `machine_reset_to_idle`
- Reason-code enum validation is not enforced centrally against design lists.
- No backend `note_added` event route flow.

---

## Phase 4 - Simulator and routes

Status: Partially complete

Implemented endpoints:

- Operators:
  - `POST /api/operators/login`
  - `POST /api/operators/logout`
- Jobs:
  - `GET /api/jobs`
  - `POST /api/jobs/select`
- Machine:
  - `GET /api/machine/state`
  - `GET /api/machine/events`
  - `POST /api/machine/setup/start`
  - `POST /api/machine/setup/confirm`
  - `POST /api/machine/cycle/start`
  - `POST /api/machine/cycle/complete` (manual part count endpoint)
- Production:
  - `POST /api/production/scrap`
  - `GET /api/production/counts`
- Dashboard:
  - `GET /api/dashboard/summary`
  - `GET /api/dashboard/events`
  - `GET /api/dashboard/timeline`

Missing versus required Phase 4 routes:

- `POST /api/jobs/finish`
- `GET /api/jobs/{job_id}/drawing`
- `POST /api/machine/cycle/pause`
- `POST /api/machine/cycle/resume`
- `POST /api/machine/alarm/trigger`
- `POST /api/machine/alarm/clear`
- `POST /api/production/note`

Simulator behavior delta:

- `backend/simulator.py` is currently a placeholder and not driving interval-based part generation.
- While design requires operator-triggered simulator flow and running-only part generation loop, current implementation uses manual `cycle/complete` API call for each part.
- Manual alarm trigger flow for demo scenario 2 is missing.

---

## Phase 5 - WebSockets

Status: Partially complete

Implemented:

- `/ws` endpoint.
- Connection manager with connect/disconnect/broadcast.
- Broadcast payloads on:
  - machine state updates
  - event creation
  - production count updates
  - scrap count updates

Delta/gaps:

- `ai_report_created` broadcast type is expected in README/frontend behavior but is not emitted by backend AI route/engine flow.
- WebSocket test script points to non-existent AI trigger endpoint (`/api/ai/placeholder-report`), so provided test harness is currently stale.

---

## Phase 6 - AI layer

Status: Partially complete

Implemented:

- AI endpoints:
  - `POST /api/ai/downtime-analysis`
  - `POST /api/ai/scrap-analysis`
  - `POST /api/ai/summary`
  - `POST /api/ai/question`
- Deterministic analysis from DB history/state.
- Writes all AI outputs to `ai_reports`.
- No machine-state or production-count mutation from AI paths.

Delta/gaps versus sequence/spec:

- Missing endpoint: `POST /api/ai/reason-suggest`.
- AI layer does not use OpenAI API key path (`OPENAI_API_KEY`) as specified in prompt sequence.
- No explicit fallback branch tied to API-key availability (because external API integration is currently absent).
- No reason-code constrained suggestion output contract (required for operator note reason suggestion flow).
- No AI WebSocket broadcast on report creation.

---

## Phase 7 - Frontend

Status: Partially complete

Implemented:

- Single React app shell (Vite).
- Two modes in one app:
  - Operator Interface
  - Supervisor Dashboard
- API service layer (`frontend/src/services/api.js`).
- WebSocket client (`frontend/src/services/ws.js`).
- State color coding and industrial-style UI baseline.
- Operator panels:
  - login
  - job select
  - drawing file display (text/path)
  - machine controls (setup/start/complete subset)
  - scrap reporting
  - note text area (UI-shell only)
- Dashboard panels:
  - machine status
  - production metrics
  - event timeline
  - runtime metrics
  - AI panel button

Delta/gaps:

- Frontend controls do not include pause/resume/alarm/clear/finish flow.
- No actual embedded PDF viewer (only drawing path text display).
- Operator notes are not sent to backend (`note_added` flow missing).
- AI panel calls non-existent endpoint `/api/ai/placeholder-report`.
- Role-based routing/login split is not fully integrated in UI (mode switch is manual).

---

## Phase 8 - Final demo prep

Status: Not complete

Missing:

- End-to-end reliable validation for both demo scenarios from spec.
- Presentation checklist.
- Full zero-to-run consistency for backend + frontend docs + test script.
- Scenario verification artifacts.

---

## 6) Endpoint delta matrix (required vs actual)

## Required machine/control flow endpoints from implementation docs

Implemented:

- `POST /api/operators/login`
- `POST /api/operators/logout`
- `GET /api/jobs`
- `POST /api/jobs/select`
- `POST /api/machine/setup/start`
- `POST /api/machine/setup/confirm`
- `POST /api/machine/cycle/start`
- `POST /api/production/scrap`
- `GET /api/machine/state`
- `GET /api/machine/events`
- `GET /api/dashboard/summary`

Missing:

- `POST /api/jobs/finish`
- `GET /api/jobs/{job_id}/drawing`
- `POST /api/machine/cycle/pause`
- `POST /api/machine/cycle/resume`
- `POST /api/machine/alarm/trigger`
- `POST /api/machine/alarm/clear`
- `POST /api/production/note`

Additional implemented endpoints not in original phase list:

- `POST /api/login` (role-aware auth helper)
- `POST /api/jobs` (job creation)
- `GET /api/jobs/completed/today`
- `GET /api/dashboard/events`
- `GET /api/dashboard/timeline`
- `GET /api/production/counts`
- `POST /api/machine/cycle/complete`

---

## 7) Demo scenario readiness delta

## Scenario 1 - Normal production

Readiness: Mostly workable using current manual cycle-complete endpoint.

Works:

- Login
- Job selection
- Setup start/confirm
- Cycle start
- Manual part counting (`cycle/complete`)

Missing for full spec-aligned flow:

- Formal job finish endpoint to force `COMPLETED` then `IDLE`.

## Scenario 2 - Interrupted production

Readiness: Blocked / incomplete.

Blocking gaps:

- No alarm trigger endpoint.
- No alarm clear endpoint.
- No pause/resume endpoints.
- No backend note endpoint + no reason-suggest AI endpoint.
- AI UI call is currently wired to a non-existent endpoint.

---

## 8) Frontend-backend contract mismatches (critical)

1. AI endpoint mismatch:
- Frontend calls `/api/ai/placeholder-report`.
- Backend exposes `/api/ai/downtime-analysis`, `/scrap-analysis`, `/summary`, `/question`.

2. WebSocket message mismatch:
- Frontend listens for `ai_report_created`.
- Backend does not emit `ai_report_created`.

3. Notes flow mismatch:
- Frontend has operator notes UI text area.
- Backend lacks `POST /api/production/note` endpoint and note event creation path.

4. Simulator flow mismatch:
- Design expects RUNNING interval part generation controlled by operator actions.
- Current backend relies on explicit `cycle/complete` call per part.

---

## 9) Documentation and operational deltas

- `README.md` documents capabilities that are partially incomplete in code (notably AI live broadcast assumptions).
- `ws_test.py` targets stale endpoint (`/api/ai/placeholder-report`).
- `.env.example` missing though required by phase docs.
- Root `data/` directory not present in repo at snapshot time (created lazily by DB path setup when backend runs).

---

## 10) Validation performed and limitations

Performed:

- Full source document read (required order).
- Full repository file inventory.
- Full backend/frontend code pass over core runtime modules.
- Endpoint grep and feature presence checks.
- Git branch/status snapshot.

Limitations encountered in this environment:

- Local Python runtime command execution is unavailable (`python` and `py` resolve to Windows app aliases that fail to execute), so backend runtime compile test was not executable here.
- Frontend build command could not be fully validated because dependencies are not installed (`node_modules` absent; `vite` command unavailable without install).

These limits mean this report is a code-level and contract-level delta, not a fully executed runtime QA report.

---

## 11) Prioritized next-agent worklist (for full agent setup)

1. Complete Phase 4 missing machine/simulator routes and event paths.
2. Implement `jobs/finish` with `COMPLETED -> IDLE` transition and completion field writes.
3. Add production note endpoint and `note_added` event.
4. Add drawing-open endpoint and `drawing_opened` event path.
5. Align frontend API calls to real AI endpoints.
6. Add/emit `ai_report_created` WebSocket message from AI report creation flow.
7. Implement Phase 6 reason-suggest endpoint with allowed reason-code mapping.
8. Add `.env.example` aligned to current env vars.
9. Reconcile `README.md` and `ws_test.py` with actual backend contracts.
10. Validate both demo scenarios end-to-end and document runbook/checklist for Phase 8.

---

## 12) Absolute-constraint compliance check

Constraint status at snapshot:

- Single-machine prototype only: PASS
- Machine ID remains `HAAS_VF2_01`: PASS
- Backend as source of truth: PASS
- AI analysis-only: PASS
- AI does not control machine: PASS
- Simulator not autonomous: PASS (currently minimal/manual)
- No architecture redesign observed: PASS
- Future-phase bleed present: PARTIAL (some change-request extensions added while core simulator phase remains incomplete)

---

## 13) Key file references for this delta

- `backend/main.py`
- `backend/database.py`
- `backend/models.py`
- `backend/schemas.py`
- `backend/event_engine.py`
- `backend/simulator.py`
- `backend/ai_engine.py`
- `backend/routes/operators.py`
- `backend/routes/jobs.py`
- `backend/routes/machine.py`
- `backend/routes/production.py`
- `backend/routes/dashboard.py`
- `backend/routes/ai.py`
- `backend/websocket/connection_manager.py`
- `frontend/src/App.jsx`
- `frontend/src/services/api.js`
- `frontend/src/services/ws.js`
- `frontend/src/pages/OperatorPage.jsx`
- `frontend/src/pages/DashboardPage.jsx`
- `README.md`
- `ws_test.py`
