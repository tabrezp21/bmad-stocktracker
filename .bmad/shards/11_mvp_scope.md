# 6. MVP Scope

## 6.1 In Scope
- All features listed in §4 (FR‑1 through FR‑7).
- `requirements.txt` containing `yfinance`, `plyer`, `requests`.
- Plain Python source file (`price_tracker.py`).
- `config.json` with `threshold`, `simulation_mode`, optional `test_price`.
- Human‑readable `price_log.txt`.

## 6.2 Out of Scope for MVP
- Support for additional tickers.
- Holiday calendar beyond weekend check.
- Alternative notification channels (email, Slack, etc.).
- Packaging as an executable or Docker container.
- Advanced resource‑limiting or async I/O.
