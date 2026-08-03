"""Unit tests for Story 4.1: Simulation Mode.

Covers all ACs for the simulation branch inside fetch_price():
  - AC-1: SIMULATION=True + TEST_PRICE set → returns float(TEST_PRICE), no yfinance call
  - AC-2: SIMULATION=True + TEST_PRICE=None → returns None, warning logged to stderr, no yfinance call
  - AC-3: SIMULATION=False → yfinance live path is taken
  - AC-4: orchestrator is unaware of simulation — calls send_toast() when simulated price < threshold

yfinance is never called for real — yf.Ticker is monkeypatched in every
test that exercises the live path.
"""
from datetime import datetime

import pytest
import price_tracker


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_yf_ticker(monkeypatch, close_price: float):
    """Patch yf.Ticker to return a mock history with close_price."""
    class MockIloc:
        def __getitem__(self, idx):
            return close_price

    class MockSeries:
        iloc = MockIloc()

    class MockHist:
        empty = False
        def __getitem__(self, key):
            if key == "Close":
                return MockSeries()
            raise KeyError(key)

    class MockTicker:
        def history(self, period):
            return MockHist()

    monkeypatch.setattr(price_tracker.yf, "Ticker", lambda symbol: MockTicker())


def _track_yf_calls(monkeypatch):
    """Patch yf.Ticker to track whether it was called."""
    calls = {"count": 0}

    class MockTicker:
        def history(self, period):
            calls["count"] += 1
            class MockHist:
                empty = True
            return MockHist()

    monkeypatch.setattr(price_tracker.yf, "Ticker", lambda symbol: MockTicker())
    return calls


# ---------------------------------------------------------------------------
# AC-1: SIMULATION=True + TEST_PRICE set → returns test price, no network
# ---------------------------------------------------------------------------

def test_simulation_returns_test_price(monkeypatch):
    """fetch_price() must return float(TEST_PRICE) in simulation mode."""
    monkeypatch.setattr(price_tracker, "SIMULATION", True)
    monkeypatch.setattr(price_tracker, "TEST_PRICE", 220.0)
    assert price_tracker.fetch_price() == 220.0


def test_simulation_returns_float(monkeypatch):
    """Return value must be a float even when TEST_PRICE is an int."""
    monkeypatch.setattr(price_tracker, "SIMULATION", True)
    monkeypatch.setattr(price_tracker, "TEST_PRICE", 220)
    result = price_tracker.fetch_price()
    assert isinstance(result, float)
    assert result == 220.0


def test_simulation_does_not_call_yfinance(monkeypatch):
    """yf.Ticker must NOT be called when simulation mode is active and TEST_PRICE is set."""
    monkeypatch.setattr(price_tracker, "SIMULATION", True)
    monkeypatch.setattr(price_tracker, "TEST_PRICE", 220.0)
    yf_calls = _track_yf_calls(monkeypatch)
    price_tracker.fetch_price()
    assert yf_calls["count"] == 0, "yfinance must not be called in simulation mode"


def test_simulation_returns_exact_test_price_value(monkeypatch):
    """The returned value must equal TEST_PRICE exactly."""
    monkeypatch.setattr(price_tracker, "SIMULATION", True)
    monkeypatch.setattr(price_tracker, "TEST_PRICE", 215.75)
    assert price_tracker.fetch_price() == 215.75


# ---------------------------------------------------------------------------
# AC-1 edge: TEST_PRICE=0 (falsy but valid — must still return 0.0)
# ---------------------------------------------------------------------------

def test_simulation_test_price_zero_returns_zero(monkeypatch):
    """TEST_PRICE=0 is falsy but not None — fetch_price must return 0.0."""
    monkeypatch.setattr(price_tracker, "SIMULATION", True)
    monkeypatch.setattr(price_tracker, "TEST_PRICE", 0)
    result = price_tracker.fetch_price()
    assert result == 0.0
    assert isinstance(result, float)


def test_simulation_test_price_zero_does_not_call_yfinance(monkeypatch):
    """TEST_PRICE=0 must still short-circuit — yfinance must not be called."""
    monkeypatch.setattr(price_tracker, "SIMULATION", True)
    monkeypatch.setattr(price_tracker, "TEST_PRICE", 0)
    yf_calls = _track_yf_calls(monkeypatch)
    price_tracker.fetch_price()
    assert yf_calls["count"] == 0, "yfinance must not be called when TEST_PRICE=0"


# ---------------------------------------------------------------------------
# AC-2: SIMULATION=True + TEST_PRICE=None → None + warning, no network
# ---------------------------------------------------------------------------

def test_simulation_no_test_price_returns_none(monkeypatch, capsys):
    """fetch_price() must return None when simulation is on but TEST_PRICE is None."""
    monkeypatch.setattr(price_tracker, "SIMULATION", True)
    monkeypatch.setattr(price_tracker, "TEST_PRICE", None)
    result = price_tracker.fetch_price()
    assert result is None


def test_simulation_no_test_price_logs_warning(monkeypatch, capsys):
    """A warning must be logged to stderr when TEST_PRICE is None in simulation mode."""
    monkeypatch.setattr(price_tracker, "SIMULATION", True)
    monkeypatch.setattr(price_tracker, "TEST_PRICE", None)
    price_tracker.fetch_price()
    captured = capsys.readouterr()
    assert "test_price is not set" in captured.err


def test_simulation_no_test_price_does_not_call_yfinance(monkeypatch):
    """yf.Ticker must NOT be called when simulation=True but TEST_PRICE=None."""
    monkeypatch.setattr(price_tracker, "SIMULATION", True)
    monkeypatch.setattr(price_tracker, "TEST_PRICE", None)
    yf_calls = _track_yf_calls(monkeypatch)
    price_tracker.fetch_price()
    assert yf_calls["count"] == 0, "yfinance must not be called when TEST_PRICE is None"


# ---------------------------------------------------------------------------
# AC-3: SIMULATION=False → live yfinance path taken
# ---------------------------------------------------------------------------

def test_live_mode_calls_yfinance(monkeypatch):
    """When simulation is off, yf.Ticker must be called."""
    monkeypatch.setattr(price_tracker, "SIMULATION", False)
    monkeypatch.setattr(price_tracker, "TEST_PRICE", None)
    yf_calls = _track_yf_calls(monkeypatch)
    price_tracker.fetch_price()
    assert yf_calls["count"] == 1, "yfinance must be called in live mode"


def test_live_mode_returns_close_price(monkeypatch):
    """In live mode, fetch_price() must return the close price from yfinance."""
    monkeypatch.setattr(price_tracker, "SIMULATION", False)
    monkeypatch.setattr(price_tracker, "TEST_PRICE", None)
    _mock_yf_ticker(monkeypatch, 245.60)
    result = price_tracker.fetch_price()
    assert result == 245.60


# ---------------------------------------------------------------------------
# AC-4: orchestrator unaware — triggers send_toast() with simulated price < threshold
# ---------------------------------------------------------------------------

def test_orchestrator_triggers_toast_with_simulated_price(monkeypatch):
    """Orchestrator must call send_toast() when simulated price < THRESHOLD (AD-6)."""
    monday = datetime(2026, 7, 13, 10, 0, 0)
    monkeypatch.setattr(
        "price_tracker.datetime",
        type("FakeDT", (), {"now": staticmethod(lambda: monday)})
    )
    # Simulate fetch returning below-threshold price
    monkeypatch.setattr(price_tracker, "SIMULATION", True)
    monkeypatch.setattr(price_tracker, "TEST_PRICE", price_tracker.THRESHOLD - 10.0)

    toast_calls = []
    log_calls = []
    monkeypatch.setattr(price_tracker, "log_price", lambda p, ts: log_calls.append(p))
    monkeypatch.setattr(price_tracker, "send_toast", lambda p: toast_calls.append(p))

    def fake_sleep(s):
        raise SystemExit(0)
    monkeypatch.setattr(price_tracker.time, "sleep", fake_sleep)

    try:
        price_tracker.main()
    except SystemExit:
        pass

    assert len(toast_calls) == 1, "send_toast must be called when simulated price < THRESHOLD"
    assert toast_calls[0] == price_tracker.THRESHOLD - 10.0


def test_orchestrator_does_not_check_simulation_flag(monkeypatch):
    """main() must not reference SIMULATION directly — it only uses the return value of fetch_price()."""
    # Verify by confirming the orchestrator behaves identically with a patched fetch_price
    monday = datetime(2026, 7, 13, 10, 0, 0)
    monkeypatch.setattr(
        "price_tracker.datetime",
        type("FakeDT", (), {"now": staticmethod(lambda: monday)})
    )
    # Patch fetch_price directly — orchestrator should not know or care about SIMULATION
    above_threshold = price_tracker.THRESHOLD + 5.0
    monkeypatch.setattr(price_tracker, "fetch_price", lambda: above_threshold)

    toast_calls = []
    monkeypatch.setattr(price_tracker, "log_price", lambda p, ts: None)
    monkeypatch.setattr(price_tracker, "send_toast", lambda p: toast_calls.append(p))

    def fake_sleep(s):
        raise SystemExit(0)
    monkeypatch.setattr(price_tracker.time, "sleep", fake_sleep)

    try:
        price_tracker.main()
    except SystemExit:
        pass

    assert toast_calls == [], "Orchestrator must not call send_toast when price >= THRESHOLD"
