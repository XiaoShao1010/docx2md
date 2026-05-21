"""Handle image extraction and reference generation for the conversion.

docx2python extracts images to a specified folder and provides metadata
about each image (filename, content type, dimensions). This module builds
the mapping from image placeholders in text to markdown references.
"""

from pathlib import Path


def build_image_map(images: dict, image_dir: str | Path, md_output_dir: str | Path) -> dict[str, str]:
    """Build a mapping from image filenames to relative markdown paths.

    Args:
        images: Dict from docx2python's DocxContent.images attribute.
        image_dir: Directory where images are (or will be) extracted.
        md_output_dir: Directory where the output .md file will be written.

    Returns:
        Dict mapping image filename -> relative path for markdown ![](ref).
    """
    image_dir = Path(image_dir)
    md_output_dir = Path(md_output_dir)

    image_map = {}
    for filename in images:
        # Compute relative path from markdown output to image
        image_path = image_dir / filename
        try:
            rel_path = image_path.relative_to(md_output_dir)
        except ValueError:
            # image_dir and md_output_dir may be siblings or different branches
            # Use images/filename as default
            rel_path = Path(image_dir.name) / filename
        image_map[filename] = str(rel_path).replace("\\", "/")

    return image_map


def extract_images(docx_content, image_dir: Path) -> dict:
    """Extract images from docx2python content to the specified directory.

    Args:
        docx_content: DocxContent object from docx2python.
        image_dir: Directory to save extracted images.

    Returns:
        Dict of image filename -> metadata.
    """
    image_dir = Path(image_dir)
    image_dir.mkdir(parents=True, exist_ok=True)
    docx_content.save_images(str(image_dir))
    return docx_content.images
