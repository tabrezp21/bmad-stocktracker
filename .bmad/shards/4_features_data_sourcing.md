# 4.1 Data Sourcing

**Description:** Pull the latest price for `BANKBARODA.NS` using the free `yfinance` library.

**Functional Requirements:**

- **FR‑1: Fetch Current Price**
  - Investor can retrieve the current share price from Yahoo Finance every 5 minutes during market hours.

**Consequences (testable):**
- The script calls `yfinance.Ticker("BANKBARODA.NS").history(period="1d")` and extracts the latest "Close" value.
- If the API call fails or returns no data, the script logs an error and retries after 5 minutes.

**Out of Scope:**
- Historical price analysis beyond the most recent price.
