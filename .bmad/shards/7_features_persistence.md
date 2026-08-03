# 4.4 Persistence

**Description:** Append a timestamped entry to `price_log.txt` after each check.

**Functional Requirements:**

- **FR‑4: Logging**
  - System must write a line `YYYY‑MM‑DD HH:MM, {price}` to `price_log.txt` for every poll, regardless of alert state.

**Consequences (testable):**
- Log file grows linearly; each line matches the format.
