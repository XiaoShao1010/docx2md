"""Assemble the final Markdown file from all converted sections."""

from pathlib import Path


def assemble_markdown(
    header_lines: list[str],
    body_lines: list[str],
    footnote_lines: list[str],
    footer_lines: list[str],
    toc_markdown: str | None = None,
) -> str:
    """Assemble all sections into a complete markdown document.

    Sections are joined with appropriate blank-line separation.

    Args:
        header_lines: Markdown lines for headers.
        body_lines: Markdown lines for document body.
        footnote_lines: Markdown lines for footnotes/endnotes.
        footer_lines: Markdown lines for footers.
        toc_markdown: Optional generated TOC to replace [TOC] placeholder.

    Returns:
        Complete markdown document as a single string.
    """
    sections = []

    for section_lines in (header_lines, body_lines, footnote_lines, footer_lines):
        if section_lines:
            text = "\n".join(section_lines).strip()
            if text:
                sections.append(text)

    result = "\n\n".join(sections)

    # Replace [TOC] placeholder with generated TOC
    if toc_markdown:
        result = result.replace("[TOC]", toc_markdown)

    # Clean up: no more than 2 consecutive blank lines
    while "\n\n\n" in result:
        result = result.replace("\n\n\n", "\n\n")

    return result + "\n"


def write_markdown(content: str, output_path: Path) -> Path:
    """Write markdown content to file.

    Args:
        content: The markdown string to write.
        output_path: Path to the output .md file.

    Returns:
        The output path.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    return output_path
