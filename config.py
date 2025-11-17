# config.py
import os
from pathlib import Path

# --- PHANTOM CONFIGURATION ---
PHANTOM_ID = "bfnaelmomeimhlpmgjnjophhpkkoljpa"

# --- CHROME PROFILE PATHS ---
# ⚠️ Make sure this path is correct for your system
SRC_PROFILE = Path.home() / "Library/Application Support/Google/Chrome/Default"
WORK_ROOT = Path.home() / "phantom-selenium-profile"
DST_PROFILE = WORK_ROOT / "Default"

# --- CREDENTIALS ---
# Fetches the password from an environment variable for security
PHANTOM_PASSWORD = os.getenv("PHANTOM_PASSWORD")