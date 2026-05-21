"""Map Word style names to Markdown block contexts.

Defines how each paragraph style in a DOCX document translates to
markdown block-level constructs (headings, lists, blockquotes, etc.).

Supports configurable overrides via a JSON style map file.
"""

from dataclasses import dataclass, field


@dataclass
class BlockContext:
    """Describes how to render a paragraph block in markdown."""
    block_type: str  # "heading", "paragraph", "list_item", "blockquote", "code_block", "toc", "hr", "empty"
    level: int = 0  # heading level (1-6), or list nesting level
    prefix: str = ""  # Markdown prefix (e.g., "# ", "> ", "- ")
    suffix: str = ""  # Markdown suffix (e.g., "\n" for code fences)


# Default style-to-block mapping
DEFAULT_STYLE_MAP: dict[str, BlockContext] = {
    "Title": BlockContext("heading", level=1, prefix="# "),
    "Subtitle": BlockContext("heading", level=2, prefix="## "),
    "Heading 1": BlockContext("heading", level=1, prefix="# "),
    "Heading 2": BlockContext("heading", level=2, prefix="## "),
    "Heading 3": BlockContext("heading", level=3, prefix="### "),
    "Heading 4": BlockContext("heading", level=4, prefix="#### "),
    "Heading 5": BlockContext("heading", level=5, prefix="##### "),
    "Heading 6": BlockContext("heading", level=6, prefix="###### "),
    "Heading1": BlockContext("heading", level=1, prefix="# "),
    "Heading2": BlockContext("heading", level=2, prefix="## "),
    "Heading3": BlockContext("heading", level=3, prefix="### "),
    "Heading4": BlockContext("heading", level=4, prefix="#### "),
    "Heading5": BlockContext("heading", level=5, prefix="##### "),
    "Heading6": BlockContext("heading", level=6, prefix="###### "),
    "List Bullet": BlockContext("list_item", prefix="- "),
    "List Bullet 2": BlockContext("list_item", level=2, prefix="    - "),
    "List Bullet 3": BlockContext("list_item", level=3, prefix="        - "),
    "ListBullet": BlockContext("list_item", prefix="- "),
    "ListBullet2": BlockContext("list_item", level=2, prefix="    - "),
    "ListBullet3": BlockContext("list_item", level=3, prefix="        - "),
    "List Number": BlockContext("list_item", prefix="1. "),
    "List Number 2": BlockContext("list_item", level=2, prefix="    1. "),
    "List Number 3": BlockContext("list_item", level=3, prefix="        1. "),
    "ListNumber": BlockContext("list_item", prefix="1. "),
    "ListNumber2": BlockContext("list_item", level=2, prefix="    1. "),
    "ListNumber3": BlockContext("list_item", level=3, prefix="        1. "),
    "Block Text": BlockContext("blockquote", prefix="> "),
    "Quote": BlockContext("blockquote", prefix="> "),
    "Intense Quote": BlockContext("blockquote", prefix="> "),
    "Code": BlockContext("code_block", prefix="```\n", suffix="\n```"),
    "HTML Code": BlockContext("code_block", prefix="```html\n", suffix="\n```"),
    "Plain Text": BlockContext("code_block", prefix="```\n", suffix="\n```"),
    "TOC Heading": BlockContext("toc"),
    "TOC 1": BlockContext("toc", level=1),
    "TOC 2": BlockContext("toc", level=2),
    "TOC1": BlockContext("toc", level=1),
    "TOC2": BlockContext("toc", level=2),
    "Normal": BlockContext("paragraph"),
    "First Paragraph": BlockContext("paragraph"),
    "Body Text": BlockContext("paragraph"),
    "Normal (Web)": BlockContext("paragraph"),
}


class StyleMapper:
    """Maps Word paragraph styles to Markdown block contexts."""

    def __init__(self, custom_map: dict | None = None):
        self._map = dict(DEFAULT_STYLE_MAP)
        if custom_map:
            for name, ctx in custom_map.items():
                if isinstance(ctx, dict):
                    self._map[name] = BlockContext(**ctx)
                else:
                    self._map[name] = ctx

    def map(self, style_name: str, html_style: list[str] | None = None) -> BlockContext:
        """Map a Word style name to a BlockContext.

        Falls back to checking html_style if style name is unknown.
        Returns BlockContext("paragraph") for unrecognized styles.

        Args:
            style_name: The paragraph's style name from docx2python (may be empty string).
            html_style: Optional list of HTML tags from the paragraph.

        Returns:
            BlockContext describing how to render this paragraph.
        """
        style_name = style_name.strip() if style_name else ""

        if style_name and style_name in self._map:
            return self._map[style_name]

        # Try without spaces (handle "Heading 1" vs "Heading1")
        style_no_space = style_name.replace(" ", "")
        if style_no_space and style_no_space in self._map:
            return self._map[style_no_space]

        # Use html_style as fallback
        if html_style:
            for tag in html_style:
                tag_lower = tag.lower()
                if tag_lower in ("h1", "h2", "h3", "h4", "h5", "h6"):
                    level = int(tag_lower[1])
                    return BlockContext("heading", level=level, prefix=f"{'#' * level} ")

        # Check for TOC pattern in style name
        if style_name.upper().startswith("TOC"):
            return BlockContext("toc")

        # Default: normal paragraph
        return BlockContext("paragraph")

    def is_toc_paragraph(self, style_name: str) -> bool:
        """Check if a paragraph belongs to a Table of Contents."""
        return style_name.strip().upper().startswith("TOC")
