# AGENTS.md

## Project

IMP CNC Production Tracking Prototype

This repository contains a **single-machine CNC production tracking
prototype** designed for a **HAAS VF2 machine**.

The system tracks: - operator activity - machine cycles - alarms - scrap
events - production counts - machine state

Machine ID must always remain:

HAAS_VF2_01

------------------------------------------------------------------------

# Absolute System Constraints

1.  The system must remain a **single-machine prototype**.
2.  Machine ID must remain **HAAS_VF2_01**.
3.  The **backend is the source of truth**.
4.  The **AI module is analysis-only**.
5.  AI must **never control the machine**.
6.  The simulator must **never run autonomously**.
7.  The simulator must **only respond to operator actions**.
8.  Do **not redesign the architecture**.
9.  Do **not invent new system components**.
10. Implement **only the current development phase**.

------------------------------------------------------------------------

# Source of Truth Documents

Before making changes read the documents in:

docs/source/

Read them in this order:

1.  03_TECHNICAL_DESIGN_FULL.md
2.  02_BUILD_RULES.md
3.  07_IMPLEMENTATION_SEQUENCE.md
4.  05_CODEX_PROMPT_SEQUENCE.md
5.  09_RUNTIME_AND_REPOSITORY_SPEC.md
6.  01_PROJECT_BRIEF.md
7.  08_DEMO_DATA_AND_SCENARIOS.md

The **technical design document is the ultimate source of truth**.

------------------------------------------------------------------------

# Development Process

Development must follow the **Implementation Sequence**.

Phases must be implemented **strictly in order**:

1.  Backend Foundation
2.  Core Production Engine
3.  Operator Flow
4.  Dashboard System
5.  AI Analysis Module
6.  Simulator
7.  Frontend (React)
8.  Integration and Testing

Do **not implement features from future phases**.

------------------------------------------------------------------------

# Backend Architecture

Language: Python\
Framework: FastAPI\
Database: SQLite

Backend responsibilities include:

-   machine state tracking
-   event logging
-   operator sessions
-   job tracking
-   production counts
-   alarm logging
-   scrap tracking
-   AI analysis access
-   simulator integration

Backend runs locally using:

uvicorn backend.main:app --reload

------------------------------------------------------------------------

# Frontend

Framework: React

Frontend modes:

-   Operator Mode
-   Dashboard Mode

Frontend runs on a **tablet connected via local WiFi**.

------------------------------------------------------------------------

# Database

Database type: SQLite

Tables include:

-   operators
-   jobs
-   machine_events
-   machine_state
-   production_counts
-   alarms
-   scrap_events
-   notes

------------------------------------------------------------------------

# Simulator

The simulator mimics machine behavior.

It can simulate:

-   cycle start
-   cycle complete
-   idle time
-   alarms

The simulator must **never run automatically**. It must **only run when
triggered by operator actions**.

------------------------------------------------------------------------

# AI Module

The AI module performs **analysis only**.

Capabilities:

-   downtime analysis
-   scrap analysis
-   operator questions
-   production summaries
-   cycle pattern detection

AI must **never modify machine state**. AI must **never control the
machine**.

------------------------------------------------------------------------

# Repository Structure

imp_cnc_demo │ ├ backend ├ frontend ├ docs/source ├ data └ AGENTS.md

Do **not change the structure unless explicitly instructed**.

------------------------------------------------------------------------

# Coding Rules

Keep implementations **simple and explicit**.

Do not introduce:

-   new frameworks
-   cloud services
-   docker
-   distributed systems
-   message queues

This project runs on **one machine only**.

------------------------------------------------------------------------

# Task Execution Rules

Before doing work:

1.  Read AGENTS.md
2.  Read docs/source files
3.  Determine current phase
4.  Implement only that phase

Before applying changes:

-   list files that will change
-   explain why

After changes:

-   summarize modifications
-   stop and wait

------------------------------------------------------------------------

# Safety Rules

Never:

-   redesign architecture
-   add multi-machine support
-   allow AI to control the machine
-   allow simulator autonomous behavior
-   add infrastructure not defined in the design

------------------------------------------------------------------------

# Local Runtime

Backend launch command:

uvicorn backend.main:app --reload

Local API URL:

http://127.0.0.1:8000

Health endpoint:

/health

Root endpoint:

/
