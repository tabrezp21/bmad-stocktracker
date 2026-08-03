---
baseline_commit: NO_VCS
---

# Story 5.2: Deployment Notes

Status: done

## Story

As a developer or maintainer,
I want documented deployment steps including optional startup configuration,
So that the tracker can be reliably deployed and handed over.

## Acceptance Criteria

1. **Given** `docs/deployment-notes.md` exists
   **When** a maintainer follows the steps
   **Then** the document covers: target environment, pre-deployment checklist, manual run instructions, optional Windows startup configuration, log management guidance, known MVP limitations, and rollback procedure
   **And** no step requires undocumented prior knowledge

2. **Given** the deployment notes simulation mode comment
   **When** a user reads the manual run section
   **Then** the `test_price` example value matches the README (220, not 0)

3. **Given** the full suite of deployment documentation
   **When** reviewed end-to-end
   **Then** it is consistent with the current `README.md`, `config.json`, and `price_tracker.py` behaviour (including the `test_price=None` warning from Story 4.1)

## Tasks / Subtasks

- [x] Audit `docs/deployment-notes.md` against all AC-1 required sections
  - [x] Target environment ✓ (already present at lines 3–11)
  - [x] Pre-deployment checklist ✓ (already present at lines 13–21)
  - [x] Manual run instructions ✓ (already present at lines 23–43)
  - [x] Optional Windows startup configuration ✓ (already present at lines 45–61)
  - [x] Log management guidance ✓ (already present at lines 67–78)
  - [x] Known MVP limitations ✓ (already present at lines 92–99)
  - [x] Rollback procedure ✓ (already present at lines 101–107)
- [x] Verify AC-2: simulation mode comment uses `test_price: 220` (not `0`) — consistent with README update in Story 5.1
- [x] Verify AC-3: cross-check deployment notes against current `README.md`, `config.json`, and `price_tracker.py` for consistency
  - [x] Confirm `test_price` warning behaviour documented (or add note referencing AC-3 from Story 4.1)
  - [x] Confirm `CHECK_INTERVAL` (5 minutes) matches log growth estimate (78 lines/day)
  - [x] Confirm no references to removed or changed behaviours
- [x] Add a note about the `test_price=None` warning behaviour to the manual run section (AC-3)
  - [x] When `simulation_mode=true` and `test_price` is absent/null → script logs warning and skips alert — mention this in the simulation usage note

## Dev Notes

### What this story DOES and DOES NOT do

| In scope | Out of scope |
|---|---|
| Audit all 7 AC-1 sections | Rewriting deployment notes from scratch |
| Consistency check against README/config/code | Windows Task Scheduler detailed setup |
| Add `test_price=None` warning note (AC-3) | Log rotation implementation |
| Minor corrections if found | Packaging / PyInstaller docs |

### Current state — pre-audit

`docs/deployment-notes.md` is 107 lines and covers all 7 AC-1 required sections. It was created as a planning artifact before implementation began. All sections are substantive and complete.

**Known consistency item to check (AC-2):**
The manual run comment at line 29 reads:
```
# Set "simulation_mode": true and "test_price": 220 in config.json
```
This is already correct (`220`, not `0`) — consistent with Story 5.1 README update. ✅

**Known gap (AC-3):**
The deployment notes do not mention the `test_price=None` warning behaviour introduced in Story 4.1. The manual run section should note that if `test_price` is absent or null when `simulation_mode=true`, the script logs a warning to stderr and no alert fires. This prevents a maintainer from being confused during testing.

### Required addition — AC-3 note in manual run section

After the existing simulation mode comment (line 29), add a clarifying note:

```markdown
# Note: if test_price is absent or null in simulation mode,
# the script logs a warning to stderr and skips the alert for that cycle.
```

### Key constraint

Only modify `docs/deployment-notes.md` — do not touch `price_tracker.py`, `config.json`, `README.md`, or any test files.

### References

- Epics: `bmad-output/planning-artifacts/epics.md` — Story 5.2 AC requirements
- Story 4.1: `4-1-simulation-mode.md` — `test_price=None` warning behaviour
- Story 5.1: `5-1-readme.md` — README config section (test_price=220)
- `docs/deployment-notes.md` — file to update (lines 29, 45–62)
- `README.md` — consistency reference

## Dev Agent Record

### Agent Model Used

aifs/claude-sonnet-4.6

### Debug Log References

None — targeted documentation update only; one two-line comment addition.

### Completion Notes List

- Audited all 7 AC-1 required sections — all present, complete, and actionable.
- AC-2 confirmed: simulation comment at line 29 uses `test_price: 220` ✅ — consistent with Story 5.1 README update.
- AC-3 cross-check: `CHECK_INTERVAL=5min` matches 78-lines/day estimate ✅; no stale references found ✅.
- Added two-line warning comment in the manual run bash block (after line 29) describing `test_price=None` behaviour from Story 4.1.
- Deployment notes now 109 lines (was 107).

### File List

- `docs/deployment-notes.md` — UPDATED: added test_price=None warning comment to manual run section
- `bmad-output/implementation-artifacts/5-2-deployment-notes.md` — updated tasks and status

### Change Log

- 2026-07-17: Story 5.2 implemented — audited all 7 AC sections; verified AC-2 consistency; added test_price=None warning note to manual run section (AC-3).
