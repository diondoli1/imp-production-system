# IMP CNC Production Tracking Prototype — Source Pack

This folder contains the source documents for the new implementation-focused project chat.

## Recommended upload order to the new project
1. `00_START_HERE.md`
2. `01_PROJECT_BRIEF.md`
3. `02_BUILD_RULES.md`
4. `03_TECHNICAL_DESIGN_FULL.md`
5. `04_TECHNICAL_DESIGN_OVERLEAF.tex`
6. `05_CODEX_PROMPT_SEQUENCE.md`
7. `06_STEP_BY_STEP_CODEX_SETUP_GUIDE.md`
8. `07_IMPLEMENTATION_SEQUENCE.md`
9. `08_DEMO_DATA_AND_SCENARIOS.md`
10. `09_RUNTIME_AND_REPOSITORY_SPEC.md`

## First message to paste into the new project chat
```text
This project is called IMP CNC Production Tracking Prototype.

Goal:
Build a working demo of a digital CNC production tracking system for IMP using:
- FastAPI backend
- SQLite
- React frontend
- WebSockets
- OpenAI API
- a simulated HAAS CNC machine

Important:
- Follow the uploaded technical documentation as the source of truth
- Do not redesign the architecture unless I explicitly ask
- Build in modules, one step at a time
- Keep the project simple and demo-focused
- Single machine only: HAAS_VF2_01
- Real tablet frontend, backend hosted on local office PC
- AI is analysis-only, never machine control

I want you to guide me step by step as if I have never done this before.
Always give me:
1. the exact next action
2. the exact command to run
3. what result I should expect
4. how to verify it worked
5. what to do if it fails

Do not skip steps.
Do not move to the next phase until the current one is confirmed working.
Never tell me to build the full app at once.
Always keep changes scoped to one module at a time.
```

## What this source pack includes
- full project brief
- build rules
- full technical design
- Overleaf/LaTeX version
- exact Codex prompt sequence
- step-by-step Codex usage guide
- implementation sequence
- demo data and scenarios
- runtime and repository specification
