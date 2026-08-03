---
baseline_commit: NO_VCS
---

# Story 4.1: Simulation Mode

Status: done

## Story

As a developer,
I want to run the script with a stubbed price so I can trigger and verify alerts without waiting for live market data,
So that I can test the full alert path locally at any time.

## Acceptance Criteria

1. **Given** `config.json` has `"simulation_mode": true` and `"test_price": 220`
   **When** `fetch_price()` is called
   **Then** it returns `220.0` without making any network call
   **And** the orchestrator triggers `send_toast()` (because 220 < 230 threshold)

2. **Given** `config.json` has `"simulation_mode": true` but `test_price` is absent or `null`
   **When** `fetch_price()` is called
   **Then** it returns `None` gracefully
   **And** it logs a warning to `stderr` (e.g. `"Simulation mode enabled but test_price is not set"`)
   **And** no network call is made

3. **Given** `config.json` has `"simulation_mode": false`
   **When** `fetch_price()` is called
   **Then** it uses the live `yfinance` network path (simulation branch is skipped entirely)

4. **Given** simulation mode is active
   **When** the orchestrator processes the returned test price
   **Then** it is completely unaware that a simulated value was returned — it behaves identically to a live price (AD-6)

## Tasks / Subtasks

- [x] Verify `fetch_price()` simulation branch in `price_tracker.py` satisfies AC-1, AC-3, AC-4
  - [x] Confirm `SIMULATION=True` + `TEST_PRICE is not None` → returns `float(TEST_PRICE)` with no network call (AC-1)
  - [x] Confirm `SIMULATION=False` → skips simulation branch entirely (AC-3)
  - [x] Confirm orchestrator call site in `main()` is unchanged — no simulation awareness (AC-4)
- [x] Fix gap: add warning + early return when `SIMULATION=True` but `TEST_PRICE is None` (AC-2)
  - [x] When `SIMULATION and TEST_PRICE is None` → print warning to `stderr`, return `None` immediately
  - [x] Ensure no `yfinance` call is made in this path
- [x] Write unit tests covering all ACs (AC: 1–4)
  - [x] `SIMULATION=True`, `TEST_PRICE=220` → returns `220.0`, no yfinance call (AC-1)
  - [x] `SIMULATION=True`, `TEST_PRICE=None` → returns `None`, warning logged to stderr, no yfinance call (AC-2)
  - [x] `SIMULATION=False` → yfinance path is taken (AC-3)
  - [x] Orchestrator calls `send_toast()` when simulated price < threshold (AC-4, end-to-end)

## Dev Notes

### Architecture Guardrails (MUST follow)

- **AD-6 (Simulation encapsulated in fetch adapter):** The simulation branch lives exclusively inside `fetch_price()`. The orchestrator (`main()`) must remain completely unaware of simulation state — it simply receives a float or None and acts accordingly.
- **AD-4 (Error isolation):** `fetch_price()` already has a try/except for the live path. The simulation early-return paths (AC-1, AC-2) are outside the try block — they return directly without needing error handling.
- **AD-1 (Layered Adapter):** Only `fetch_price()` touches `yfinance` or the simulation branch. The orchestrator must not check `SIMULATION` or `TEST_PRICE` directly.
- **AD-3 (Config boundary):** `SIMULATION` and `TEST_PRICE` come from module-level constants loaded from `config.json`. Never hardcode simulation values.

### What this story DOES and DOES NOT do

| In scope | Out of scope |
|---|---|
| Simulation branch in `fetch_price()` | Simulation in `log_price()` or `send_toast()` |
| Warning when `test_price` is missing | Multi-price simulation sequences |
| Unit tests for all simulation paths | End-to-end smoke test (Story 4.3) |
| Orchestrator unaware of simulation (AD-6) | Config file hot-reload |

### Existing code — current state (price_tracker.py lines 44–59)

```python
def fetch_price() -> float | None:
    """Fetch latest closing price for BANKBARODA.NS.
    Returns None on failure.
    """
    if SIMULATION and TEST_PRICE is not None:
        return float(TEST_PRICE)
    try:
        ticker = yf.Ticker("BANKBARODA.NS")
        hist = ticker.history(period="1d")
        if hist.empty:
            return None
        return float(hist["Close"].iloc[-1])
    except Exception as e:
        print(f"Error fetching price: {e}", file=sys.stderr)
        return None
```

**AC-1 satisfied:** `SIMULATION=True` + `TEST_PRICE is not None` → returns `float(TEST_PRICE)` ✅

**AC-2 GAP:** When `SIMULATION=True` but `TEST_PRICE is None`, the code falls through to the live yfinance path — it does NOT return `None` with a warning. This violates AC-2 and AD-6 (simulation leaks to network).

### Required fix for AC-2

Add an early return with warning immediately after the AC-1 check:

```python
def fetch_price() -> float | None:
    """Fetch latest closing price for BANKBARODA.NS.
    Returns None on failure.
    """
    if SIMULATION and TEST_PRICE is not None:
        return float(TEST_PRICE)
    if SIMULATION and TEST_PRICE is None:
        print("Simulation mode enabled but test_price is not set.", file=sys.stderr)
        return None
    try:
        ticker = yf.Ticker("BANKBARODA.NS")
        hist = ticker.history(period="1d")
        if hist.empty:
            return None
        return float(hist["Close"].iloc[-1])
    except Exception as e:
        print(f"Error fetching price: {e}", file=sys.stderr)
        return None
```

This ensures:
- `SIMULATION=True` + `TEST_PRICE is not None` → returns test price (AC-1)
- `SIMULATION=True` + `TEST_PRICE is None` → warns and returns None, no network call (AC-2)
- `SIMULATION=False` → falls through to yfinance path (AC-3)

### Key technical facts

- `SIMULATION` and `TEST_PRICE` are module-level constants — patch them with `monkeypatch.setattr(price_tracker, "SIMULATION", True)` in tests (same pattern as `test_fetch_adapter.py`).
- The `yfinance` call must be mocked in tests — never make a real network call. Use `monkeypatch.setattr(price_tracker.yf, "Ticker", ...)`.
- AC-4 (orchestrator unaware) is tested by verifying the orchestrator calls `send_toast()` when the simulated price is below threshold — the same flow as a real price.
- `config.json` in the project has `"test_price": 0` — note that `0` is falsy in Python but `is not None` is `True`. So `TEST_PRICE = 0.0` would trigger the simulation return path correctly. No issue here, but be aware.

### Test patterns (from test_fetch_adapter.py — established in Story 2.1)

```python
import price_tracker

def test_simulation_returns_test_price(monkeypatch):
    monkeypatch.setattr(price_tracker, "SIMULATION", True)
    monkeypatch.setattr(price_tracker, "TEST_PRICE", 220.0)
    assert price_tracker.fetch_price() == 220.0

def test_simulation_no_test_price_returns_none(monkeypatch, capsys):
    monkeypatch.setattr(price_tracker, "SIMULATION", True)
    monkeypatch.setattr(price_tracker, "TEST_PRICE", None)
    result = price_tracker.fetch_price()
    assert result is None
    assert "test_price is not set" in capsys.readouterr().err
```

### Project structure notes

```
BMAD_Project/
  price_tracker.py    ← UPDATE: add AC-2 warning + early return to fetch_price()
  config.json         ← reference only (simulation_mode, test_price keys)
  bmad-output/
    implementation-artifacts/
      test_fetch_adapter.py   ← reference for simulation monkeypatch patterns
      4-1-simulation-mode.md  ← this story
```

Test file to create: `bmad-output/implementation-artifacts/test_simulation_mode.py`

### References

- Architecture Spine: `bmad-output/planning-artifacts/architecture/architecture-BMAD_Project-2026-07-16/ARCHITECTURE-SPINE.md` — AD-6, AD-4, AD-1, AD-3
- Epics: `bmad-output/planning-artifacts/epics.md` — Story 4.1 (FR-6, AD-6)
- Story 2.1: `bmad-output/implementation-artifacts/2-1-fetch-adapter.md` — simulation test patterns
- `price_tracker.py` lines 44–59 — existing `fetch_price()` with gap at AC-2

## Dev Agent Record

### Agent Model Used

aifs/claude-sonnet-4.6

### Debug Log References

None — fix was a clean two-line addition; no unexpected issues.

### Completion Notes List

- Verified AC-1, AC-3, AC-4 already satisfied by existing `fetch_price()` implementation.
- Identified AC-2 gap: `SIMULATION=True` + `TEST_PRICE=None` was falling through to live yfinance (violation of AD-6).
- Fixed by adding early return guard in `fetch_price()` — prints warning to stderr, returns None immediately, no network call made.
- Created `test_simulation_mode.py` with 11 unit tests covering all 4 ACs including end-to-end orchestrator flow.
- Full regression suite: 66/66 passed, zero regressions.

### File List

- `price_tracker.py` — UPDATED: added AC-2 warning + early return guard to `fetch_price()`
- `bmad-output/implementation-artifacts/test_simulation_mode.py` — CREATED: 11 unit tests
- `bmad-output/implementation-artifacts/4-1-simulation-mode.md` — updated tasks and status

### Change Log

- 2026-07-17: Story 4.1 implemented — fixed AC-2 gap in fetch_price() simulation branch; created 11-test suite covering all simulation/live/orchestrator paths.
