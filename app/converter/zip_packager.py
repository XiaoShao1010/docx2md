"""Package converted markdown and images into a zip file for download."""

import zipfile
from pathlib import Path


def create_zip(
    md_path: Path,
    image_dir: Path,
    output_zip_path: Path,
    md_name: str = "output.md",
) -> Path:
    """Create a zip archive containing the markdown file and images folder.

    Args:
        md_path: Path to the .md file to include.
        image_dir: Directory containing extracted images.
        output_zip_path: Where to write the output .zip file.
        md_name: Name of the markdown file inside the zip.

    Returns:
        Path to the created zip file.
    """
    output_zip_path = Path(output_zip_path)
    output_zip_path.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(output_zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # Add markdown file
        if md_path.exists():
            zf.write(md_path, md_name)

        # Add images folder
        if image_dir.exists():
            for img_file in image_dir.iterdir():
                if img_file.is_file():
                    zf.write(img_file, f"images/{img_file.name}")

    return output_zip_path
