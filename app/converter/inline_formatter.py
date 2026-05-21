"""Convert docx2python HTML run tags to Markdown inline formatting.

The docx2python library with html=True produces runs where each run's
html_style is a list of tag names like ["b"], ["i"], ["b", "i"], ["a"], etc.
This module converts those to markdown inline syntax.
"""

from app.utils.sanitizer import sanitize_text

# Mapping from HTML tag name to (markdown_open, markdown_close)
TAG_MAP = {
    "b": ("**", "**"),
    "strong": ("**", "**"),
    "i": ("*", "*"),
    "em": ("*", "*"),
    "s": ("~~", "~~"),
    "del": ("~~", "~~"),
    "u": ("<u>", "</u>"),
    "sup": ("^", "^"),
    "sub": ("~", "~"),
    "code": ("`", "`"),
    "h1": ("", ""),
    "h2": ("", ""),
    "h3": ("", ""),
    "h4": ("", ""),
    "h5": ("", ""),
    "h6": ("", ""),
    "p": ("", ""),
    "br": ("", ""),
    "pre": ("", ""),
}

# HTML tags that do not produce markdown wrappers (block-level or structural)
SKIP_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6", "p", "br", "pre"}


def format_run(text: str, html_style: list[str]) -> str:
    """Convert a single run's text with its html_style tags to markdown.

    Args:
        text: The run's text content.
        html_style: List of HTML tag names applied to this run (e.g. ["b", "i"]).

    Returns:
        Markdown-formatted string for this run.
    """
    text = sanitize_text(text)
    if not text:
        return ""

    wrappers = []
    for tag in html_style:
        tag_lower = tag.lower().strip("</>")
        if tag_lower in SKIP_TAGS:
            continue
        mapping = TAG_MAP.get(tag_lower)
        if mapping:
            wrappers.append(mapping)

    # Apply wrappers from outermost to innermost
    # The html_style list is in document order (outer first)
    for open_md, close_md in wrappers:
        text = f"{open_md}{text}{close_md}"

    return text


def format_par_runs(runs, image_map: dict[str, str] | None = None) -> str:
    """Convert all runs in a paragraph to a single markdown string.

    Args:
        runs: List of Run objects from docx2python Par.
        image_map: Optional dict mapping image filenames to relative paths.

    Returns:
        Concatenated markdown string for the paragraph content.
    """
    parts = []
    for run in runs:
        if not run.text.strip():
            continue
        formatted = format_run(run.text, run.html_style)
        if formatted:
            parts.append(formatted)

    result = "".join(parts)
    if image_map:
        result = replace_image_placeholders(result, image_map)

    return result


def replace_image_placeholders(text: str, image_map: dict[str, str]) -> str:
    """Replace image placeholders with markdown image references.

    docx2python uses placeholders like ``----media/image1.jpg----`` in text,
    but the image_map keys are just the base filenames like ``image1.jpg``.
    """
    for filename, rel_path in image_map.items():
        alt = filename.rsplit(".", 1)[0] if "." in filename else filename
        md_ref = f"![{alt}]({rel_path})"
        # docx2python uses ----media/filename---- format
        text = text.replace(f"----media/{filename}----", md_ref)
        # Also check bare ----filename---- format
        text = text.replace(f"----{filename}----", md_ref)
    return text


def extract_text_from_runs(runs) -> str:
    """Extract plain text from runs, ignoring formatting."""
    return "".join(run.text for run in runs if run.text.strip()).strip()
