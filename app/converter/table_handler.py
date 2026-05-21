"""Convert docx2python table structures to GFM (GitHub-Flavored Markdown) tables.

A table in docx2python is a list of rows, each row is a list of cells,
each cell is a list of paragraphs (Par objects).
"""

from app.converter.inline_formatter import format_par_runs


def convert_table(table_rows: list, paragraph_handler=None) -> list[str]:
    """Convert a docx2python table structure to GFM markdown table lines.

    Args:
        table_rows: Nested list [[row[cell[par, ...], ...], ...], ...].
        paragraph_handler: Optional ParagraphHandler for cell content conversion.

    Returns:
        List of markdown lines (no trailing newlines).
    """
    if not table_rows:
        return []

    num_cols = max(len(row) for row in table_rows) if table_rows else 0
    if num_cols == 0:
        return []

    # Extract cell text
    matrix = []
    for row in table_rows:
        cells = []
        for cell in row:
            parts = []
            for par in cell:
                if paragraph_handler:
                    text = format_par_runs(par.runs, paragraph_handler.image_map)
                else:
                    text = format_par_runs(par.runs)
                if text:
                    parts.append(text)
            # Join multiple paragraphs in a cell with <br>
            cells.append("<br>".join(parts) if parts else "")
        # Pad to num_cols
        while len(cells) < num_cols:
            cells.append("")
        matrix.append(cells)

    lines = []
    # Header row (first row)
    header_cells = matrix[0]
    lines.append("| " + " | ".join(_escape_cell(c) for c in header_cells) + " |")

    # Separator row with alignment
    alignments = _detect_alignments(table_rows, num_cols)
    sep_parts = []
    for i in range(num_cols):
        align = alignments[i] if i < len(alignments) else "left"
        if align == "center":
            sep_parts.append(":---:")
        elif align == "right":
            sep_parts.append("---:")
        else:
            sep_parts.append(":---")
    lines.append("| " + " | ".join(sep_parts) + " |")

    # Data rows
    for row in matrix[1:]:
        lines.append("| " + " | ".join(_escape_cell(c) for c in row) + " |")

    return lines


def _escape_cell(text: str) -> str:
    """Escape pipe characters and trim whitespace in table cells."""
    return text.replace("|", "\\|").replace("\n", " ").strip()


def _detect_alignments(table_rows: list, num_cols: int) -> list[str]:
    """Detect column alignments from the first data row's paragraph properties.

    Uses python-docx paragraph alignment. Falls back to "left" for all columns.
    """
    alignments = []
    if not table_rows:
        return alignments

    for col_idx in range(num_cols):
        # Try to find alignment from the first row's paragraphs
        if table_rows and col_idx < len(table_rows[0]):
            cell = table_rows[0][col_idx]
            if cell:
                for par in cell:
                    if hasattr(par, 'elem') and par.elem is not None:
                        # Check for jc (justification) in paragraph properties
                        pPr = par.elem.find(
                            "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}pPr"
                        )
                        if pPr is not None:
                            jc = pPr.find(
                                "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}jc"
                            )
                            if jc is not None:
                                val = jc.get(
                                    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val"
                                )
                                if val == "center":
                                    alignments.append("center")
                                elif val == "right":
                                    alignments.append("right")
                                elif val == "left":
                                    alignments.append("left")
                                else:
                                    alignments.append("left")
                                break
                    # Fallback: detect from paragraph style
                    if hasattr(par, 'style') and par.style:
                        style_lower = par.style.lower()
                        if 'center' in style_lower:
                            alignments.append("center")
                            break
                        elif 'right' in style_lower:
                            alignments.append("right")
                            break
                else:
                    alignments.append("left")
            else:
                alignments.append("left")
        else:
            alignments.append("left")

    return alignments
