import re

_MD_SPECIAL = re.compile(r"([\\`*_{}\[\]()#+\-.!|~<>])")


def escape_markdown(text: str) -> str:
    return _MD_SPECIAL.sub(r"\\\1", text)


def sanitize_text(text: str) -> str:
    """Remove null bytes and normalize whitespace."""
    if not text:
        return ""
    text = text.replace("\x00", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text
