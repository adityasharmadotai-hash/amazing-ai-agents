"""
config.py
---------
Central configuration for the Email Summary & Action Items Agent.

Everything tunable lives here so you never hunt through the codebase to change
a model name, a scope, or a file path. Values are pulled from environment
variables (via a .env file) with sensible defaults.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# --- Project paths -----------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# OAuth + token storage
CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", str(BASE_DIR / "credentials.json"))
TOKEN_FILE = os.getenv("GOOGLE_TOKEN_FILE", str(DATA_DIR / "token.json"))

# Local SQLite database
DB_PATH = os.getenv("DB_PATH", str(DATA_DIR / "emails.db"))

# --- Google API scopes -------------------------------------------------------
# Read-only Gmail + full Sheets/Drive access for creating and updating sheets.
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]

# --- OpenAI ------------------------------------------------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# --- Google Sheet ------------------------------------------------------------
# If you already have a sheet, set its ID; otherwise the app creates one and
# stores the ID in the database for reuse.
SHEET_ID = os.getenv("SHEET_ID", "")
SHEET_TITLE = os.getenv("SHEET_TITLE", "Email Action Items")
SHEET_TAB = "Inbox Actions"
SHEET_HEADERS = [
    "Date",
    "Sender",
    "Subject",
    "Email Summary",
    "Action Item",
    "Priority",
    "Due Date",
    "Status",
]

# --- Fetching defaults -------------------------------------------------------
DEFAULT_MAX_EMAILS = int(os.getenv("MAX_EMAILS", "25"))
DEFAULT_LABEL = os.getenv("DEFAULT_LABEL", "INBOX")

# Valid priority values, ordered most -> least urgent.
PRIORITIES = ["High", "Medium", "Low"]
STATUSES = ["Pending", "Completed"]
