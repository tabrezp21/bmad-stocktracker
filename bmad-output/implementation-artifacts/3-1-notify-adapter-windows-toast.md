---
baseline_commit: NO_VCS
---

# Story 3.1: Notify Adapter (Windows Toast)

Status: done

## Story

As an investor,
I want a Windows toast notification when the price drops below my threshold,
So that I am alerted immediately without watching the terminal.

## Acceptance Criteria

1. **Given** `price < threshold`
   **When** `send_toast(price)` is called
   **Then** a Windows toast appears with title `"Bank of Baroda Price Alert"`
   **And** the message is `"Price dropped to ₹{price:.2f} (target ₹{THRESHOLD})"`
   **And** the toast fires within 2 seconds of the price check (NFR-1)

2. **Given** `price >= threshold`
   **When** the orchestrator evaluates the price
   **Then** `send_toast()` is NOT called

3. **Given** `plyer` raises an exception (e.g. notifications disabled)
   **When** `send_toast()` is called
   **Then** the error is logged to `stderr` and the orchestrator loop continues — no crash (AD-4)

4. **Given** `send_toast(price)` is called
   **When** `plyer.notification.notify()` is invoked
   **Then** it receives `title`, `message`, and `timeout=5` as keyword arguments

5. **Given** the adapter is called
   **When** it completes (success or failure)
   **Then** it returns `None` — it never raises to the caller

## Tasks / Subtasks

- [x] Verify `send_toast()` in `price_tracker.py` satisfies all ACs (AC: 1–5)
  - [x] Confirm title is exactly `"Bank of Baroda Price Alert"` (AC: 1)
  - [x] Confirm message format is `f"Price dropped to ₹{price:.2f} (target ₹{THRESHOLD})"` (AC: 1)
  - [x] Confirm `timeout=5` is passed to `notification.notify()` (AC: 4)
  - [x] Confirm try/except wraps entire call — error logged to stderr (AC: 3, 5)
  - [x] Confirm orchestrator only calls `send_toast()` when `price < THRESHOLD` (AC: 2)
- [x] Write unit tests covering all ACs (AC: 1–5)
  - [x] `send_toast()` invokes `notification.notify()` with correct title, message, timeout (AC: 1, 4)
  - [x] `send_toast()` formats price correctly to 2 decimal places (AC: 1)
  - [x] `send_toast()` logs error to stderr and returns None when plyer raises (AC: 3, 5)
  - [x] Orchestrator does NOT call `send_toast()` when price >= threshold (AC: 2)
  - [x] `send_toast()` returns None on success (AC: 5)

## Dev Notes

### Architecture Guardrails (MUST follow)

- **AD-1 (Layered Adapter):** `send_toast()` is a pure output adapter — it must only wrap `plyer.notification.notify()`. It must not check prices, read config, or do any scheduling logic.
- **AD-4 (Error isolation):** `send_toast()` must catch all exceptions, log to `stderr`, and return silently. It must never raise to the orchestrator.
- **AD-3 (Config boundary):** `THRESHOLD` in the message comes from the module-level constant loaded from `config.json` — never hardcoded.
- **AD-5 (Scheduling ownership):** The decision to call `send_toast()` (i.e., `price < THRESHOLD`) lives in the orchestrator (`main()`), not inside `send_toast()` itself.

### What this story DOES and DOES NOT do

| In scope | Out of scope |
|---|---|
| Verify `send_toast()` implementation | macOS/Linux notification support (deferred) |
| Title, message format, timeout verification | Notification sound/icon customisation |
| Error isolation (try/except) | Windows notification permission setup |
| Unit tests for all ACs | End-to-end toast visible on screen (Epic 4) |

### Existing code to verify (do NOT blindly overwrite)

`send_toast()` in `price_tracker.py` at lines 74–83 (updated in Story 2.3):

```python
def send_toast(price: float) -> None:
    """Send a Windows toast notification when price drops below threshold.
    Logs error to stderr on failure — never raises to caller (AD-4).
    """
    try:
        title = "Bank of Baroda Price Alert"
        message = f"Price dropped to ₹{price:.2f} (target ₹{THRESHOLD})"
        notification.notify(title=title, message=message, timeout=5)
    except Exception as e:
        print(f"Error sending notification: {e}", file=sys.stderr)
```

**This implementation already satisfies all ACs.** Tasks are verify + write tests.

The orchestrator call site in `main()` (lines 100–101):

```python
if price < THRESHOLD:
    send_toast(price)
```

This satisfies AC-2 (send_toast not called when price >= threshold).

### Key technical facts

- `plyer.notification.notify()` is the cross-platform notification API. On Windows it uses the native WinRT/win10toast backend.
- The function signature is `notification.notify(title, message, app_name, app_icon, timeout, ticker, toast)`. We pass only `title`, `message`, and `timeout` as keyword args — this is correct for the MVP.
- `timeout=5` means the toast auto-dismisses after 5 seconds — this is the correct value per the epics spec.
- The ₹ character (U+20B9) is a Unicode Rupee sign — it must be preserved exactly in the message format string. Do NOT replace with `Rs.` or `INR`.
- `THRESHOLD` in the message is the module-level float (e.g., `230.0`). The format string uses `₹{THRESHOLD}` without `.2f` — this is intentional (shows as `₹230` or `₹230.0` depending on value). Do not change this formatting.
- `plyer` must NOT be called during tests — mock `price_tracker.notification.notify` using `monkeypatch`.
- Testing `notification.notify` kwargs: capture call args via a list-appending lambda or `unittest.mock.MagicMock`.

### Test patterns (from Stories 2.1–2.3)

Import `price_tracker` at module level. Use `monkeypatch` to replace `price_tracker.notification.notify`:

```python
import price_tracker

def test_send_toast_calls_notify_with_correct_args(monkeypatch):
    calls = []
    monkeypatch.setattr(
        price_tracker.notification, "notify",
        lambda **kwargs: calls.append(kwargs)
    )
    price_tracker.send_toast(220.50)
    assert len(calls) == 1
    assert calls[0]["title"] == "Bank of Baroda Price Alert"
    assert "220.50" in calls[0]["message"]
    assert calls[0]["timeout"] == 5
```

For the error isolation test, raise from the mock:

```python
monkeypatch.setattr(
    price_tracker.notification, "notify",
    lambda **kwargs: (_ for _ in ()).throw(RuntimeError("toast failed"))
)
```

### Reference: message format verification

Given `price = 220.50` and `THRESHOLD = 230`:
- Expected message: `"Price dropped to ₹220.50 (target ₹230)"`

Given `price = 229.99`:
- Expected message: `"Price dropped to ₹229.99 (target ₹230)"`

### Project structure notes

```
BMAD_Project/
  price_tracker.py    ← VERIFY: send_toast() at lines 74–83, orchestrator call at lines 100–101
  bmad-output/
    implementation-artifacts/
      test_orchestrator_loop.py   ← reference: notification mock patterns
      3-1-notify-adapter-windows-toast.md  ← this story
```

Test file to create: `bmad-output/implementation-artifacts/test_notify_adapter.py`

### References

- Architecture Spine: `bmad-output/planning-artifacts/architecture/architecture-BMAD_Project-2026-07-16/ARCHITECTURE-SPINE.md` — AD-1, AD-4, AD-3, AD-5
- Epics: `bmad-output/planning-artifacts/epics.md` — Story 3.1 (FR-3, AD-1, AD-4, NFR-1)
- Previous story: `bmad-output/implementation-artifacts/2-3-orchestrator-loop-retry.md` — error isolation pattern
- `price_tracker.py` lines 74–83 — existing `send_toast()` implementation
- `price_tracker.py` lines 100–101 — orchestrator call gate

## Dev Agent Record

### Agent Model Used

aifs/claude-sonnet-4.6

### Debug Log References

None — existing implementation satisfied all ACs; no code changes required.

### Completion Notes List

- Verified `send_toast()` at `price_tracker.py:74–83` satisfies all 5 ACs without modification.
- Title, message format (₹{price:.2f}), timeout=5, try/except error isolation all confirmed correct.
- Orchestrator gate at `price_tracker.py:100–101` correctly prevents toast when `price >= THRESHOLD`.
- Created `test_notify_adapter.py` with 14 unit tests covering all ACs — no real plyer calls made.
- Full regression suite: 43/43 passed, zero regressions.

### File List

- `price_tracker.py` — verified only, no changes needed
- `bmad-output/implementation-artifacts/test_notify_adapter.py` — CREATED: 14 unit tests
- `bmad-output/implementation-artifacts/3-1-notify-adapter-windows-toast.md` — updated tasks and status

### Change Log

- 2026-07-17: Story 3.1 implemented — verified send_toast() against all ACs; created 14-test suite covering title/message/timeout/error-isolation/orchestrator-gate.
