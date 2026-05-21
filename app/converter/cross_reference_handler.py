"""Handle bookmarks and cross-reference fields (REF/PAGEREF).

Word documents can contain bookmarks and internal cross-references
that refer to those bookmarks. This module detects them and converts
them to Markdown anchor links.
"""

import re

from lxml import etree

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


class CrossReferenceHandler:
    """Detects bookmarks and REF fields, converts to Markdown links."""

    def __init__(self, python_docx_document):
        self.bookmarks: dict[str, str] = {}
        self._parse_bookmarks(python_docx_document)

    def _parse_bookmarks(self, doc) -> None:
        """Scan all paragraphs for bookmarkStart elements."""
        for paragraph in doc.paragraphs:
            for bm in paragraph._element.iter(f"{{{W_NS}}}bookmarkStart"):
                name = bm.get(f"{{{W_NS}}}name")
                if name and name != "_GoBack":
                    self.bookmarks[name] = self._anchor_id(name)

    @staticmethod
    def _anchor_id(name: str) -> str:
        """Generate a GitHub-flavored Markdown anchor ID from bookmark name.

        Rules: lowercase, remove punctuation (except - and _),
        spaces to hyphens, collapse consecutive hyphens.
        """
        anchor = name.lower().strip()
        anchor = re.sub(r'[^\w\s\-_]', '', anchor)
        anchor = re.sub(r'[\s_]+', '-', anchor)
        anchor = re.sub(r'-+', '-', anchor)
        return anchor.strip('-')

    def get_anchor_id(self, bookmark_name: str) -> str:
        """Get the anchor ID for a bookmark, computing it if not already known."""
        if bookmark_name not in self.bookmarks:
            self.bookmarks[bookmark_name] = self._anchor_id(bookmark_name)
        return self.bookmarks[bookmark_name]

    def resolve_ref(self, paragraph_element, display_text: str) -> str | None:
        """If the paragraph contains a REF/PAGEREF field, return a Markdown link.

        Args:
            paragraph_element: The lxml paragraph element.
            display_text: The current display text of the paragraph.

        Returns:
            Markdown link string if a cross-reference is found, None otherwise.
        """
        target_bookmark = None
        for instr in paragraph_element.iter(f"{{{W_NS}}}instrText"):
            if instr.text:
                text = instr.text.strip()
                if text.startswith("REF ") or text.startswith("PAGEREF "):
                    parts = text.split()
                    if len(parts) >= 2:
                        target_bookmark = parts[1].rstrip("\\")
                        break

        if target_bookmark is None:
            return None

        anchor = self.get_anchor_id(target_bookmark)
        return f"[{display_text}](#{anchor})"

    @staticmethod
    def has_ref_field(paragraph_element) -> bool:
        """Check if a paragraph contains a REF or PAGEREF field."""
        for instr in paragraph_element.iter(f"{{{W_NS}}}instrText"):
            if instr.text:
                t = instr.text.strip()
                if t.startswith("REF ") or t.startswith("PAGEREF "):
                    return True
        return False
