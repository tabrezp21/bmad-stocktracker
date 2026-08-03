---
title: Bank of Baroda Price Tracker & Alerter
created: 2026-07-15
updated: 2026-07-15
---

# PRD: Bank of Baroda Price Tracker & Alerter
*Working title — confirm.*

## 0. Document Purpose
This PRD is for the product manager, developers, and downstream stakeholders responsible for building a lightweight Python utility that monitors the real‑time share price of Bank of Baroda (ticker `BANKBARODA.NS`) and notifies the user via a native Windows toast when the price falls below a configurable threshold. It outlines the vision, target user, functional requirements, scope, and success criteria for the MVP.

## 1. Vision
Create a reliable, low‑maintenance script that runs continuously during Indian market hours, polls the latest price every five minutes, logs each check, and immediately alerts the user with a Windows toast if the price drops below a user‑defined threshold (default ₹230). The tool should be simple to configure, tolerant of transient network failures, and extensible for future tickers or alert channels.

## 2. Target User

### 2.1 Jobs To Be Done
- **Investor monitoring:** I need to be warned the moment a share price dips below my buy‑point so I can act quickly.
- **Casual watcher:** I want a set‑and‑forget script that runs in the background during market hours without manual intervention.

### 2.2 Non‑Users (v1)
- Users on non‑Windows platforms.
- Users requiring multi‑ticker tracking or complex alert routing (e.g., Slack, email).
- Users needing holiday‑aware scheduling beyond simple weekend skips.

### 2.3 Key User Journeys
- **UJ‑1. Price Drop Alert**
  - **Persona + context:** An individual investor on a Windows PC, market‑open, running the script.
  - **Entry state:** Script is started and the config file sets `threshold: 230`.
  - **Path:** Every 5 min the script fetches the current price via `yfinance`; price is compared to the threshold.
  - **Climax:** When price < 230, a Windows toast pops up displaying the price and timestamp.
  - **Resolution:** User sees the toast, can manually act (e.g., place a trade). Script continues monitoring.
  - **Edge case:** If `yfinance` returns `None` or an empty response, the script logs the failure, waits 5 min, and retries without crashing.

## 3. Glossary
- **Ticker:** The market symbol for a security (`BANKBARODA.NS`).
- **Threshold:** The price (in INR) below which an alert must be generated.
- **IST:** Indian Standard Time (UTC+5:30).
- **Toast Notification:** A native Windows OS popup used for transient alerts.

## 4. Features

### 4.1 Data Sourcing
**Description:** Pull the latest price for `BANKBARODA.NS` using the free `yfinance` library.

**Functional Requirements:**

#### FR‑1: Fetch Current Price
Investor can retrieve the current share price from Yahoo Finance every 5 minutes during market hours.

**Consequences (testable):**
- The script calls `yfinance.Ticker("BANKBARODA.NS").history(period="1d")` and extracts the latest "Close" value.
- If the API call fails or returns no data, the script logs an error and retries after 5 minutes.

**Out of Scope:**
- Historical price analysis beyond the most recent price.

### 4.2 Scheduling & Market Hours
**Description:** Run a loop that sleeps for 5 minutes between polls, but only between 09:15 AM and 03:30 PM IST, Monday‑Friday.

**Functional Requirements:**

#### FR‑2: Time‑Window Enforcement
System must poll only when the current local time is within the defined market window and the day is a weekday.

**Consequences (testable):**
- The script checks `datetime.now().weekday()` (0‑4) and `datetime.time` bounds before each fetch.

### 4.3 Alert Channel
**Description:** Emit a native Windows toast using `plyer` when the price falls below the threshold.

**Functional Requirements:**

#### FR‑3: Threshold Alert
When `price < threshold`, the script must display a toast with the message: "Bank of Baroda price dropped to ₹{price} (target ₹{threshold})."

**Consequences (testable):**
- Toast appears within 2 seconds of price check.
- The toast includes the timestamp of the check.

**Out of Scope:**
- Alternative channels (email, Slack, SMS).

### 4.4 Persistence
**Description:** Append a timestamped entry to `price_log.txt` after each check.

**Functional Requirements:**

#### FR‑4: Logging
System must write a line `YYYY‑MM‑DD HH:MM, {price}` to `price_log.txt` for every poll, regardless of alert state.

**Consequences (testable):**
- Log file grows linearly; each line matches the format.

### 4.5 Configuration
**Description:** Read `config.json` from the script directory to obtain `threshold` and optional `simulation_mode`.

**Functional Requirements:**

#### FR‑5: Configurable Threshold
User can set `"threshold": 230` in `config.json` to change the alert level without code changes.

#### FR‑6: Simulation Mode
When `"simulation_mode": true`, the script uses a stubbed price value defined in `"test_price"` to force an alert for testing.

**Out of Scope:**
- Dynamic reloading of config while the script runs.

### 4.6 Error Handling
**Description:** Gracefully handle network failures.

**Functional Requirements:**

#### FR‑7: Retry on Failure
If a network error occurs, the script must wait 5 minutes and retry indefinitely without exiting.

**Consequences (testable):**
- No unhandled exceptions propagate to the console.
- Retry count is not limited.

## 5. Non‑Goals (Explicit)
- Multi‑ticker support.
- Holiday calendar beyond Saturday/Sunday.
- Cross‑platform notifications (macOS/Linux).
- Persistent background service registration (e.g., Windows Task Scheduler).
- GUI or web interface.

## 6. MVP Scope

### 6.1 In Scope
- All features listed in §4 (FR‑1 through FR‑7).
- `requirements.txt` containing `yfinance`, `plyer`, `requests`.
- Plain Python source file (`price_tracker.py`).
- `config.json` with `threshold`, `simulation_mode`, optional `test_price`.
- Human‑readable `price_log.txt`.

### 6.2 Out of Scope for MVP
- Support for additional tickers.
- Holiday calendar beyond weekend check.
- Alternative notification channels (email, Slack, etc.).
- Packaging as an executable or Docker container.
- Advanced resource‑limiting or async I/O.

## 7. Success Metrics

**Primary**
- **SM‑1:** Alert fires within 2 seconds of price check when price < threshold (≥ 95 % of such events during a test run).
- **SM‑2:** Script runs continuously for a full market day without crashing (≥ 99 % uptime).

**Secondary**
- **SM‑3:** `price_log.txt` contains exactly one entry per poll (5‑minute intervals) for a given market day.

**Counter‑metrics**
- **SM‑C1:** CPU usage stays below 5 % of a single core during idle periods.

## 8. Open Questions
1. Should the toast include a clickable action (e.g., open a browser to a trading platform)?
2. Desired log file rotation policy after the file reaches a certain size?

## 9. Assumptions Index
- `[ASSUMPTION]` Host machine’s system clock is set to IST.
- `[ASSUMPTION]` User runs the script on Windows 10/11 where `plyer` can display toasts.
- `[ASSUMPTION]` Network connectivity is generally stable; transient failures are rare.
- `[ASSUMPTION]` `yfinance` remains free and functional for the required ticker.

---
