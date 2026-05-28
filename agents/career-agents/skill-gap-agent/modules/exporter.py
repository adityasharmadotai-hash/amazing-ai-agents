"""
modules/exporter.py
-------------------
Generates downloadable PDF reports using ReportLab.
"""

from __future__ import annotations
import io
from datetime import datetime
from pathlib import Path

EXPORTS_DIR = Path("exports")


def _ensure_dir() -> None:
    EXPORTS_DIR.mkdir(exist_ok=True)


def export_full_report(
    profile: dict,
    readiness: dict,
    gap_analysis: dict,
    roadmap: dict,
    courses: dict,
    target_role: str,
    industry: str,
) -> bytes:
    """Generate a comprehensive skill gap PDF report."""
    _ensure_dir()
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.platypus import (
            SimpleDocTemplate,
            Paragraph,
            Spacer,
            Table,
            TableStyle,
            HRFlowable,
        )
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
    except ImportError:
        raise ImportError("reportlab is required: pip install reportlab")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()
    PURPLE = colors.HexColor("#7C3AED")
    DARK = colors.HexColor("#1A1A2E")
    GRAY = colors.HexColor("#64748B")

    title_style = ParagraphStyle(
        "Title", parent=styles["Title"],
        textColor=PURPLE, fontSize=22, spaceAfter=4,
    )
    h1_style = ParagraphStyle(
        "H1", parent=styles["Heading1"],
        textColor=PURPLE, fontSize=14, spaceAfter=6, spaceBefore=14,
    )
    h2_style = ParagraphStyle(
        "H2", parent=styles["Heading2"],
        textColor=DARK, fontSize=11, spaceAfter=4, spaceBefore=8,
    )
    body_style = ParagraphStyle(
        "Body", parent=styles["Normal"],
        fontSize=9, leading=13, spaceAfter=4,
    )
    small_style = ParagraphStyle(
        "Small", parent=styles["Normal"],
        fontSize=8, textColor=GRAY, spaceAfter=2,
    )

    elements = []
    name = profile.get("name", "Candidate")
    score = readiness.get("overall_score", 0)
    grade = readiness.get("grade", "?")

    # Header
    elements.append(Paragraph("AI Skill Gap Analysis Report", title_style))
    elements.append(Paragraph(f"Prepared for: {name}", h2_style))
    elements.append(Paragraph(
        f"Target Role: {target_role} | Industry: {industry} | "
        f"Generated: {datetime.now().strftime('%B %d, %Y')}",
        small_style,
    ))
    elements.append(HRFlowable(width="100%", thickness=1, color=PURPLE, spaceAfter=10))

    # Readiness Score
    elements.append(Paragraph("Career Readiness Score", h1_style))
    score_data = [
        ["Overall Score", "Grade", "Timeline", "Market Position"],
        [
            f"{score}/100",
            f"{grade} — {readiness.get('grade_label', '')}",
            readiness.get("timeline_to_ready", "N/A"),
            readiness.get("market_positioning", "N/A")[:60],
        ],
    ]
    t = Table(score_data, colWidths=[1.2 * inch, 2 * inch, 1.5 * inch, 2.3 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PURPLE),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("FONTSIZE", (0, 1), (-1, 1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements += [t, Spacer(1, 10)]

    # Score Breakdown
    breakdown = readiness.get("score_breakdown", {})
    if breakdown:
        bd_data = [["Category", "Score", "Weight"]]
        for cat, vals in breakdown.items():
            bd_data.append([
                cat.replace("_", " ").title(),
                f"{vals.get('score', 0)}/100",
                f"{int(vals.get('weight', 0) * 100)}%",
            ])
        t2 = Table(bd_data, colWidths=[3 * inch, 1.5 * inch, 1.5 * inch])
        t2.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), DARK),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        elements += [t2, Spacer(1, 10)]

    # Skill Gaps
    elements.append(Paragraph("Critical Skill Gaps", h1_style))
    missing = gap_analysis.get("missing_skills", [])
    if missing:
        gap_data = [["Skill", "Priority", "Difficulty", "Weeks to Learn"]]
        for s in missing[:10]:
            gap_data.append([
                s.get("skill", ""),
                s.get("priority", "").upper(),
                s.get("difficulty", ""),
                str(s.get("weeks_to_learn", "?")),
            ])
        t3 = Table(gap_data, colWidths=[2.5 * inch, 1.2 * inch, 1.2 * inch, 1.5 * inch])
        t3.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PURPLE),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        elements += [t3, Spacer(1, 10)]

    # 6-Month Roadmap
    elements.append(Paragraph("6-Month Learning Roadmap", h1_style))
    monthly = roadmap.get("monthly_plan", [])
    for month in monthly:
        elements.append(Paragraph(
            f"Month {month.get('month', '?')}: {month.get('theme', '')}",
            h2_style,
        ))
        elements.append(Paragraph(
            f"Focus: {', '.join(month.get('focus_areas', []))} | "
            f"Hours/week: {month.get('hours_per_week', '?')}",
            small_style,
        ))
        elements.append(Paragraph(
            f"Milestone: {month.get('milestone', '')}",
            body_style,
        ))

    # Quick Wins
    quick = readiness.get("quick_wins", [])
    if quick:
        elements.append(Paragraph("Quick Wins (Start Now)", h1_style))
        for qw in quick:
            elements.append(Paragraph(f"• {qw}", body_style))

    # Footer
    elements.append(Spacer(1, 20))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=GRAY))
    elements.append(Paragraph(
        "Generated by AI Skill Gap Agent — Powered by GPT-4o",
        small_style,
    ))

    doc.build(elements)
    return buffer.getvalue()
