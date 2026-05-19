"""
exporter.py — Export cover letters and analyses to PDF
"""

import io
from datetime import datetime


def export_cover_letter_pdf(content: str, candidate_name: str, company: str, job_title: str) -> bytes:
    """Generate a PDF of the cover letter using reportlab."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=1 * inch,
            leftMargin=1 * inch,
            topMargin=1 * inch,
            bottomMargin=1 * inch,
        )

        styles = getSampleStyleSheet()
        story = []

        # Header style
        header_style = ParagraphStyle(
            "Header",
            parent=styles["Normal"],
            fontSize=14,
            fontName="Helvetica-Bold",
            textColor=colors.HexColor("#1e3a5f"),
            spaceAfter=4,
        )
        sub_style = ParagraphStyle(
            "Sub",
            parent=styles["Normal"],
            fontSize=10,
            fontName="Helvetica",
            textColor=colors.HexColor("#555555"),
            spaceAfter=2,
        )
        body_style = ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontSize=11,
            fontName="Helvetica",
            leading=16,
            spaceAfter=8,
        )
        date_style = ParagraphStyle(
            "Date",
            parent=styles["Normal"],
            fontSize=10,
            fontName="Helvetica",
            textColor=colors.HexColor("#888888"),
            spaceAfter=20,
        )

        story.append(Paragraph(candidate_name or "Candidate", header_style))
        story.append(Paragraph(f"Application for: {job_title} at {company}", sub_style))
        story.append(Spacer(1, 0.1 * inch))
        story.append(Paragraph(datetime.now().strftime("%B %d, %Y"), date_style))

        # Divider line via a colored box
        from reportlab.platypus import HRFlowable
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1e3a5f")))
        story.append(Spacer(1, 0.2 * inch))

        # Body text — split paragraphs
        for para in content.split("\n\n"):
            para = para.strip()
            if para:
                # Escape HTML-special chars for reportlab
                safe = para.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                story.append(Paragraph(safe, body_style))

        doc.build(story)
        buffer.seek(0)
        return buffer.read()

    except ImportError:
        # Fallback: plain text PDF-like bytes (actually just text)
        return content.encode("utf-8")
    except Exception as e:
        return f"Error generating PDF: {e}".encode("utf-8")


def export_analysis_pdf(match_result: dict, ats_result: dict, candidate_name: str, job_title: str, company: str) -> bytes:
    """Generate a PDF report of the job match and ATS analysis."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                                rightMargin=0.75*inch, leftMargin=0.75*inch,
                                topMargin=0.75*inch, bottomMargin=0.75*inch)
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle("Title", parent=styles["Normal"],
                                     fontSize=18, fontName="Helvetica-Bold",
                                     textColor=colors.HexColor("#1e3a5f"), spaceAfter=4)
        h2_style = ParagraphStyle("H2", parent=styles["Normal"],
                                  fontSize=13, fontName="Helvetica-Bold",
                                  textColor=colors.HexColor("#1e3a5f"), spaceAfter=6, spaceBefore=12)
        body_style = ParagraphStyle("Body", parent=styles["Normal"],
                                    fontSize=10, leading=14, spaceAfter=4)
        bullet_style = ParagraphStyle("Bullet", parent=styles["Normal"],
                                      fontSize=10, leading=14, leftIndent=12,
                                      bulletIndent=0, spaceAfter=3)

        story = []
        story.append(Paragraph("📊 Resume Analysis Report", title_style))
        story.append(Paragraph(f"{candidate_name}  →  {job_title} at {company}", body_style))
        story.append(Paragraph(datetime.now().strftime("%B %d, %Y"), body_style))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1e3a5f")))
        story.append(Spacer(1, 0.15*inch))

        # Match Score
        score = match_result.get("match_score", 0)
        grade = match_result.get("grade", "N/A")
        story.append(Paragraph("Job Match Analysis", h2_style))

        score_color = "#22c55e" if score >= 75 else "#f59e0b" if score >= 50 else "#ef4444"
        score_data = [
            ["Match Score", "Grade", "Experience Match", "Education Match"],
            [f"{score}%", grade,
             match_result.get("experience_match", "N/A"),
             match_result.get("education_match", "N/A")],
        ]
        score_table = Table(score_data, colWidths=[1.5*inch]*4)
        score_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f0f4ff"), colors.white]),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#d1d5db")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(score_table)
        story.append(Spacer(1, 0.1*inch))

        story.append(Paragraph(match_result.get("summary", ""), body_style))

        if match_result.get("strengths"):
            story.append(Paragraph("Strengths:", h2_style))
            for s in match_result["strengths"]:
                story.append(Paragraph(f"• {s}", bullet_style))

        if match_result.get("missing_skills"):
            story.append(Paragraph("Missing Skills:", h2_style))
            for s in match_result["missing_skills"]:
                story.append(Paragraph(f"• {s}", bullet_style))

        if match_result.get("recommendations"):
            story.append(Paragraph("Recommendations:", h2_style))
            for r in match_result["recommendations"]:
                story.append(Paragraph(f"• {r}", bullet_style))

        # ATS Section
        story.append(Spacer(1, 0.2*inch))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#d1d5db")))
        story.append(Paragraph("ATS Compatibility Analysis", h2_style))
        ats_score = ats_result.get("ats_score", 0)
        story.append(Paragraph(f"ATS Score: {ats_score}% ({ats_result.get('grade','N/A')})", body_style))
        story.append(Paragraph(ats_result.get("summary", ""), body_style))

        if ats_result.get("optimization_suggestions"):
            story.append(Paragraph("Optimization Suggestions:", h2_style))
            for s in ats_result["optimization_suggestions"]:
                p = s.get("priority", "")
                text = s.get("suggestion", "")
                story.append(Paragraph(f"• [{p}] {text}", bullet_style))

        doc.build(story)
        buffer.seek(0)
        return buffer.read()

    except ImportError:
        return b"reportlab not installed. Install it with: pip install reportlab"
    except Exception as e:
        return f"Error generating PDF: {e}".encode("utf-8")
