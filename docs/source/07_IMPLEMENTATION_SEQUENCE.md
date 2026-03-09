# Implementation Sequence

Follow this exact order.

## Phase 1 — Backend foundation
Deliverables:
- FastAPI app
- DB connection
- route registration
- `/`
- `/health`
- requirements
- env example
- README

Git commit:
`Backend foundation generated`

## Phase 2 — Database models and seed data
Deliverables:
- all DB tables
- seed machine
- seed operators with PINs
- seed jobs with drawing file paths

Git commit:
`Database models and seed data`

## Phase 3 — Event engine
Deliverables:
- event creation service
- transition validation
- machine state updater
- counts update logic
- helper queries

Git commit:
`Event engine implemented`

## Phase 4 — Simulator and routes
Deliverables:
- operator login/logout
- job select/finish
- machine setup/cycle/alarm routes
- production note/scrap routes
- running-state part generation
- manual alarm trigger

Git commit:
`Simulator and machine routes implemented`

## Phase 5 — WebSockets
Deliverables:
- `/ws`
- connection manager
- broadcast hooks
- live payloads

Git commit:
`WebSocket live updates added`

## Phase 6 — AI layer
Deliverables:
- reason suggestion endpoint
- summary endpoint
- question endpoint
- ai_reports storage
- graceful fallback if no API key

Git commit:
`AI layer implemented`

## Phase 7 — Frontend
Deliverables:
- single React app
- Operator mode
- Dashboard mode
- REST service layer
- WebSocket client
- state colors and large controls

Git commit:
`Frontend shell implemented`

## Phase 8 — Final demo prep
Deliverables:
- reliable demo flow
- seed data polish
- README from zero
- presentation checklist
- scenario validation

Git commit:
`Demo preparation completed`
