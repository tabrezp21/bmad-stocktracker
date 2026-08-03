---
baseline_commit: NO_VCS
---

# Story 1.2: Configuration Loader

Status: done

## Story

As a developer,
I want a robust `load_config()` function that reads `config.json` and validates its contents,
So that the rest of the application can rely on a single source of truth without hard‑coded values.

## Acceptance Criteria

1. **Given** a valid `config.json` file containing `threshold` (number), `simulation_mode` (boolean), and optional `test_price` (number) **When** `load_config()` is called **Then** it returns a dictionary with correctly typed values and defaults for missing optional fields.
2. **Given** `config.json` is missing **When** `load_config()` is called **Then** the function prints a clear error to `stderr` and exits with a non‑zero status.
3. **Given** `config.json` is malformed JSON **When** `load_config()` is called **Then** the function prints a parsing error to `stderr` and exits with a non‑zero status.
4. **Given** any required key is of the wrong type (e.g., `threshold` is a string) **When** `load_config()` is called **Then** the function raises a `ValueError` describing the type mismatch.
5. **Given** the application runs on Windows 10/11 with Python ≥ 3.10 **When** `load_config()` is used elsewhere **Then** no hard‑coded magic numbers appear in source code; all tunables come from the returned config dictionary.

## Tasks / Subtasks

- [x] Implement `load_config()` in `price_tracker.py` (or a separate `config.py` module) **(AC: 1‑4)**
  - [x] Read `config.json` using `json.load()`
  - [x] Validate required keys (`threshold`, `simulation_mode`) exist and have correct types
  - [x] Provide defaults for optional `test_price` if absent
  - [x] Raise `ValueError` on type mismatches with clear messages
- [x] Add error handling for missing or malformed files (AC: 2‑3)
  - [x] Catch `FileNotFoundError` and `json.JSONDecodeError`
  - [x] Print to `stderr` and exit with `sys.exit(1)`
- [x] Write unit tests covering all acceptance criteria
  - [x] Test successful load with full config
  - [x] Test missing optional `test_price`
  - [x] Test missing file → proper error handling
  - [x] Test malformed JSON → proper error handling
  - [x] Test type‑mismatch errors
- [x] Verify no hard‑coded literals remain in `price_tracker.py` (e.g., remove any `230` or `False` literals)
  - [x] Search the file for numeric literals and replace with config lookups

## Dev Notes

### Architecture Guardrails (MUST follow — from ARCHITECTURE-SPINE.md)

- **AD-2 (Runtime):** Python ≥ 3.10, CPython, Windows 10/11 – do not use syntax beyond 3.10.
- **AD-3 (Config boundary):** This story is *the* source of truth for all tunable values. No other module may define defaults for `threshold`, `simulation_mode`, or `test_price`.
- **AD-1 (Layered Adapter):** `load_config()` belongs to a **configuration adapter** layer. It must expose a pure function returning a dict; the orchestrator may call it but must not import `json` or perform I/O directly.

### Existing files to check (do not blindly overwrite)

- `config.json` – already contains defaults; ensure `load_config()` reads from this file.
- `price_tracker.py` – currently contains a placeholder config loading block; replace it with a call to the new `load_config()` function.
- `README.md` – installation steps remain unchanged; no impact.

### Project Structure Notes

```
BMAD_Project/
  config.json                 # User‑editable settings
  price_tracker.py            # Will import `load_config()` from `config.py`
  config.py                   # New module for configuration loading (to be created)
```

### References

- Architecture Spine: `bmad-output/planning-artifacts/architecture/architecture-BMAD_Project-2026-07-16/ARCHITECTURE-SPINE.md` (AD‑2, AD‑3, AD‑1)
- PRD: `bmad-prd.md` – functional requirement FR‑5 (configurable threshold)
- Story 1.1 – ensures environment is ready before this config loader runs.

## Dev Agent Record

### Agent Model Used

aifs/claude-sonnet-4.6

### Debug Log References

### Completion Notes List

### File List

- `config.json` – read only
- `price_tracker.py` – will be updated to import `load_config`
- `config.py` – new module created
