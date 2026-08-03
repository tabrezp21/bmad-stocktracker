import sys
from pathlib import Path

# Ensure the project root is on sys.path so test modules can import
# price_tracker, config, etc. regardless of where pytest is invoked from.
sys.path.insert(0, str(Path(__file__).parent))
