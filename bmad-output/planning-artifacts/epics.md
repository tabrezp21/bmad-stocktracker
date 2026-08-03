---
stepsCompleted: [step-01-validate-prerequisites]
inputDocuments:
  - bmad-prd.md
  - bmad-output/planning-artifacts/architecture/architecture-BMAD_Project-2026-07-16/ARCHITECTURE-SPINE.md
  - README.md
  - docs/deployment-notes.md
---

# Bank of Baroda Price Tracker & Alerter - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for the Bank of Baroda Price Tracker & Alerter, decomposing the requirements from the PRD and Architecture Spine into implementable stories.

## Requirements Inventory

### Functional Requirements

FR-1: Fetch the current share price for `BANKBARODA.NS` via `yfinance` on every poll cycle during market hours.
FR-2: Enforce market time window — poll only on weekdays (Mon–Fri) between 09:15 and 15:30 IST.
FR-3: Display a native Windows toast notification when `price < threshold`, including price and timestamp.
FR-4: Append a timestamped line `YYYY-MM-DD HH:MM, {price}` to `price_log.txt` on every poll, regardless of alert state.
FR-5: Load all user-tunable values (`threshold`, `interval`, `simulation_mode`, `test_price`) from `config.json` — no hardcoded values in source.
FR-6: When `simulation_mode = true`, return `test_price` from config instead of making any network call.
FR-7: On any network/fetch failure, log the error to stderr, wait `CHECK_INTERVAL`, and retry — the main loop must never exit due to an adapter error.

### Non-Functional Requirements

NFR-1: Toast alert fires within 2 seconds of the triggering price check (≥95% of alert events).
NFR-2: Script runs continuously for a full market day without crashing (≥99% uptime, ~375 consecutive polls).
NFR-3: CPU usage stays below 5% of a single core during idle periods between polls.
NFR-4: `price_log.txt` contains exactly one entry per poll cycle with no duplicates or gaps.

### Additional Requirements

- AD-1 (Layered Adapter): All external I/O (`yfinance`, `plyer`, file writes) must live in dedicated adapter functions; orchestrator calls only pure functions and adapter interfaces — never a library directly.
- AD-2 (Runtime): Python ≥ 3.10, CPython, Windows 10/11 only.
- AD-3 (Config boundary): `config.json` is the single source of truth; no magic literals in source.
- AD-4 (Error isolation): Every adapter wraps its call in try/except and returns `None` on failure; the orchestrator handles `None` and retries.
- AD-5 (Scheduling ownership): `is_market_open()` guard lives exclusively in the orchestrator; adapters are stateless with respect to time.
- AD-6 (Simulation encapsulation): Simulation-mode branch is inside the fetch adapter only — the orchestrator is unaware of simulation state.
- Environment setup story required: virtual environment, `pip install -r requirements.txt`, clock set to IST.
- No starter template — single-file Python MVP (`price_tracker.py`).

### UX Design Requirements

N/A — this is a headless background script with no user interface. All user interaction is via `config.json` (input) and Windows toast + `price_log.txt` (output).

### FR Coverage Map

| FR / NFR | Epic | Story |
|---|---|---|
| FR-5, AD-2, AD-3 | Epic 1 | 1.1 Environment & Config Setup |
| FR-1, AD-1, AD-6 | Epic 2 | 2.1 Fetch Adapter |
| FR-2, AD-5 | Epic 2 | 2.2 Scheduler / Market-Hours Guard |
| FR-7, AD-4 | Epic 2 | 2.3 Error Handling & Retry Loop |
| FR-3, AD-1, AD-4, NFR-1 | Epic 3 | 3.1 Notify Adapter (Toast) |
| FR-4, AD-1, AD-4, NFR-4 | Epic 3 | 3.2 Log Adapter |
| FR-6, AD-6 | Epic 4 | 4.1 Simulation Mode |
| NFR-2, NFR-3 | Epic 4 | 4.2 Integration & Smoke Test |
| AD-2, docs | Epic 5 | 5.1 README & Deployment Notes |

## Epic List

1. **Epic 1 — Environment & Project Setup**: Establish a reproducible Python environment and validated configuration loader.
2. **Epic 2 — Core Polling Engine**: Implement the fetch adapter, market-hours scheduler, orchestrator loop, and retry logic.
3. **Epic 3 — Output Adapters**: Implement the Windows toast notifier and the price log writer.
4. **Epic 4 — Simulation, Testing & Validation**: Wire simulation mode, write unit tests, and run an end-to-end smoke test.
5. **Epic 5 — Documentation & Deployment**: Finalise README and deployment notes; validate the script is runnable on a clean Windows machine.

---

## Epic 1: Environment & Project Setup

Establish a reproducible, validated Python environment and a working configuration loader so all subsequent epics build on a stable foundation.

### Story 1.1: Environment Setup & Dependency Installation

As a developer,
I want a documented, reproducible virtual environment with all dependencies installed,
So that any contributor can run the project from a clean Windows machine without manual guesswork.

**Acceptance Criteria:**

**Given** a clean Windows 10/11 machine with Python 3.10+ installed
**When** the developer runs `python -m venv .venv && .venv\Scripts\activate && pip install -r requirements.txt`
**Then** all packages install without error and `python -c "import yfinance, plyer"` exits with code 0
**And** `requirements.txt` lists `yfinance` and `plyer` (no pinned conflicts)

### Story 1.2: Configuration Loader

As a developer,
I want a `load_config()` function that reads `config.json` and returns validated values,
So that all tunables come from one place and no magic literals appear in the source.

**Acceptance Criteria:**

**Given** a valid `config.json` with keys `threshold`, `simulation_mode`, `test_price`
**When** `load_config()` is called
**Then** it returns a dict with correct types (`threshold` as float, `simulation_mode` as bool, `test_price` as float)
**And** missing optional keys (`test_price`) default gracefully without raising an exception

**Given** `config.json` is absent or malformed
**When** `load_config()` is called
**Then** the script prints a clear error message to stderr and exits with a non-zero code

---

## Epic 2: Core Polling Engine

Implement the three core behaviours that drive the main loop: price fetching, market-hours enforcement, and fault-tolerant retry.

### Story 2.1: Fetch Adapter

As the orchestrator,
I want a `fetch_price(config)` adapter function that returns the latest close price for `BANKBARODA.NS`,
So that price retrieval is isolated from scheduling and alert logic.

**Acceptance Criteria:**

**Given** a live internet connection and market data available
**When** `fetch_price(config)` is called with `simulation_mode = false`
**Then** it calls `yfinance.Ticker("BANKBARODA.NS").history(period="1d")`, extracts the latest "Close" value, and returns it as a float
**And** it does not call any notification or logging function

**Given** `yfinance` returns an empty DataFrame or raises an exception
**When** `fetch_price(config)` is called
**Then** it logs the error to stderr and returns `None`
**And** no exception propagates to the caller

### Story 2.2: Market-Hours Scheduler

As the orchestrator,
I want an `is_market_open(now: datetime) -> bool` function,
So that the poll loop skips all fetches outside 09:15–15:30 IST on weekdays.

**Acceptance Criteria:**

**Given** `now` is a weekday datetime between 09:15 and 15:30
**When** `is_market_open(now)` is called
**Then** it returns `True`

**Given** `now` is a Saturday, Sunday, or outside 09:15–15:30
**When** `is_market_open(now)` is called
**Then** it returns `False`
**And** the orchestrator loop sleeps for `CHECK_INTERVAL` and does not call `fetch_price`

### Story 2.3: Orchestrator Loop & Retry

As a user,
I want the script to keep running and retrying after network failures,
So that a temporary outage does not require me to manually restart the script.

**Acceptance Criteria:**

**Given** `fetch_price()` returns `None` (network failure)
**When** the orchestrator processes the result
**Then** it logs "Failed to retrieve price; will retry." to stderr, waits `CHECK_INTERVAL`, and calls `fetch_price()` again on the next cycle
**And** the loop continues indefinitely — no `sys.exit()` is called

**Given** the script has been running for a full simulated market day (≥375 cycles in simulation)
**When** no unhandled exceptions occur
**Then** the process is still alive and `price_log.txt` contains one entry per cycle (NFR-2, NFR-4)

---

## Epic 3: Output Adapters

Implement the two output side-effects: the Windows toast alert and the persistent price log.

### Story 3.1: Notify Adapter (Windows Toast)

As an investor,
I want a Windows toast notification when the price drops below my threshold,
So that I am alerted immediately without watching the terminal.

**Acceptance Criteria:**

**Given** `price < threshold`
**When** `send_toast(price, threshold)` is called
**Then** a Windows toast appears with the title "Bank of Baroda Price Alert" and message "Price dropped to ₹{price:.2f} (target ₹{threshold})"
**And** the toast fires within 2 seconds of the price check (NFR-1)

**Given** `price >= threshold`
**When** the orchestrator evaluates the price
**Then** `send_toast` is NOT called

**Given** `plyer` raises an exception (e.g. notifications disabled)
**When** `send_toast` is called
**Then** the error is logged to stderr and the orchestrator loop continues — no crash (AD-4)

### Story 3.2: Log Adapter

As a user,
I want every price check appended to `price_log.txt`,
So that I have a permanent record of all checks for review.

**Acceptance Criteria:**

**Given** a successful price fetch
**When** `log_price(price, timestamp)` is called
**Then** a line in the format `YYYY-MM-DD HH:MM, {price:.2f}` is appended to `price_log.txt`
**And** exactly one line is written per poll cycle — no duplicates (NFR-4)

**Given** `price_log.txt` does not yet exist
**When** `log_price` is called for the first time
**Then** the file is created automatically

**Given** `log_price` raises an IOError
**When** the error is caught
**Then** it is logged to stderr and the orchestrator loop continues without crashing (AD-4)

---

## Epic 4: Simulation, Testing & Validation

Wire simulation mode for safe local testing, write unit tests for all adapter functions, and run an integration smoke test.

### Story 4.1: Simulation Mode

As a developer,
I want to run the script with a stubbed price so I can trigger and verify alerts without waiting for live market data,
So that I can test the full alert path locally at any time.

**Acceptance Criteria:**

**Given** `config.json` has `"simulation_mode": true` and `"test_price": 220`
**When** `fetch_price(config)` is called
**Then** it returns `220.0` without making any network call
**And** the orchestrator triggers `send_toast` (because 220 < 230 threshold)

**Given** `config.json` has `"simulation_mode": true` but `test_price` is absent
**When** `fetch_price(config)` is called
**Then** it returns `None` gracefully and logs a warning to stderr

### Story 4.2: Unit Tests

As a developer,
I want unit tests for each adapter and the scheduler,
So that regressions are caught before manual testing.

**Acceptance Criteria:**

**Given** the test suite is run with `pytest`
**When** all tests pass
**Then** the following are covered with passing tests:
- `load_config()` — valid config, missing file, malformed JSON
- `fetch_price()` — simulation mode returns `test_price`; yfinance error returns `None`
- `is_market_open()` — weekday in-window (True), weekend (False), outside hours (False)
- `log_price()` — correct line format appended to a temp file
- `send_toast()` — called when `price < threshold`; NOT called when `price >= threshold`
**And** no test makes a live network call (all external calls mocked)

### Story 4.3: End-to-End Smoke Test

As a user,
I want to verify the script runs for at least 2 full poll cycles in simulation mode without crashing,
So that I have confidence it will survive a full market day.

**Acceptance Criteria:**

**Given** `simulation_mode = true`, `test_price = 220`, `threshold = 230`, and `CHECK_INTERVAL` reduced to 2 seconds for the test
**When** the script runs for 2 poll cycles
**Then** `price_log.txt` contains exactly 2 entries
**And** a toast was triggered on each cycle (220 < 230)
**And** no unhandled exceptions were raised

---

## Epic 5: Documentation & Deployment

Finalise all user-facing documentation and verify the script is deployable on a clean Windows machine.

### Story 5.1: README

As a new user,
I want a clear README that explains installation, configuration, and usage,
So that I can set up and run the tracker without asking for help.

**Acceptance Criteria:**

**Given** `README.md` exists in the project root
**When** a new user reads it
**Then** it contains: project overview, prerequisites, installation steps, configuration reference, usage instructions, log format description, and a troubleshooting table
**And** all commands in the README execute successfully on a clean Windows 10/11 machine with Python 3.10+

### Story 5.2: Deployment Notes

As a developer or maintainer,
I want documented deployment steps including optional startup configuration,
So that the tracker can be reliably deployed and handed over.

**Acceptance Criteria:**

**Given** `docs/deployment-notes.md` exists
**When** a maintainer follows the steps
**Then** the document covers: target environment, pre-deployment checklist, manual run instructions, optional Windows startup configuration, log management guidance, known MVP limitations, and rollback procedure
**And** no step requires undocumented prior knowledge
