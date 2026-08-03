"""Configuration loader for the Bank of Baroda Price Tracker.
Provides a single source of truth for tunable values via `config.json`.
"""

import json
import sys
from pathlib import Path

CONFIG_PATH = Path(__file__).with_name("config.json")

def load_config() -> dict:
    """Load and validate the configuration.
    Returns a dict with keys: threshold (float), simulation_mode (bool), test_price (float or None).
    Raises FileNotFoundError, json.JSONDecodeError, ValueError.
    """
    if not CONFIG_PATH.is_file():
        print(f"Error: config file not found at {CONFIG_PATH}", file=sys.stderr)
        sys.exit(1)
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error parsing config.json: {e}", file=sys.stderr)
        sys.exit(1)
    # Required keys
    for key in ("threshold", "simulation_mode"):
        if key not in data:
            raise ValueError(f"Missing required config key: {key}")
    if not isinstance(data["threshold"], (int, float)):
        raise ValueError("threshold must be a number")
    if not isinstance(data["simulation_mode"], bool):
        raise ValueError("simulation_mode must be a boolean")
    test_price = data.get("test_price")
    if test_price is not None and not isinstance(test_price, (int, float)):
        raise ValueError("test_price must be a number if provided")
    return {
        "threshold": float(data["threshold"]),
        "simulation_mode": bool(data["simulation_mode"]),
        "test_price": float(test_price) if test_price is not None else None,
    }
