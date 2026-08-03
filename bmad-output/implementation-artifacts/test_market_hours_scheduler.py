"""Unit tests for Story 2.2: Market-Hours Scheduler.

Covers is_market_open() boundary conditions and the orchestrator gate
in main() that prevents fetch_price() from being called outside market hours.

Reference datetimes (all deterministic — no wall-clock dependency):
  - 2026-07-13 (Monday), 2026-07-14 (Tuesday) … 2026-07-17 (Friday)
  - 2026-07-11 (Saturday), 2026-07-12 (Sunday)
"""
from datetime import datetime

import price_tracker


# ---------------------------------------------------------------------------
# AC-1: Weekday inside window → True
# ---------------------------------------------------------------------------

def test_weekday_inside_window_monday():
    now = datetime(2026, 7, 13, 10, 0, 0)   # Monday 10:00
    assert price_tracker.is_market_open(now) is True


def test_weekday_inside_window_friday():
    now = datetime(2026, 7, 17, 14, 0, 0)   # Friday 14:00
    assert price_tracker.is_market_open(now) is True


# ---------------------------------------------------------------------------
# AC-2: Saturday / Sunday → False
# ---------------------------------------------------------------------------

def test_saturday_returns_false():
    now = datetime(2026, 7, 11, 10, 0, 0)   # Saturday 10:00
    assert price_tracker.is_market_open(now) is False


def test_sunday_returns_false():
    now = datetime(2026, 7, 12, 10, 0, 0)   # Sunday 10:00
    assert price_tracker.is_market_open(now) is False


# ---------------------------------------------------------------------------
# AC-3: Weekday outside hours → False
# ---------------------------------------------------------------------------

def test_weekday_before_market_open():
    now = datetime(2026, 7, 13, 8, 0, 0)    # Monday 08:00
    assert price_tracker.is_market_open(now) is False


def test_weekday_after_market_close():
    now = datetime(2026, 7, 13, 16, 0, 0)   # Monday 16:00
    assert price_tracker.is_market_open(now) is False


# ---------------------------------------------------------------------------
# AC-6: Boundary times are inclusive
# ---------------------------------------------------------------------------

def test_boundary_market_open_exact():
    now = datetime(2026, 7, 13, 9, 15, 0)   # Monday 09:15:00 exactly
    assert price_tracker.is_market_open(now) is True


def test_boundary_market_close_exact():
    now = datetime(2026, 7, 13, 15, 30, 0)  # Monday 15:30:00 exactly
    assert price_tracker.is_market_open(now) is True


def test_one_second_before_open():
    now = datetime(2026, 7, 13, 9, 14, 59)  # Monday 09:14:59
    assert price_tracker.is_market_open(now) is False


def test_one_second_after_close():
    now = datetime(2026, 7, 13, 15, 30, 1)  # Monday 15:30:01
    assert price_tracker.is_market_open(now) is False


# ---------------------------------------------------------------------------
# AC-4 & AC-5: Orchestrator gate — fetch_price() must NOT be called when
# market is closed, and MUST be called when market is open.
# ---------------------------------------------------------------------------

def test_orchestrator_skips_fetch_when_market_closed(monkeypatch):
    """When is_market_open returns False, fetch_price must not be called."""
    call_count = {"fetch": 0, "sleep": 0}

    # Disable simulation so fetch_price goes through the normal path
    monkeypatch.setattr(price_tracker, "SIMULATION", False)
    # Patch is_market_open directly to return False (market closed)
    monkeypatch.setattr(price_tracker, "is_market_open", lambda now: False)

    def fake_sleep(seconds):
        call_count["sleep"] += 1
        raise SystemExit(0)   # break the infinite loop after first iteration

    def fake_fetch():
        call_count["fetch"] += 1
        return 250.0

    monkeypatch.setattr(price_tracker.time, "sleep", fake_sleep)
    monkeypatch.setattr(price_tracker, "fetch_price", fake_fetch)

    try:
        price_tracker.main()
    except SystemExit:
        pass

    assert call_count["fetch"] == 0, "fetch_price must NOT be called when market is closed"
    assert call_count["sleep"] == 1, "sleep must be called once to wait for next check"


def test_orchestrator_calls_fetch_when_market_open(monkeypatch):
    """When is_market_open returns True, fetch_price must be called."""
    call_count = {"fetch": 0}

    # Monday 10:00 — market is open
    monday = datetime(2026, 7, 13, 10, 0, 0)
    datetimes = iter([monday])

    monkeypatch.setattr(
        "price_tracker.datetime",
        type("FakeDT", (), {"now": staticmethod(lambda: next(datetimes))})
    )

    def fake_fetch():
        call_count["fetch"] += 1
        return 250.0   # above threshold — no toast

    def fake_log(price, ts):
        pass

    def fake_sleep(seconds):
        raise SystemExit(0)   # break after first full cycle

    monkeypatch.setattr(price_tracker, "fetch_price", fake_fetch)
    monkeypatch.setattr(price_tracker, "log_price", fake_log)
    monkeypatch.setattr(price_tracker.time, "sleep", fake_sleep)

    try:
        price_tracker.main()
    except SystemExit:
        pass

    assert call_count["fetch"] == 1, "fetch_price MUST be called when market is open"
