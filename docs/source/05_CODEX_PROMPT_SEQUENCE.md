# Codex Prompt Sequence

Use these prompts in order. Do not skip ahead.

## Prompt 1 — Backend foundation
```text
You are building a local prototype called "IMP CNC Production Tracking Prototype".

Goal:
Create the backend foundation for a single-machine CNC production tracking demo.

Tech stack:
- Python 3.11+
- FastAPI
- SQLite
- SQLAlchemy or SQLModel
- WebSocket support
- Environment variables via .env
- Clean modular structure

Project requirements:
- Single machine only: HAAS_VF2_01
- Backend runs on local office PC
- Frontend will connect over LAN from a real tablet
- This is a prototype, not a production MES
- Keep implementation simple, readable, and easy to extend

Create this backend structure:

backend/
  main.py
  database.py
  models.py
  schemas.py
  event_engine.py
  simulator.py
  ai_engine.py
  routes/
    operators.py
    jobs.py
    machine.py
    production.py
    dashboard.py
    ai.py

Also create:
- requirements.txt
- .env.example
- README.md

Requirements:
1. Set up FastAPI app with CORS enabled for local frontend development
2. Set up SQLite database connection
3. Add startup hook to initialize database tables
4. Add a health endpoint: GET /health
5. Add a simple root endpoint: GET /
6. Keep code modular and documented
7. Add placeholder route registration for all route modules even if endpoints are stubbed
8. Use Git-friendly clean formatting
9. Do not build frontend yet
10. After creating files, explain what was created and any commands I should run

Important:
- Do not invent extra architecture
- Keep it aligned with a single-machine prototype
- Prefer simple and explicit code over abstractions
```

## Prompt 2 — Models and seed data
```text
Now implement the backend data model for the IMP CNC prototype.

Use the existing backend structure.

Create database models and schemas for these tables:

1. machines
- machine_id
- machine_name
- machine_type
- is_active
- created_at

2. operators
- operator_id
- operator_name
- pin
- is_active
- created_at

3. jobs
- job_id
- part_name
- material
- target_quantity
- drawing_file
- status
- created_at

4. machine_events
- event_id
- timestamp
- machine_id
- event_type
- machine_state
- job_id
- operator_id
- reason_code
- details (JSON/text)

5. machine_state
- machine_id
- current_state
- active_job_id
- active_operator_id
- produced_count
- scrap_count
- last_event_id
- updated_at

6. scrap_reports
- scrap_id
- timestamp
- machine_id
- job_id
- operator_id
- quantity
- reason_code
- note

7. ai_reports
- report_id
- timestamp
- machine_id
- job_id
- operator_id
- report_type
- input_reference
- output_text

Requirements:
- Use SQLite-friendly field types
- Add relationships where useful, but keep it simple
- Seed initial data for:
  - one machine: HAAS_VF2_01
  - three operators: Albert, Ardin, Demo Operator
  - include PIN fields
  - three demo jobs with drawing file paths
- Add a database init/seed function
- Keep all constants realistic and easy to change
- Add Pydantic schemas for request/response models where needed

Also:
- Update README with setup instructions
- Explain how to initialize the DB and verify seeded records
```

## Prompt 3 — Event engine
```text
Now implement the event engine for the IMP CNC prototype.

Context:
This system uses a hybrid model:
- full event log in machine_events
- current live state in machine_state

Machine states:
- OFFLINE
- IDLE
- SETUP
- READY
- RUNNING
- PAUSED
- ALARM
- COMPLETED

Event types:
Operator events:
- operator_logged_in
- operator_logged_out
- job_selected
- drawing_opened
- setup_started
- setup_confirmed
- cycle_started
- cycle_paused
- cycle_resumed
- note_added
- scrap_reported
- job_finished

Machine events:
- machine_state_changed
- part_completed
- alarm_triggered
- alarm_cleared
- machine_reset_to_idle

State transition rules:
- OFFLINE -> IDLE
- IDLE -> SETUP
- SETUP -> READY
- READY -> RUNNING
- RUNNING -> PAUSED
- PAUSED -> RUNNING
- RUNNING -> ALARM
- ALARM -> READY
- RUNNING -> COMPLETED
- COMPLETED -> IDLE

Constraints:
- part_completed only valid in RUNNING
- cycle_started only valid from READY
- cycle_resumed only valid from PAUSED
- alarm_cleared only valid from ALARM
- job_finished only valid when a job is active
- no direct IDLE -> RUNNING
- no SETUP -> COMPLETED

Reason codes:
Pause:
- TOOL_CHANGE
- INSPECTION
- DRAWING_REVIEW
- MATERIAL_CHECK
- WAITING_INSTRUCTIONS
- OPERATOR_BREAK

Alarm:
- TOOL_WEAR
- PROGRAM_STOP
- FIXTURE_ISSUE
- DIMENSION_CHECK
- UNKNOWN_FAULT

Scrap:
- DIMENSION_OUT
- SURFACE_DEFECT
- WRONG_SETUP
- TOOL_MARK
- OPERATOR_ERROR

Implement:
1. Event creation service in event_engine.py
2. State transition validation
3. Automatic machine_state updates whenever events are created
4. Produced count derived by incrementing on part_completed
5. Scrap count updated on scrap_reported
6. Helper functions to fetch current state and recent events
7. Clean exceptions for invalid transitions
8. Logging that is useful for debugging
9. Unit-test-friendly structure, even if tests are not added yet

Also:
- initialize machine current state if missing
- ensure machine returns COMPLETED then IDLE after job finish flow
- explain where the transition rules live
```

## Prompt 4 — Simulator and routes
```text
Now implement the CNC simulator and machine-control routes.

Goal:
Simulate one HAAS machine controlled by operator actions from the UI.

Important:
The simulator must NOT run autonomously.
It must respond to operator actions and manual triggers.

Machine:
- machine_id = HAAS_VF2_01

Implement these REST endpoints:

Operator:
- POST /api/operators/login
- POST /api/operators/logout

Jobs:
- GET /api/jobs
- POST /api/jobs/select
- POST /api/jobs/finish
- GET /api/jobs/{job_id}/drawing

Machine:
- POST /api/machine/setup/start
- POST /api/machine/setup/confirm
- POST /api/machine/cycle/start
- POST /api/machine/cycle/pause
- POST /api/machine/cycle/resume
- POST /api/machine/alarm/trigger
- POST /api/machine/alarm/clear

Production:
- POST /api/production/scrap
- POST /api/production/note

Dashboard:
- GET /api/machine/state
- GET /api/machine/events
- GET /api/dashboard/summary

Behavior requirements:
- operator login uses operator_name + pin
- selecting a job creates job_selected event
- setup start moves machine to SETUP
- setup confirm moves machine to READY
- cycle start moves machine to RUNNING
- while RUNNING, simulator should begin creating part_completed events on an interval
- pause stops part generation
- resume restarts part generation
- manual alarm trigger moves machine to ALARM and stops production
- clearing alarm moves machine to READY
- finish job moves machine to COMPLETED and then back to IDLE
- produced counts and scrap counts must update correctly

Simulator requirements:
- keep it simple
- use a background task/thread/async loop only when cycle is RUNNING
- part completion interval should be configurable
- manual alarm trigger must exist for demo control
- no random autonomous alarms

Also:
- return clear JSON responses
- update README with route descriptions
- explain how to test the flow manually
```

## Prompt 5 — WebSockets
```text
Now add WebSocket support for live frontend updates.

Goal:
The frontend should receive live updates without polling.

Implement:
- WebSocket endpoint: /ws

Push live events whenever:
- machine state changes
- new event is created
- produced count changes
- scrap count changes
- AI report is created

WebSocket message types:
- machine_state_updated
- event_created
- production_count_updated
- scrap_count_updated
- ai_report_created

Requirements:
1. Create a simple connection manager
2. Broadcast JSON payloads to all connected clients
3. Integrate broadcasts into event creation flow
4. Keep payloads explicit and readable
5. Do not over-engineer for multiple machines, but keep machine_id in messages
6. Handle disconnects gracefully
7. Add a small README section showing how messages are structured

Example payload shape:
{
  "type": "machine_state_updated",
  "machine_id": "HAAS_VF2_01",
  "current_state": "RUNNING",
  "produced_count": 5,
  "scrap_count": 1,
  "updated_at": "..."
}

Also explain exactly which backend files were changed.
```

## Prompt 6 — AI layer
```text
Now implement the AI layer for the IMP CNC prototype.

Goal:
AI acts only as an analysis and assistance layer.
It must never control machine behavior.

Implement these endpoints:
- POST /api/ai/reason-suggest
- POST /api/ai/summary
- POST /api/ai/question

AI responsibilities:
1. Suggest reason code from operator note
2. Generate production / shift summary from event history
3. Answer simple questions about machine activity
4. Generate downtime analysis
5. Save all AI outputs into ai_reports

Important limits:
- AI cannot change machine state
- AI cannot modify production counts
- AI cannot start or stop jobs
- AI outputs are recommendations only

Implementation requirements:
- use OpenAI API through environment variable OPENAI_API_KEY
- keep prompts explicit and deterministic
- prefer structured outputs where reasonable
- include fallback handling when API key is missing
- save every AI output to ai_reports with:
  - report_type
  - machine_id
  - job_id if available
  - operator_id if available
  - input_reference
  - output_text

Reason suggestion behavior:
- map notes to one of the allowed reason codes only
- return suggested_reason_code plus optional explanation

Summary behavior:
- summarize machine activity from stored events and current state

Question behavior:
- answer using event history from the database, not hallucinated machine knowledge

Also:
- create helper functions in ai_engine.py
- document environment setup in README
- explain how to test each AI endpoint
```

## Prompt 7 — Frontend shell
```text
Now build the frontend as a single React application with two modes:
- Operator Interface
- Supervisor Dashboard

Do not build fancy styling.
Make it look industrial, clean, readable, high-contrast, and touch-friendly.

Requirements:
- single React app
- simple routing or mode switch
- API service layer for REST calls
- WebSocket integration for live updates

Operator interface screens:
1. Login with operator name + PIN
2. Job selection list
3. Drawing viewer
4. Machine control panel
5. Scrap reporting panel
6. Operator notes panel

Dashboard panels:
1. Machine status panel
2. Production metrics
3. Event timeline
4. Runtime metrics
5. AI insight panel

Behavior:
- all machine control comes from backend API
- all live updates come from WebSocket
- show one machine only
- large buttons for tablet use
- clear color-coded machine states:
  - RUNNING green
  - PAUSED yellow
  - ALARM red
  - IDLE gray
  - SETUP blue
- no unnecessary animations

Also:
- create a clean folder structure under frontend/src
- explain how to run frontend locally
- keep code readable for manual edits later
```

## Prompt 8 — Final demo prep
```text
Now do a final demo-preparation pass across the repo.

Goals:
- make the prototype easy to run
- ensure the two demo scenarios work
- improve clarity without changing architecture

Tasks:
1. Review backend and frontend for consistency
2. Ensure the two demo scenarios are supported:
   - normal production job
   - interrupted production job with alarm, note, scrap, AI analysis
3. Add demo seed data for realistic jobs and operators
4. Add README run instructions from zero
5. Add a simple checklist for presentation setup
6. Verify no endpoints contradict the technical design
7. Keep implementation simple and stable
8. If anything is missing for demo reliability, add it minimally

Deliverable:
- summarize what you changed
- list exact commands I should run to launch backend and frontend
- list the recommended order for presenting the demo
```
