import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]          # repository root (holds assessment-0N.json and oa_lib.py)
DB_PATH = Path(os.environ.get("OA_DB", ROOT / "data" / "attempts.db"))
TEST_MODE = os.environ.get("OA_TEST_MODE") == "1"    # enables /api/test/* (fake clock). Never enable for real use.
DIST = ROOT / "frontend" / "dist"
SECTIONS = ["mcq", "apt", "da", "sql", "pandas", "dsa"]
PROFILES = {"standard": "standard"}   # candidate-facing name -> key in the bank's `timing` (one fixed schedule per OA)
