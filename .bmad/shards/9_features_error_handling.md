# 4.6 Error Handling

**Description:** Gracefully handle network failures.

**Functional Requirements:**

- **FR‑7: Retry on Failure**
  - If a network error occurs, the script must wait 5 minutes and retry indefinitely without exiting.

**Consequences (testable):**
- No unhandled exceptions propagate to the console.
- Retry count is not limited.
