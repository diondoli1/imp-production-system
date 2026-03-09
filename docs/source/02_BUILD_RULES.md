# Build Rules

These rules are the non-negotiable constraints for the project.

## Scope rules
- Single machine only
- Machine ID must remain `HAAS_VF2_01`
- No real CNC integration in v1
- No SteelTrack integration in v1
- No Docker in v1
- No multi-machine logic
- No ERP logic
- No predictive maintenance

## Architecture rules
- Backend is the source of truth
- Frontend must never invent machine behavior
- Use event log + current machine state table
- Build modules separately
- Keep implementation simple and explicit
- Do not redesign architecture unless explicitly requested

## AI rules
- AI gives suggestions only
- AI never changes machine state
- AI never starts or stops production
- AI never edits production counts
- AI outputs must be saved in `ai_reports`

## Workflow rules
- Build backend before frontend
- Verify each phase before moving on
- Commit after each completed module
- Keep prompts scoped to one module at a time
- Prefer small fixes over broad rewrites

## UI rules
- One React application only
- Two modes only: Operator / Dashboard
- Real tablet target
- Industrial style, not flashy
- Large buttons
- High contrast
- Color-coded states

## Demo rules
- Two demo scenarios only
- One normal production scenario
- One interrupted production scenario
- Alarm must be manually triggerable
- Simulator must not run autonomously outside operator-controlled flow
