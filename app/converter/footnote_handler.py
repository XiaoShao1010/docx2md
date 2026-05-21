"""Handle footnotes and endnotes conversion.

docx2python v3 extracts footnote and endnote content and inserts
placeholders like ``----footnote1----`` and ``----endnote1----`` in the body text.
This module:
1. Collects footnote/endnote definitions from the _pars structures.
2. Replaces inline placeholders with numbered references [^N].
3. Appends the definitions at the end of the document.
"""

import re
from app.converter.inline_formatter import format_par_runs

FOOTNOTE_PLACEHOLDER = re.compile(r"----footnote(\d+)----")
ENDNOTE_PLACEHOLDER = re.compile(r"----endnote(\d+)----")


class FootnoteCollector:
    """Collects and assembles footnotes and endnotes."""

    def __init__(self):
        self.footnotes: dict[str, str] = {}  # id -> markdown text
        self.endnotes: dict[str, str] = {}
        self._footnote_counter = 0
        self._endnote_counter = 0

    def collect(self, footnotes_pars: list, endnotes_pars: list):
        """Extract footnote and endnote definitions from docx2python output.

        Args:
            footnotes_pars: docx2python's footnotes_pars (4-depth nested list).
            endnotes_pars: docx2python's endnotes_pars (4-depth nested list).
        """
        self._collect_group(footnotes_pars, self.footnotes)
        self._collect_group(endnotes_pars, self.endnotes)

    def _collect_group(self, pars: list, target: dict[str, str]):
        """Parse footnotes or endnotes from 4-depth structure into the target dict."""
        if not pars:
            return

        # docx2python footnote structure: [[[[Par, Par, ...], ...], ...]]
        # Each footnote has an id we need to extract
        for i, table_like in enumerate(pars):
            parts = []
            for row in table_like:
                for cell in row:
                    for par in cell:
                        text = format_par_runs(par.runs)
                        if text.strip():
                            parts.append(text.strip())

            if parts:
                fn_id = str(i + 1)
                target[fn_id] = " ".join(parts)

    def replace_in_text(self, text: str) -> str:
        """Replace footnote/endnote placeholders with markdown references.

        Side-effect: assigns sequential numbers to references as encountered.
        Call this for body text BEFORE calling get_definitions().
        """
        # Replace footnotes
        def replace_fn(m):
            fn_id = m.group(1)
            self._footnote_counter += 1
            ref_num = self._footnote_counter
            # Store mapping from original id to assigned number
            if fn_id not in self._fn_id_to_num:
                self._fn_id_to_num[fn_id] = ref_num
            return f"[^{ref_num}]"

        # Replace endnotes
        def replace_en(m):
            en_id = m.group(1)
            self._endnote_counter += 1
            ref_num = self._endnote_counter
            if en_id not in self._en_id_to_num:
                self._en_id_to_num[en_id] = ref_num
            return f"[^{ref_num}]"

        self._fn_id_to_num: dict[str, int] = {}
        self._en_id_to_num: dict[str, int] = {}

        text = FOOTNOTE_PLACEHOLDER.sub(replace_fn, text)
        text = ENDNOTE_PLACEHOLDER.sub(replace_en, text)
        return text

    def get_definitions(self) -> list[str]:
        """Return markdown lines for footnote/endnote definitions.

        Returns:
            List of markdown lines, or empty list if no footnotes/endnotes.
        """
        lines = []

        # Add footnote definitions
        for orig_id, text in self.footnotes.items():
            num = self._fn_id_to_num.get(orig_id, int(orig_id))
            lines.append(f"[^{num}]: {text}")

        # Add endnote definitions (using E prefix to distinguish)
        for orig_id, text in self.endnotes.items():
            num = self._en_id_to_num.get(orig_id, int(orig_id))
            lines.append(f"[^{num}]: {text}")

        if lines:
            lines.insert(0, "")  # blank line before definitions

        return lines

    @property
    def count(self) -> int:
        return len(self.footnotes) + len(self.endnotes)


def process_footnotes_body(text: str, footnotes_pars: list, endnotes_pars: list) -> tuple[str, list[str]]:
    """Convenience function: process body text and return (modified_text, definitions).

    Args:
        text: Body markdown text that may contain footnotes/endnotes placeholders.
        footnotes_pars: docx2python footnotes_pars.
        endnotes_pars: docx2python endnotes_pars.

    Returns:
        Tuple of (text_with_refs, definition_lines).
    """
    collector = FootnoteCollector()
    collector.collect(footnotes_pars, endnotes_pars)
    text = collector.replace_in_text(text)
    return text, collector.get_definitions()
