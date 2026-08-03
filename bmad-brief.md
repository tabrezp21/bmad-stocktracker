# Product Brief: Bank of Baroda Price Tracker & Alerter

## Objective
Build a stable Python script that tracks the real-time share price of Bank of Baroda (BANKBARODA.NS) and triggers an alert if the price falls below a target threshold.

## Core Requirements
1. **Data Sourcing:** Fetch data using the free `yfinance` library. 
2. **Timing:** Poll the price every 5 minutes. Run only during Indian market hours (9:15 AM to 3:30 PM IST, Monday-Friday).
3. **Alert Channel:** Generate a system notification or log a high-priority alert.
4. **Persistence:** Save a timestamped record of every check in a local `price_log.txt` file.
5. **Configuration:** Keep the threshold price (₹230) and intervals flexible inside a local `config.json` file.
6. **Error Handling:** If the network disconnects, wait 5 minutes and retry quietly without crashing.
