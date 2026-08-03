"""Unit tests for Story 3.2: Log Adapter.

Covers all ACs for log_price() in price_tracker.py:
  - AC-1: line format is 'YYYY-MM-DD HH:MM, {price:.2f}' appended to price_log.txt
  - AC-2: file auto-created when it does not exist
  - AC-3: IOError caught, logged to stderr, returns None (no crash)
  - AC-4: file opened in 'a' (append) mode — existing entries never overwritten
  - AC-5: always returns None
  - AC-6: timestamp has no seconds; price formatted to exactly 2 decimal places

All tests redirect LOG_PATH to tmp_path — the real price_log.txt is never touched.
"""
from datetime import datetime
from pathlib import Path
import builtins

import pytest
import price_tracker


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _set_log_path(monkeypatch, tmp_path) -> Path:
    """Redirect LOG_PATH to a temp directory and return the temp log path."""
    log_file = tmp_path / "price_log.txt"
    monkeypatch.setattr(price_tracker, "LOG_PATH", log_file)
    return log_file


TS = datetime(2026, 7, 13, 10, 30, 0)   # Monday 10:30:00 — used across tests


# ---------------------------------------------------------------------------
# AC-1 & AC-6: correct line format written
# ---------------------------------------------------------------------------

def test_log_price_writes_correct_format(monkeypatch, tmp_path):
    """Line must be 'YYYY-MM-DD HH:MM, {price:.2f}'."""
    log_file = _set_log_path(monkeypatch, tmp_path)
    price_tracker.log_price(231.45, TS)
    lines = log_file.read_text(encoding="utf-8").splitlines()
    assert lines == ["2026-07-13 10:30, 231.45"]


def test_log_price_timestamp_has_no_seconds(monkeypatch, tmp_path):
    """Timestamp format must not include seconds."""
    log_file = _set_log_path(monkeypatch, tmp_path)
    price_tracker.log_price(231.45, TS)
    line = log_file.read_text(encoding="utf-8").strip()
    # Should have exactly 'YYYY-MM-DD HH:MM' — no seconds field
    timestamp_part = line.split(",")[0]
    assert len(timestamp_part) == len("2026-07-13 10:30")


def test_log_price_formats_price_two_decimals(monkeypatch, tmp_path):
    """Price must be formatted to exactly 2 decimal places."""
    log_file = _set_log_path(monkeypatch, tmp_path)
    price_tracker.log_price(229.9, TS)
    line = log_file.read_text(encoding="utf-8").strip()
    assert "229.90" in line


def test_log_price_format_with_round_number(monkeypatch, tmp_path):
    """Round number price must still show 2 decimal places."""
    log_file = _set_log_path(monkeypatch, tmp_path)
    price_tracker.log_price(230.0, TS)
    line = log_file.read_text(encoding="utf-8").strip()
    assert "230.00" in line


def test_log_price_line_ends_with_newline(monkeypatch, tmp_path):
    """Each written line must end with a newline character."""
    log_file = _set_log_path(monkeypatch, tmp_path)
    price_tracker.log_price(231.45, TS)
    raw = log_file.read_text(encoding="utf-8")
    assert raw.endswith("\n")


# ---------------------------------------------------------------------------
# AC-2: file auto-created when absent
# ---------------------------------------------------------------------------

def test_log_price_creates_file_if_absent(monkeypatch, tmp_path):
    """log_price() must create price_log.txt if it does not exist."""
    log_file = _set_log_path(monkeypatch, tmp_path)
    assert not log_file.exists(), "Pre-condition: file must not exist"
    price_tracker.log_price(231.45, TS)
    assert log_file.exists(), "File must be created after log_price() is called"


# ---------------------------------------------------------------------------
# AC-4: append mode — existing entries never overwritten
# ---------------------------------------------------------------------------

def test_log_price_appends_does_not_overwrite(monkeypatch, tmp_path):
    """Multiple calls must append lines, not overwrite."""
    log_file = _set_log_path(monkeypatch, tmp_path)
    ts1 = datetime(2026, 7, 13, 10, 30, 0)
    ts2 = datetime(2026, 7, 13, 10, 35, 0)
    price_tracker.log_price(231.45, ts1)
    price_tracker.log_price(229.80, ts2)
    lines = log_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert "231.45" in lines[0]
    assert "229.80" in lines[1]


def test_log_price_each_call_writes_exactly_one_line(monkeypatch, tmp_path):
    """Each log_price() call must append exactly one line (NFR-4)."""
    log_file = _set_log_path(monkeypatch, tmp_path)
    for i in range(5):
        ts = datetime(2026, 7, 13, 10, 30 + i, 0)
        price_tracker.log_price(230.0 + i, ts)
    lines = log_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 5


def test_log_price_preserves_existing_content(monkeypatch, tmp_path):
    """Existing content in price_log.txt must be preserved on each append."""
    log_file = _set_log_path(monkeypatch, tmp_path)
    existing = "2026-07-12 10:00, 235.00\n"
    log_file.write_text(existing, encoding="utf-8")
    price_tracker.log_price(231.45, TS)
    content = log_file.read_text(encoding="utf-8")
    assert content.startswith(existing), "Existing content must not be overwritten"
    assert "231.45" in content


# ---------------------------------------------------------------------------
# AC-3 & AC-5: IOError caught, logged to stderr, returns None
# ---------------------------------------------------------------------------

def test_log_price_ioerror_logged_to_stderr(monkeypatch, tmp_path, capsys):
    """An IOError must be caught and logged to stderr."""
    _set_log_path(monkeypatch, tmp_path)
    real_open = builtins.open

    def bad_open(path, *args, **kwargs):
        if "price_log" in str(path):
            raise IOError("disk full")
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", bad_open)
    price_tracker.log_price(231.45, TS)
    captured = capsys.readouterr()
    assert "Error writing price log" in captured.err


def test_log_price_ioerror_does_not_propagate(monkeypatch, tmp_path):
    """An IOError must not propagate — log_price must return cleanly."""
    _set_log_path(monkeypatch, tmp_path)
    real_open = builtins.open

    def bad_open(path, *args, **kwargs):
        if "price_log" in str(path):
            raise IOError("disk full")
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", bad_open)
    try:
        result = price_tracker.log_price(231.45, TS)
    except Exception as exc:
        pytest.fail(f"log_price raised unexpectedly: {exc}")
    assert result is None


# ---------------------------------------------------------------------------
# AC-5: always returns None
# ---------------------------------------------------------------------------

def test_log_price_returns_none_on_success(monkeypatch, tmp_path):
    """log_price() must return None on a successful write."""
    _set_log_path(monkeypatch, tmp_path)
    result = price_tracker.log_price(231.45, TS)
    assert result is None
