---
baseline_commit: NO_VCS
---

# Story 4.2: Unit Tests

Status: done

## Story

As a developer,
I want unit tests for each adapter and the scheduler,
So that regressions are caught before manual testing.

## Acceptance Criteria

All of the following must be covered by passing tests, with no test making a live network call:

1. `load_config()` — valid config, missing file, malformed JSON ✅ covered by `test_config.py`
2. `fetch_price()` — simulation mode returns `test_price`; yfinance error returns `None` ✅ covered by `test_fetch_adapter.py` + `test_simulation_mode.py`
3. `is_market_open()` — weekday in-window (`True`), weekend (`False`), outside hours (`False`) ✅ covered by `test_market_hours_scheduler.py`
4. `log_price()` — correct line format appended to a temp file ✅ covered by `test_log_adapter.py`
5. `send_toast()` — called when `price < threshold`; NOT called when `price >= threshold` ✅ covered by `test_notify_adapter.py`
6. No test makes a live network call (all external calls mocked) ✅ all yfinance/plyer calls patched via monkeypatch

## Tasks / Subtasks

- [x] Audit existing test suite against all AC requirements (AC: 1–6)
  - [x] Confirm `load_config()` coverage: valid, missing file, malformed JSON (AC: 1)
  - [x] Confirm `fetch_price()` coverage: simulation mode, yfinance error path (AC: 2)
  - [x] Confirm `is_market_open()` coverage: in-window, weekend, outside hours (AC: 3)
  - [x] Confirm `log_price()` coverage: correct format to temp file (AC: 4)
  - [x] Confirm `send_toast()` coverage: called below threshold, NOT called above (AC: 5)
  - [x] Confirm no test makes a live network call (AC: 6)
- [x] Run full test suite and confirm all 66 tests pass with zero failures
- [x] Confirm all test files use `tmp_path` or `monkeypatch` — no real file/network side-effects
- [x] Update story status to done (this is a consolidation story — no new test files needed)

## Dev Notes

### Coverage status — pre-verified

A full audit was conducted before this story was created. All 6 AC requirements are already
satisfied by the test suite written across Stories 1.2–4.1:

| AC | Requirement | Test file | Tests |
|---|---|---|---|
| 1 | `load_config()` — valid, missing, malformed | `test_config.py` | 5 |
| 2 | `fetch_price()` — simulation + error | `test_fetch_adapter.py`, `test_simulation_mode.py` | 3 + 11 |
| 3 | `is_market_open()` — in-window, weekend, outside | `test_market_hours_scheduler.py` | 12 |
| 4 | `log_price()` — format + temp file | `test_log_adapter.py` | 12 |
| 5 | `send_toast()` — threshold gate | `test_notify_adapter.py` | 14 |
| 6 | No live network calls | all files | all 66 |

**Total: 66 tests across 6 test files. All passing as of Story 4.1.**

### What this story DOES and DOES NOT do

| In scope | Out of scope |
|---|---|
| Audit and confirm existing test coverage | Writing new test files |
| Verify full suite passes (66 tests) | End-to-end smoke test (Story 4.3) |
| Confirm no live network/file side-effects | Performance / load testing |
| Mark suite as validated for MVP | Integration tests beyond unit scope |

### How to run the full suite

```powershell
# From project root (venv activated):
.venv\Scripts\pytest.exe bmad-output/implementation-artifacts/ -v
```

Expected: `66 passed` with no warnings or errors.

### Test files inventory

| File | Adapter / Component | Tests |
|---|---|---|
| `test_config.py` | `load_config()` | 5 |
| `test_fetch_adapter.py` | `fetch_price()` — core | 3 |
| `test_simulation_mode.py` | `fetch_price()` — simulation branch | 11 |
| `test_market_hours_scheduler.py` | `is_market_open()` + orchestrator gate | 12 |
| `test_log_adapter.py` | `log_price()` | 12 |
| `test_notify_adapter.py` | `send_toast()` | 14 |
| `test_orchestrator_loop.py` | `main()` loop branches | 9 |
| **Total** | | **66** |

### Architecture guardrails (for reference)

- **AD-4 (Error isolation):** All adapter error paths (None return, stderr log) are covered by tests.
- **AD-6 (Simulation encapsulation):** Simulation branch fully tested; confirmed orchestrator has no simulation awareness.
- **AD-5 (Scheduling ownership):** `is_market_open()` boundary conditions and orchestrator gate both tested.

### References

- Epics: `bmad-output/planning-artifacts/epics.md` — Story 4.2 AC requirements
- All test files: `bmad-output/implementation-artifacts/test_*.py`
- `conftest.py` — project root, adds root to `sys.path` for all tests

## Dev Agent Record

### Agent Model Used

aifs/claude-sonnet-4.6

### Debug Log References

None — pure audit story, no code changes needed.

### Completion Notes List

- Full AC audit completed — all 6 ACs confirmed satisfied by existing 66-test suite.
- AC-6 verified: grep confirmed all `yf.Ticker` and `notification.notify` references in tests are monkeypatched, not live calls. All `price_log.txt` references use `tmp_path`.
- Full suite run: 66/66 passed in 0.91s.
- Story marked `done` directly (no review needed — consolidation/audit only).

### File List

- No new files created — all test files already existed
- `bmad-output/implementation-artifacts/4-2-unit-tests.md` — updated tasks and status

### Change Log

- 2026-07-17: Story 4.2 completed — full AC audit passed; 66/66 tests confirmed green; no live network or file side-effects in any test.
