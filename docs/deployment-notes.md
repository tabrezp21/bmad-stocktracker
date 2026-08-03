# Deployment Notes — Bank of Baroda Price Tracker & Alerter

## Target Environment

| Item | Requirement |
|---|---|
| OS | Windows 10 or Windows 11 (64-bit) |
| Python | CPython 3.10 or higher |
| Internet | Required during market hours (09:15–15:30 IST) |
| Notifications | Windows Action Center must be enabled |

## Pre-Deployment Checklist

- [ ] Python 3.10+ installed and on PATH
- [ ] Virtual environment created and activated
- [ ] `pip install -r requirements.txt` completed successfully
- [ ] `config.json` reviewed and threshold set to desired value
- [ ] Windows notification permissions granted for Python (`python.exe`)
- [ ] System clock confirmed set to IST (UTC+5:30)
- [ ] Internet connectivity verified

## Manual Run (Development / Testing)

```bash
# Activate virtual environment
.venv\Scripts\activate

# Optional: test with simulation mode first
# Set "simulation_mode": true and "test_price": 220 in config.json
# Note: if test_price is absent or null in simulation mode,
# the script logs a warning to stderr and skips the alert for that cycle.

python price_tracker.py
```

Expected output on first run (outside market hours):
```
# No output — script waits silently until market opens
```

Expected output during market hours:
```
# price_log.txt appended every 5 minutes
# Toast fires when price < threshold
```

## Running at Windows Startup (Optional — Post-MVP)

To run the tracker automatically when Windows starts:

1. Press `Win + R`, type `shell:startup`, press Enter.
2. Create a shortcut to `price_tracker.py` (or a `.bat` launcher) in the Startup folder.
3. In the shortcut properties, set **Start in** to the project directory.

Example `start_tracker.bat`:
```bat
@echo off
cd /d "C:\path\to\BMAD_Project"
call .venv\Scripts\activate
python price_tracker.py
```

> Note: Windows Task Scheduler is a more robust alternative for production use. See Microsoft documentation for setup.

## Environment Variables (None Required)

The script reads all configuration from `config.json`. No environment variables are needed.

## Log Management

`price_log.txt` grows at approximately **1 line per 5 minutes** during market hours (~75 lines/day, ~17 KB/month). No automatic rotation is implemented in MVP.

**Manual rotation:**
```bash
# Archive and reset the log
copy price_log.txt price_log_backup_YYYYMMDD.txt
del price_log.txt
```

> Log rotation policy is an open question (PRD §8, Q2) — to be addressed post-MVP.

## Dependency Versions

| Package | Minimum Version | Notes |
|---|---|---|
| `yfinance` | 0.2.x | Free tier; no API key required |
| `plyer` | 2.1.x | Windows toast via `notification.notify` |

Install exact versions for reproducibility:
```bash
pip freeze > requirements-lock.txt
```

## Known Limitations (MVP)

- Windows only — `plyer` toast is not cross-platform in this configuration
- No holiday calendar — only Saturday/Sunday are skipped
- Single ticker (`BANKBARODA.NS`) — multi-ticker is post-MVP
- No automatic log rotation
- No persistent background service registration (no Windows Service wrapper)

## Rollback

To revert to a previous state:
1. Stop the script (`Ctrl+C` or kill the terminal)
2. Restore `config.json` from backup if needed
3. Restart the script

No database or registry changes are made — rollback is simply stopping the process.
