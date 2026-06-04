"""
modules/newsletter.py
---------------------
Assembles the structured AI output + source list into a final Markdown
document ready for preview, copy, and download.
"""

from datetime import datetime


def build_markdown(generated: dict, summaries: list = None,
                   include_sources: bool = True) -> str:
    """Render the generated newsletter dict into clean Markdown."""
    summaries = summaries or []
    lines = []

    title = generated.get("title", "").strip() or "Untitled Newsletter"
    subject = generated.get("subject_line", "").strip()
    intro = generated.get("introduction", "").strip()
    insights = generated.get("key_insights", [])
    conclusion = generated.get("conclusion", "").strip()
    cta = generated.get("cta", "").strip()

    lines.append(f"# {title}")
    lines.append("")
    if subject:
        lines.append(f"**Subject line:** {subject}")
        lines.append("")
    lines.append(f"*{datetime.utcnow().strftime('%B %d, %Y')}*")
    lines.append("")
    lines.append("---")
    lines.append("")

    if intro:
        lines.append(intro)
        lines.append("")

    if insights:
        lines.append("## Key Insights")
        lines.append("")
        for i, ins in enumerate(insights, 1):
            heading = ins.get("heading", "").strip()
            body = ins.get("body", "").strip()
            if heading:
                lines.append(f"### {i}. {heading}")
            else:
                lines.append(f"### {i}.")
            lines.append("")
            if body:
                lines.append(body)
                lines.append("")

    if conclusion:
        lines.append("## Conclusion")
        lines.append("")
        lines.append(conclusion)
        lines.append("")

    if cta:
        lines.append("---")
        lines.append("")
        lines.append(f"**{cta}**")
        lines.append("")

    if include_sources and summaries:
        lines.append("---")
        lines.append("")
        lines.append("### Sources")
        lines.append("")
        for s in summaries:
            src_title = s.get("title", "Source")
            url = s.get("url", "")
            source_name = s.get("source", "")
            label = f"{src_title}" + (f" — *{source_name}*" if source_name else "")
            if url:
                lines.append(f"- [{label}]({url})")
            else:
                lines.append(f"- {label}")
        lines.append("")

    return "\n".join(lines).strip() + "\n"
