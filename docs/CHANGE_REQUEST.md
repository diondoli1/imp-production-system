
# CHANGE_REQUEST.md

---

# 1. OVERVIEW

This change request defines improvements to an existing CNC production tracking prototype. The current system functions correctly but requires enhancements to support a **realistic live demo environment for CNC manufacturing**.

The improvements focus on:

- improving the **operator workflow**
- adding **role-based login and supervisor dashboard**
- adding **machine simulation controls directly in the operator interface**
- integrating a **PDF drawing viewer**
- allowing **supervisors to create jobs**
- providing **production visibility through a shift timeline**
- improving **dashboard insights and job completion reporting**

These changes **must preserve the existing architecture** while enhancing usability, realism, and production analysis capabilities.

---

# 2. CURRENT SYSTEM SUMMARY

The system is a CNC production tracking prototype designed to simulate a production environment for a single CNC machine.

### Technology Stack

Backend:
- FastAPI
- SQLite
- WebSocket broadcasting
- deterministic AI analysis engine
- event-driven architecture

Frontend:
- React
- Vite
- WebSocket client
- API service layer

### System Features

Current system capabilities include:

- operator login
- operator interface
- supervisor dashboard
- machine simulation engine
- production event tracking
- scrap reporting
- event timeline
- AI production analysis
- WebSocket real-time updates

### Machine Scope

The system currently models a **single CNC machine**:

```
HAAS_VF2_01
```

### Backend Services

The backend currently contains:

```
event_engine.py
ai_engine.py
simulator.py
routes/
```

Routes include:

```
/operators
/jobs
/machine
/production
/dashboard
/ai
```

### Frontend Pages

Current frontend pages include:

```
OperatorPage
DashboardPage
```

With components:

- machine status panels
- event timeline
- websocket client
- API services

---

# 3. MAJOR ARCHITECTURAL RULES (DO NOT BREAK)

The following architecture rules must remain intact.

### Backend

- FastAPI must remain the backend framework
- Event-driven architecture must remain
- EventEngine must remain the central event validator
- Backend remains the **source of truth**
- Machine state must remain derived from events
- WebSocket broadcasting must remain

### Frontend

- React must remain the frontend framework
- Vite must remain the build tool
- Frontend communicates with backend via REST API + WebSocket

### Database

- SQLite remains the database
- Existing tables must remain compatible

### System Design

- System remains **single-machine**
- Machine ID remains:

```
HAAS_VF2_01
```

### AI

- AI must remain **analysis-only**
- AI must **not generate machine events**

---

# 4. REQUIRED CHANGES

---

## CHANGE 1 — Role-Based Login

### Problem

Currently the system only supports operator login.

The system must support two roles:

- operator
- supervisor

### Requested Behavior

Users log in with:

```
name
PIN
```

After login:

| Role | Redirect |
|-----|-----|
| OPERATOR | Operator View |
| SUPERVISOR | Supervisor Dashboard |

Example supervisor:

```
Valdrin
```

### Technical Impact

Backend:
- login endpoint must return role

Database:
- add role column

Frontend:
- role-based routing

---

## CHANGE 2 — Operator Interface Redesign

### Problem

The current operator interface separates machine simulation from operator workflow.

### Requested Behavior

Operator page must be redesigned into **two-column layout**:

Left side: **Machine Panel**

Right side: **Operator Work Area**

### Machine Panel

Contains:

- machine image (HAAS VF2)
- machine state
- cycle timer
- produced vs target
- machine control buttons

Machine control buttons:

```
Start Setup
Confirm Setup Ready
Cycle Start
Pause
Resume
Trigger Alarm
Clear Alarm
Reset
Finish Job
Emergency Stop (optional)
```

Buttons must enable/disable depending on machine state.

### Technical Impact

Frontend:
- redesign OperatorPage layout
- new MachinePanel component
- new MachineControls component

Backend:
- no architecture changes
- existing machine endpoints reused

---

## CHANGE 3 — Real PDF Drawing Viewer

### Problem

Operators currently cannot view technical drawings directly in the interface.

### Requested Behavior

Operators must be able to open a **PDF drawing** associated with a job.

Features:

- embedded PDF viewer
- page navigation
- zoom
- fit width

Opening a drawing should emit event:

```
drawing_opened
```

### Technical Impact

Backend:
- serve drawing files via static route

Frontend:
- integrate PDF viewer component

---

## CHANGE 4 — Supervisor Dashboard Improvements

### Problem

Supervisor dashboard lacks operational visibility.

### Requested Behavior

Supervisor dashboard must include:

```
Machine Status
Active Operator
Active Job
Production Metrics
Runtime vs Downtime
Event Timeline
Completed Jobs Today
Add Job Form
AI Insights
Shift Timeline
```

### Technical Impact

Frontend:
- dashboard layout redesign
- new components

Backend:
- new summary endpoints

---

## CHANGE 5 — Job Creation From Dashboard

### Problem

Jobs currently must be seeded in the database.

### Requested Behavior

Supervisor can create jobs from dashboard.

Fields:

```
Part Name
Material
Target Quantity
Drawing File
Planned Cycle Time
```

### Technical Impact

Backend:
- new POST /jobs endpoint

Frontend:
- AddJobForm component

Database:
- additional job fields

---

## CHANGE 6 — Completed Jobs Today Panel

### Problem

Supervisors cannot easily see production results for the day.

### Requested Behavior

Dashboard must show:

Table:

| Time | Job | Produced | Scrap | Operator |

KPIs:

```
Jobs Completed Today
Parts Produced Today
Scrap Today
```

### Technical Impact

Backend:
- new summary query

Frontend:
- CompletedJobsToday component

---

## CHANGE 7 — Shift Timeline / Production Story

### Problem

Supervisors cannot easily understand machine activity across time.

### Requested Behavior

Add **Shift Timeline** visualizing machine state transitions.

States shown:

```
SETUP
RUNNING
PAUSED
ALARM
COMPLETED
```

Timeline shows colored segments representing machine activity.

Hover shows:

```
state
start time
end time
duration
reason code
```

### Technical Impact

Backend:
- timeline aggregation endpoint

Frontend:
- ShiftTimeline component

---

## CHANGE 8 — Machine Visual State Indicator

### Problem

Machine state is currently displayed as text only.

### Requested Behavior

Machine panel must visually reflect machine state.

State colors:

| State | Color |
|------|------|
| IDLE | Grey |
| SETUP | Blue |
| READY | Cyan |
| RUNNING | Green |
| PAUSED | Yellow |
| ALARM | Red |
| ESTOP | Dark Red |

### Technical Impact

Frontend:
- machine state overlay
- state color logic

---

# 5. DATABASE CHANGES

### Modify operators table

Add:

```
role TEXT NOT NULL DEFAULT 'OPERATOR'
```

---

### Modify jobs table

Add:

```
planned_cycle_time_sec INTEGER
completed_at DATETIME
produced_quantity_final INTEGER
scrap_quantity_final INTEGER
completed_by_operator_id TEXT
```

---

# 6. BACKEND CHANGES

### New Endpoints

```
POST /api/login
POST /api/jobs
GET /api/jobs
GET /api/jobs/completed/today
GET /api/dashboard/summary
GET /api/dashboard/timeline
```

---

### Event Engine

Ensure events exist for:

```
drawing_opened
job_completed
machine_reset
```

---

### Timeline Aggregation

Add service to compute timeline segments from events.

Example output:

```json
[
  {
    "state": "RUNNING",
    "start": "2026-03-09T09:00:00",
    "end": "2026-03-09T09:20:00",
    "duration_sec": 1200
  }
]
```

---

# 7. FRONTEND CHANGES

### New Routes

```
/login
/operator
/supervisor
```

---

### New Components

Operator View:

```
MachinePanel
MachineControls
JobCard
JobSelector
PdfViewer
NotesPanel
ScrapPanel
```

Supervisor Dashboard:

```
KpiCards
MachineStatusCard
CompletedJobsToday
AddJobForm
ShiftTimeline
AiInsightsPanel
```

---

# 8. AI SYSTEM CHANGES

AI engine must support new analysis contexts.

### New AI Inputs

Include:

```
timeline segments
completed jobs
downtime events
scrap reports
operator notes
```

### AI Reports

Add:

```
Shift summary
Downtime explanation
Production efficiency summary
Scrap insights
```

AI remains **read-only analysis**.

---

# 9. BREAKING CHANGES

Potential breaking changes:

- operators table schema change
- frontend routing changes
- dashboard layout modifications

Existing API endpoints should remain compatible.

---

# 10. ACCEPTANCE CRITERIA

System is considered complete when:

### Authentication

- operator login works
- supervisor login works
- role-based routing works

### Operator Workflow

- job selection works
- PDF drawings open correctly
- machine buttons control simulation
- events recorded correctly
- scrap reporting works

### Supervisor Dashboard

- machine state updates live
- completed jobs displayed
- job creation works
- shift timeline renders correctly

### AI

- AI analysis endpoints return valid reports
- reports reflect real production data

### Realtime Updates

- WebSocket updates propagate state changes

---

# 11. IMPLEMENTATION PRIORITY

### Phase 1 — Database + Backend Foundations

- schema updates
- login endpoint
- new job fields
- timeline aggregation endpoint

---

### Phase 2 — Backend Logic Updates

- job completion tracking
- drawing event support
- dashboard summary queries

---

### Phase 3 — Frontend Integration

- login screen
- operator page redesign
- supervisor dashboard improvements
- PDF viewer integration

---

### Phase 4 — AI Improvements

- shift summary
- downtime insights
- scrap analysis

---

### Phase 5 — Cleanup and Testing

- UI polish
- edge case handling
- performance testing
- demo scenario validation

---

**End of Change Request**
