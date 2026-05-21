"""Detect and handle Table of Contents (TOC) elements in DOCX documents.

Word TOC fields are complex field codes stored as OOXML <w:instrText> elements.
docx2python does not render them. This module provides detection and placeholder
generation for TOC elements.
"""


def detect_toc_by_style(style_name: str) -> bool:
    """Check if a paragraph style indicates a TOC entry."""
    return style_name.strip().upper().startswith("TOC")


def format_toc_placeholder() -> str:
    """Return the markdown placeholder for a TOC."""
    return "[TOC]"


def detect_toc_field_in_document(python_docx_document) -> bool:
    """Check if the document contains a TOC field code using python-docx.

    Args:
        python_docx_document: A python-docx Document object.

    Returns:
        True if a TOC field code is found in any paragraph.
    """
    ns = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    for paragraph in python_docx_document.paragraphs:
        for instr in paragraph._element.iter(f"{{{ns}}}instrText"):
            if instr.text and "TOC" in instr.text.upper():
                return True
    return False


def is_toc_paragraph(style_name: str) -> bool:
    """Determine if a paragraph belongs to a TOC based on its style name.

    Args:
        style_name: Paragraph style name from docx2python.

    Returns:
        True if this paragraph appears to be part of a TOC.
    """
    if not style_name:
        return False
    return detect_toc_by_style(style_name)
