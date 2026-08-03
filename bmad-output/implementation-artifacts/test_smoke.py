"""End-to-end smoke test for Story 4.3.

Exercises the full main() loop for exactly 2 complete poll cycles in
simulation mode and asserts all end-to-end outcomes:

  - AC-1: price_log.txt contains exactly 2 entries after 2 cycles
  - AC-2: send_toast (notification.notify) called exactly 2 times (220 < 230)
  - AC-3: no unhandled exception propagates from main()
  - AC-4: each log entry is in correct format 'YYYY-MM-DD HH:MM, 220.00'

Only system boundaries are patched (datetime, time.sleep, LOG_PATH,
notification.notify). The full adapter stack runs end-to-end:
  main() → is_market_open() → fetch_price() [sim] → log_price() → send_toast()

No yfinance network calls are made (SIMULATION=True).
No real Windows toast is fired (notification.notify is patched).
No real price_log.txt is written (LOG_PATH redirected to tmp_path).
"""
from datetime import datetime

import pytest
import price_tracker


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _market_open_datetime():
    """Return a deterministic market-open Monday datetime."""
    return datetime(2026, 7, 13, 10, 0, 0)   # Monday 10:00


def _break_after_n_cycles(n, monkeypatch):
    """
    Patch time.sleep to raise SystemExit after n complete cycles.

    Each successful market-open cycle calls time.sleep exactly once
    (at the end of the loop body). So to run exactly n cycles, raise
    SystemExit on the nth sleep call.
    """
    calls = {"count": 0}

    def fake_sleep(s):
        calls["count"] += 1
        if calls["count"] >= n:
            raise SystemExit(0)

    monkeypatch.setattr(price_tracker.time, "sleep", fake_sleep)
    return calls


# ---------------------------------------------------------------------------
# Primary 2-cycle smoke test (covers all 4 ACs)
# ---------------------------------------------------------------------------

def test_two_cycle_smoke(monkeypatch, tmp_path):
    """
    Full end-to-end smoke: 2 cycles, simulation mode, 220.0 < 230 threshold.

    AC-1: price_log.txt has exactly 2 entries.
    AC-2: toast fired exactly 2 times.
    AC-3: no exception propagates.
    AC-4: each log line matches 'YYYY-MM-DD HH:MM, 220.00'.
    """
    # --- Simulation config ---
    monkeypatch.setattr(price_tracker, "SIMULATION", True)
    monkeypatch.setattr(price_tracker, "TEST_PRICE", 220.0)
    monkeypatch.setattr(price_tracker, "THRESHOLD", 230.0)
    monkeypatch.setattr(price_tracker, "CHECK_INTERVAL", 0)

    # --- Inject market-open datetime ---
    monday = _market_open_datetime()
    monkeypatch.setattr(
        "price_tracker.datetime",
        type("FakeDT", (), {"now": staticmethod(lambda: monday)})
    )

    # --- Redirect log file to tmp_path ---
    log_file = tmp_path / "price_log.txt"
    monkeypatch.setattr(price_tracker, "LOG_PATH", log_file)

    # --- Capture toast calls (no real Windows notification) ---
    toast_calls = []

    class FakeNotification:
        def __init__(self, app_id, title, msg, duration="short"):
            toast_calls.append({"title": title, "msg": msg})
        def show(self):
            pass

    monkeypatch.setattr(price_tracker, "Notification", FakeNotification)

    # --- Break after exactly 2 complete cycles ---
    _break_after_n_cycles(2, monkeypatch)

    # --- Run ---
    try:
        price_tracker.main()
    except SystemExit:
        pass
    except Exception as exc:
        pytest.fail(f"main() raised an unhandled exception: {exc}")   # AC-3

    # --- AC-1: exactly 2 log entries ---
    assert log_file.exists(), "price_log.txt must be created"
    lines = log_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2, f"Expected 2 log lines, got {len(lines)}: {lines}"

    # --- AC-2: toast fired exactly 2 times ---
    assert len(toast_calls) == 2, (
        f"Expected 2 toast calls (220 < 230), got {len(toast_calls)}"
    )

    # --- AC-4: each line matches correct format ---
    for line in lines:
        assert "220.00" in line, f"Price not formatted correctly in: {line!r}"
        assert "2026-07-13 10:00" in line, f"Timestamp wrong in: {line!r}"
        # Verify full format: 'YYYY-MM-DD HH:MM, price'
        parts = line.split(", ")
        assert len(parts) == 2, f"Line format wrong (expected 'ts, price'): {line!r}"


# ---------------------------------------------------------------------------
# AC-3: no exception on adapter errors during cycles
# ---------------------------------------------------------------------------

def test_smoke_survives_log_error(monkeypatch, tmp_path):
    """
    Even if log_price raises IOError, the loop must complete without crash (AC-3).
    Toast must still fire; log file may be empty due to errors.
    """
    monkeypatch.setattr(price_tracker, "SIMULATION", True)
    monkeypatch.setattr(price_tracker, "TEST_PRICE", 220.0)
    monkeypatch.setattr(price_tracker, "THRESHOLD", 230.0)
    monkeypatch.setattr(price_tracker, "CHECK_INTERVAL", 0)

    monday = _market_open_datetime()
    monkeypatch.setattr(
        "price_tracker.datetime",
        type("FakeDT", (), {"now": staticmethod(lambda: monday)})
    )

    # Redirect LOG_PATH but make writes fail
    log_file = tmp_path / "price_log.txt"
    monkeypatch.setattr(price_tracker, "LOG_PATH", log_file)

    import builtins
    real_open = builtins.open

    def bad_open(path, *args, **kwargs):
        if "price_log" in str(path):
            raise IOError("disk full")
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", bad_open)

    toast_calls = []

    class FakeNotification:
        def __init__(self, app_id, title, msg, duration="short"):
            toast_calls.append({"title": title, "msg": msg})
        def show(self):
            pass

    monkeypatch.setattr(price_tracker, "Notification", FakeNotification)

    _break_after_n_cycles(2, monkeypatch)

    try:
        price_tracker.main()
    except SystemExit:
        pass
    except Exception as exc:
        pytest.fail(f"main() must not crash on log errors: {exc}")

    # Toast should still fire despite log errors
    assert len(toast_calls) == 2


# ---------------------------------------------------------------------------
# AC-2: toast NOT fired when simulated price >= threshold
# ---------------------------------------------------------------------------

def test_smoke_no_toast_above_threshold(monkeypatch, tmp_path):
    """When test_price >= threshold, no toasts must fire across 2 cycles (AC-2)."""
    monkeypatch.setattr(price_tracker, "SIMULATION", True)
    monkeypatch.setattr(price_tracker, "TEST_PRICE", 240.0)   # above threshold
    monkeypatch.setattr(price_tracker, "THRESHOLD", 230.0)
    monkeypatch.setattr(price_tracker, "CHECK_INTERVAL", 0)

    monday = _market_open_datetime()
    monkeypatch.setattr(
        "price_tracker.datetime",
        type("FakeDT", (), {"now": staticmethod(lambda: monday)})
    )

    log_file = tmp_path / "price_log.txt"
    monkeypatch.setattr(price_tracker, "LOG_PATH", log_file)

    toast_calls = []

    class FakeNotification:
        def __init__(self, app_id, title, msg, duration="short"):
            toast_calls.append({"title": title, "msg": msg})
        def show(self):
            pass

    monkeypatch.setattr(price_tracker, "Notification", FakeNotification)

    _break_after_n_cycles(2, monkeypatch)

    try:
        price_tracker.main()
    except SystemExit:
        pass

    # 2 log entries (price is valid), but no toasts
    lines = log_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert len(toast_calls) == 0, "Toast must NOT fire when price >= threshold"


# ---------------------------------------------------------------------------
# AC-1 & AC-4: log entry format verification in detail
# ---------------------------------------------------------------------------

def test_smoke_log_entry_format(monkeypatch, tmp_path):
    """Each log entry must be 'YYYY-MM-DD HH:MM, 220.00' — no extra fields (AC-4)."""
    monkeypatch.setattr(price_tracker, "SIMULATION", True)
    monkeypatch.setattr(price_tracker, "TEST_PRICE", 220.0)
    monkeypatch.setattr(price_tracker, "THRESHOLD", 230.0)
    monkeypatch.setattr(price_tracker, "CHECK_INTERVAL", 0)

    monday = _market_open_datetime()
    monkeypatch.setattr(
        "price_tracker.datetime",
        type("FakeDT", (), {"now": staticmethod(lambda: monday)})
    )

    log_file = tmp_path / "price_log.txt"
    monkeypatch.setattr(price_tracker, "LOG_PATH", log_file)
    class FakeNotification:
        def __init__(self, **kwargs):
            pass
        def show(self):
            pass
    monkeypatch.setattr(price_tracker, "Notification", FakeNotification)

    _break_after_n_cycles(1, monkeypatch)

    try:
        price_tracker.main()
    except SystemExit:
        pass

    lines = log_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    # Exact expected line
    assert lines[0] == "2026-07-13 10:00, 220.00"
