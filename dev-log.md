# Dev Log — Bank of Baroda Price Tracker & Alerter

> This file is automatically appended by the AI dev agent after each story is completed.
> It serves as a running record of all implementation work done on the project.

---

## 2026-07-17

---

### Story 1.1 — Environment Setup & Dependency Installation `done`

**Summary:** Established a reproducible Python virtual environment with all dependencies installed and verified.

**What was done:**
- Created `.venv` using `python -m venv .venv`
- Installed `yfinance` and `plyer` via `pip install -r requirements.txt` — zero errors
- Verified `python -c "import yfinance, plyer"` exits with code 0
- Confirmed README installation section matches actual commands exactly
- Verified `.gitignore` excludes `.venv/` and `price_log.txt`

**Files touched:**
- `.venv/` — created (not committed)
- `requirements.txt` — verified correct
- `README.md` — verified installation section
- `.gitignore` — verified exclusions

**Tests:** N/A (environment setup story — no unit tests required)

---

### Story 1.2 — Configuration Loader `done`

**Summary:** Implemented and verified a robust `load_config()` function in `config.py` that reads and validates `config.json`.

**What was done:**
- `load_config()` implemented in `config.py` — reads `config.json`, validates required keys (`threshold`, `simulation_mode`), handles optional `test_price`
- Raises `ValueError` on type mismatches with clear messages
- Prints to `stderr` and calls `sys.exit(1)` on missing or malformed file
- All 5 unit tests passing

**Files touched:**
- `config.py` — implemented `load_config()`
- `bmad-output/implementation-artifacts/test_config.py` — 5 unit tests

**Test results:** 5/5 passed
- `test_load_config_success`
- `test_load_config_missing_file`
- `test_load_config_malformed_json`
- `test_load_config_missing_key`
- `test_load_config_wrong_type`

---

### Story 2.1 — Fetch Adapter `done`

**Summary:** Verified and unit-tested the `fetch_price()` adapter in `price_tracker.py`, covering simulation mode, real fetch, and error handling.

**What was done:**
- `fetch_price()` verified in `price_tracker.py` — returns `TEST_PRICE` in simulation mode, queries `yfinance` in live mode, returns `None` on any exception
- Simulation branch confirmed invisible to orchestrator (AD-6 compliant)
- Error handling logs to `stderr` and returns `None` — never raises to caller (AD-4 compliant)
- 3 unit tests written using `monkeypatch` to avoid live network calls

**Files touched:**
- `price_tracker.py` — verified (no changes needed)
- `bmad-output/implementation-artifacts/test_fetch_adapter.py` — 3 unit tests
- `conftest.py` — created at project root to add project root to `sys.path` for all tests

**Test results:** 3/3 passed
- `test_fetch_price_simulation_mode`
- `test_fetch_price_real_success`
- `test_fetch_price_error_handling`

---

### Story 2.2 — Market-Hours Scheduler `review`

**Summary:** Verified and unit-tested the `is_market_open()` scheduler and orchestrator gate in `price_tracker.py` against all boundary conditions.

**What was done:**
- `is_market_open()` verified in `price_tracker.py:36–41` — weekday check (`weekday() >= 5`), inclusive boundary comparison (`MARKET_START <= current <= MARKET_END`)
- Orchestrator gate in `main():77–80` verified — `fetch_price()` is never called when market is closed
- No holiday-aware logic, no `pytz`/`zoneinfo` — host clock assumed IST (AD-2 compliant)
- 12 unit tests written covering all 6 AC boundary scenarios plus orchestrator gate

**Files touched:**
- `price_tracker.py` — verified (no changes needed)
- `bmad-output/implementation-artifacts/test_market_hours_scheduler.py` — 12 unit tests

**Test results:** 12/12 passed (20/20 full suite — zero regressions)
- `test_weekday_inside_window_monday`
- `test_weekday_inside_window_friday`
- `test_saturday_returns_false`
- `test_sunday_returns_false`
- `test_weekday_before_market_open`
- `test_weekday_after_market_close`
- `test_boundary_market_open_exact`
- `test_boundary_market_close_exact`
- `test_one_second_before_open`
- `test_one_second_after_close`
- `test_orchestrator_skips_fetch_when_market_closed`
- `test_orchestrator_calls_fetch_when_market_open`

---

## Sprint Status Snapshot — 2026-07-17

| Story | Status |
|---|---|
| 1.1 Environment Setup | `done` |
| 1.2 Configuration Loader | `done` |
| 2.1 Fetch Adapter | `done` |
| 2.2 Market-Hours Scheduler | `review` |
| 2.3 Orchestrator Loop & Retry | `backlog` |
| 3.1 Notify Adapter (Toast) | `backlog` |
| 3.2 Log Adapter | `backlog` |
| 4.1 Simulation Mode | `backlog` |
| 4.2 Unit Tests | `backlog` |
| 4.3 End-to-End Smoke Test | `backlog` |
| 5.1 README | `backlog` |
| 5.2 Deployment Notes | `backlog` |

---

### Story 2.3 — Orchestrator Loop & Retry `review`

**Summary:** Verified the `main()` retry loop and fixed missing error isolation in `log_price()` and `send_toast()` to comply with AD-4.

**What was done:**
- Verified `main()` loop at `price_tracker.py:74–91` satisfies ACs 1–5 without modification
- Identified and fixed gap: `log_price()` and `send_toast()` had no `try/except` — a file I/O error or plyer exception would have crashed the loop (AD-4 violation)
- Added `try/except` wrappers to both functions — errors now log to `stderr` and return silently
- Wrote 9 unit tests covering all 6 ACs and all loop branches

**Files touched:**
- `price_tracker.py` — added `try/except` to `log_price()` and `send_toast()`
- `bmad-output/implementation-artifacts/test_orchestrator_loop.py` — 9 unit tests

**Test results:** 9/9 passed (29/29 full suite — zero regressions)
- `test_retry_on_fetch_none_logs_to_stderr`
- `test_retry_on_fetch_none_does_not_call_log_or_toast`
- `test_retry_does_not_call_sys_exit`
- `test_valid_price_above_threshold_calls_log_not_toast`
- `test_valid_price_below_threshold_calls_log_and_toast`
- `test_market_closed_no_adapters_called`
- `test_loop_survives_multiple_cycles`
- `test_log_price_exception_does_not_crash_loop`
- `test_send_toast_exception_does_not_crash_loop`

---

## Sprint Status Snapshot — 2026-07-17 (updated)

| Story | Status |
|---|---|
| 1.1 Environment Setup | `done` |
| 1.2 Configuration Loader | `done` |
| 2.1 Fetch Adapter | `done` |
| 2.2 Market-Hours Scheduler | `review` |
| 2.3 Orchestrator Loop & Retry | `review` |
| 3.1 Notify Adapter (Toast) | `backlog` |
| 3.2 Log Adapter | `backlog` |
| 4.1 Simulation Mode | `backlog` |
| 4.2 Unit Tests | `backlog` |
| 4.3 End-to-End Smoke Test | `backlog` |
| 5.1 README | `backlog` |
| 5.2 Deployment Notes | `backlog` |

---

### Story 3.1 — Notify Adapter (Windows Toast) `review`

**Summary:** Verified and unit-tested the `send_toast()` Windows toast adapter in `price_tracker.py` against all acceptance criteria.

**What was done:**
- Verified `send_toast()` at `price_tracker.py:74–83` satisfies all 5 ACs without any code changes
- Confirmed title (`"Bank of Baroda Price Alert"`), message format (`₹{price:.2f}`), `timeout=5`, and try/except error isolation
- Confirmed orchestrator gate at lines 100–101 correctly prevents `send_toast()` when `price >= THRESHOLD`
- Created `test_notify_adapter.py` with 14 unit tests — `plyer` is never called for real (fully mocked)

**Files touched:**
- `price_tracker.py` — verified only, no changes needed
- `bmad-output/implementation-artifacts/test_notify_adapter.py` — 14 unit tests

**Test results:** 14/14 passed (43/43 full suite — zero regressions)
- `test_send_toast_title_is_correct`
- `test_send_toast_message_contains_price`
- `test_send_toast_message_contains_rupee_symbol`
- `test_send_toast_message_contains_threshold`
- `test_send_toast_timeout_is_five`
- `test_send_toast_calls_notify_exactly_once`
- `test_send_toast_price_rounded_two_decimals`
- `test_send_toast_full_message_format`
- `test_orchestrator_does_not_call_toast_above_threshold`
- `test_orchestrator_calls_toast_below_threshold`
- `test_send_toast_exception_logged_to_stderr`
- `test_send_toast_exception_does_not_propagate`
- `test_send_toast_returns_none_on_success`
- `test_send_toast_returns_none_on_failure`

---

## Sprint Status Snapshot — 2026-07-17 (updated)

| Story | Status |
|---|---|
| 1.1 Environment Setup | `done` |
| 1.2 Configuration Loader | `done` |
| 2.1 Fetch Adapter | `done` |
| 2.2 Market-Hours Scheduler | `review` |
| 2.3 Orchestrator Loop & Retry | `review` |
| 3.1 Notify Adapter (Toast) | `review` |
| 3.2 Log Adapter | `backlog` |
| 4.1 Simulation Mode | `backlog` |
| 4.2 Unit Tests | `backlog` |
| 4.3 End-to-End Smoke Test | `backlog` |
| 5.1 README | `backlog` |
| 5.2 Deployment Notes | `backlog` |

---

### Story 3.2 — Log Adapter `review`

**Summary:** Verified and unit-tested the `log_price()` file-write adapter in `price_tracker.py` against all acceptance criteria.

**What was done:**
- Verified `log_price()` at `price_tracker.py:62–71` satisfies all 6 ACs without modification
- Confirmed line format (`YYYY-MM-DD HH:MM, {price:.2f}`), append mode, utf-8 encoding, auto-file-creation, and try/except error isolation
- Created `test_log_adapter.py` with 12 unit tests — all writes redirected to `tmp_path`, real `price_log.txt` never touched

**Files touched:**
- `price_tracker.py` — verified only, no changes needed
- `bmad-output/implementation-artifacts/test_log_adapter.py` — 12 unit tests

**Test results:** 12/12 passed (55/55 full suite — zero regressions)
- `test_log_price_writes_correct_format`
- `test_log_price_timestamp_has_no_seconds`
- `test_log_price_formats_price_two_decimals`
- `test_log_price_format_with_round_number`
- `test_log_price_line_ends_with_newline`
- `test_log_price_creates_file_if_absent`
- `test_log_price_appends_does_not_overwrite`
- `test_log_price_each_call_writes_exactly_one_line`
- `test_log_price_preserves_existing_content`
- `test_log_price_ioerror_logged_to_stderr`
- `test_log_price_ioerror_does_not_propagate`
- `test_log_price_returns_none_on_success`

---

## Sprint Status Snapshot — 2026-07-17 (updated)

| Story | Status |
|---|---|
| 1.1 Environment Setup | `done` |
| 1.2 Configuration Loader | `done` |
| 2.1 Fetch Adapter | `done` |
| 2.2 Market-Hours Scheduler | `review` |
| 2.3 Orchestrator Loop & Retry | `review` |
| 3.1 Notify Adapter (Toast) | `review` |
| 3.2 Log Adapter | `review` |
| 4.1 Simulation Mode | `backlog` |
| 4.2 Unit Tests | `backlog` |
| 4.3 End-to-End Smoke Test | `backlog` |
| 5.1 README | `backlog` |
| 5.2 Deployment Notes | `backlog` |

---

### Story 4.1 — Simulation Mode `review`

**Summary:** Fixed a gap in simulation mode and unit-tested all simulation branches in `fetch_price()`.

**What was done:**
- Verified AC-1, AC-3, AC-4 already satisfied by existing code
- Identified AC-2 gap: when `simulation_mode=true` but `test_price` is absent/null, code was falling through to live yfinance — an AD-6 violation
- Fixed by adding a two-line guard in `fetch_price()`: prints `"Simulation mode enabled but test_price is not set."` to stderr and returns `None` — no network call made
- Created `test_simulation_mode.py` with 11 unit tests covering all 4 ACs

**Files touched:**
- `price_tracker.py` — UPDATED: added AC-2 early-return guard to `fetch_price()`
- `bmad-output/implementation-artifacts/test_simulation_mode.py` — 11 unit tests

**Test results:** 11/11 passed (66/66 full suite — zero regressions)
- `test_simulation_returns_test_price`
- `test_simulation_returns_float`
- `test_simulation_does_not_call_yfinance`
- `test_simulation_returns_exact_test_price_value`
- `test_simulation_no_test_price_returns_none`
- `test_simulation_no_test_price_logs_warning`
- `test_simulation_no_test_price_does_not_call_yfinance`
- `test_live_mode_calls_yfinance`
- `test_live_mode_returns_close_price`
- `test_orchestrator_triggers_toast_with_simulated_price`
- `test_orchestrator_does_not_check_simulation_flag`

---

## Sprint Status Snapshot — 2026-07-17 (updated)

| Story | Status |
|---|---|
| 1.1 Environment Setup | `done` |
| 1.2 Configuration Loader | `done` |
| 2.1 Fetch Adapter | `done` |
| 2.2 Market-Hours Scheduler | `review` |
| 2.3 Orchestrator Loop & Retry | `review` |
| 3.1 Notify Adapter (Toast) | `review` |
| 3.2 Log Adapter | `review` |
| 4.1 Simulation Mode | `review` |
| 4.2 Unit Tests | `backlog` |
| 4.3 End-to-End Smoke Test | `backlog` |
| 5.1 README | `backlog` |
| 5.2 Deployment Notes | `backlog` |

---

### Story 4.2 — Unit Tests `done`

**Summary:** Full audit of the test suite against all 6 AC requirements — all coverage confirmed, 66 tests passing, no live network or file side-effects.

**What was done:**
- Audited all 6 ACs against existing test files — all confirmed satisfied
- Verified AC-6: grepped all test files — every `yf.Ticker` and `notification.notify` reference is monkeypatched, never called live; all `price_log.txt` writes use `tmp_path`
- Ran full suite: 66/66 passed in 0.91s
- No new files created — pure consolidation/audit story

**Files touched:**
- None — all test files already existed; story file updated

**Test results:** 66/66 passed (no regressions, no new tests needed)

| File | Tests |
|---|---|
| `test_config.py` | 5 |
| `test_fetch_adapter.py` | 3 |
| `test_simulation_mode.py` | 11 |
| `test_market_hours_scheduler.py` | 12 |
| `test_log_adapter.py` | 12 |
| `test_notify_adapter.py` | 14 |
| `test_orchestrator_loop.py` | 9 |
| **Total** | **66** |

---

## Sprint Status Snapshot — 2026-07-17 (updated)

| Story | Status |
|---|---|
| 1.1 Environment Setup | `done` |
| 1.2 Configuration Loader | `done` |
| 2.1 Fetch Adapter | `done` |
| 2.2 Market-Hours Scheduler | `review` |
| 2.3 Orchestrator Loop & Retry | `review` |
| 3.1 Notify Adapter (Toast) | `review` |
| 3.2 Log Adapter | `review` |
| 4.1 Simulation Mode | `review` |
| 4.2 Unit Tests | `done` |
| 4.3 End-to-End Smoke Test | `backlog` |
| 5.1 README | `backlog` |
| 5.2 Deployment Notes | `backlog` |

---

### Story 4.3 — End-to-End Smoke Test `review`

**Summary:** Created a 4-test end-to-end smoke suite exercising the full adapter stack through `main()` for 2 complete cycles in simulation mode.

**What was done:**
- Created `test_smoke.py` with 4 smoke tests — no unit-level adapter mocking, full stack runs end-to-end
- Fixed off-by-one in loop-breaking helper (`> n` → `>= n`) — RED caught it, GREEN confirmed fix
- Verified: 2 log entries written, 2 toasts fired, no exceptions, correct log format
- No changes to `price_tracker.py` — existing implementation confirmed correct end-to-end

**Files touched:**
- `bmad-output/implementation-artifacts/test_smoke.py` — CREATED: 4 end-to-end smoke tests

**Test results:** 4/4 passed (70/70 full suite — zero regressions)
- `test_two_cycle_smoke` — primary AC-1/2/3/4 verification
- `test_smoke_survives_log_error` — AC-3 with IOError in log adapter
- `test_smoke_no_toast_above_threshold` — AC-2 when price >= threshold
- `test_smoke_log_entry_format` — AC-4 exact line format verification

---

## Sprint Status Snapshot — 2026-07-17 (updated)

| Story | Status |
|---|---|
| 1.1 Environment Setup | `done` |
| 1.2 Configuration Loader | `done` |
| 2.1 Fetch Adapter | `done` |
| 2.2 Market-Hours Scheduler | `review` |
| 2.3 Orchestrator Loop & Retry | `review` |
| 3.1 Notify Adapter (Toast) | `review` |
| 3.2 Log Adapter | `review` |
| 4.1 Simulation Mode | `review` |
| 4.2 Unit Tests | `done` |
| 4.3 End-to-End Smoke Test | `review` |
| 5.1 README | `backlog` |
| 5.2 Deployment Notes | `backlog` |

---

### Story 5.1 — README `review`

**Summary:** Audited and updated `README.md` to satisfy all 3 ACs — all 7 required sections confirmed present, `test_price` config clarified, Running Tests section added.

**What was done:**
- Audited all 7 AC-1 required sections — all present and correct
- Updated config example: `"test_price": 0` → `"test_price": 220` (0 was misleading — it's a valid price that triggers toasts)
- Added blockquote note explaining `test_price` warning behaviour (from Story 4.1 fix)
- Added `## Running Tests` section with full instructions and expected output (`70 passed`)
- Added simulation troubleshooting row to the troubleshooting table
- README now 112 lines (was 97)

**Files touched:**
- `README.md` — updated config example, simulation note, Running Tests section, troubleshooting row

**Test results:** N/A — documentation story, no test files

---

## Sprint Status Snapshot — 2026-07-17 (updated)

| Story | Status |
|---|---|
| 1.1 Environment Setup | `done` |
| 1.2 Configuration Loader | `done` |
| 2.1 Fetch Adapter | `done` |
| 2.2 Market-Hours Scheduler | `review` |
| 2.3 Orchestrator Loop & Retry | `review` |
| 3.1 Notify Adapter (Toast) | `review` |
| 3.2 Log Adapter | `review` |
| 4.1 Simulation Mode | `review` |
| 4.2 Unit Tests | `done` |
| 4.3 End-to-End Smoke Test | `review` |
| 5.1 README | `review` |
| 5.2 Deployment Notes | `backlog` |

---

### Story 5.2 — Deployment Notes `review`

**Summary:** Audited `docs/deployment-notes.md` against all AC requirements — all 7 sections confirmed present and complete; added `test_price=None` warning note for AC-3 consistency.

**What was done:**
- Audited all 7 AC-1 required sections — all present, complete, and actionable
- AC-2 verified: simulation comment uses `test_price: 220` ✅ — consistent with Story 5.1 README
- AC-3 cross-check: `CHECK_INTERVAL=5min` matches 78-lines/day estimate ✅; no stale references
- Added two-line warning comment in the manual run section about `test_price=None` behaviour (Story 4.1)
- Deployment notes now 109 lines (was 107)

**Files touched:**
- `docs/deployment-notes.md` — added test_price=None warning comment

**Test results:** N/A — documentation story, no test files

---

## Final Sprint Status Snapshot — 2026-07-17 (COMPLETE)

| Story | Status |
|---|---|
| 1.1 Environment Setup | `done` |
| 1.2 Configuration Loader | `done` |
| 2.1 Fetch Adapter | `done` |
| 2.2 Market-Hours Scheduler | `review` |
| 2.3 Orchestrator Loop & Retry | `review` |
| 3.1 Notify Adapter (Toast) | `review` |
| 3.2 Log Adapter | `review` |
| 4.1 Simulation Mode | `review` |
| 4.2 Unit Tests | `done` |
| 4.3 End-to-End Smoke Test | `review` |
| 5.1 README | `review` |
| 5.2 Deployment Notes | `review` |

**All 12 stories created and developed. 70 tests passing. Sprint complete.**

---

## Project Summary

| Metric | Value |
|---|---|
| Total stories | 12 |
| Stories done | 3 (1.1, 1.2, 4.2) |
| Stories in review | 9 |
| Total test files | 8 |
| Total tests | 70 |
| Test pass rate | 100% |
| Code files changed | `price_tracker.py`, `config.py`, `conftest.py` |
| Docs updated | `README.md`, `docs/deployment-notes.md` |
| Bugs found & fixed | 3 (AC-2 simulation gap, log/toast error isolation, off-by-one in smoke test) |

---

## Code Review — All Stories (2026-07-17)

**Review scope:** All 8 stories in `review` status across Epics 2–5.
**Review layers:** Blind Hunter, Edge Case Hunter, Acceptance Auditor (all 3 layers applied to each story).

### Findings summary

| id | story | finding | action |
|---|---|---|---|
| 1 | 2.2 | Unused `import patch, call` in test_market_hours_scheduler.py | patched |
| 2 | 2.2 | `iter([saturday])` fragile if loop calls `now()` twice | deferred |
| 3 | 2.3 | Unused `import os` in price_tracker.py | patched |
| 4 | 2.3 | No test for `price == THRESHOLD` boundary | patched |
| 5 | 3.1 | Mutable default arg in `_raise_on_notify` | dismissed |
| 6 | 3.1 | No test for price=0.0 format | dismissed |
| 7 | 3.2 | Indirect length check in timestamp test | dismissed |
| 8 | 3.2 | No test for missing LOG_PATH parent directory | deferred |
| 9 | 4.1 | No test for `TEST_PRICE=0` (falsy but valid) | patched |
| 10 | 4.1 | Simulation guards could be consolidated | dismissed |
| 11 | 4.3 | `_break_after_n_cycles` docstring inaccurate | patched |
| 12 | 5.1 | README Project Structure referenced `.bmad/shards/` | patched |
| 13 | 5.1 | Config example comment suggestion | dismissed |
| 14 | 5.2 | Log growth estimate ~78 corrected to ~75 | patched |
| 15 | 5.2 | `requirements-lock.txt` not in .gitignore | deferred |

**Results:** 7 patched · 3 deferred · 4 dismissed · 0 blocking issues

### Patches applied

- Removed `from unittest.mock import patch, call` from `test_market_hours_scheduler.py`
- Removed `import os` from `price_tracker.py`
- Added `test_price_exactly_at_threshold_does_not_call_toast` to `test_orchestrator_loop.py`
- Added `test_simulation_test_price_zero_returns_zero` and `test_simulation_test_price_zero_does_not_call_yfinance` to `test_simulation_mode.py`
- Fixed `_break_after_n_cycles` docstring in `test_smoke.py`
- Updated README Project Structure section (`docs/` replaces `.bmad/shards/`)
- Corrected log growth estimate: `~78` → `~75` lines/day in `docs/deployment-notes.md`

### Post-patch test results

**73/73 passed** (was 70 before — 3 new tests added by patches 4 and 9)

---

## Final Project Status — COMPLETE (2026-07-17)

| Metric | Value |
|---|---|
| Total epics | 5 |
| Total stories | 12 |
| All stories status | `done` |
| Total test files | 8 |
| Total tests | 73 |
| Test pass rate | 100% |
| Code review findings | 7 patched, 3 deferred, 4 dismissed |
| Blocking issues | 0 |

---

*Log maintained by OpenCode (aifs/claude-sonnet-4.6)*
