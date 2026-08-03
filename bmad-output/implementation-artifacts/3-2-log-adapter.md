---
baseline_commit: NO_VCS
---

# Story 3.2: Log Adapter

Status: done

## Story

As a user,
I want every price check appended to `price_log.txt`,
So that I have a permanent record of all checks for review.

## Acceptance Criteria

1. **Given** a successful price fetch
   **When** `log_price(price, timestamp)` is called
   **Then** a line in the format `YYYY-MM-DD HH:MM, {price:.2f}` is appended to `price_log.txt`
   **And** exactly one line is written per poll cycle — no duplicates (NFR-4)

2. **Given** `price_log.txt` does not yet exist
   **When** `log_price()` is called for the first time
   **Then** the file is created automatically

3. **Given** `log_price()` raises an `IOError`
   **When** the error is caught
   **Then** it is logged to `stderr` and the orchestrator loop continues without crashing (AD-4)

4. **Given** `log_price(price, timestamp)` is called
   **When** it writes to the file
   **Then** it uses `"a"` (append) mode — it must never overwrite existing entries

5. **Given** the function completes (success or failure)
   **When** it returns
   **Then** it always returns `None` — it never raises to the caller

6. **Given** a valid price and timestamp
   **When** `log_price()` writes the line
   **Then** the timestamp is formatted as `YYYY-MM-DD HH:MM` (no seconds)
   **And** the price is formatted to exactly 2 decimal places

## Tasks / Subtasks

- [x] Verify `log_price()` in `price_tracker.py` satisfies all ACs (AC: 1–6)
  - [x] Confirm line format is `f"{timestamp.strftime('%Y-%m-%d %H:%M')}, {price:.2f}\n"` (AC: 1, 6)
  - [x] Confirm file opened in `"a"` (append) mode (AC: 4)
  - [x] Confirm `encoding="utf-8"` used (AC: 1)
  - [x] Confirm `try/except` wraps entire write — error logged to `stderr` (AC: 3, 5)
  - [x] Confirm `LOG_PATH` resolves to `price_tracker.py`'s parent directory (AC: 2)
- [x] Write unit tests covering all ACs (AC: 1–6)
  - [x] Line format written correctly — `YYYY-MM-DD HH:MM, {price:.2f}` (AC: 1, 6)
  - [x] File created automatically when it does not exist (AC: 2)
  - [x] Each call appends exactly one line (AC: 1, NFR-4)
  - [x] Multiple calls append multiple lines without overwriting (AC: 4)
  - [x] `IOError` caught, logged to `stderr`, returns `None` (AC: 3, 5)
  - [x] Returns `None` on success (AC: 5)

## Dev Notes

### Architecture Guardrails (MUST follow)

- **AD-1 (Layered Adapter):** `log_price()` is a pure output adapter — it only writes to a file. It must not check prices, call `yfinance`, or send notifications.
- **AD-4 (Error isolation):** `log_price()` must catch all exceptions, log to `stderr`, and return silently. It must never raise to the orchestrator.
- **AD-3 (Config boundary):** `LOG_PATH` is a module-level constant (`Path(__file__).parent / "price_log.txt"`) — never hardcoded inline.
- **NFR-4:** Exactly one line per poll cycle — the function is called once per successful fetch in `main()` and must not write duplicate lines.

### What this story DOES and DOES NOT do

| In scope | Out of scope |
|---|---|
| Verify `log_price()` implementation | Log rotation policy (deferred post-MVP) |
| Line format verification | Log compression or archiving |
| File auto-creation (append mode) | Structured logging / JSON format |
| Error isolation (try/except) | Multi-file logging |
| Unit tests for all ACs | Integration smoke test (Story 4.3) |

### Existing code to verify (do NOT blindly overwrite)

`log_price()` in `price_tracker.py` at lines 62–71 (try/except added in Story 2.3):

```python
def log_price(price: float, timestamp: datetime) -> None:
    """Append a timestamped price entry to price_log.txt.
    Logs error to stderr on failure — never raises to caller (AD-4).
    """
    try:
        line = f"{timestamp.strftime('%Y-%m-%d %H:%M')}, {price:.2f}\n"
        with open(LOG_PATH, "a", encoding="utf-8") as log_file:
            log_file.write(line)
    except Exception as e:
        print(f"Error writing price log: {e}", file=sys.stderr)
```

`LOG_PATH` at line 29:
```python
LOG_PATH = Path(__file__).parent / "price_log.txt"
```

**This implementation satisfies all ACs.** Tasks are verify + write tests.

The orchestrator call site in `main()` (line 99):
```python
log_price(price, now)
```
Called exactly once per successful poll cycle — satisfies NFR-4.

### Key technical facts

- `open(LOG_PATH, "a", ...)` — Python's `"a"` mode auto-creates the file if absent and always appends. This satisfies both AC-2 and AC-4 in a single call.
- `encoding="utf-8"` is correct for cross-platform safety and for the ₹ symbol used in `send_toast()` (though `log_price` itself doesn't use ₹).
- `LOG_PATH` is a `Path` object — `open()` accepts `Path` directly in Python 3.6+; no need to call `str()`.
- `timestamp.strftime('%Y-%m-%d %H:%M')` produces `2026-07-17 10:30` — no seconds, which matches the spec format exactly.
- Tests must use a `tmp_path` fixture (pytest built-in) to write to a temporary file — never write to the real `price_log.txt`.
- Monkeypatch `price_tracker.LOG_PATH` to redirect writes to `tmp_path / "price_log.txt"` in each test.

### Test patterns (from Stories 2.1–3.1)

Monkeypatch `price_tracker.LOG_PATH` to a temp path, then read back and assert:

```python
from datetime import datetime
from pathlib import Path
import price_tracker

def test_log_price_writes_correct_format(monkeypatch, tmp_path):
    log_file = tmp_path / "price_log.txt"
    monkeypatch.setattr(price_tracker, "LOG_PATH", log_file)

    ts = datetime(2026, 7, 13, 10, 30, 0)
    price_tracker.log_price(231.45, ts)

    lines = log_file.read_text(encoding="utf-8").splitlines()
    assert lines == ["2026-07-13 10:30, 231.45"]
```

For the error isolation test, monkeypatch `builtins.open` to raise `IOError` when `price_log` is in the path (same pattern used in `test_orchestrator_loop.py`).

### Reference: line format verification

Given `price = 231.45`, `timestamp = datetime(2026, 7, 13, 10, 30, 0)`:
- Expected line: `"2026-07-13 10:30, 231.45"`

Given `price = 229.9`, `timestamp = datetime(2026, 7, 13, 15, 5, 0)`:
- Expected line: `"2026-07-13 15:05, 229.90"`

### Project structure notes

```
BMAD_Project/
  price_tracker.py      ← VERIFY: log_price() at lines 62–71, LOG_PATH at line 29
  price_log.txt         ← runtime output (not committed to VCS)
  bmad-output/
    implementation-artifacts/
      test_notify_adapter.py        ← reference for monkeypatch patterns
      test_orchestrator_loop.py     ← reference for builtins.open mock pattern
      3-2-log-adapter.md            ← this story
```

Test file to create: `bmad-output/implementation-artifacts/test_log_adapter.py`

### References

- Architecture Spine: `bmad-output/planning-artifacts/architecture/architecture-BMAD_Project-2026-07-16/ARCHITECTURE-SPINE.md` — AD-1, AD-4, AD-3
- Epics: `bmad-output/planning-artifacts/epics.md` — Story 3.2 (FR-4, AD-1, AD-4, NFR-4)
- Previous story: `bmad-output/implementation-artifacts/2-3-orchestrator-loop-retry.md` — `builtins.open` mock pattern for IOError test
- `price_tracker.py` lines 29, 62–71 — existing `LOG_PATH` and `log_price()` implementation

## Dev Agent Record

### Agent Model Used

aifs/claude-sonnet-4.6

### Debug Log References

None — existing implementation satisfied all ACs; no code changes required.

### Completion Notes List

- Verified `log_price()` at `price_tracker.py:62–71` satisfies all 6 ACs without modification.
- Confirmed line format, append mode, utf-8 encoding, try/except error isolation, and LOG_PATH all correct.
- Created `test_log_adapter.py` with 12 unit tests — all writes redirected to `tmp_path`, real `price_log.txt` never touched.
- Full regression suite: 55/55 passed, zero regressions.

### File List

- `price_tracker.py` — verified only, no changes needed
- `bmad-output/implementation-artifacts/test_log_adapter.py` — CREATED: 12 unit tests
- `bmad-output/implementation-artifacts/3-2-log-adapter.md` — updated tasks and status

### Change Log

- 2026-07-17: Story 3.2 implemented — verified log_price() against all ACs; created 12-test suite covering format/append/auto-create/error-isolation/NFR-4.
