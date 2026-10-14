# Multi-Company Stock Price Tracker & Alerter

A lightweight Python utility that monitors real-time share prices for a configurable list of companies across Indian (NSE/BSE) and US (NASDAQ/NYSE) markets — such as TCS, Infosys, HDFC Bank, Bank of Baroda, Nvidia, and Apple — and sends a native Windows toast notification when any tracked price falls below its per-company threshold.

## Features

- Tracks multiple companies simultaneously — each with its own ticker, threshold, and market
- Supports both **IN** (NSE/BSE) and **US** (NASDAQ/NYSE) markets with correct timezone handling
- US market DST handled automatically via `ZoneInfo("America/New_York")` — no manual updates needed
- Configurable poll interval via `check_interval_seconds` (default 60s)
- Runs only during each market's trading hours (skips closed markets silently)
- Fetches the most accurate live price using 1-minute intraday data, with a daily-close fallback
- Sends a Windows toast alert (with INR/USD currency label) when price drops below the company's threshold
- Appends a timestamped record to a **per-company** log file on every poll
- Gracefully retries on network failures without crashing
- Simulation mode for local testing without a live market connection

## Requirements

- Windows 10 or 11
- Python 3.10 or higher
- Internet connection during market hours

## Installation

```bash
# 1. Clone or download the project
# 2. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

## Configuration

Edit `config.json` before running:

```json
{
  "simulation_mode": false,
  "check_interval_seconds": 60,
  "companies": [
    {
      "company_name": "Bank of Baroda",
      "ticker": "BANKBARODA.NS",
      "market": "IN",
      "threshold": 250,
      "test_price": 220
    },
    {
      "company_name": "Nvidia Corporation",
      "ticker": "NVDA",
      "market": "US",
      "threshold": 235.00,
      "test_price": 235
    }
  ]
}
```

### Top-level keys

| Key | Type | Default | Description |
|---|---|---|---|
| `simulation_mode` | boolean | `false` | Set `true` to test alerts without live price fetches |
| `check_interval_seconds` | number | `10` (code fallback) | Seconds between poll cycles (set explicitly in config) |
| `companies` | array | — | List of company entries to track (must not be empty) |

### Per-company keys (each entry in `companies`)

| Key | Type | Required | Description |
|---|---|---|---|
| `company_name` | string | yes | Display name shown in toasts and logs |
| `ticker` | string | yes | yfinance ticker symbol (e.g. `BANKBARODA.NS`, `NVDA`) |
| `market` | string | yes | `"IN"` or `"US"` — selects market hours and currency |
| `threshold` | number | yes | Alert fires when price drops below this value |
| `test_price` | number | no | Price returned when `simulation_mode` is `true` |

> **Note:** When `simulation_mode` is `true`, each company you want to test must have `test_price` set to a meaningful value below its `threshold` for the alert to fire. If `test_price` is absent/`null` for a company in simulation mode, the script logs a warning to stderr and returns no price for that cycle — no alert fires for that company.

### Market hours

| Market | Trading hours | Timezone |
|---|---|---|
| IN (NSE/BSE) | 09:15 – 15:30, Monday–Friday | Asia/Kolkata (IST) |
| US (NASDAQ/NYSE) | 09:30 – 16:00, Monday–Friday | America/New_York (ET, DST auto) |

The tracker skips any company whose market is currently closed and retries it on the next cycle.

## Usage

```bash
python price_tracker.py
```

The script will:
1. Load `config.json` from the same directory and validate every company entry
2. Print the list of tracked companies
3. On each cycle, for every company whose market is open: fetch the price, log it, and send a toast if price < threshold
4. Sleep for `check_interval_seconds`, then repeat
5. Retry silently on any network error

Stop the script at any time with `Ctrl+C`.

## Log Files

Each poll appends one line to a **per-company** log file named `price_log_{ticker}.txt`, where `.` in the ticker is replaced with `_` (e.g. `BANKBARODA.NS` → `price_log_BANKBARODA_NS.txt`, `NVDA` → `price_log_NVDA.txt`):

```
2026-07-16 10:15, Bank of Baroda, 231.45
2026-07-16 10:16, Nvidia Corporation, 234.80
```

## Project Structure

```
BMAD_Project/
  price_tracker.py        # Main script
  config.json             # User configuration (companies, thresholds, interval)
  requirements.txt        # Python dependencies
  price_log_{ticker}.txt  # Per-company runtime price logs (auto-created)
  README.md               # This file
  bmad-prd.md             # Product Requirements Document
  bmad-brief.md           # Product Brief
  bmad-output/            # Planning and implementation artifacts
  docs/                   # Deployment notes and documentation
```

## Running Tests

With the virtual environment activated:

```powershell
pip install pytest   # only needed once
pytest bmad-output/implementation-artifacts/
```

Expected output: `70 passed` (no failures).

## Troubleshooting

| Problem | Solution |
|---|---|
| No toast appears | Ensure Windows notification permissions are enabled for Python |
| `yfinance` returns no data | Market may be closed; check market hours and internet connection |
| Script exits at startup | Check `stderr` — usually a missing/invalid `ticker`, `company_name`, `threshold`, or `market` in `config.json` |
| Wrong price threshold | Edit the company's `threshold` in `config.json` and restart the script |
| Simulation mode not alerting | Ensure that company's `test_price` is a number below its `threshold` in `config.json` |
| US alerts fire at wrong times | Expected during DST transitions — handled automatically; verify system clock/timezone is correct |
