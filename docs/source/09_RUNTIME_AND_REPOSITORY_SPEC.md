# Runtime and Repository Specification

## Runtime model

### Office PC
Runs:
- FastAPI backend
- SQLite database
- simulator
- AI module

### Tablet
Connects over local Wi-Fi and opens the single React application in browser.

The app supports:
- Operator mode
- Dashboard mode

Internet use is acceptable and required for AI calls.

## Network assumptions
- office PC and tablet will be on the same local Wi-Fi
- tablet accesses the app using the office PC IP address
- frontend can run on port 3000
- backend can run on port 8000

## Repository structure target
```text
imp_cnc_demo/

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

frontend/
    src/
        pages/
        components/
        services/

database/
    schema.sql

data/
    demo_jobs.json
    demo_operators.json

docs/
    technical_design.md
```

## Environment variables
Suggested env vars:
- OPENAI_API_KEY
- BACKEND_HOST
- BACKEND_PORT
- FRONTEND_PORT
- DATABASE_PATH
- PART_COMPLETION_INTERVAL_SECONDS

## Suggested ports
- frontend: 3000
- backend: 8000

## Launch target after full build

### Backend
```bash
uvicorn backend.main:app --reload
```

### Frontend
Typical React dev start command:
```bash
npm install
npm start
```

## Operational principles
- backend is source of truth
- simulator runs only when cycle is RUNNING
- manual alarm trigger exists for presentation control
- machine finishes as COMPLETED then resets to IDLE
- all machine and operator actions are stored as events
- all AI outputs are stored in ai_reports
