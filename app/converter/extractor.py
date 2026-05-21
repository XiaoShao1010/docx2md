"""Wrap docx2python and python-docx to provide unified document content access.

docx2python is the primary engine. python-docx is used only for:
1. Reading section properties to map headers/footers to sections.
2. Accessing OOXML field codes for TOC detection.
"""

from pathlib import Path

from docx2python import docx2python
from docx2python.docx_output import DocxContent
from docx import Document as DocxDocument
from lxml import etree


class ExtractedDocx:
    """Unified interface to all extracted DOCX content."""

    def __init__(self, docx_path: Path, image_dir: Path | None = None):
        image_folder = str(image_dir) if image_dir else None
        self.content: DocxContent = docx2python(
            str(docx_path), image_folder=image_folder, html=True, duplicate_merged_cells=True
        )
        self._python_docx = DocxDocument(str(docx_path))

    @property
    def body_pars(self):
        """Return document body paragraphs (4-depth nested list)."""
        return self.content.document_pars

    @property
    def header_pars(self):
        """Return header paragraphs."""
        return self.content.header_pars

    @property
    def footer_pars(self):
        """Return footer paragraphs."""
        return self.content.footer_pars

    @property
    def footnotes_pars(self):
        """Return footnote paragraphs."""
        return self.content.footnotes_pars

    @property
    def endnotes_pars(self):
        """Return endnote paragraphs."""
        return self.content.endnotes_pars

    @property
    def images(self) -> dict:
        """Return dict of image metadata extracted from the docx."""
        return self.content.images

    @property
    def core_properties(self) -> dict:
        """Return document core properties (title, creator, etc.)."""
        return self.content.core_properties

    def has_toc_field(self) -> bool:
        """Check if the document contains a TOC field code in its XML."""
        nsmap = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        for paragraph in self._python_docx.paragraphs:
            for instr in paragraph._element.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}instrText"):
                if instr.text and "TOC" in instr.text.upper():
                    return True
        return False

    def iter_paragraphs(self):
        """Iterate over all paragraphs in document_pars at depth 4.

        Yields (par, lineage, table_info) tuples where:
            par: The Par object.
            lineage: tuple of indices describing position (doc_idx, table_idx, row_idx, cell_idx).
            is_in_table: bool indicating if this par is inside a table.
        """
        pars = self.body_pars
        if not pars:
            return

        # Non-table content is always in pars[0]
        for table_like in pars:
            # Determine if this is a table by checking structure
            # Tables: [[row1[cell1, cell2, ...]], [row2[...]], ...]
            # Non-table: [[paragraph_list]]
            is_table = self._is_table_element(table_like)
            if not is_table:
                for row in table_like:
                    for cell in row:
                        for par in cell:
                            yield (par, False)
            else:
                for row_idx, row in enumerate(table_like):
                    for cell_idx, cell in enumerate(row):
                        for par in cell:
                            yield (par, True)

    def _is_table_element(self, element) -> bool:
        """Heuristic: a table element has multiple rows, each with multiple cells."""
        if not isinstance(element, list) or not element:
            return False
        # If there are multiple sub-lists and each has same length > 1, it's a table
        if len(element) > 1 and all(
            isinstance(row, list) and len(row) >= 1 for row in element
        ):
            cell_counts = [len(row) for row in element]
            if len(set(cell_counts)) == 1 and cell_counts[0] >= 1:
                return True
        return False
