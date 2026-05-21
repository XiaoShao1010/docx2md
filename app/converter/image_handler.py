"""Handle image extraction and reference generation for the conversion.

docx2python extracts images to a specified folder and provides metadata
about each image (filename, content type, dimensions). This module builds
the mapping from image placeholders in text to markdown references.
"""

import base64
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
        image_path = image_dir / filename
        try:
            rel_path = image_path.relative_to(md_output_dir)
        except ValueError:
            rel_path = Path(image_dir.name) / filename
        image_map[filename] = str(rel_path).replace("\\", "/")

    return image_map


def build_image_data_uris(images: dict, image_dir: Path) -> dict[str, str]:
    """Build a mapping from image filenames to base64 data URIs.

    This allows the .md file to be fully self-contained without needing
    a separate images folder.

    Args:
        images: Dict from docx2python's DocxContent.images attribute.
        image_dir: Directory where images have been extracted.

    Returns:
        Dict mapping image filename -> data URI string.
    """
    uri_map = {}
    for filename in images:
        image_path = image_dir / filename
        if not image_path.exists():
            continue
        image_data = image_path.read_bytes()
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "png"
        mime = _ext_to_mime(ext)
        b64 = base64.b64encode(image_data).decode("ascii")
        uri_map[filename] = f"data:{mime};base64,{b64}"
    return uri_map


def _ext_to_mime(ext: str) -> str:
    """Map file extension to MIME type."""
    mime_map = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "gif": "image/gif",
        "bmp": "image/bmp",
        "webp": "image/webp",
        "svg": "image/svg+xml",
        "ico": "image/x-icon",
        "tiff": "image/tiff",
        "tif": "image/tiff",
        "emf": "image/emf",
        "wmf": "image/wmf",
    }
    return mime_map.get(ext, "application/octet-stream")


def extract_images(docx_content, image_dir: Path) -> dict:
    """Extract images from docx2python content to the specified directory."""
    image_dir = Path(image_dir)
    image_dir.mkdir(parents=True, exist_ok=True)
    docx_content.save_images(str(image_dir))
    return docx_content.images
