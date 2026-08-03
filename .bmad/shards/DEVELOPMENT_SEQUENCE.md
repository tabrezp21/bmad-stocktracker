# Development Sequence

## 1. Environment Setup
1. Install Python 3.9+.
2. Create a virtual environment:
   ```
   python -m venv .venv
   .\.venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Verify `yfinance` and `plyer` import without errors.

## 2. Configuration
1. Edit `config.json` to set the desired `threshold` (default ₹230).
2. Optionally enable `simulation_mode` and set `test_price` for testing.

## 3. Core Implementation
1. Implement **Data Sourcing** (`price_tracker.py` – FR‑1).
2. Add **Scheduling & Market Hours** logic (FR‑2).
3. Integrate **Alert Channel** using `plyer` (FR‑3).
4. Add **Persistence** logging to `price_log.txt` (FR‑4).
5. Wire **Configuration** loading (FR‑5, FR‑6).
6. Implement **Error Handling** with retry loop (FR‑7).

## 4. Testing
1. Unit tests for each function (fetch, schedule, toast, logging, config parsing).
2. Integration test in `simulation_mode` to trigger an alert.
3. Verify log file format and rotation policy (address Open Question 2).

## 5. CI/CD (optional)
1. Add a GitHub Actions workflow to:
   - Set up Python.
   - Run `pip install -r requirements.txt`.
   - Execute tests.
2. Linting with `ruff` or `flake8`.

## 6. Deployment Configuration
1. Package script for distribution (e.g., PyInstaller) if required.
2. Create a Windows shortcut or scheduled task to run the script at login.
3. Document deployment steps in `README.md`.

## 7. Release
1. Tag a release version (e.g., `v1.0.0`).
2. Publish artifacts (executable, source archive).

---
*Each shard in `.bmad/shards/` corresponds to a functional area and can be edited independently. Follow the sequence above to build, test, and deploy the Price Tracker.*
