# 7. Success Metrics

## Primary
- **SM‑1:** Alert fires within 2 seconds of price check when price < threshold (≥ 95 % of such events during a test run).
- **SM‑2:** Script runs continuously for a full market day without crashing (≥ 99 % uptime).

## Secondary
- **SM‑3:** `price_log.txt` contains exactly one entry per poll (5‑minute intervals) for a given market day.

## Counter‑metrics
- **SM‑C1:** CPU usage stays below 5 % of a single core during idle periods.
