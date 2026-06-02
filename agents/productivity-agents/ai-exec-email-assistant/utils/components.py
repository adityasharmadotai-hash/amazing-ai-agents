"""Reusable Streamlit render components."""
from __future__ import annotations

from typing import Iterable

import streamlit as st

from database.models import Email
from utils.theme import pill


def email_card(email: Email, key_prefix: str = "") -> None:
    pills = []
    if email.is_unread:
        pills.append(pill("Unread", "accent"))
    if email.is_starred:
        pills.append(pill("★ Starred", "warn"))
    if email.is_important:
        pills.append(pill("Important", "bad"))
    if email.needs_followup:
        pills.append(pill("Follow-up", "good"))
    when = email.received_at.strftime("%d %b, %H:%M") if email.received_at else ""
    unread_mark = "🔵 " if email.is_unread else ""
    title = f"{unread_mark}**{email.subject or '(no subject)'}** — {email.sender}"
    with st.expander(title, expanded=False):
        meta = " · ".join(filter(None, [email.sender_email, when]))
        st.caption(meta)
        if pills:
            st.markdown(" ".join(pills), unsafe_allow_html=True)
        if email.ai_summary:
            st.info(f"💡 {email.ai_summary}")
        body = email.body or email.snippet or "(no content)"
        st.write(body[:3000] + ("…" if len(body) > 3000 else ""))


def email_list(emails: Iterable[Email], empty_msg: str = "No emails found.",
               key_prefix: str = "") -> None:
    emails = list(emails)
    if not emails:
        st.info(empty_msg)
        return
    for i, e in enumerate(emails):
        email_card(e, key_prefix=f"{key_prefix}_{i}")


def export_buttons(title: str, content: str, key_prefix: str = "exp") -> None:
    """Render PDF / DOCX / Markdown download buttons for any content."""
    from services.export_service import ExportService

    if not content:
        return
    c1, c2, c3 = st.columns(3)
    safe = "".join(ch if ch.isalnum() else "_" for ch in title)[:40] or "export"
    with c1:
        st.download_button(
            "⬇️ PDF", ExportService.to_pdf(title, content),
            file_name=f"{safe}.pdf", mime="application/pdf",
            use_container_width=True, key=f"{key_prefix}_pdf",
        )
    with c2:
        st.download_button(
            "⬇️ DOCX", ExportService.to_docx(title, content),
            file_name=f"{safe}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True, key=f"{key_prefix}_docx",
        )
    with c3:
        st.download_button(
            "⬇️ Markdown", ExportService.to_markdown(title, content),
            file_name=f"{safe}.md", mime="text/markdown",
            use_container_width=True, key=f"{key_prefix}_md",
        )
