---
baseline_commit: NO_VCS
---

# Story 2.2: Market-Hours Scheduler

Status: done

## Story

As the orchestrator,
I want an `is_market_open(now: datetime) -> bool` function,
So that the poll loop skips all fetches outside 09:15–15:30 IST on weekdays.

## Acceptance Criteria

1. **Given** `now` is a weekday (Monday–Friday) datetime with time between 09:15 and 15:30 (inclusive)
   **When** `is_market_open(now)` is called
   **Then** it returns `True`

2. **Given** `now` is a Saturday or Sunday (any time)
   **When** `is_market_open(now)` is called
   **Then** it returns `False`

3. **Given** `now` is a weekday but the time is before 09:15 or after 15:30
   **When** `is_market_open(now)` is called
   **Then** it returns `False`

4. **Given** `is_market_open(now)` returns `False`
   **When** the orchestrator loop evaluates the result
   **Then** it sleeps for `CHECK_INTERVAL` seconds and does NOT call `fetch_price()`

5. **Given** `is_market_open(now)` returns `True`
   **When** the orchestrator loop evaluates the result
   **Then** it proceeds to call `fetch_price()` and process the result

6. **Given** the boundary times exactly 09:15:00 and 15:30:00
   **When** `is_market_open(now)` is called
   **Then** it returns `True` (boundary is inclusive on both ends)

## Tasks / Subtasks

- [x] Verify `is_market_open()` already exists in `price_tracker.py` (AC: 1–6)
  - [x] Confirm the function handles weekday check (`weekday() >= 5` is weekend)
  - [x] Confirm boundary times are inclusive (`MARKET_START <= current <= MARKET_END`)
- [x] Verify orchestrator loop in `main()` correctly gates `fetch_price()` on `is_market_open()` (AC: 4, 5)
- [x] Write unit tests covering all AC boundary conditions (AC: 1–6)
  - [x] Weekday inside window → `True`
  - [x] Saturday → `False`
  - [x] Sunday → `False`
  - [x] Weekday before 09:15 → `False`
  - [x] Weekday after 15:30 → `False`
  - [x] Exactly 09:15:00 → `True` (boundary inclusive)
  - [x] Exactly 15:30:00 → `True` (boundary inclusive)
  - [x] Verify orchestrator skips `fetch_price()` when market is closed
- [x] Ensure no holiday-aware logic is introduced (out of scope for MVP — weekends only)

## Dev Notes

### Architecture Guardrails (MUST follow)

- **AD-5 (Scheduling ownership):** `is_market_open()` guard lives **exclusively** in the orchestrator. Adapters (`fetch_price`, `send_toast`, `log_price`) are always-on and stateless with respect to time — they must NOT check market hours themselves.
- **AD-1 (Layered Adapter):** The scheduler function is pure logic (no I/O, no network). It takes a `datetime` argument and returns a `bool`. No side effects.
- **AD-2 (Runtime):** Python ≥ 3.10, CPython, Windows 10/11. Use `datetime.time` for comparisons. No `zoneinfo` or `pytz` — host clock is assumed to be IST.
- **AD-3 (Config boundary):** `CHECK_INTERVAL` must come from `config` or remain as a module-level constant derived from config. No magic literals.

### What this story DOES and DOES NOT do

| In scope | Out of scope |
|---|---|
| `is_market_open(now)` pure function | NSE holiday calendar (post-MVP) |
| Weekday/weekend check | Timezone conversion (host clock assumed IST) |
| 09:15–15:30 boundary check (inclusive) | Intraday break handling |
| Orchestrator loop gate (`main()`) | Any change to `fetch_price()` or adapters |
| Unit tests for all boundary conditions | Integration / smoke tests (Epic 4) |

### Existing code to verify (do NOT blindly overwrite)

`price_tracker.py` already contains an `is_market_open()` implementation at line 36:

```python
MARKET_START = dtime(hour=9, minute=15)
MARKET_END   = dtime(hour=15, minute=30)

def is_market_open(now: datetime) -> bool:
    if now.weekday() >= 5:   # Saturday=5, Sunday=6
        return False
    current = now.time()
    return MARKET_START <= current <= MARKET_END
```

And the orchestrator gate in `main()` at line 77:

```python
if not is_market_open(now):
    time.sleep(CHECK_INTERVAL)
    continue
```

**This implementation already satisfies all acceptance criteria.** The primary task is:
1. Verify the existing code is correct against all AC boundary conditions.
2. Write unit tests to prove it.
3. Confirm the orchestrator gate prevents `fetch_price()` from being called when market is closed.

### Key technical facts

- `datetime.weekday()` returns 0=Monday … 6=Sunday. So `>= 5` correctly catches Saturday (5) and Sunday (6).
- `dtime` is imported as `from datetime import time as dtime` to avoid collision with `datetime.datetime`.
- Boundary comparison `MARKET_START <= current <= MARKET_END` is inclusive on both ends — this is correct and intended.
- `CHECK_INTERVAL = 5 * 60` (300 seconds) is defined at module level. It must not be hardcoded in tests; reference `price_tracker.CHECK_INTERVAL`.
- **No timezone-aware datetimes** — the host machine is assumed to be set to IST. Do NOT introduce `pytz` or `zoneinfo` in this story.
- Holiday-aware scheduling (NSE calendar) is explicitly deferred post-MVP per architecture deferred section.

### Test helper pattern (from Story 2.1)

Tests for `price_tracker` should use `monkeypatch` to patch module-level globals where needed. Import the module at the top level (not inside helper functions) to avoid reload complexity:

```python
import price_tracker
from datetime import datetime, time as dtime

def test_market_open_weekday_in_window():
    # Monday 10:00
    now = datetime(2026, 7, 13, 10, 0, 0)  # Monday
    assert price_tracker.is_market_open(now) is True
```

Use `datetime(year, month, day, hour, minute, second)` for all test datetimes to keep tests deterministic and independent of the wall clock.

### Reference datetimes for tests

| Scenario | datetime value | Expected |
|---|---|---|
| Monday 10:00 (in window) | `datetime(2026, 7, 13, 10, 0)` | `True` |
| Saturday 10:00 (weekend) | `datetime(2026, 7, 11, 10, 0)` | `False` |
| Sunday 10:00 (weekend) | `datetime(2026, 7, 12, 10, 0)` | `False` |
| Monday 08:00 (before open) | `datetime(2026, 7, 13, 8, 0)` | `False` |
| Monday 16:00 (after close) | `datetime(2026, 7, 13, 16, 0)` | `False` |
| Monday 09:15:00 (boundary open) | `datetime(2026, 7, 13, 9, 15, 0)` | `True` |
| Monday 15:30:00 (boundary close) | `datetime(2026, 7, 13, 15, 30, 0)` | `True` |

### Project structure notes

```
BMAD_Project/
  price_tracker.py     ← VERIFY: is_market_open() and main() gate — no changes needed if correct
  bmad-output/
    implementation-artifacts/
      test_fetch_adapter.py      ← reference for test patterns
      test_config.py             ← reference for test patterns
      2-2-market-hours-scheduler.md  ← this story
```

Test file to create: `bmad-output/implementation-artifacts/test_market_hours_scheduler.py`

### References

- Architecture Spine: `bmad-output/planning-artifacts/architecture/architecture-BMAD_Project-2026-07-16/ARCHITECTURE-SPINE.md` — AD-5 (scheduling ownership), AD-1, AD-2, AD-3
- Epics: `bmad-output/planning-artifacts/epics.md` — Story 2.2 requirements (FR-2, AD-5)
- Previous story: `bmad-output/implementation-artifacts/2-1-fetch-adapter.md` — test patterns
- `price_tracker.py` lines 31–41 — existing `is_market_open()` implementation

## Dev Agent Record

### Agent Model Used

aifs/claude-sonnet-4.6

### Debug Log References

None — implementation was straightforward; existing code satisfied all ACs.

### Completion Notes List

- Verified `is_market_open()` at `price_tracker.py:36–41` satisfies all 6 ACs without modification.
- Verified orchestrator gate at `price_tracker.py:77–80` correctly prevents `fetch_price()` from being called when market is closed.
- Confirmed no holiday-aware logic, no `pytz`/`zoneinfo` imports — host clock assumed IST per architecture guardrail.
- Created `test_market_hours_scheduler.py` with 12 tests: 10 boundary condition tests + 2 orchestrator gate tests.
- Full regression suite: 20/20 passed, zero regressions.

### File List

- `price_tracker.py` — verified only, no changes needed
- `bmad-output/implementation-artifacts/test_market_hours_scheduler.py` — CREATED: 12 unit tests
- `bmad-output/implementation-artifacts/2-2-market-hours-scheduler.md` — updated tasks and status

### Change Log

- 2026-07-17: Story 2.2 implemented — verified existing `is_market_open()` and orchestrator gate; created 12-test suite covering all AC boundary conditions and orchestrator gate behaviour.
