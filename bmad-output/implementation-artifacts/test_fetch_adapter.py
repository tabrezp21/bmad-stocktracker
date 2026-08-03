import json
from pathlib import Path

import pytest
import price_tracker


def test_fetch_price_simulation_mode(monkeypatch):
    """Simulation mode must return test_price without hitting the network."""
    monkeypatch.setattr(price_tracker, "SIMULATION", True)
    monkeypatch.setattr(price_tracker, "TEST_PRICE", 123.45)

    result = price_tracker.fetch_price()
    assert result == 123.45


def test_fetch_price_real_success(monkeypatch):
    """Real fetch should return the most recent close price as a float."""
    monkeypatch.setattr(price_tracker, "SIMULATION", False)
    monkeypatch.setattr(price_tracker, "TEST_PRICE", None)

    # Build a minimal pandas-like mock with iloc[-1] == 250.0
    class MockIloc:
        def __getitem__(self, idx):
            return 250.0

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
    price = price_tracker.fetch_price()
    assert isinstance(price, float)
    assert price == 250.0


def test_fetch_price_error_handling(monkeypatch, capsys):
    """Exceptions inside fetch_price must be caught; None returned and error logged."""
    monkeypatch.setattr(price_tracker, "SIMULATION", False)
    monkeypatch.setattr(price_tracker, "TEST_PRICE", None)

    class BadTicker:
        def history(self, period):
            raise RuntimeError("network error")

    monkeypatch.setattr(price_tracker.yf, "Ticker", lambda symbol: BadTicker())
    price = price_tracker.fetch_price()
    assert price is None
    captured = capsys.readouterr()
    assert "Error fetching price" in captured.err
