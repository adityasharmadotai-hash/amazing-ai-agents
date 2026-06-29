"""Export service.

Exports query results and AI reports to CSV, Excel, JSON, Markdown and PDF.
All exports return raw bytes (for Streamlit download buttons) and are also
written to the configured ``export_dir`` for auditing.
"""

from __future__ import annotations

import io
import json
import os
from datetime import datetime
from typing import Optional

import pandas as pd

from core.exceptions import ExportError
from core.logging_config import get_logger
from core.models import QueryResult

logger = get_logger(__name__)


class ExportService:
    """Generates downloadable artefacts from results and reports."""

    def __init__(self, export_dir: str = "exports") -> None:
        self.export_dir = export_dir
        os.makedirs(export_dir, exist_ok=True)

    # --- helpers ----------------------------------------------------------
    @staticmethod
    def to_dataframe(result: QueryResult) -> pd.DataFrame:
        return pd.DataFrame(result.rows, columns=result.columns)

    def _timestamp(self) -> str:
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def _persist(self, filename: str, data: bytes) -> str:
        path = os.path.join(self.export_dir, filename)
        with open(path, "wb") as fh:
            fh.write(data)
        logger.info("Wrote export: %s (%d bytes)", path, len(data))
        return path

    # --- CSV --------------------------------------------------------------
    def to_csv(self, result: QueryResult, persist: bool = True) -> bytes:
        try:
            df = self.to_dataframe(result)
            data = df.to_csv(index=False).encode("utf-8")
            if persist:
                self._persist(f"result_{self._timestamp()}.csv", data)
            return data
        except Exception as exc:  # noqa: BLE001
            raise ExportError(detail=str(exc)) from exc

    # --- Excel ------------------------------------------------------------
    def to_excel(self, result: QueryResult, persist: bool = True) -> bytes:
        try:
            df = self.to_dataframe(result)
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                df.to_excel(writer, index=False, sheet_name="Results")
                meta = pd.DataFrame(
                    {
                        "metric": ["SQL", "Rows", "Execution time (ms)"],
                        "value": [result.sql, result.row_count, result.execution_time_ms],
                    }
                )
                meta.to_excel(writer, index=False, sheet_name="Metadata")
            data = buffer.getvalue()
            if persist:
                self._persist(f"result_{self._timestamp()}.xlsx", data)
            return data
        except Exception as exc:  # noqa: BLE001
            raise ExportError(detail=str(exc)) from exc

    # --- JSON -------------------------------------------------------------
    def to_json(self, result: QueryResult, persist: bool = True) -> bytes:
        try:
            payload = {
                "sql": result.sql,
                "columns": result.columns,
                "row_count": result.row_count,
                "execution_time_ms": result.execution_time_ms,
                "rows": result.to_records(),
            }
            data = json.dumps(payload, indent=2, default=str).encode("utf-8")
            if persist:
                self._persist(f"result_{self._timestamp()}.json", data)
            return data
        except Exception as exc:  # noqa: BLE001
            raise ExportError(detail=str(exc)) from exc

    # --- Markdown report --------------------------------------------------
    def to_markdown(
        self,
        title: str,
        report_markdown: str,
        result: Optional[QueryResult] = None,
        persist: bool = True,
    ) -> bytes:
        try:
            parts = [f"# {title}", "", report_markdown, ""]
            if result and result.rows:
                df = self.to_dataframe(result).head(50)
                parts.append("## Data (first 50 rows)")
                parts.append("")
                parts.append(df.to_markdown(index=False))
            data = "\n".join(parts).encode("utf-8")
            if persist:
                self._persist(f"report_{self._timestamp()}.md", data)
            return data
        except Exception as exc:  # noqa: BLE001
            raise ExportError(detail=str(exc)) from exc

    # --- PDF report -------------------------------------------------------
    def to_pdf(
        self,
        title: str,
        report_markdown: str,
        result: Optional[QueryResult] = None,
        persist: bool = True,
    ) -> bytes:
        """Render a simple, clean PDF report using ReportLab."""
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.units import cm
            from reportlab.platypus import (
                Paragraph,
                SimpleDocTemplate,
                Spacer,
                Table,
                TableStyle,
            )

            buffer = io.BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                leftMargin=2 * cm,
                rightMargin=2 * cm,
                topMargin=2 * cm,
                bottomMargin=2 * cm,
                title=title,
            )
            styles = getSampleStyleSheet()
            story = [Paragraph(title, styles["Title"]), Spacer(1, 12)]
            story.append(
                Paragraph(
                    f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    styles["Italic"],
                )
            )
            story.append(Spacer(1, 12))

            for block in report_markdown.split("\n\n"):
                block = block.strip()
                if not block:
                    continue
                if block.startswith("# "):
                    story.append(Paragraph(block[2:], styles["Heading1"]))
                elif block.startswith("## "):
                    story.append(Paragraph(block[3:], styles["Heading2"]))
                elif block.startswith("### "):
                    story.append(Paragraph(block[4:], styles["Heading3"]))
                else:
                    safe = block.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    story.append(Paragraph(safe.replace("\n", "<br/>"), styles["BodyText"]))
                story.append(Spacer(1, 8))

            if result and result.rows:
                story.append(Spacer(1, 12))
                story.append(Paragraph("Data sample (first 20 rows)", styles["Heading2"]))
                df = self.to_dataframe(result).head(20)
                table_data = [list(df.columns)] + df.astype(str).values.tolist()
                table = Table(table_data, repeatRows=1)
                table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563eb")),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                            ("FONTSIZE", (0, 0), (-1, -1), 7),
                            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")]),
                        ]
                    )
                )
                story.append(table)

            doc.build(story)
            data = buffer.getvalue()
            if persist:
                self._persist(f"report_{self._timestamp()}.pdf", data)
            return data
        except ImportError as exc:  # pragma: no cover
            raise ExportError("PDF export requires reportlab.", detail=str(exc)) from exc
        except Exception as exc:  # noqa: BLE001
            raise ExportError(detail=str(exc)) from exc
