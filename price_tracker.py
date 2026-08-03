# price_tracker.py
"""Configurable Multi-Company Stock Price Tracker
Implements the specifications from bmad-prd.md.
Companies, tickers, thresholds, and market regions are all configured via config.json.
Supports IN (NSE/BSE) and US (NASDAQ/NYSE) markets with correct timezone handling.
"""

import json
import sys
import time
from datetime import datetime, time as dtime
from pathlib import Path
from zoneinfo import ZoneInfo

import yfinance as yf
from winotify import Notification

# Load configuration
CONFIG_PATH = Path(__file__).parent / "config.json"
if not CONFIG_PATH.is_file():
    print(f"Config file not found at {CONFIG_PATH}", file=sys.stderr)
    sys.exit(1)

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)

SIMULATION = config.get("simulation_mode", False)
CHECK_INTERVAL = config.get("check_interval_seconds", 10)
COMPANIES = config.get("companies", [])

if not COMPANIES:
    print("Error: No companies defined in config.json under 'companies'.", file=sys.stderr)
    sys.exit(1)

# Validate each company entry
for i, company in enumerate(COMPANIES):
    if not company.get("ticker"):
        print(f"Error: Company at index {i} is missing 'ticker' in config.json", file=sys.stderr)
        sys.exit(1)
    if not company.get("company_name"):
        print(f"Error: Company at index {i} is missing 'company_name' in config.json", file=sys.stderr)
        sys.exit(1)
    if company.get("threshold") is None:
        print(f"Error: Company '{company.get('company_name')}' is missing 'threshold' in config.json", file=sys.stderr)
        sys.exit(1)
    market = company.get("market", "IN").upper()
    if market not in ("IN", "US"):
        print(f"Error: Company '{company.get('company_name')}' has invalid 'market' value '{market}'. Use 'IN' or 'US'.", file=sys.stderr)
        sys.exit(1)

LOG_DIR = Path(__file__).parent

# Indian market: NSE/BSE — 9:15 AM to 3:30 PM IST
TZ_IN = ZoneInfo("Asia/Kolkata")
IN_MARKET_START = dtime(hour=9, minute=15)
IN_MARKET_END = dtime(hour=15, minute=30)

# US market: NASDAQ/NYSE — 9:30 AM to 4:00 PM EST/EDT
TZ_US = ZoneInfo("America/New_York")
US_MARKET_START = dtime(hour=9, minute=30)
US_MARKET_END = dtime(hour=16, minute=0)


def is_market_open(market: str) -> bool:
    """Return True if the given market (IN or US) is currently open."""
    if market == "US":
        now_local = datetime.now(tz=TZ_US)
        if now_local.weekday() >= 5:  # Saturday=5, Sunday=6
            return False
        return US_MARKET_START <= now_local.time() <= US_MARKET_END
    else:  # IN
        now_local = datetime.now(tz=TZ_IN)
        if now_local.weekday() >= 5:
            return False
        return IN_MARKET_START <= now_local.time() <= IN_MARKET_END


def fetch_price(ticker: str, test_price: float | None) -> float | None:
    """Fetch latest price for the given ticker.
    Returns None on failure.
    Simulation branch (AD-6): when SIMULATION=True the real network is never called.
    Uses 1-minute interval intraday data for the most accurate live price.
    """
    if SIMULATION and test_price is not None:
        return float(test_price)
    if SIMULATION and test_price is None:
        print(f"Simulation mode enabled but test_price is not set for {ticker}.", file=sys.stderr)
        return None
    try:
        stock = yf.Ticker(ticker)
        # Use 1-minute interval for accurate live price during market hours
        hist = stock.history(period="1d", interval="1m")
        if hist.empty:
            # Fallback to daily close if intraday data is unavailable
            hist = stock.history(period="1d")
        if hist.empty:
            return None
        return float(hist["Close"].iloc[-1])
    except Exception as e:
        print(f"Error fetching price for {ticker}: {e}", file=sys.stderr)
        return None


def log_price(company_name: str, ticker: str, price: float, timestamp: datetime) -> None:
    """Append a timestamped price entry to a per-company log file.
    Logs error to stderr on failure — never raises to caller (AD-4).
    """
    try:
        safe_ticker = ticker.replace(".", "_")
        log_path = LOG_DIR / f"price_log_{safe_ticker}.txt"
        line = f"{timestamp.strftime('%Y-%m-%d %H:%M')}, {company_name}, {price:.2f}\n"
        with open(log_path, "a", encoding="utf-8") as log_file:
            log_file.write(line)
    except Exception as e:
        print(f"Error writing price log for {company_name}: {e}", file=sys.stderr)


def send_toast(company_name: str, price: float, threshold: float, currency: str) -> None:
    """Send a Windows toast notification when price drops below threshold.
    Logs error to stderr on failure — never raises to caller (AD-4).
    """
    try:
        title = f"{company_name}: {currency}{price:.2f}"
        message = f"Target: {currency}{threshold:.2f}"
        toast = Notification(
            app_id=f"{company_name} Tracker",
            title=title,
            msg=message,
            duration="short"
        )
        toast.show()
    except Exception as e:
        print(f"Error sending notification for {company_name}: {e}", file=sys.stderr)


def main() -> None:
    print(f"Tracking {len(COMPANIES)} company/companies: {', '.join(c['company_name'] for c in COMPANIES)}")
    while True:
        now = datetime.now()

        for company in COMPANIES:
            name = company["company_name"]
            ticker = company["ticker"]
            threshold = company["threshold"]
            test_price = company.get("test_price", None)
            market = company.get("market", "IN").upper()
            currency = "USD " if market == "US" else "INR "

            if not is_market_open(market):
                continue

            price = fetch_price(ticker, test_price)
            if price is None:
                print(f"Failed to retrieve price for {name} ({ticker}); will retry.", file=sys.stderr)
                continue

            log_price(name, ticker, price, now)

            if price < threshold:
                send_toast(name, price, threshold, currency)

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted by user.")
