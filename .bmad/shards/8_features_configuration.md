# 4.5 Configuration

**Description:** Read `config.json` from the script directory to obtain `threshold` and optional `simulation_mode`.

**Functional Requirements:**

- **FR‑5: Configurable Threshold**
  - User can set `"threshold": 230` in `config.json` to change the alert level without code changes.

- **FR‑6: Simulation Mode**
  - When `"simulation_mode": true`, the script uses a stubbed price value defined in `"test_price"` to force an alert for testing.

**Out of Scope:**
- Dynamic reloading of config while the script runs.
