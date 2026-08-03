# 4.2 Scheduling & Market Hours

**Description:** Run a loop that sleeps for 5 minutes between polls, but only between 09:15 AM and 03:30 PM IST, Monday‑Friday.

**Functional Requirements:**

- **FR‑2: Time‑Window Enforcement**
  - System must poll only when the current local time is within the defined market window and the day is a weekday.

**Consequences (testable):**
- The script checks `datetime.now().weekday()` (0‑4) and `datetime.time` bounds before each fetch.
