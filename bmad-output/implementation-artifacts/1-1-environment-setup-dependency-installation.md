---
baseline_commit: NO_VCS
---

# Story 1.1: Environment Setup & Dependency Installation

Status: done

## Story

As a developer,
I want a documented, reproducible virtual environment with all dependencies installed,
So that any contributor can run the project from a clean Windows machine without manual guesswork.

## Acceptance Criteria

1. **Given** a clean Windows 10/11 machine with Python 3.10+ installed  
   **When** the developer runs `python -m venv .venv && .venv\Scripts\activate && pip install -r requirements.txt`  
   **Then** all packages install without error and `python -c "import yfinance, plyer"` exits with code 0  
   **And** `requirements.txt` lists `yfinance` and `plyer` with no pinned conflicts

2. **Given** the virtual environment is activated  
   **When** `python --version` is run  
   **Then** the output confirms Python 3.10 or higher

3. **Given** `requirements.txt` exists in the project root  
   **When** a developer runs `pip install -r requirements.txt` on a fresh venv  
   **Then** all packages resolve without dependency conflicts

## Tasks / Subtasks

- [x] Verify Python 3.10+ is the baseline (AC: 2)
  - [x] Confirm `python --version` returns ≥ 3.10 in local env
- [x] Create/update `requirements.txt` in project root (AC: 1, 3)
  - [x] Include `yfinance` (no version pin required for MVP)
  - [x] Include `plyer` (no version pin required for MVP)
  - [x] Remove any stale or incorrect entries
- [x] Validate environment setup end-to-end (AC: 1)
  - [x] Create `.venv` with `python -m venv .venv`
  - [x] Activate with `.venv\Scripts\activate`
  - [x] Run `pip install -r requirements.txt` — confirm zero errors
  - [x] Run `python -c "import yfinance, plyer"` — confirm exit code 0
- [x] Confirm README installation steps match actual commands (AC: 1)
  - [x] Cross-check `README.md` installation section against verified steps

## Dev Notes

### Architecture Guardrails (MUST follow — from ARCHITECTURE-SPINE.md)

- **AD-2 (Runtime):** Python ≥ 3.10, CPython only, Windows 10/11 target. Do NOT introduce syntax that requires 3.11+.
- **AD-3 (Config boundary):** This story does NOT touch `config.json` logic — that is Story 1.2. Keep scope clean.
- **AD-1 (Layered Adapter):** No source code changes to `price_tracker.py` in this story — environment only.

### What this story DOES and DOES NOT do

| In scope | Out of scope |
|---|---|
| `requirements.txt` content and validation | `config.json` loader (Story 1.2) |
| Virtual environment creation steps | Any `price_tracker.py` code changes |
| README installation section accuracy | Simulation mode, adapters, tests |

### Existing files to check (do not blindly overwrite)

- `requirements.txt` — already exists at project root with `yfinance` and `plyer`. Verify contents are correct and sufficient. Do NOT add `requests` (it was listed in the PRD brief but is not actually used — `yfinance` handles HTTP internally).
- `README.md` — already exists at project root. The installation section must match the validated commands exactly. Do NOT rewrite the whole file — only correct the installation section if it is wrong.

### Key technical facts

- `yfinance` pulls `requests`, `pandas`, `numpy`, etc. as transitive deps — no need to list them in `requirements.txt`.
- `plyer` on Windows uses `win10toast` or the native WinRT backend depending on version. No extra Windows SDK needed for `plyer ≥ 2.1`.
- `.venv\Scripts\activate` is the Windows activation path. On PowerShell use `.venv\Scripts\Activate.ps1`. Both are valid — README should show the `cmd`/PowerShell variant.
- Do NOT commit `.venv/` to version control — verify `.gitignore` includes `.venv` and `price_log.txt`.

### .gitignore check

Confirm `.gitignore` (already exists in project root) includes at minimum:
```
.venv/
price_log.txt
__pycache__/
*.pyc
```
Add any missing entries.

### Project Structure Notes

```
BMAD_Project/           ← project root
  requirements.txt      ← UPDATE: verify yfinance + plyer, remove requests if present
  README.md             ← UPDATE: verify installation section only
  .gitignore            ← UPDATE: ensure .venv/, price_log.txt are excluded
  .venv/                ← CREATE: virtual environment (not committed)
  price_tracker.py      ← DO NOT TOUCH in this story
  config.json           ← DO NOT TOUCH in this story
```

### References

- Architecture Spine: `bmad-output/planning-artifacts/architecture/architecture-BMAD_Project-2026-07-16/ARCHITECTURE-SPINE.md` — AD-2 (runtime), AD-3 (config boundary)
- PRD: `bmad-prd.md` — §6.1 MVP Scope (requirements.txt contents)
- README: `README.md` — Installation section to validate
- Deployment Notes: `docs/deployment-notes.md` — Pre-deployment checklist

## Dev Agent Record

### Agent Model Used

aifs/claude-sonnet-4.6

### Debug Log References

### Completion Notes List

### File List

- `requirements.txt` — verify/update
- `README.md` — verify installation section
- `.gitignore` — verify exclusions
