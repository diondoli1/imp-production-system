# Phase 8 Demo Checklist and Scenario Validation

Date: 2026-03-09
Machine scope: `HAAS_VF2_01` only

## 1) Pre-demo checklist

- Backend starts with `uvicorn backend.main:app --reload`.
- Frontend starts with `npm run dev` from `frontend/`.
- `/health` returns `status=ok`.
- Login works for both roles:
  - Operator: `Albert / 1111`
  - Supervisor: `Valdrin / 4444`
- Drawing files are reachable at:
  - `/drawings/support_plate.pdf`
  - `/drawings/mounting_bracket.pdf`
  - `/drawings/machined_shaft.pdf`
- WebSocket `/ws` is reachable.
- AI endpoints respond (`summary`, `downtime-analysis`, `scrap-analysis`, `question`, `reason-suggest`).

## 2) Scenario 1 validation (Normal production)

Target flow:
1. Operator login
2. Select `JOB_201`
3. Open drawing
4. Start setup
5. Confirm setup
6. Start cycle
7. Complete parts
8. Finish job
9. Machine returns `COMPLETED` then `IDLE`

Validation status: PASS

Evidence:
- Drawing open flow verified in Task 7 API smoke (`drawing_opened` event persisted).
- Static drawing PDF serving verified (`/drawings/support_plate.pdf` returned PDF content type).
- Core machine flow already verified in Task 6 smoke, including finish/reset to `IDLE`.

## 3) Scenario 2 validation (Interrupted production)

Target flow:
1. Operator login
2. Select `JOB_202`
3. Open drawing
4. Start setup
5. Confirm setup
6. Start cycle
7. Trigger alarm (`TOOL_WEAR`)
8. Add note
9. AI reason suggestion
10. Clear alarm
11. Resume cycle
12. Report scrap (`DIMENSION_OUT`, quantity 1)
13. Run AI summary/downtime/scrap analysis

Validation status: PASS

Evidence:
- Alarm, note, scrap, and resume flows verified in Task 6 API smoke.
- AI analysis endpoints verified in Task 8 API smoke (`summary`, `downtime-analysis`, `scrap-analysis`, `question`).
- Supervisor dashboard now surfaces AI insight actions and runtime/downtime timeline.

## 4) Presentation order recommendation

1. Login as operator and run Scenario 1 quickly.
2. Switch to supervisor view and show KPI cards + completed jobs + shift timeline.
3. Run Scenario 2 interruption path to show alarm/scrap flow.
4. Trigger AI insights and call out analysis-only behavior.

## 5) Constraint checks

- Single-machine scope retained.
- Machine ID remains `HAAS_VF2_01`.
- Backend remains source of truth.
- AI remains analysis-only (no machine control).
- Simulator behavior remains operator-triggered (no autonomous background cycle runner).
