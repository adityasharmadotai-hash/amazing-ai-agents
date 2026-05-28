"""
modules/parser.py
-----------------
Extracts raw text from uploaded resume files (PDF or DOCX).
Also accepts pasted LinkedIn profile text directly.
"""

from __future__ import annotations
import io
import re


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from a PDF file using pdfplumber with pypdf fallback."""
    text = ""

    # Try pdfplumber first (better layout handling)
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            pages = [p.extract_text() or "" for p in pdf.pages]
            text = "\n".join(pages)
        if text.strip():
            return _clean_text(text)
    except Exception:
        pass

    # Fallback: pypdf
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(file_bytes))
        pages = [page.extract_text() or "" for page in reader.pages]
        text = "\n".join(pages)
    except Exception as e:
        raise ValueError(f"Could not parse PDF: {e}") from e

    return _clean_text(text)


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text from a DOCX file."""
    try:
        from docx import Document
        doc = Document(io.BytesIO(file_bytes))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return _clean_text("\n".join(paragraphs))
    except Exception as e:
        raise ValueError(f"Could not parse DOCX: {e}") from e


def extract_text(uploaded_file) -> str:
    """
    Dispatch to the correct extractor based on file extension.
    Accepts a Streamlit UploadedFile object.
    """
    name = uploaded_file.name.lower()
    file_bytes = uploaded_file.read()

    if name.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)
    elif name.endswith(".docx"):
        return extract_text_from_docx(file_bytes)
    elif name.endswith(".txt"):
        return _clean_text(file_bytes.decode("utf-8", errors="ignore"))
    else:
        raise ValueError(f"Unsupported file type: {uploaded_file.name}")


def clean_linkedin_text(raw: str) -> str:
    """Clean up pasted LinkedIn profile text."""
    return _clean_text(raw)


def _clean_text(text: str) -> str:
    """Normalize whitespace and remove non-printable characters."""
    text = re.sub(r"[^\x20-\x7E\n]", " ", text)
    text = re.sub(r" {2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
