"""Export analyzed emails to CSV / Excel / PDF."""
import io

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

COLUMNS = ["date", "sender", "subject", "summary",
           "action_item", "priority", "status"]


def _frame(emails: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(emails)
    cols = [c for c in COLUMNS if c in df.columns]
    return df[cols] if cols else df


def to_csv(emails: list[dict]) -> bytes:
    return _frame(emails).to_csv(index=False).encode("utf-8")


def to_excel(emails: list[dict]) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        _frame(emails).to_excel(writer, index=False, sheet_name="Emails")
    return buf.getvalue()


def to_pdf(emails: list[dict]) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(letter))
    df = _frame(emails)
    data = [list(df.columns)] + df.astype(str).values.tolist()
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4F46E5")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    doc.build([table])
    return buf.getvalue()
