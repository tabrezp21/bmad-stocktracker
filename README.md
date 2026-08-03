# Bank of Baroda Price Tracker & Alerter

A lightweight Python utility that monitors the real-time share price of Bank of Baroda (`BANKBARODA.NS`) and sends a native Windows toast notification when the price falls below a configurable threshold.

## Features

- Polls the latest price every 5 minutes via `yfinance`
- Runs only during Indian market hours (09:15–15:30 IST, Monday–Friday)
- Sends a Windows toast alert when price drops below the threshold (default ₹230)
- Appends a timestamped record to `price_log.txt` on every poll
- Gracefully retries on network failures without crashing
- Fully configurable via `config.json` — no code changes needed
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
  "threshold": 230,
  "simulation_mode": false,
  "test_price": 220
}
```

| Key | Type | Description |
|---|---|---|
| `threshold` | number | Alert fires when price drops below this value (INR) |
| `simulation_mode` | boolean | Set `true` to test alerts without a live price fetch |
| `test_price` | number | Price returned when `simulation_mode` is `true` — must be a valid number |

> **Note:** When `simulation_mode` is `true`, `test_price` must be set to a meaningful price value (e.g. `220`).
> If `test_price` is absent or `null`, the script logs a warning to stderr and returns no price for that cycle — no alert will fire.

## Usage

```bash
python price_tracker.py
```

The script will:
1. Load `config.json` from the same directory
2. Wait for market hours if started outside 09:15–15:30 IST on a weekday
3. Poll the price every 5 minutes and append to `price_log.txt`
4. Display a Windows toast notification if the price drops below the threshold
5. Retry silently after 5 minutes on any network error

Stop the script at any time with `Ctrl+C`.

## Log File

Each poll appends one line to `price_log.txt`:

```
2026-07-16 10:15, 231.45
2026-07-16 10:20, 229.80
```

## Project Structure

```
BMAD_Project/
  price_tracker.py      # Main script
  config.json           # User configuration
  requirements.txt      # Python dependencies
  price_log.txt         # Runtime price log (auto-created)
  README.md             # This file
  bmad-prd.md           # Product Requirements Document
  bmad-brief.md         # Product Brief
  bmad-output/          # Planning and implementation artifacts
  docs/                 # Deployment notes and documentation
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
| Script exits unexpectedly | Check `stderr` output for unhandled errors; open an issue |
| Wrong price threshold | Edit `threshold` in `config.json` and restart the script |
| Simulation mode not alerting | Ensure `test_price` is set to a number below `threshold` in `config.json` |
