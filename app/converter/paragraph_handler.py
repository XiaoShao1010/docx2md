"""Convert docx2python paragraph structures to Markdown block lines.

Handles headings, lists, blockquotes, code blocks, plain paragraphs,
math formulas, cross-references, and heading anchor IDs for TOC linking.
"""

import re

from app.converter.inline_formatter import format_par_runs
from app.converter.style_mapper import StyleMapper, BlockContext
from app.converter.table_handler import convert_table
from app.converter.math_handler import has_math, convert_paragraph_math
from app.converter.numbering_handler import NumberingHandler
from app.converter.cross_reference_handler import CrossReferenceHandler


class ParagraphHandler:
    """Converts a stream of Par objects to markdown lines."""

    def __init__(
        self,
        style_mapper: StyleMapper | None = None,
        image_map: dict | None = None,
        numbering_handler: NumberingHandler | None = None,
        cross_ref_handler: CrossReferenceHandler | None = None,
        python_docx=None,
    ):
        self.mapper = style_mapper or StyleMapper()
        self.image_map = image_map or {}
        self.numbering = numbering_handler
        self.cross_ref = cross_ref_handler
        self._python_docx = python_docx
        self._list_counters: dict[tuple[int, int], int] = {}  # (numId, ilvl) -> counter
        self._depth_counters: dict[int, int] = {}  # depth -> counter (fallback)
        self._last_num_key: tuple[int, int] | None = None
        self._headings: list[tuple[int, str]] = []  # (level, text) for TOC generation
        self._para_index: int = 0  # tracks non-table paragraph position

    @property
    def headings(self) -> list[tuple[int, str]]:
        """Return collected headings for TOC generation."""
        return self._headings

    def handle_body(self, body_pars: list) -> list[str]:
        """Convert the full body_pars structure to markdown lines."""
        lines = []
        if not body_pars:
            return lines

        for table_like in body_pars:
            if self._is_header_footer(table_like):
                continue
            if self._is_table(table_like):
                lines.extend(convert_table(table_like, self))
                lines.append("")
            else:
                self._list_counters.clear()
                self._last_num_key = None
                for row in table_like:
                    for cell in row:
                        for par in cell:
                            md_lines = self.handle_par(par)
                            lines.extend(md_lines)
        return lines

    def handle_par(self, par) -> list[str]:
        """Convert a single Par to one or more markdown line(s)."""
        py_el = self._get_para_element()

        # Check for math first
        if py_el is not None:
            has_m, _ = has_math(py_el)
            if has_m:
                result = convert_paragraph_math(py_el)
                self._para_index += 1
                if result:
                    return [result, ""]
                return [""]

        ctx = self.mapper.map(par.style, par.html_style)
        inline_text = format_par_runs(par.runs, self.image_map)

        # Cross-reference resolution
        if self.cross_ref is not None and py_el is not None:
            if CrossReferenceHandler.has_ref_field(py_el):
                resolved = self.cross_ref.resolve_ref(py_el, inline_text)
                if resolved is not None:
                    inline_text = resolved

        # Advance index for non-table paragraphs (after lookups)
        self._para_index += 1

        if ctx.block_type == "toc":
            return ["[TOC]", ""]
        elif ctx.block_type == "heading":
            heading_text = inline_text if inline_text else "(empty heading)"
            anchor = self._make_anchor(heading_text)
            self._headings.append((ctx.level, heading_text))
            return ["", f'{ctx.prefix}<a id="{anchor}"></a>{heading_text}', ""]
        elif ctx.block_type == "code_block":
            return ["", ctx.prefix.rstrip("\n"), inline_text, ctx.suffix.strip("\n"), ""]
        elif ctx.block_type == "list_item":
            return self._handle_list_item(ctx, inline_text, py_el)
        elif ctx.block_type == "blockquote":
            return [f"{ctx.prefix}{inline_text}", ""]
        elif ctx.block_type == "empty":
            return [""]
        else:
            if inline_text:
                return [inline_text, ""]
            else:
                return [""]

    def _handle_list_item(self, ctx: BlockContext, text: str, py_el=None) -> list[str]:
        """Handle list items with proper numbering from Word numPr."""
        depth = ctx.level
        prefix = ctx.prefix

        if prefix.strip().startswith("1."):
            num_id = None
            ilvl = depth
            if py_el is not None:
                info = NumberingHandler.extract_num_info(py_el)
                if info is not None:
                    num_id, ilvl = info

            num_key = (num_id if num_id is not None else -1, ilvl)
            if num_key != self._last_num_key:
                if num_key not in self._list_counters:
                    start = 1
                    if self.numbering is not None and num_id is not None:
                        start = self.numbering.get_start(num_id, ilvl)
                    self._list_counters[num_key] = start - 1
                self._last_num_key = num_key

            self._list_counters[num_key] += 1
            num = self._list_counters[num_key]
            if self.numbering is not None and num_id is not None:
                fmt = self.numbering.get_numfmt(num_id, ilvl)
                formatted = NumberingHandler.format_num(num, fmt)
            else:
                formatted = str(num)

            indent = "    " * depth
            prefix = f"{indent}{formatted}. "

        return [f"{prefix}{text}"]

    def _get_para_element(self):
        """Get the python-docx paragraph element at the current position."""
        if self._python_docx is None:
            return None
        paragraphs = self._python_docx.paragraphs
        if self._para_index < len(paragraphs):
            return paragraphs[self._para_index]._element
        return None

    @staticmethod
    def _make_anchor(text: str) -> str:
        """Generate a GitHub-flavored anchor ID from heading text."""
        anchor = text.lower().strip()
        anchor = re.sub(r'[^\w\s\-_]', '', anchor)
        anchor = re.sub(r'[\s_]+', '-', anchor)
        anchor = re.sub(r'-+', '-', anchor)
        return anchor.strip('-')

    @staticmethod
    def _is_table(element) -> bool:
        """Detect if a docx2python element at depth 1 represents a table."""
        if not isinstance(element, list) or not element:
            return False
        if len(element) > 1 and all(isinstance(r, list) and len(r) >= 1 for r in element):
            cell_counts = [len(r) for r in element]
            if len(set(cell_counts)) == 1 and cell_counts[0] >= 1:
                if any(len(r) > 1 for r in element):
                    return True
                if len(element) >= 2 and all(len(r) == 1 for r in element):
                    for row in element:
                        for cell in row:
                            for par in cell:
                                if hasattr(par, 'style') and par.style:
                                    style = par.style.strip().lower()
                                    if 'list' in style or 'bullet' in style:
                                        return False
                    return True
        return False

    @staticmethod
    def _is_header_footer(element) -> bool:
        """Detect if a docx2python element is header or footer content."""
        if not isinstance(element, list) or not element:
            return False
        try:
            all_pars = []
            for row in element:
                for cell in row:
                    for par in cell:
                        all_pars.append(par)
            if not all_pars:
                return False
            return any(
                hasattr(p, 'style') and p.style.strip().lower() in ('header', 'footer')
                for p in all_pars
            )
        except (TypeError, IndexError):
            return False
