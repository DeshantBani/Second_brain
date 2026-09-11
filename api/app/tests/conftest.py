import os
import sys
from pathlib import Path

# Ensure `app` package is importable when pytest is invoked from the api/ directory.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

os.environ.setdefault("CASE_LAW_PROVIDER", "mock")
