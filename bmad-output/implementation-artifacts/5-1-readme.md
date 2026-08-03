---
baseline_commit: NO_VCS
---

# Story 5.1: README

Status: done

## Story

As a new user,
I want a clear README that explains installation, configuration, and usage,
So that I can set up and run the tracker without asking for help.

## Acceptance Criteria

1. **Given** `README.md` exists in the project root
   **When** a new user reads it
   **Then** it contains: project overview, prerequisites, installation steps, configuration reference, usage instructions, log format description, and a troubleshooting table
   **And** all commands in the README execute successfully on a clean Windows 10/11 machine with Python 3.10+

2. **Given** the README configuration section
   **When** a user reads the `simulation_mode` and `test_price` entries
   **Then** it is clear that `test_price` must be set to a meaningful price value when `simulation_mode` is `true`
   **And** a warning is noted that leaving `test_price` absent/null will log a warning and return no price

3. **Given** the README
   **When** a developer reads it
   **Then** it includes instructions for running the test suite with `pytest`

## Tasks / Subtasks

- [x] Audit existing `README.md` against all AC-1 required sections
  - [x] Project overview ✓ (already present)
  - [x] Prerequisites ✓ (already present)
  - [x] Installation steps ✓ (verified in Story 1.1)
  - [x] Configuration reference ✓ (already present — minor update needed for AC-2)
  - [x] Usage instructions ✓ (already present)
  - [x] Log format description ✓ (already present)
  - [x] Troubleshooting table ✓ (already present)
- [x] Update configuration section to clarify `test_price` behaviour (AC-2)
  - [x] Add note: when `simulation_mode=true`, `test_price` must be a valid number
  - [x] Add note: if `test_price` is absent or null, a warning is logged and no price is returned
  - [x] Update example `config.json` snippet — change `"test_price": 0` to `"test_price": 220` for clarity
- [x] Add a **Running Tests** section (AC-3)
  - [x] Activate venv instruction
  - [x] `pip install pytest` (if not already installed)
  - [x] `pytest bmad-output/implementation-artifacts/` command
  - [x] Expected output: `70 passed`

## Dev Notes

### What this story DOES and DOES NOT do

| In scope | Out of scope |
|---|---|
| Audit all 7 required sections (AC-1) | Rewriting the entire README |
| Clarify `test_price` behaviour (AC-2) | Adding architecture/design documentation |
| Add Running Tests section (AC-3) | Deployment automation scripts |
| Minor config example update | API documentation |

### Current README state — pre-audit (97 lines)

All 7 AC-1 required sections already exist:

| Section | Lines | Status |
|---|---|---|
| Project overview | 1–13 | ✅ present |
| Prerequisites | 15–19 | ✅ present |
| Installation steps | 21–31 | ✅ verified in Story 1.1 |
| Configuration reference | 33–49 | ✅ present — needs AC-2 update |
| Usage instructions | 51–64 | ✅ present |
| Log format description | 66–73 | ✅ present |
| Troubleshooting table | 90–97 | ✅ present |

### Required changes

**1. Configuration section update (AC-2)**

Current config example shows `"test_price": 0` which is misleading — `0` is a valid price value and would trigger a toast alert (0 < 230). Should be changed to `220` as a realistic example. Also add a note clarifying behavior when `test_price` is absent.

Current table row:
```
| `test_price` | number | Price returned when `simulation_mode` is `true` |
```

Should become more explicit — add a note below the table explaining the warning behaviour introduced in Story 4.1.

**2. Running Tests section (AC-3)**

Add a new `## Running Tests` section after the Troubleshooting section:

```markdown
## Running Tests

With the virtual environment activated:

```powershell
pip install pytest   # only needed once
pytest bmad-output/implementation-artifacts/
```

Expected output: `70 passed` (no failures).
```

### Key constraint

Only modify `README.md` — do not touch `price_tracker.py`, `config.json`, or any test files. This is documentation-only.

### References

- Epics: `bmad-output/planning-artifacts/epics.md` — Story 5.1 AC requirements
- Story 4.1 `4-1-simulation-mode.md` — `test_price=None` warning behaviour to document
- Story 1.1 `1-1-environment-setup-dependency-installation.md` — installation steps verified
- `README.md` — file to update (project root)

## Dev Agent Record

### Agent Model Used

aifs/claude-sonnet-4.6

### Debug Log References

None — targeted documentation updates only; no logic changes.

### Completion Notes List

- Audited all 7 AC-1 required sections — all present and correct.
- Updated configuration section: changed `"test_price": 0` to `"test_price": 220` in example; added blockquote note explaining warning behaviour when `test_price` is absent (Story 4.1 fix).
- Added `## Running Tests` section with venv activation, `pip install pytest`, and `pytest bmad-output/implementation-artifacts/` command; expected output noted as `70 passed`.
- Added troubleshooting row for simulation mode not alerting.
- README now 112 lines (was 97).

### File List

- `README.md` — UPDATED: test_price example, simulation note, Running Tests section, troubleshooting row
- `bmad-output/implementation-artifacts/5-1-readme.md` — updated tasks and status

### Change Log

- 2026-07-17: Story 5.1 implemented — audited README; clarified test_price config; added Running Tests section and simulation troubleshooting row.
