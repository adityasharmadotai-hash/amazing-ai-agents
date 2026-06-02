"""Google Sheets output."""
import gspread

from .gmail_client import get_credentials

HEADERS = [
    "Date", "Sender", "Subject", "Email Summary",
    "Action Item", "Priority", "Status",
]


def get_sheet(sheet_name: str, token_file: str = "token.json"):
    """Open the sheet by name, creating it (with headers) if missing."""
    creds = get_credentials(token_file=token_file)
    client = gspread.authorize(creds)
    try:
        sh = client.open(sheet_name)
    except gspread.SpreadsheetNotFound:
        sh = client.create(sheet_name)
    ws = sh.sheet1
    # Ensure header row exists.
    if ws.row_values(1) != HEADERS:
        ws.update("A1", [HEADERS])
    return ws


def append_rows(ws, records: list[dict]) -> None:
    """Append analyzed emails to the sheet."""
    rows = [
        [
            r.get("date", ""),
            r.get("sender", ""),
            r.get("subject", ""),
            r.get("summary", ""),
            r.get("action_item", ""),
            r.get("priority", ""),
            r.get("status", "Pending"),
        ]
        for r in records
    ]
    if rows:
        ws.append_rows(rows, value_input_option="USER_ENTERED")
