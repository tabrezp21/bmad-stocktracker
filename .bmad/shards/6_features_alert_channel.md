# 4.3 Alert Channel

**Description:** Emit a native Windows toast using `plyer` when the price falls below the threshold.

**Functional Requirements:**

- **FR‑3: Threshold Alert**
  - When `price < threshold`, the script must display a toast with the message: "Bank of Baroda price dropped to ₹{price} (target ₹{threshold})."

**Consequences (testable):**
- Toast appears within 2 seconds of price check.
- The toast includes the timestamp of the check.

**Out of Scope:**
- Alternative channels (email, Slack, SMS).
