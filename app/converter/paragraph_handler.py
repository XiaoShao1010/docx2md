"""Convert docx2python paragraph structures to Markdown block lines.

Handles headings, lists, blockquotes, code blocks, and plain paragraphs.
Delegates to StyleMapper for block context and inline_formatter for text.
"""

from app.converter.inline_formatter import format_par_runs
from app.converter.style_mapper import StyleMapper, BlockContext
from app.converter.table_handler import convert_table


class ParagraphHandler:
    """Converts a stream of Par objects to markdown lines."""

    def __init__(self, style_mapper: StyleMapper | None = None, image_map: dict | None = None):
        self.mapper = style_mapper or StyleMapper()
        self.image_map = image_map or {}
        self._list_number_counters: dict[int, int] = {}  # depth -> counter for numbered lists

    def handle_body(self, body_pars: list) -> list[str]:
        """Convert the full body_pars structure to markdown lines.

        body_pars is the 4-depth nested list from docx2python's document_pars.
        """
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
                self._list_number_counters.clear()
                for row in table_like:
                    for cell in row:
                        for par in cell:
                            md_lines = self.handle_par(par)
                            lines.extend(md_lines)
        return lines

    def handle_par(self, par) -> list[str]:
        """Convert a single Par to one or more markdown line(s).

        Returns a list of strings (usually 1 line, more for code blocks).
        """
        ctx = self.mapper.map(par.style, par.html_style)
        inline_text = format_par_runs(par.runs, self.image_map)

        if ctx.block_type == "toc":
            return ["[TOC]", ""]
        elif ctx.block_type == "heading":
            heading_text = inline_text if inline_text else "(empty heading)"
            return ["", f"{ctx.prefix}{heading_text}", ""]
        elif ctx.block_type == "code_block":
            return ["", ctx.prefix.rstrip("\n"), inline_text, ctx.suffix.strip("\n"), ""]
        elif ctx.block_type == "list_item":
            return self._handle_list_item(ctx, inline_text)
        elif ctx.block_type == "blockquote":
            return [f"{ctx.prefix}{inline_text}", ""]
        elif ctx.block_type == "empty":
            return [""]
        else:
            # Regular paragraph
            if inline_text:
                return [inline_text, ""]
            else:
                return [""]

    def _handle_list_item(self, ctx: BlockContext, text: str) -> list[str]:
        """Handle list items with proper numbering for ordered lists."""
        depth = ctx.level
        prefix = ctx.prefix

        # For ordered lists (numbered), generate proper sequential numbers
        if prefix.strip().startswith("1."):
            if depth not in self._list_number_counters:
                self._list_number_counters[depth] = 0
            self._list_number_counters[depth] += 1
            num = self._list_number_counters[depth]
            indent = "    " * depth
            prefix = f"{indent}{num}. "
        else:
            # For unordered lists, reset numbered counters at this depth
            # and just use the prefix from style map
            pass

        return [f"{prefix}{text}"]

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
