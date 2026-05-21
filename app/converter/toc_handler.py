"""Detect and handle Table of Contents (TOC) elements in DOCX documents.

Word TOC fields are complex field codes stored as OOXML <w:instrText> elements.
This module provides detection of TOC elements and generation of actual
Markdown table-of-contents from heading structures.
"""

import re


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
    """Determine if a paragraph belongs to a TOC based on its style name."""
    if not style_name:
        return False
    return detect_toc_by_style(style_name)


def _anchor_id(heading_text: str) -> str:
    """Generate a GitHub-flavored Markdown anchor ID from heading text.

    Rules: lowercase, remove punctuation except - and _, spaces to hyphens,
    collapse consecutive hyphens.
    """
    anchor = heading_text.lower().strip()
    anchor = re.sub(r'[^\w\s\-_]', '', anchor)
    anchor = re.sub(r'[\s_]+', '-', anchor)
    anchor = re.sub(r'-+', '-', anchor)
    return anchor.strip('-')


class TocGenerator:
    """Generates a Markdown table of contents from document headings."""

    def __init__(self, headings: list[tuple[int, str]]):
        """Args:
            headings: [(level, text), ...] in document order.
        """
        self._headings = headings
        self._used_anchors: dict[str, int] = {}

    def _unique_anchor(self, heading_text: str) -> str:
        """Generate a unique anchor ID, handling duplicates."""
        base = _anchor_id(heading_text)
        if base not in self._used_anchors:
            self._used_anchors[base] = 1
            return base
        count = self._used_anchors[base]
        self._used_anchors[base] = count + 1
        return f"{base}-{count}"

    def generate(self, max_level: int = 3) -> str:
        """Generate a Markdown TOC list.

        Args:
            max_level: Maximum heading level to include (default 3).

        Returns:
            Markdown string of the TOC, e.g.:
            - [Introduction](#introduction)
                - [Background](#background)
            - [Methods](#methods)
        """
        if not self._headings:
            return ""

        lines = []
        for level, text in self._headings:
            if level > max_level:
                continue
            anchor = self._unique_anchor(text)
            indent = "    " * (level - 1)
            lines.append(f"{indent}- [{text}](#{anchor})")

        return "\n".join(lines)
