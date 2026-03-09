# IMP CNC Production Tracking Prototype

Phase 6 backend AI analysis module for a single-machine CNC tracking demo.

Machine ID is fixed to:
`HAAS_VF2_01`

## Scope in this phase

- SQLite models for:
  - `machines`
  - `operators`
  - `jobs`
  - `machine_events`
  - `machine_state`
  - `scrap_reports`
  - `ai_reports`
- Startup table initialization and seed data:
  - machine `HAAS_VF2_01`
  - operators `OP_001`, `OP_002`, `OP_003`
  - jobs `JOB_201`, `JOB_202`, `JOB_203`
- Hybrid event/state core backend flow
  - event persistence in `machine_events`
  - current state persistence in `machine_state`
  - produced count updates on `part_completed`
  - scrap count updates on `scrap_reported`
- Backend cycle flow support:
  - setup start
  - setup confirm
  - cycle start
  - cycle complete (part counted)
- Scrap event recording endpoint
- Operator login/logout flow:
  - login by `operator_name + pin`
  - logout by `operator_id`
  - active operator tracked in `machine_state.active_operator_id`
  - operator events persisted in `machine_events`
- Dashboard read endpoints:
  - summary view for current state/job/operator/counts
  - recent machine event history for timeline views
- WebSocket live updates:
  - endpoint: `/ws`
  - broadcasts on machine state changes, new events, produced count changes, scrap count changes
  - broadcasts `ai_report_created` when AI report hooks create reports
- AI analysis module:
  - deterministic, backend-read-only analysis from machine state/history
  - downtime analysis output
  - scrap analysis output
  - production summary output
  - operator question/answer output
  - every output persisted in `ai_reports`
  - no machine control and no production state/count mutations

## Run locally

1. Create and activate a Python virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the backend:

```bash
uvicorn backend.main:app --reload
```

4. Verify endpoints:
- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/health`

## Phase 5 WebSocket endpoint

- `GET /ws` (WebSocket upgrade)

Broadcast message types:
- `machine_state_updated`
- `event_created`
- `production_count_updated`
- `scrap_count_updated`
- `ai_report_created`

Example payloads:

```json
{
  "type": "machine_state_updated",
  "machine_id": "HAAS_VF2_01",
  "current_state": "RUNNING",
  "active_job_id": "JOB_201",
  "active_operator_id": "OP_001",
  "produced_count": 3,
  "scrap_count": 1,
  "updated_at": "2026-03-07T12:00:00"
}
```

```json
{
  "type": "event_created",
  "machine_id": "HAAS_VF2_01",
  "event": {
    "event_id": 15,
    "timestamp": "2026-03-07T12:00:02",
    "event_type": "part_completed",
    "machine_state": "RUNNING",
    "job_id": "JOB_201",
    "operator_id": "OP_001",
    "reason_code": null,
    "details": {
      "produced_count": 3
    }
  }
}
```

## Phase 6 AI endpoints

AI:
- `POST /api/ai/downtime-analysis`
- `POST /api/ai/scrap-analysis`
- `POST /api/ai/summary`
- `POST /api/ai/question`

## Phase 4 dashboard endpoints

Dashboard:
- `GET /api/dashboard/summary`
- `GET /api/dashboard/events?limit=50`

## Phase 3 operator endpoints

Operators:
- `POST /api/operators/login`
- `POST /api/operators/logout`

## Phase 2 API endpoints

Jobs:
- `GET /api/jobs`
- `POST /api/jobs/select`

Machine:
- `GET /api/machine/state`
- `GET /api/machine/events?limit=50`
- `POST /api/machine/setup/start`
- `POST /api/machine/setup/confirm`
- `POST /api/machine/cycle/start`
- `POST /api/machine/cycle/complete`

Production:
- `POST /api/production/scrap`
- `GET /api/production/counts`


## Manual flow example

0. Operator login: `POST /api/operators/login`
1. Select a job: `POST /api/jobs/select`
2. Move to setup: `POST /api/machine/setup/start`
3. Confirm setup (READY): `POST /api/machine/setup/confirm`
4. Start cycle (RUNNING): `POST /api/machine/cycle/start`
5. Complete one cycle / part: `POST /api/machine/cycle/complete`
6. Record scrap if needed: `POST /api/production/scrap`
7. Operator logout: `POST /api/operators/logout`

## Environment

Copy `.env.example` to `.env` and adjust values if needed.

Important variables:
- `DATABASE_PATH`
- `FRONTEND_ORIGINS`
- `BACKEND_HOST`
- `BACKEND_PORT`
