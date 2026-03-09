# Step-by-Step Codex Setup Guide

This guide assumes you have never used Codex before.

## 1. Install required tools
Install on your office PC:
- Git
- Python 3.11+
- Node.js + npm
- VS Code

## 2. Create the project folder
```bash
mkdir imp_cnc_demo
cd imp_cnc_demo
git init
```

## 3. Open in VS Code
```bash
code .
```

## 4. Add the source docs into the repo
Create these folders first:
```bash
mkdir backend frontend docs data
```

Put the uploaded source documents inside `docs/` or keep them nearby.

## 5. Sign in to Codex
If using Codex CLI:
```bash
codex logout
codex
```

If using VS Code extension:
- install the Codex extension
- sign in with your ChatGPT account

## 6. Make your first Git checkpoint
```bash
git add .
git commit -m "Initial repo structure"
```

## 7. Run Prompt 1 only
Use Prompt 1 from `05_CODEX_PROMPT_SEQUENCE.md`.

Do not run the other prompts yet.

## 8. Review what Codex created
Check:
- did it create the backend folder and files?
- is `requirements.txt` present?
- is `.env.example` present?
- is `GET /health` implemented?
- did it keep the structure simple?

Then commit:
```bash
git add .
git commit -m "Backend foundation generated"
```

## 9. Create Python virtual environment
### Windows PowerShell
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### macOS/Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 10. Run the backend
```bash
uvicorn backend.main:app --reload
```

Test:
- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/health`

Do not continue until these work.

## 11. Then use the prompts in order
1. Prompt 1 — backend foundation
2. Prompt 2 — database models and seed data
3. Prompt 3 — event engine
4. Prompt 4 — simulator and routes
5. Prompt 5 — WebSockets
6. Prompt 6 — AI layer
7. Prompt 7 — frontend
8. Prompt 8 — final demo prep

## 12. What to do after every prompt
Always follow this rhythm:
1. Let Codex finish
2. Read the changed files
3. Run the app
4. Test the new feature
5. Commit to Git

## 13. How to ask for fixes
Never say:
`fix everything`

Say:
```text
Review only backend/event_engine.py and fix state transition validation for cycle_started. Do not modify unrelated files.
```

Or:
```text
The backend starts, but /api/operators/login returns a 500 error. Diagnose only that route and related schema/model code. Keep all route names unchanged.
```

## 14. Session one target
For your first session, do only this:
- create the repo
- sign in to Codex
- run Prompt 1
- install backend dependencies
- run FastAPI
- verify `/` and `/health`
- commit
