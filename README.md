# Mock OA Platform (Data Science Intern practice)

Five timed mock assessments (61-62 questions, 1,800 marks each, difficulty rising from OA 1 easy to OA 5 hard) served by a FastAPI backend with a React/TypeScript frontend.
Question banks: `assessment-01.json` … `assessment-05.json` (schema v2, see `SCHEMA.md`; the earlier v1 banks are in `legacy/`). Grader: `oa_lib.py`.

Practice material only — not official Nasdaq questions and **not secure exam proctoring** (see Limitations).

## Layout

| path | what |
|---|---|
| `assessment-0N.json`, `oa_lib.py`, `validate.py`, `SCHEMA.md`, `src/` | existing question banks, grader, validator, generator |
| `backend/app/` | FastAPI app: `engine.py` (section state machine), `execution.py` + `runner.py` (sandboxed Python/SQL grading subprocess), `bank.py` (candidate-safe views), `db.py` (SQLite) |
| `backend/tests/` | pytest acceptance tests |
| `frontend/` | Vite + React + TS + Tailwind + CodeMirror + SQL.js (Web Worker); Vitest unit tests; Playwright e2e |
| `data/attempts.db` | created on first run (attempt state, answers, submissions, results) |

## Install

Backend (Python ≥ 3.11):
```bash
python -m venv .venv && . .venv/bin/activate        # or: uv venv && uv pip install ...
pip install -r requirements.txt
```
Frontend (Node ≥ 20):
```bash
cd frontend && npm install && npx playwright install chromium
```
> This repo was developed in WSL2 where Node only exists on Windows: run Node commands through `cmd.exe /c "npm install"` etc.

## Run (production build, one port)
```bash
cd frontend && npm run build && cd ..
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
# open http://localhost:8000
```
FastAPI serves the compiled app from `frontend/dist` plus the API under `/api`.

Development workflow: run the API on :8000 as above and `cd frontend && npm run dev` (Vite on :5173 proxies `/api` to :8000).

## Test
```bash
python validate.py                                   # original bank validator (reference solutions, marks, overlap)
python -m pytest backend/tests -q                    # acceptance tests (fake clock; real code/SQL execution)
cd frontend && npm test                              # Vitest (timer + palette helpers)
npm run build                                        # tsc + vite build
# e2e: start a throw-away server in TEST mode (fake clock endpoint), then run Playwright against it
OA_TEST_MODE=1 OA_DB=/tmp/e2e.db python -m uvicorn backend.app.main:app --port 8001 &
cd frontend && E2E_BASE_URL=http://localhost:8001 npx playwright test
```
`OA_TEST_MODE=1` exposes `POST /api/test/clock {"seconds": N}`; never set it for real practice. Restart the e2e server (fresh `OA_DB`) before each run.

## How the timing works
* Six sections in a fixed order: CS/AI/ML/Stats/Testing MCQs → Aptitude → Data Analysis (charts) → SQL → Pandas → DSA. Each OA has its own fixed schedule (OA1/2: 145 min, OA3: 135, OA4/5: 140; see `SCHEMA.md`). There is a single "standard" profile.
* The server stores absolute deadlines. Every API call first applies any passed deadline (`engine.sync`): the section is graded and frozen, and the next section's window starts **at the previous deadline** (so even after hours of downtime the schedule is correct and cascades through several sections). After DSA the attempt is completed.
* **Early finish:** once every question of the active section is submitted (MCQ-type: option chosen; coding: Submit pressed) the *Finish Section* button unlocks (*End Test* in the last section). It locks the section for good and starts the next one **now** with its full time. Before that the server answers `409 not_all_submitted`.
* Writes to a finished/locked section are rejected (HTTP 403/409), including grading results that arrive after the deadline.
* The browser countdown is cosmetic; it is re-synchronised from the server on load, every 5 s, and every second after reaching 0.
* **Hints** (OA1-3 only): a button on every question reveals formula hints (MCQ, aptitude, data analysis) or three progressive hints (coding).

## Scoring
Per-question marks come from the bank's weighted tests: `marks × Σ(passed weights) / Σ(all weights)` (identical to `oa_lib.grade_question`; a test asserts equality). MCQs are all-or-nothing. The **latest submission** counts; a final draft that was never submitted is auto-graded when the section ends.

## Limitations
* Candidate Python runs in a separate process with a temp working dir, CPU/memory/file-size `rlimit`s and a hard timeout, but it is **not a security sandbox**: no network or filesystem isolation (no containers), and the grading process can read the question bank. Fine for your own practice on your own machine; do not expose this server to untrusted users.
* Anyone with filesystem access can read `assessment-0N.json` (it contains reference answers). The API itself never sends them until the attempt is over.
* SQL "Run Query" in the browser uses SQL.js (SQLite compiled to WASM) against the public sample data; graded runs use Python's `sqlite3` on the server with a fresh in-memory DB per test. Tiny engine-version differences are possible.
* Pandas/DSA reference code was verified on pandas 3.0.

## Troubleshooting
* Blank page / 404 for assets: run `npm run build` in `frontend/`.
* Port 8000 busy: use another `--port`; for dev set the proxy target in `frontend/vite.config.ts`.
* Browser cannot reach WSL server: use `http://<output of wsl hostname -I>:8000`.
* Reset all attempts: stop the server and delete `data/attempts.db`.
* "Runner crashed" messages mean the grading subprocess failed (e.g. out of memory); the submission is **not** recorded.
