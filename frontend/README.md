# Frontend Shell (Phase 7)

This frontend is a single React application with two modes:
- Operator Interface
- Supervisor Dashboard

Machine context is fixed to:
`HAAS_VF2_01`

## Implemented in this phase

- Single app shell and mode switch
- Operator interface panels:
  - login with name + PIN
  - job selection
  - drawing viewer
  - machine controls
  - scrap reporting
  - operator notes panel (UI shell)
- Dashboard panels:
  - machine status
  - production metrics
  - event timeline
  - runtime metrics
  - AI insight trigger panel
- REST API service layer
- WebSocket client for live updates
- Industrial high-contrast styling with explicit machine state colors

## Run

```bash
cd frontend
npm install
npm run dev
```

Default dev target (Vite): `http://127.0.0.1:5173`

Backend should be running on:
`http://127.0.0.1:8000`
