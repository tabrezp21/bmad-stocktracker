---
baseline_commit: NO_VCS
---

# Story 4.3: End-to-End Smoke Test

Status: done

## Story

As a user,
I want to verify the script runs for at least 2 full poll cycles in simulation mode without crashing,
So that I have confidence it will survive a full market day.

## Acceptance Criteria

1. **Given** `simulation_mode=true`, `test_price=220`, `threshold=230`, and `CHECK_INTERVAL` reduced to 2 seconds for the test
   **When** the script runs for 2 poll cycles
   **Then** `price_log.txt` contains exactly 2 entries

2. **Given** the same configuration
   **When** 2 poll cycles complete
   **Then** a toast was triggered on each cycle (220 < 230)

3. **Given** the same configuration
   **When** 2 poll cycles complete
   **Then** no unhandled exceptions were raised

4. **Given** the script is run during market hours (or with a mocked datetime)
   **When** 2 poll cycles complete
   **Then** the `price_log.txt` entries are in the correct format `YYYY-MM-DD HH:MM, 220.00`

## Tasks / Subtasks

- [x] Write a smoke test in `test_smoke.py` that exercises the full `main()` loop end-to-end (AC: 1–4)
  - [x] Patch `SIMULATION=True`, `TEST_PRICE=220.0`, `THRESHOLD=230.0` (AC: 1, 2)
  - [x] Patch `CHECK_INTERVAL` to 0 to avoid real sleeps (AC: 1, 2, 3)
  - [x] Patch `datetime.now()` to return a market-open weekday time (AC: 1, 4)
  - [x] Patch `notification.notify` to capture toast calls without real system notification (AC: 2)
  - [x] Redirect `LOG_PATH` to `tmp_path` to capture log entries without touching real file (AC: 1, 4)
  - [x] Break the loop after exactly 2 cycles using `time.sleep` side_effect (AC: 1, 2, 3)
  - [x] Assert `price_log.txt` has exactly 2 lines (AC: 1)
  - [x] Assert each line matches `YYYY-MM-DD HH:MM, 220.00` format (AC: 4)
  - [x] Assert toast was called exactly 2 times (AC: 2)
  - [x] Assert no exception propagated (AC: 3)

## Dev Notes

### Architecture Guardrails (MUST follow)

- **AD-6 (Simulation):** `SIMULATION=True` and `TEST_PRICE=220.0` must be set — no yfinance calls.
- **AD-4 (Error isolation):** The smoke test must verify the loop survives 2 full cycles without any exception reaching `main()`.
- **AD-1 (Layered Adapter):** Test exercises the full stack — config globals → orchestrator → fetch adapter → log adapter → notify adapter — without touching the real OS (no real toasts, no real file writes outside tmp_path).
- **AD-5 (Scheduling ownership):** Market-open datetime must be injected so `is_market_open()` returns `True` for both cycles.

### What this story DOES and DOES NOT do

| In scope | Out of scope |
|---|---|
| 2-cycle end-to-end smoke via `main()` | 375-cycle full-day endurance test |
| `price_log.txt` content verification | Real Windows toast firing |
| Toast call count verification | Real yfinance network call |
| No unhandled exceptions | Performance / CPU benchmarks |
| Format verification of log entries | Multi-ticker or multi-config scenarios |

### Key design decisions for the smoke test

**Breaking the infinite loop:**
Use `time.sleep` side_effect to count calls and raise `SystemExit` after the Nth call.
Each successful market-open cycle calls `time.sleep` exactly once (end of loop).
So to run exactly 2 cycles: raise `SystemExit` on the 3rd sleep call.

```python
sleep_calls = {"n": 0}
def fake_sleep(s):
    sleep_calls["n"] += 1
    if sleep_calls["n"] >= 3:
        raise SystemExit(0)
monkeypatch.setattr(price_tracker.time, "sleep", fake_sleep)
```

**Why 3rd sleep = 2 cycles:**
- Cycle 1: fetch → log → toast → sleep (call #1) → continue
- Cycle 2: fetch → log → toast → sleep (call #2) → continue
- Cycle 3: fetch → log → toast → sleep (call #3) → SystemExit raised

**Redirecting LOG_PATH:**
```python
log_file = tmp_path / "price_log.txt"
monkeypatch.setattr(price_tracker, "LOG_PATH", log_file)
```

**Injecting market-open time:**
```python
monday = datetime(2026, 7, 13, 10, 0, 0)
monkeypatch.setattr(
    "price_tracker.datetime",
    type("FakeDT", (), {"now": staticmethod(lambda: monday)})
)
```

**Capturing toast calls:**
```python
toast_calls = []
monkeypatch.setattr(
    price_tracker.notification, "notify",
    lambda **kwargs: toast_calls.append(kwargs)
)
```

**Setting CHECK_INTERVAL to 0:**
```python
monkeypatch.setattr(price_tracker, "CHECK_INTERVAL", 0)
```

### Full smoke test structure

```python
def test_two_cycle_smoke(monkeypatch, tmp_path):
    # 1. Simulation config
    monkeypatch.setattr(price_tracker, "SIMULATION", True)
    monkeypatch.setattr(price_tracker, "TEST_PRICE", 220.0)
    monkeypatch.setattr(price_tracker, "THRESHOLD", 230.0)
    monkeypatch.setattr(price_tracker, "CHECK_INTERVAL", 0)

    # 2. Market-open datetime
    monday = datetime(2026, 7, 13, 10, 0, 0)
    monkeypatch.setattr(
        "price_tracker.datetime",
        type("FakeDT", (), {"now": staticmethod(lambda: monday)})
    )

    # 3. Redirect log file
    log_file = tmp_path / "price_log.txt"
    monkeypatch.setattr(price_tracker, "LOG_PATH", log_file)

    # 4. Capture toast calls
    toast_calls = []
    monkeypatch.setattr(
        price_tracker.notification, "notify",
        lambda **kwargs: toast_calls.append(kwargs)
    )

    # 5. Break after 2 complete cycles (3rd sleep)
    sleep_calls = {"n": 0}
    def fake_sleep(s):
        sleep_calls["n"] += 1
        if sleep_calls["n"] >= 3:
            raise SystemExit(0)
    monkeypatch.setattr(price_tracker.time, "sleep", fake_sleep)

    # 6. Run
    try:
        price_tracker.main()
    except SystemExit:
        pass

    # 7. Assertions
    lines = log_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2                          # AC-1
    assert len(toast_calls) == 2                    # AC-2
    for line in lines:
        assert "220.00" in line                     # AC-4
        assert "2026-07-13 10:00" in line           # AC-4
```

### Test patterns (from prior stories)

All monkeypatch patterns established in `test_orchestrator_loop.py` and `test_simulation_mode.py` apply directly. No new patterns needed.

### Important: `CHECK_INTERVAL` in sleep calls

When `CHECK_INTERVAL=0`, `time.sleep(0)` is called — this is valid Python. The `fake_sleep` function receives `0` as the argument and still increments the counter. This correctly simulates the loop timing without real delays.

### Project structure notes

```
BMAD_Project/
  price_tracker.py     ← no changes needed
  bmad-output/
    implementation-artifacts/
      test_orchestrator_loop.py   ← reference for loop-breaking pattern
      test_log_adapter.py         ← reference for tmp_path LOG_PATH pattern
      test_notify_adapter.py      ← reference for notification mock pattern
      4-3-end-to-end-smoke-test.md ← this story
```

Test file to create: `bmad-output/implementation-artifacts/test_smoke.py`

### References

- Epics: `bmad-output/planning-artifacts/epics.md` — Story 4.3 (NFR-2, NFR-4)
- `price_tracker.py` lines 86–110 — `main()` loop (target of smoke test)
- `test_orchestrator_loop.py` — loop-breaking with `SystemExit` pattern
- `test_log_adapter.py` — `tmp_path` + `LOG_PATH` redirect pattern
- `test_notify_adapter.py` — `notification.notify` mock pattern

## Dev Agent Record

### Agent Model Used

aifs/claude-sonnet-4.6

### Debug Log References

Fixed off-by-one in `_break_after_n_cycles` helper: initial `> n` condition produced n+1 cycles instead of n. Corrected to `>= n` — all 4 tests then passed immediately.

### Completion Notes List

- Created `test_smoke.py` with 4 end-to-end smoke tests exercising the full adapter stack through `main()`.
- Fixed off-by-one in loop-breaking helper (`> n` → `>= n`).
- No changes to `price_tracker.py` — smoke confirmed the existing implementation is correct end-to-end.
- Full regression suite: 70/70 passed, zero regressions.

### File List

- `price_tracker.py` — verified only, no changes needed
- `bmad-output/implementation-artifacts/test_smoke.py` — CREATED: 4 smoke tests
- `bmad-output/implementation-artifacts/4-3-end-to-end-smoke-test.md` — updated tasks and status

### Change Log

- 2026-07-17: Story 4.3 implemented — created 4-test end-to-end smoke suite; verified full adapter stack integration; fixed off-by-one in loop-break helper; 70/70 tests green.
