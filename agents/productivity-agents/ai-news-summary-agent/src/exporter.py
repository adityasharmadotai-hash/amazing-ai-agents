"""
src/exporter.py
---------------
Export the analyzed inbox to CSV, Excel, or PDF.

Each function returns raw bytes so Streamlit can hand them straight to a
download button without writing temp files.
"""

from __future__ import annotations

import io

import pandas as pd

from src import database

EXPORT_COLUMNS = [
    "date",
    "sender",
    "subject",
    "summary",
    "action_item",
    "priority",
    "due_date",
    "status",
]
PRETTY = {
    "date": "Date",
    "sender": "Sender",
    "subject": "Subject",
    "summary": "Email Summary",
    "action_item": "Action Item",
    "priority": "Priority",
    "due_date": "Due Date",
    "status": "Status",
}


def _frame() -> pd.DataFrame:
    rows = database.get_all_emails()
    df = pd.DataFrame(rows)
    if df.empty:
        df = pd.DataFrame(columns=EXPORT_COLUMNS)
    df = df[[c for c in EXPORT_COLUMNS if c in df.columns]]
    return df.rename(columns=PRETTY)


def to_csv() -> bytes:
    return _frame().to_csv(index=False).encode("utf-8")


def to_excel() -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        _frame().to_excel(writer, index=False, sheet_name="Action Items")
    return buf.getvalue()


def to_pdf() -> bytes:
    """Render a simple tabular PDF report with reportlab."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    df = _frame()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), title="Email Action Items")
    styles = getSampleStyleSheet()
    elements = [Paragraph("Email Summary & Action Items", styles["Title"]), Spacer(1, 12)]

    # Keep the PDF readable: trim long fields.
    display_cols = ["Date", "Sender", "Subject", "Action Item", "Priority", "Status"]
    cols = [c for c in display_cols if c in df.columns]
    header = cols
    data = [header]
    for _, row in df.iterrows():
        data.append([str(row.get(c, ""))[:60] for c in cols])

    table = Table(data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4F46E5")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F4F6")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    elements.append(table)
    doc.build(elements)
    return buf.getvalue()
