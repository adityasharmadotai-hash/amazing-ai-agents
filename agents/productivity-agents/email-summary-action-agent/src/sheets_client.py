"""
src/sheets_client.py
--------------------
Creates and updates the shareable Google Sheet.

On first run it creates a sheet, writes the header row, and saves the sheet ID
to the database. On every run after that it reuses that sheet and appends new
rows. The sheet is the human-friendly, shareable mirror of our SQLite data.
"""

from __future__ import annotations

from typing import Optional

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

import config
from src import database


class SheetsClient:
    def __init__(self, creds: Credentials):
        self.creds = creds
        self.service = build("sheets", "v4", credentials=creds)

    # --- sheet lifecycle -----------------------------------------------------
    def get_or_create_sheet(self) -> str:
        """Return a usable spreadsheet ID, creating one if needed."""
        sheet_id = config.SHEET_ID or database.get_meta("sheet_id")
        if sheet_id:
            return sheet_id

        spreadsheet = (
            self.service.spreadsheets()
            .create(
                body={
                    "properties": {"title": config.SHEET_TITLE},
                    "sheets": [{"properties": {"title": config.SHEET_TAB}}],
                },
                fields="spreadsheetId",
            )
            .execute()
        )
        sheet_id = spreadsheet["spreadsheetId"]
        database.set_meta("sheet_id", sheet_id)
        self._write_headers(sheet_id)
        return sheet_id

    def _write_headers(self, sheet_id: str) -> None:
        self.service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range=f"{config.SHEET_TAB}!A1",
            valueInputOption="RAW",
            body={"values": [config.SHEET_HEADERS]},
        ).execute()

    # --- writing rows --------------------------------------------------------
    def append_rows(self, records: list[dict]) -> int:
        """Append analyzed-email rows. Returns number of rows written."""
        if not records:
            return 0
        sheet_id = self.get_or_create_sheet()
        rows = [
            [
                r.get("date", ""),
                r.get("sender", ""),
                r.get("subject", ""),
                r.get("summary", ""),
                r.get("action_item", "None"),
                r.get("priority", "Low"),
                r.get("due_date", ""),
                r.get("status", "Pending"),
            ]
            for r in records
        ]
        self.service.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range=f"{config.SHEET_TAB}!A1",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": rows},
        ).execute()
        return len(rows)

    def sheet_url(self, sheet_id: Optional[str] = None) -> str:
        sheet_id = sheet_id or self.get_or_create_sheet()
        return f"https://docs.google.com/spreadsheets/d/{sheet_id}"
