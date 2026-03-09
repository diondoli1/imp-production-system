# IMP CNC Production Tracking Prototype
## Full Technical Design Review Document

# 1. Project Purpose

This project is a working prototype of a digital CNC production tracking system for IMP.

The system demonstrates how production tracking could function using a tablet interface, a simulated CNC machine, a supervisor dashboard, and AI-assisted analysis of production events.

The prototype is intended to validate workflow design, architecture, and system behavior before any full production implementation is considered.

The prototype simulates a single CNC production cell using:
- a simulated HAAS CNC machine
- a tablet-based operator interface
- a supervisor dashboard
- an event-driven backend system
- AI-assisted analysis of production activity

# 2. Actual Business Problem

IMP currently operates multiple HAAS CNC machines used for machining production parts and spare components.

The current workflow is manual:
1. Operators receive printed technical drawings for parts to be produced.
2. During production, the operator writes the number of completed parts directly on the drawing.
3. Scrap parts, machine downtime, and interruptions are typically not formally recorded.
4. After production is completed, the printed drawing is placed in a folder for later review by management.

Important production information is not systematically recorded:
- machine runtime
- machine idle time
- production interruptions
- scrap quantities
- operator interventions
- machine alarms

Management therefore lacks real-time visibility into production activity.

# 3. System Scope

The system is a prototype that simulates a single CNC production cell.

Included:
- CNC machine simulator
- backend API server
- operator tablet interface
- supervisor dashboard
- event-based production tracking
- AI analysis module

Out of scope:
- direct integration with real CNC machines
- ERP integration
- multi-machine coordination
- production scheduling systems
- automated machine control
- predictive maintenance algorithms

The prototype focuses strictly on:
- operator workflow
- machine state tracking
- event-based production logging
- real-time monitoring
- AI-assisted data interpretation

# 4. Stakeholders and Users

## Machine Operator
The operator is the primary user of the tablet interface.

Operator responsibilities:
- log into the system
- select production jobs
- open technical drawings
- start machine setup
- start production cycles
- pause or resume production
- report scrap parts
- enter production notes

## Production Management
Production management uses the supervisor dashboard to observe:
- machine state
- production output
- interruptions
- event timelines
- AI-generated insights

## Technical Reviewer
Senior software developers may review:
- system architecture
- event model design
- database schema
- API design
- implementation strategy

# 5. System Architecture

The system follows a modular architecture with four primary components:
- CNC Machine Simulator
- Backend API Server
- Operator Tablet Interface
- Supervisor Dashboard

The backend server acts as the central system controller.

It is responsible for:
- receiving machine events
- storing production data
- managing machine state
- exposing API endpoints
- broadcasting real-time updates
- interacting with AI services

The CNC simulator represents a single HAAS CNC machine.
Machine ID:
`HAAS_VF2_01`

The simulator is controlled through operator actions. It does not run as an uncontrolled autonomous machine.

The frontend application provides two modes:
- operator interface
- supervisor dashboard

# 6. Infrastructure and Runtime Environment

The prototype runs in a simple local development environment.

Office PC hosts:
- FastAPI backend server
- SQLite database
- machine simulator
- AI integration module

Tablet connects through the local network using a browser.

The frontend is a single web application served over LAN.

This architecture is intentionally simple to support:
- fast development
- easy debugging
- low setup complexity
- realistic demo behavior

# 7. Event Engine and Machine Event Model

The system uses a hybrid event architecture:
- full event log
- current machine state table

## Machine states
- OFFLINE
- IDLE
- SETUP
- READY
- RUNNING
- PAUSED
- ALARM
- COMPLETED

After a job is completed, the machine briefly enters `COMPLETED` and then returns to `IDLE`.

## Event types

### Operator events
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

### Machine events
- machine_state_changed
- part_completed
- alarm_triggered
- alarm_cleared
- machine_reset_to_idle

## Event schema
Every event contains:
- event_id
- timestamp
- machine_id
- event_type
- machine_state
- job_id
- operator_id
- reason_code
- details

Production totals are derived from `part_completed` events.

## State transitions
Valid flow:
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
- `part_completed` only valid in `RUNNING`
- `cycle_started` only valid from `READY`
- `cycle_resumed` only valid from `PAUSED`
- `alarm_cleared` only valid from `ALARM`
- `job_finished` only valid when a job is active
- no direct `IDLE -> RUNNING`
- no `SETUP -> COMPLETED`

## Reason codes

### Pause reason codes
- TOOL_CHANGE
- INSPECTION
- DRAWING_REVIEW
- MATERIAL_CHECK
- WAITING_INSTRUCTIONS
- OPERATOR_BREAK

### Alarm reason codes
- TOOL_WEAR
- PROGRAM_STOP
- FIXTURE_ISSUE
- DIMENSION_CHECK
- UNKNOWN_FAULT

### Scrap reason codes
- DIMENSION_OUT
- SURFACE_DEFECT
- WRONG_SETUP
- TOOL_MARK
- OPERATOR_ERROR

### AI-assisted reason suggestion
AI may suggest a reason code from operator notes, but the operator always confirms the final value.

# 8. Database Design

Database engine:
`SQLite`

Core tables:
- machines
- operators
- jobs
- machine_events
- machine_state
- scrap_reports
- ai_reports

## machines
Fields:
- machine_id
- machine_name
- machine_type
- is_active
- created_at

Prototype contains one machine only:
`HAAS_VF2_01`

## operators
Fields:
- operator_id
- operator_name
- pin
- is_active
- created_at

## jobs
Fields:
- job_id
- part_name
- material
- target_quantity
- drawing_file
- status
- created_at

## machine_events
Fields:
- event_id
- timestamp
- machine_id
- event_type
- machine_state
- job_id
- operator_id
- reason_code
- details

## machine_state
Fields:
- machine_id
- current_state
- active_job_id
- active_operator_id
- produced_count
- scrap_count
- last_event_id
- updated_at

## scrap_reports
Fields:
- scrap_id
- timestamp
- machine_id
- job_id
- operator_id
- quantity
- reason_code
- note

## ai_reports
Fields:
- report_id
- timestamp
- machine_id
- job_id
- operator_id
- report_type
- input_reference
- output_text

Design principle:
- event log preserves history
- machine_state supports fast UI updates
- scrap_reports keeps scrap structured
- ai_reports preserves AI traceability

# 9. API Design

The backend exposes:
- REST API endpoints
- WebSocket live updates

## REST responsibilities
- operator login/logout
- job selection/finish
- drawing access
- machine setup/cycle/alarm control
- scrap reporting
- note submission
- dashboard data
- AI requests

## WebSocket responsibilities
Push live updates whenever:
- machine state changes
- produced count changes
- scrap count changes
- new event is created
- AI report is created

## Login
Operator login must use:
- operator name
- PIN

## Drawing handling
Drawings are referenced by file path, not stored as binary in DB.

## Alarm handling
Alarm trigger must be manually available from the demo.

# 10. AI Responsibilities and Limits

AI acts as an analysis and assistance layer only.

## AI responsibilities
- operator note structuring
- reason code suggestion
- production summary generation
- natural-language question answering
- downtime analysis

## AI inputs
- machine event history
- operator notes
- scrap reports
- machine state transitions
- job information

## AI limits
AI must never:
- change machine states
- trigger machine cycles
- start or stop production
- modify production counts
- create production jobs
- override operator decisions

All AI outputs are recommendations only.

All AI outputs must be saved in `ai_reports`.

# 11. Frontend System Design

The frontend is a single React application with two modes:
- Operator Interface
- Supervisor Dashboard

## Operator Interface
Features:
- operator login with name + PIN
- job selection
- drawing viewer
- machine control panel
- scrap reporting panel
- operator notes panel

Machine control buttons:
- Start Setup
- Confirm Setup
- Start Cycle
- Pause Cycle
- Resume Cycle
- Finish Job

## Supervisor Dashboard
Panels:
- machine status
- production metrics
- event timeline
- runtime metrics
- AI insight panel

## Visual style
- industrial / professional
- high contrast
- large buttons
- simple layout
- color-coded states
  - RUNNING = green
  - PAUSED = yellow
  - ALARM = red
  - IDLE = gray
  - SETUP = blue

## Real-time behavior
Frontend uses WebSocket updates for immediate refreshes.

# 12. Demo Scenario and Presentation Flow

The demo uses two short production scenarios.

## Scenario 1 — Normal Production
1. operator login
2. job selection
3. drawing opened
4. setup start
5. setup confirm
6. cycle start
7. simulated part completion
8. finish job
9. machine goes COMPLETED then IDLE

Example job:
- Support Plate
- Material: S355
- Target Quantity: 10

## Scenario 2 — Interrupted Production
1. start second job
2. run machine
3. manually trigger alarm
4. operator enters note
5. AI suggests reason code
6. clear alarm
7. resume production
8. report scrap
9. run downtime analysis

Example job:
- Mounting Bracket
- Material: Aluminum
- Target Quantity: 8

This demonstrates:
- digital operator workflow
- real-time machine visibility
- structured event logging
- scrap reporting
- AI-assisted analysis

# 13. Project Implementation Plan

The prototype will be built using AI-assisted development.

Technologies:
- Python
- FastAPI
- SQLite
- React
- WebSockets
- OpenAI API
- Git
- VS Code
- Node.js
- Python virtual environment
- npm

## Development approach
Use a spec-first workflow:
1. architecture definition
2. event model design
3. database schema design
4. API specification
5. AI feature definition
6. frontend workflow definition
7. modular code generation and integration

## Modular code generation strategy
Generate in modules, not as one monolithic app.

Modules:
- database models
- backend API foundation
- event engine
- machine simulator
- operator routes
- production routes
- AI engine
- WebSocket update system
- frontend operator interface
- frontend dashboard

## Development phases
1. Backend foundation
2. Event engine and simulator
3. Operator interface
4. Supervisor dashboard
5. AI features
6. Demo preparation

## Version control strategy
Use Git.
Commit after each completed module.

## Success criteria
The prototype is successful if it demonstrates:
- operator login with name and PIN
- job selection and drawing display
- machine state transitions
- automatic part completion simulation
- pause and alarm handling
- scrap reporting
- real-time dashboard updates
- AI-generated operational insights
