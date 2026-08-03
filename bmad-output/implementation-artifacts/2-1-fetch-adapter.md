---
baseline_commit: NO_VCS
---

# Story 2.1: Fetch Adapter

Status: done

## Story

As a developer,
I want a robust fetch adapter that retrieves the latest price for BANKBARODA.NS and supports simulation mode,
So that the core polling engine can obtain price data without being coupled to external services.

## Acceptance Criteria

1. **Given** `simulation_mode` is `true` and `test_price` is set in `config.json`
   **When** `fetch_price()` is called
   **Then** it returns `float(test_price)` without making any network request.

2. **Given** `simulation_mode` is `false`
   **When** `fetch_price()` is called
   **Then** it queries Yahoo Finance via `yfinance.Ticker("BANKBARODA.NS")` and returns the most recent close price as a float.

3. **Given** a network or API error occurs
   **When** `fetch_price()` encounters an exception
   **Then** it logs the error to `stderr` and returns `None`.

4. **Given** the function returns a valid price
   **When** the price is logged by `log_price()`
   **Then** a line `YYYY-MM-DD HH:MM, <price>` is appended to `price_log.txt`.

5. **Given** the fetched price is below the configured `threshold`
   **When** the main loop processes the price
   **Then** a Windows toast notification is sent via `send_toast()`.

## Tasks / Subtasks

- [x] Verify `fetch_price()` returns simulated price when `SIMULATION` is enabled.
- [x] Verify real fetch via `yfinance` returns a non‑None float.
- [x] Add unit tests for simulation branch and real fetch (mock `yfinance`).
- [x] Ensure error handling returns `None` on exception.
- [x] Document adapter responsibilities in `price_tracker.py` comments.

## Dev Notes

### Architecture Guardrails (must follow)

- **AD-1 (Layered Adapter):** All external data access must be encapsulated in the fetch adapter; the orchestrator loop must not call `yfinance` directly.
- **AD-6 (Simulation Mode):** Simulation logic must reside entirely within this adapter; the orchestrator should be unaware of simulation state.

### Existing files to check (do not overwrite)

- `price_tracker.py` — contains the current implementation of `fetch_price()`.
- `config.json` — holds `simulation_mode` and `test_price` flags.
- `requirements.txt` — must include `yfinance`.

## Dev Agent Record

### Agent Model Used

aifs/claude-sonnet-4.6
