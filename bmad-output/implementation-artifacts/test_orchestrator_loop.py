"""Unit tests for Story 2.3: Orchestrator Loop & Retry.

Covers all branches of main() in price_tracker.py:
  - AC-1: fetch_price() returns None → log to stderr, sleep, retry (no sys.exit)
  - AC-2: valid price → log_price() called, sleep called
  - AC-3: price >= threshold → send_toast() NOT called
        price <  threshold → send_toast() called
  - AC-4: market closed → fetch_price/log_price/send_toast NOT called
  - AC-5: loop survives multiple cycles
  - AC-6: log_price() / send_toast() exceptions do NOT crash the loop

All tests inject a deterministic Monday 10:00 datetime (market open) unless
testing the market-closed branch. The infinite loop is broken by raising
SystemExit on the Nth time.sleep() call.
"""
from datetime import datetime

import pytest
import price_tracker

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MARKET_OPEN_TIME = datetime(2026, 7, 13, 10, 0, 0)   # Monday 10:00
MARKET_CLOSED_TIME = datetime(2026, 7, 11, 10, 0, 0)  # Saturday 10:00


def _fake_datetime(dt):
    """Return a fake datetime class whose .now() always returns dt."""
    return type("FakeDT", (), {"now": staticmethod(lambda: dt)})


def _break_after(n, monkeypatch):
    """Patch time.sleep to raise SystemExit after being called n times."""
    calls = {"count": 0}

    def fake_sleep(seconds):
        calls["count"] += 1
        if calls["count"] >= n:
            raise SystemExit(0)

    monkeypatch.setattr(price_tracker.time, "sleep", fake_sleep)
    return calls


# ---------------------------------------------------------------------------
# AC-1: fetch_price() returns None → retry path
# ---------------------------------------------------------------------------

def test_retry_on_fetch_none_logs_to_stderr(monkeypatch, capsys):
    """fetch_price returning None must log the retry message to stderr."""
    monkeypatch.setattr("price_tracker.datetime", _fake_datetime(MARKET_OPEN_TIME))
    monkeypatch.setattr(price_tracker, "fetch_price", lambda: None)
    _break_after(1, monkeypatch)

    try:
        price_tracker.main()
    except SystemExit:
        pass

    captured = capsys.readouterr()
    assert "Failed to retrieve price; will retry." in captured.err


def test_retry_on_fetch_none_does_not_call_log_or_toast(monkeypatch):
    """When fetch_price returns None, log_price and send_toast must NOT be called."""
    monkeypatch.setattr("price_tracker.datetime", _fake_datetime(MARKET_OPEN_TIME))
    monkeypatch.setattr(price_tracker, "fetch_price", lambda: None)
    _break_after(1, monkeypatch)

    log_calls = []
    toast_calls = []
    monkeypatch.setattr(price_tracker, "log_price", lambda p, ts: log_calls.append(p))
    monkeypatch.setattr(price_tracker, "send_toast", lambda p: toast_calls.append(p))

    try:
        price_tracker.main()
    except SystemExit:
        pass

    assert log_calls == []
    assert toast_calls == []


def test_retry_does_not_call_sys_exit(monkeypatch):
    """The loop must never call sys.exit() on a fetch failure."""
    monkeypatch.setattr("price_tracker.datetime", _fake_datetime(MARKET_OPEN_TIME))
    monkeypatch.setattr(price_tracker, "fetch_price", lambda: None)
    _break_after(1, monkeypatch)

    exited_via_sys = {"flag": False}
    real_exit = price_tracker.sys.exit

    def spy_exit(code=0):
        exited_via_sys["flag"] = True
        raise SystemExit(code)

    monkeypatch.setattr(price_tracker.sys, "exit", spy_exit)

    try:
        price_tracker.main()
    except SystemExit:
        pass

    assert not exited_via_sys["flag"], "sys.exit() must NOT be called on fetch failure"


# ---------------------------------------------------------------------------
# AC-2 & AC-3: valid price path — log always, toast only when below threshold
# ---------------------------------------------------------------------------

def test_valid_price_above_threshold_calls_log_not_toast(monkeypatch):
    """Price >= THRESHOLD: log_price called, send_toast NOT called."""
    monkeypatch.setattr("price_tracker.datetime", _fake_datetime(MARKET_OPEN_TIME))
    above_threshold = price_tracker.THRESHOLD + 10.0
    monkeypatch.setattr(price_tracker, "fetch_price", lambda: above_threshold)
    _break_after(1, monkeypatch)

    log_calls = []
    toast_calls = []
    monkeypatch.setattr(price_tracker, "log_price", lambda p, ts: log_calls.append(p))
    monkeypatch.setattr(price_tracker, "send_toast", lambda p: toast_calls.append(p))

    try:
        price_tracker.main()
    except SystemExit:
        pass

    assert len(log_calls) == 1
    assert log_calls[0] == above_threshold
    assert toast_calls == []


def test_valid_price_below_threshold_calls_log_and_toast(monkeypatch):
    """Price < THRESHOLD: both log_price and send_toast called."""
    monkeypatch.setattr("price_tracker.datetime", _fake_datetime(MARKET_OPEN_TIME))
    below_threshold = price_tracker.THRESHOLD - 10.0
    monkeypatch.setattr(price_tracker, "fetch_price", lambda: below_threshold)
    _break_after(1, monkeypatch)

    log_calls = []
    toast_calls = []
    monkeypatch.setattr(price_tracker, "log_price", lambda p, ts: log_calls.append(p))
    monkeypatch.setattr(price_tracker, "send_toast", lambda p: toast_calls.append(p))

    try:
        price_tracker.main()
    except SystemExit:
        pass

    assert len(log_calls) == 1
    assert len(toast_calls) == 1
    assert toast_calls[0] == below_threshold


# ---------------------------------------------------------------------------
# AC-3 boundary: price == THRESHOLD → toast must NOT fire
# ---------------------------------------------------------------------------

def test_price_exactly_at_threshold_does_not_call_toast(monkeypatch):
    """Price == THRESHOLD must NOT trigger send_toast (strict less-than gate)."""
    monkeypatch.setattr("price_tracker.datetime", _fake_datetime(MARKET_OPEN_TIME))
    at_threshold = price_tracker.THRESHOLD   # exactly equal
    monkeypatch.setattr(price_tracker, "fetch_price", lambda: at_threshold)
    _break_after(1, monkeypatch)

    log_calls = []
    toast_calls = []
    monkeypatch.setattr(price_tracker, "log_price", lambda p, ts: log_calls.append(p))
    monkeypatch.setattr(price_tracker, "send_toast", lambda p: toast_calls.append(p))

    try:
        price_tracker.main()
    except SystemExit:
        pass

    assert len(log_calls) == 1, "log_price must be called when price == THRESHOLD"
    assert toast_calls == [], "send_toast must NOT be called when price == THRESHOLD"


# ---------------------------------------------------------------------------
# AC-4: market closed → no adapters called
# ---------------------------------------------------------------------------

def test_market_closed_no_adapters_called(monkeypatch):
    """When market is closed, fetch/log/toast must not be called."""
    monkeypatch.setattr(price_tracker, "SIMULATION", False)
    monkeypatch.setattr(price_tracker, "is_market_open", lambda now: False)
    _break_after(1, monkeypatch)

    fetch_calls = []
    log_calls = []
    toast_calls = []
    monkeypatch.setattr(price_tracker, "fetch_price", lambda: fetch_calls.append(1) or 250.0)
    monkeypatch.setattr(price_tracker, "log_price", lambda p, ts: log_calls.append(p))
    monkeypatch.setattr(price_tracker, "send_toast", lambda p: toast_calls.append(p))

    try:
        price_tracker.main()
    except SystemExit:
        pass

    assert fetch_calls == []
    assert log_calls == []
    assert toast_calls == []


# ---------------------------------------------------------------------------
# AC-5: loop survives multiple cycles
# ---------------------------------------------------------------------------

def test_loop_survives_multiple_cycles(monkeypatch):
    """Loop must complete multiple cycles without exiting."""
    monkeypatch.setattr("price_tracker.datetime", _fake_datetime(MARKET_OPEN_TIME))
    above_threshold = price_tracker.THRESHOLD + 5.0
    monkeypatch.setattr(price_tracker, "fetch_price", lambda: above_threshold)
    sleep_calls = _break_after(3, monkeypatch)  # break after 3 sleep calls

    log_calls = []
    monkeypatch.setattr(price_tracker, "log_price", lambda p, ts: log_calls.append(p))
    monkeypatch.setattr(price_tracker, "send_toast", lambda p: None)

    try:
        price_tracker.main()
    except SystemExit:
        pass

    # 3 sleep calls → 3 full successful cycles
    assert len(log_calls) == 3
    assert sleep_calls["count"] == 3


# ---------------------------------------------------------------------------
# AC-6: adapter exceptions must not crash the loop
# ---------------------------------------------------------------------------

def test_log_price_exception_does_not_crash_loop(monkeypatch, capsys):
    """An exception in log_price must be caught; loop must continue."""
    monkeypatch.setattr("price_tracker.datetime", _fake_datetime(MARKET_OPEN_TIME))
    above_threshold = price_tracker.THRESHOLD + 5.0
    monkeypatch.setattr(price_tracker, "fetch_price", lambda: above_threshold)

    sleep_calls = _break_after(2, monkeypatch)

    # Patch the open() call inside log_price to raise IOError
    import builtins
    real_open = builtins.open

    def bad_open(path, *args, **kwargs):
        if "price_log" in str(path):
            raise IOError("disk full")
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", bad_open)
    monkeypatch.setattr(price_tracker, "send_toast", lambda p: None)

    try:
        price_tracker.main()
    except SystemExit:
        pass

    captured = capsys.readouterr()
    assert "Error writing price log" in captured.err
    # Loop must have continued to a second sleep despite the error
    assert sleep_calls["count"] == 2


def test_send_toast_exception_does_not_crash_loop(monkeypatch, capsys):
    """An exception in send_toast must be caught; loop must continue."""
    monkeypatch.setattr("price_tracker.datetime", _fake_datetime(MARKET_OPEN_TIME))
    below_threshold = price_tracker.THRESHOLD - 10.0
    monkeypatch.setattr(price_tracker, "fetch_price", lambda: below_threshold)
    sleep_calls = _break_after(2, monkeypatch)

    monkeypatch.setattr(price_tracker, "log_price", lambda p, ts: None)

    # Patch Notification.show to raise
    class BadNotification:
        def __init__(self, **kwargs):
            pass
        def show(self):
            raise RuntimeError("toast failed")
    monkeypatch.setattr(price_tracker, "Notification", BadNotification)

    try:
        price_tracker.main()
    except SystemExit:
        pass

    captured = capsys.readouterr()
    assert "Error sending notification" in captured.err
    assert sleep_calls["count"] == 2
