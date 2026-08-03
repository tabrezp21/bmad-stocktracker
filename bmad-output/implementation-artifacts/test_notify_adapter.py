"""Unit tests for Story 3.1: Notify Adapter (Windows Toast).

Covers all ACs for send_toast() in price_tracker.py:
  - AC-1: correct title, message format (₹{price:.2f}), and timeout=5
  - AC-2: orchestrator does NOT call send_toast() when price >= threshold
  - AC-3: plyer exception caught → logged to stderr, no crash
  - AC-4: notification.notify() receives title, message, timeout as kwargs
  - AC-5: send_toast() always returns None

plyer is never called for real — notification.notify is monkeypatched
in every test.
"""
from datetime import datetime

import pytest
import price_tracker


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _capture_notify_calls(monkeypatch):
    """Patch Notification.show to capture calls."""
    calls = []

    class FakeNotification:
        def __init__(self, app_id, title, msg, duration="short"):
            self._data = {"title": title, "message": msg, "app_id": app_id, "timeout": 5}
            calls.append(self._data)

        def show(self):
            pass

    monkeypatch.setattr(price_tracker, "Notification", FakeNotification)
    return calls


def _raise_on_notify(monkeypatch, exc=RuntimeError("notifications disabled")):
    """Patch Notification so show() raises exc."""
    class BadNotification:
        def __init__(self, **kwargs):
            pass

        def show(self):
            raise exc

    monkeypatch.setattr(price_tracker, "Notification", BadNotification)


# ---------------------------------------------------------------------------
# AC-1 & AC-4: correct title, message, timeout passed to notify()
# ---------------------------------------------------------------------------

def test_send_toast_title_is_correct(monkeypatch):
    """Title must be exactly 'Bank of Baroda Price Alert'."""
    calls = _capture_notify_calls(monkeypatch)
    price_tracker.send_toast(220.50)
    assert calls[0]["title"] == "Bank of Baroda Price Alert"


def test_send_toast_message_contains_price(monkeypatch):
    """Message must contain the price formatted to 2 decimal places."""
    calls = _capture_notify_calls(monkeypatch)
    price_tracker.send_toast(220.50)
    assert "220.50" in calls[0]["message"]


def test_send_toast_message_contains_rupee_symbol(monkeypatch):
    """Message must contain Rs. before the price."""
    calls = _capture_notify_calls(monkeypatch)
    price_tracker.send_toast(220.50)
    assert "Rs.220.50" in calls[0]["message"]


def test_send_toast_message_contains_threshold(monkeypatch):
    """Message must reference the configured threshold."""
    calls = _capture_notify_calls(monkeypatch)
    price_tracker.send_toast(220.50)
    assert str(price_tracker.THRESHOLD) in calls[0]["message"]


def test_send_toast_timeout_is_five(monkeypatch):
    """Notification duration must map to timeout=5."""
    calls = _capture_notify_calls(monkeypatch)
    price_tracker.send_toast(220.50)
    assert calls[0]["timeout"] == 5


def test_send_toast_calls_notify_exactly_once(monkeypatch):
    """Notification must be created exactly once per send_toast() invocation."""
    calls = _capture_notify_calls(monkeypatch)
    price_tracker.send_toast(220.50)
    assert len(calls) == 1


def test_send_toast_price_rounded_two_decimals(monkeypatch):
    """Price in message must be formatted to exactly 2 decimal places."""
    calls = _capture_notify_calls(monkeypatch)
    price_tracker.send_toast(229.9)
    assert "229.90" in calls[0]["message"]


def test_send_toast_full_message_format(monkeypatch):
    """Verify full message string structure."""
    calls = _capture_notify_calls(monkeypatch)
    price_tracker.send_toast(215.75)
    expected_message = f"Price dropped to Rs.215.75 (target Rs.{price_tracker.THRESHOLD})"
    assert calls[0]["message"] == expected_message


# ---------------------------------------------------------------------------
# AC-2: orchestrator does NOT call send_toast() when price >= threshold
# ---------------------------------------------------------------------------

def test_orchestrator_does_not_call_toast_above_threshold(monkeypatch):
    """When price >= THRESHOLD, send_toast must not be called."""
    monday = datetime(2026, 7, 13, 10, 0, 0)
    monkeypatch.setattr(
        "price_tracker.datetime",
        type("FakeDT", (), {"now": staticmethod(lambda: monday)})
    )
    above = price_tracker.THRESHOLD + 1.0
    monkeypatch.setattr(price_tracker, "fetch_price", lambda: above)
    monkeypatch.setattr(price_tracker, "log_price", lambda p, ts: None)

    toast_calls = []
    monkeypatch.setattr(price_tracker, "send_toast", lambda p: toast_calls.append(p))

    sleep_calls = {"n": 0}
    def fake_sleep(s):
        sleep_calls["n"] += 1
        raise SystemExit(0)
    monkeypatch.setattr(price_tracker.time, "sleep", fake_sleep)

    try:
        price_tracker.main()
    except SystemExit:
        pass

    assert toast_calls == [], "send_toast must NOT be called when price >= THRESHOLD"


def test_orchestrator_calls_toast_below_threshold(monkeypatch):
    """When price < THRESHOLD, send_toast must be called exactly once."""
    monday = datetime(2026, 7, 13, 10, 0, 0)
    monkeypatch.setattr(
        "price_tracker.datetime",
        type("FakeDT", (), {"now": staticmethod(lambda: monday)})
    )
    below = price_tracker.THRESHOLD - 10.0
    monkeypatch.setattr(price_tracker, "fetch_price", lambda: below)
    monkeypatch.setattr(price_tracker, "log_price", lambda p, ts: None)

    toast_calls = []
    monkeypatch.setattr(price_tracker, "send_toast", lambda p: toast_calls.append(p))

    def fake_sleep(s):
        raise SystemExit(0)
    monkeypatch.setattr(price_tracker.time, "sleep", fake_sleep)

    try:
        price_tracker.main()
    except SystemExit:
        pass

    assert len(toast_calls) == 1
    assert toast_calls[0] == below


# ---------------------------------------------------------------------------
# AC-3: plyer exception must be caught, logged to stderr, no crash
# ---------------------------------------------------------------------------

def test_send_toast_exception_logged_to_stderr(monkeypatch, capsys):
    """plyer raising must log 'Error sending notification' to stderr."""
    _raise_on_notify(monkeypatch)
    price_tracker.send_toast(220.50)
    captured = capsys.readouterr()
    assert "Error sending notification" in captured.err


def test_send_toast_exception_does_not_propagate(monkeypatch):
    """plyer raising must not propagate — send_toast must return cleanly."""
    _raise_on_notify(monkeypatch)
    try:
        result = price_tracker.send_toast(220.50)
    except Exception as exc:
        pytest.fail(f"send_toast raised unexpectedly: {exc}")
    assert result is None


# ---------------------------------------------------------------------------
# AC-5: send_toast() always returns None
# ---------------------------------------------------------------------------

def test_send_toast_returns_none_on_success(monkeypatch):
    """send_toast() must return None on a successful notify call."""
    _capture_notify_calls(monkeypatch)
    result = price_tracker.send_toast(220.50)
    assert result is None


def test_send_toast_returns_none_on_failure(monkeypatch):
    """send_toast() must return None even when plyer raises."""
    _raise_on_notify(monkeypatch)
    result = price_tracker.send_toast(220.50)
    assert result is None
