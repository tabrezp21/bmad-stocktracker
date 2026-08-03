---
baseline_commit: NO_VCS
---

# Story 2.3: Orchestrator Loop & Retry

Status: done

## Story

As a user,
I want the script to keep running and retrying after network failures,
So that a temporary outage does not require me to manually restart the script.

## Acceptance Criteria

1. **Given** `fetch_price()` returns `None` (network failure)
   **When** the orchestrator processes the result
   **Then** it logs `"Failed to retrieve price; will retry."` to `stderr`
   **And** it waits `CHECK_INTERVAL` seconds
   **And** it calls `fetch_price()` again on the next cycle
   **And** the loop continues indefinitely — `sys.exit()` is never called

2. **Given** `fetch_price()` returns a valid float
   **When** the orchestrator processes the result
   **Then** it calls `log_price(price, now)` to record the price
   **And** if `price < THRESHOLD` it calls `send_toast(price)`
   **And** it sleeps `CHECK_INTERVAL` before the next poll

3. **Given** `fetch_price()` returns a valid float >= `THRESHOLD`
   **When** the orchestrator processes the result
   **Then** `send_toast()` is NOT called

4. **Given** the main loop is running
   **When** `is_market_open()` returns `False`
   **Then** the loop sleeps `CHECK_INTERVAL` and does NOT call `fetch_price()`, `log_price()`, or `send_toast()`

5. **Given** the script has been running for multiple cycles in simulation mode
   **When** no unhandled exceptions occur
   **Then** the process remains alive and `price_log.txt` contains exactly one entry per successful poll cycle (NFR-2, NFR-4)

6. **Given** any adapter (`fetch_price`, `log_price`, `send_toast`) raises an unexpected exception
   **When** the orchestrator loop encounters it
   **Then** the loop must never exit due to the adapter error — it retries after `CHECK_INTERVAL`

## Tasks / Subtasks

- [x] Verify `main()` retry loop in `price_tracker.py` satisfies all ACs (AC: 1–6)
  - [x] Confirm `fetch_price() == None` path logs correct message to `stderr` (AC: 1)
  - [x] Confirm `fetch_price() == None` path sleeps and continues without `sys.exit()` (AC: 1)
  - [x] Confirm valid price path calls `log_price()` then conditionally `send_toast()` (AC: 2, 3)
  - [x] Confirm `price >= THRESHOLD` does NOT call `send_toast()` (AC: 3)
  - [x] Confirm `is_market_open() == False` path skips all adapters (AC: 4)
  - [x] Confirm `while True` loop never exits on adapter error (AC: 6)
- [x] Write unit tests covering all AC branches (AC: 1–6)
  - [x] `fetch_price()` returns `None` → stderr message logged, sleep called, no exit
  - [x] `fetch_price()` returns price above threshold → `log_price()` called, `send_toast()` NOT called
  - [x] `fetch_price()` returns price below threshold → `log_price()` called, `send_toast()` called
  - [x] `is_market_open()` returns `False` → none of `fetch_price()`, `log_price()`, `send_toast()` called
  - [x] Loop survives multiple cycles without exiting
- [x] Verify `log_price()` and `send_toast()` have error isolation — exceptions must not crash the loop (AC: 6)

## Dev Notes

### Architecture Guardrails (MUST follow)

- **AD-4 (Error isolation):** Every adapter wraps its call in try/except; failures return `None` or log and return silently. The orchestrator catches `None` / logged failures and retries after `CHECK_INTERVAL` — **the loop must never exit on an adapter error**.
- **AD-5 (Scheduling ownership):** `is_market_open()` guard lives exclusively in the orchestrator; adapters are stateless with respect to time.
- **AD-1 (Layered Adapter):** The orchestrator calls adapters; it must never call `yfinance`, `plyer`, or file I/O directly.
- **AD-3 (Config boundary):** `THRESHOLD` and `CHECK_INTERVAL` come from module-level constants loaded from config — no magic literals in the loop.

### What this story DOES and DOES NOT do

| In scope | Out of scope |
|---|---|
| Verify and test `main()` retry loop | Any new orchestrator features |
| Error isolation for all adapters | Multi-ticker support (post-MVP) |
| `log_price()` and `send_toast()` call sequencing | Async / non-blocking I/O (deferred) |
| Unit tests for all loop branches | End-to-end smoke test (Story 4.3) |

### Existing code to verify (do NOT blindly overwrite)

`price_tracker.py` `main()` at lines 74–91 already implements the full orchestrator loop:

```python
def main() -> None:
    while True:
        now = datetime.now()
        if not is_market_open(now):          # AC-4: market closed gate
            time.sleep(CHECK_INTERVAL)
            continue
        price = fetch_price()
        if price is None:                    # AC-1: retry on failure
            print("Failed to retrieve price; will retry.", file=sys.stderr)
            time.sleep(CHECK_INTERVAL)
            continue
        log_price(price, now)                # AC-2: always log valid price
        if price < THRESHOLD:               # AC-3: conditional toast
            send_toast(price)
        time.sleep(CHECK_INTERVAL)          # AC-2: wait before next poll
```

**This implementation already satisfies ACs 1–5.** However:
- `log_price()` (line 64–65) does NOT have a try/except wrapper — a file I/O error would propagate to `main()` and crash the loop. **This must be fixed to satisfy AC-6 / AD-4.**
- `send_toast()` (line 68–71) does NOT have a try/except wrapper — a plyer exception would crash the loop. **This must also be fixed.**

### Required fix — error isolation for `log_price()` and `send_toast()`

Both adapter functions need try/except wrappers to comply with AD-4:

```python
def log_price(price: float, timestamp: datetime) -> None:
    try:
        line = f"{timestamp.strftime('%Y-%m-%d %H:%M')}, {price:.2f}\n"
        with open(LOG_PATH, "a", encoding="utf-8") as log_file:
            log_file.write(line)
    except Exception as e:
        print(f"Error writing price log: {e}", file=sys.stderr)


def send_toast(price: float) -> None:
    try:
        title = "Bank of Baroda Price Alert"
        message = f"Price dropped to ₹{price:.2f} (target ₹{THRESHOLD})"
        notification.notify(title=title, message=message, timeout=5)
    except Exception as e:
        print(f"Error sending notification: {e}", file=sys.stderr)
```

### Key technical facts

- `while True` with `continue` and `time.sleep()` is the correct synchronous polling pattern for this MVP — no async needed.
- `CHECK_INTERVAL = 5 * 60` (300 seconds) — reference as `price_tracker.CHECK_INTERVAL` in tests, never hardcode.
- `THRESHOLD` is a module-level float loaded from config — reference as `price_tracker.THRESHOLD` in tests.
- `datetime.now()` is called at the top of each loop iteration — monkeypatch `price_tracker.datetime` in tests to inject deterministic timestamps.
- Tests must break the infinite `while True` loop using `side_effect` with `SystemExit` on `time.sleep` after the desired number of iterations.
- No `sys.exit()` should ever be called inside the loop body — only at module import time if config.json is missing.

### Test patterns (learnings from Stories 2.1 and 2.2)

Import `price_tracker` at module level. Use `monkeypatch` to patch globals and functions:

```python
import price_tracker

def test_retry_on_none(monkeypatch, capsys):
    # Patch datetime.now to return a market-open time
    monday = datetime(2026, 7, 13, 10, 0, 0)
    monkeypatch.setattr(
        "price_tracker.datetime",
        type("FakeDT", (), {"now": staticmethod(lambda: monday)})
    )
    # fetch returns None → retry path
    monkeypatch.setattr(price_tracker, "fetch_price", lambda: None)

    sleep_calls = []
    def fake_sleep(s):
        sleep_calls.append(s)
        raise SystemExit(0)   # break loop after first sleep

    monkeypatch.setattr(price_tracker.time, "sleep", fake_sleep)

    try:
        price_tracker.main()
    except SystemExit:
        pass

    captured = capsys.readouterr()
    assert "Failed to retrieve price; will retry." in captured.err
    assert len(sleep_calls) == 1
```

Use `SystemExit` on the Nth `time.sleep` call to control how many loop iterations run.

### Project structure notes

```
BMAD_Project/
  price_tracker.py    ← UPDATE: add try/except to log_price() and send_toast()
  bmad-output/
    implementation-artifacts/
      test_market_hours_scheduler.py  ← reference for orchestrator mock pattern
      test_fetch_adapter.py           ← reference for monkeypatch patterns
      2-3-orchestrator-loop-retry.md  ← this story
```

Test file to create: `bmad-output/implementation-artifacts/test_orchestrator_loop.py`

### References

- Architecture Spine: `bmad-output/planning-artifacts/architecture/architecture-BMAD_Project-2026-07-16/ARCHITECTURE-SPINE.md` — AD-4 (error isolation), AD-5, AD-1, AD-3
- Epics: `bmad-output/planning-artifacts/epics.md` — Story 2.3 (FR-7, AD-4, NFR-2, NFR-4)
- Previous story: `bmad-output/implementation-artifacts/2-2-market-hours-scheduler.md` — orchestrator mock pattern
- `price_tracker.py` lines 62–71 — `log_price()` and `send_toast()` (need try/except)
- `price_tracker.py` lines 74–91 — existing `main()` loop

## Dev Agent Record

### Agent Model Used

aifs/claude-sonnet-4.6

### Debug Log References

None — all ACs satisfied cleanly; gap in error isolation was the only code change required.

### Completion Notes List

- Verified `main()` loop at `price_tracker.py:74–91` satisfies ACs 1–5 without modification.
- Identified gap: `log_price()` and `send_toast()` had no try/except wrappers (AC-6 / AD-4 violation).
- Added try/except to `log_price()` (line 62) and `send_toast()` (line 73) — both now log errors to stderr and return silently on failure.
- Created `test_orchestrator_loop.py` with 9 unit tests covering all 6 ACs and all loop branches.
- Full regression suite: 29/29 passed, zero regressions.

### File List

- `price_tracker.py` — UPDATED: added try/except to `log_price()` and `send_toast()`
- `bmad-output/implementation-artifacts/test_orchestrator_loop.py` — CREATED: 9 unit tests
- `bmad-output/implementation-artifacts/2-3-orchestrator-loop-retry.md` — updated tasks and status

### Change Log

- 2026-07-17: Story 2.3 implemented — verified orchestrator loop; added error isolation (try/except) to log_price() and send_toast(); created 9-test suite covering all loop branches.
