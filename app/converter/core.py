"""Core conversion pipeline orchestrator.

Coordinates all converter modules to transform a DOCX file to Markdown.
"""

import logging
from pathlib import Path

from app.config import settings
from app.converter.extractor import ExtractedDocx
from app.converter.image_handler import build_image_map, convert_image_format
from app.converter.header_footer_handler import convert_headers, convert_footers
from app.converter.footnote_handler import FootnoteCollector
from app.converter.paragraph_handler import ParagraphHandler
from app.converter.style_mapper import StyleMapper
from app.converter.toc_handler import detect_toc_field_in_document, TocGenerator
from app.converter.markdown_writer import assemble_markdown, write_markdown
from app.converter.zip_packager import create_zip
from app.converter.math_handler import has_math

logger = logging.getLogger("docx2md")


class ConversionResult:
    """Holds the result of a conversion, including metadata."""

    def __init__(self):
        self.image_count: int = 0
        self.footnote_count: int = 0
        self.toc_detected: bool = False
        self.toc_generated: bool = False
        self.math_formula_count: int = 0
        self.warnings: list[str] = []


def convert_docx(
    docx_path: Path,
    output_dir: Path,
    output_format: str = "md",
    include_headers_footers: bool = True,
    custom_style_map: dict | None = None,
    image_format: str = "original",
    image_quality: int = 85,
) -> tuple[Path, ConversionResult]:
    """Convert a DOCX file to Markdown.

    Args:
        docx_path: Path to the input .docx file.
        output_dir: Directory for output files (.md and images/).
        output_format: "md" for single file, "zip" for zipped result.
        include_headers_footers: Whether to include header/footer content.
        custom_style_map: Optional dict of style name -> BlockContext overrides.
        image_format: "original", "png", "jpg", or "webp".
        image_quality: JPEG/WebP quality 1-100.

    Returns:
        Tuple of (output_file_path, ConversionResult).
    """
    result = ConversionResult()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    image_dir = output_dir / settings.image_folder_name
    md_output_path = output_dir / "output.md"

    # Step 1 & 2: Extract content
    logger.info("Extracting DOCX: %s", docx_path)
    extracted = ExtractedDocx(docx_path, image_dir=image_dir)
    result.image_count = len(extracted.images)

    # Step 2.5: Convert image formats if requested
    if image_format != "original" and extracted.images:
        for filename in list(extracted.images):
            image_path = image_dir / filename
            new_path = convert_image_format(image_path, image_format, image_quality)
            new_filename = new_path.name
            if new_filename != filename:
                extracted.images[new_filename] = extracted.images.pop(filename)

    # Step 3: Build image map
    image_map = build_image_map(extracted.images, image_dir, output_dir)

    # Step 4: TOC detection
    result.toc_detected = detect_toc_field_in_document(extracted.python_docx)

    # Step 4.5: Count math formulas
    math_count = 0
    for para in extracted.python_docx.paragraphs:
        has_m, _ = has_math(para._element)
        if has_m:
            math_count += 1
    result.math_formula_count = math_count

    # Step 5: Process headers and footers
    header_lines = []
    footer_lines = []
    if include_headers_footers:
        header_lines = convert_headers(extracted.header_pars)
        footer_lines = convert_footers(extracted.footer_pars)

    # Step 6: Process footnotes / endnotes
    footnote_collector = FootnoteCollector()
    footnote_collector.collect(extracted.footnotes_pars, extracted.endnotes_pars)
    result.footnote_count = footnote_collector.count

    # Step 7: Process body
    style_mapper = StyleMapper(custom_style_map)
    handler = ParagraphHandler(
        style_mapper=style_mapper,
        image_map=image_map,
        numbering_handler=extracted.numbering_handler,
        cross_ref_handler=extracted.cross_reference_handler,
        python_docx=extracted.python_docx,
    )
    body_lines = handler.handle_body(extracted.body_pars)

    # Apply footnote placeholder replacement to body lines
    body_text = "\n".join(body_lines)
    body_text = footnote_collector.replace_in_text(body_text)
    body_lines = body_text.split("\n")

    # Step 8: Generate TOC from headings if detected
    toc_markdown = None
    if result.toc_detected and handler.headings:
        toc_gen = TocGenerator(handler.headings)
        toc_markdown = toc_gen.generate()
        if toc_markdown:
            result.toc_generated = True

    # Step 9: Assemble and write markdown
    footnote_defs = footnote_collector.get_definitions()
    markdown_text = assemble_markdown(
        header_lines, body_lines, footnote_defs, footer_lines,
        toc_markdown=toc_markdown,
    )
    write_markdown(markdown_text, md_output_path)

    # Step 10: Package
    has_images = bool(extracted.images)
    if output_format == "zip" or has_images:
        zip_path = output_dir / "result.zip"
        create_zip(md_output_path, image_dir, zip_path)
        return zip_path, result

    return md_output_path, result
