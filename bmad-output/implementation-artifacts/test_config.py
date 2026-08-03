import json
import os
import sys
from pathlib import Path

import pytest

# Import the module under test
import config

# Helper to create a temporary config file and point the module to it
def write_config(tmp_path, data):
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(json.dumps(data), encoding="utf-8")
    # Patch the CONFIG_PATH used by config module
    config.CONFIG_PATH = cfg_path
    return cfg_path

def test_load_config_success(tmp_path):
    data = {"threshold": 230, "simulation_mode": False, "test_price": 200}
    write_config(tmp_path, data)
    cfg = config.load_config()
    assert cfg["threshold"] == 230.0
    assert cfg["simulation_mode"] is False
    assert cfg["test_price"] == 200.0

def test_load_config_missing_file(tmp_path):
    # Point to a non‑existent file
    config.CONFIG_PATH = Path("nonexistent.json")
    with pytest.raises(SystemExit):
        config.load_config()

def test_load_config_malformed_json(tmp_path):
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text("{ invalid json }", encoding="utf-8")
    config.CONFIG_PATH = cfg_path
    with pytest.raises(SystemExit):
        config.load_config()

def test_load_config_missing_key(tmp_path):
    # Missing 'threshold'
    data = {"simulation_mode": True}
    write_config(tmp_path, data)
    with pytest.raises(ValueError) as exc:
        config.load_config()
    assert "Missing required config key" in str(exc.value)

def test_load_config_wrong_type(tmp_path):
    # threshold as string
    data = {"threshold": "high", "simulation_mode": False}
    write_config(tmp_path, data)
    with pytest.raises(ValueError) as exc:
        config.load_config()
    assert "must be a number" in str(exc.value)
