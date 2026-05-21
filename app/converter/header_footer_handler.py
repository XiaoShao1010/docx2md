"""Convert DOCX headers and footers to markdown.

Headers and footers are rendered as blockquote-style text with metadata labels
at the top and bottom of the document respectively.
"""

from app.converter.inline_formatter import format_par_runs, extract_text_from_runs


def convert_headers(header_pars: list) -> list[str]:
    """Convert header paragraphs to markdown lines.

    Headers appear at the top of the document as blockquoted text.

    Args:
        header_pars: The 4-depth nested list from docx2python's header_pars.

    Returns:
        List of markdown lines for headers, or empty list if no headers.
    """
    lines = _convert_hf(header_pars, "Header")
    return lines


def convert_footers(footer_pars: list) -> list[str]:
    """Convert footer paragraphs to markdown lines.

    Footers appear at the bottom of the document.

    Args:
        footer_pars: The 4-depth nested list from docx2python's footer_pars.

    Returns:
        List of markdown lines for footers, or empty list if no footers.
    """
    lines = _convert_hf(footer_pars, "Footer")
    return lines


def _convert_hf(pars: list, label: str) -> list[str]:
    """Convert header or footer paragraphs to markdown blockquotes.

    Args:
        pars: 4-depth nested list of Par objects.
        label: "Header" or "Footer" for the markdown label.

    Returns:
        List of markdown lines.
    """
    if not pars:
        return []

    lines = []
    content_parts = []
    for table_like in pars:
        for row in table_like:
            for cell in row:
                for par in cell:
                    text = format_par_runs(par.runs)
                    if text.strip():
                        content_parts.append(text.strip())

    if content_parts:
        lines.append("")  # blank line before
        lines.append(f"> **{label}**: " + " | ".join(content_parts))
        lines.append("")  # blank line after

    return lines
