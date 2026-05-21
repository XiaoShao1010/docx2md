"""Convert OMML (Office Math Markup Language) to LaTeX.

Word stores math equations as OMML elements (<m:oMath>, <m:oMathPara>).
This module recursively traverses the OMML XML tree and produces
LaTeX math expressions.
"""

import logging

from lxml import etree

M_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"

logger = logging.getLogger("docx2md")

# Character mappings for nary operators
_NARY_CHAR_MAP: dict[str, str] = {
    "∑": r"\sum",
    "∏": r"\prod",
    "∐": r"\coprod",
    "∫": r"\int",
    "∬": r"\iint",
    "∭": r"\iiint",
    "∮": r"\oint",
    "⋃": r"\bigcup",
    "⋂": r"\bigcap",
    "⨁": r"\bigoplus",
    "⨂": r"\bigotimes",
    "⋁": r"\bigvee",
    "⋀": r"\bigwedge",
}

# Character mappings for accents
_ACCENT_CHAR_MAP: dict[str, str] = {
    "̂": r"\hat",       # combining circumflex
    "̃": r"\tilde",     # combining tilde
    "̇": r"\dot",       # combining dot above
    "̈": r"\ddot",      # combining diaeresis
    "⃗": r"\vec",       # combining right arrow above
    "̄": r"\bar",       # combining macron
    "̆": r"\breve",     # combining breve
    "̌": r"\check",     # combining caron
    "̀": r"\grave",     # combining grave accent
    "́": r"\acute",     # combining acute accent
}

# Delimiter character mappings
_DELIM_OPEN_MAP: dict[str, str] = {
    "(": r"\left(",
    "[": r"\left[",
    "{": r"\left\{",
    "|": r"\left|",
    "‖": r"\|",
    "⌊": r"\lfloor",
    "⌈": r"\lceil",
    "〈": r"\langle",
    "⟦": r"\llbracket",
    "": "",  # no delimiter
}

_DELIM_CLOSE_MAP: dict[str, str] = {
    ")": r"\right)",
    "]": r"\right]",
    "}": r"\right\}",
    "|": r"\right|",
    "‖": r"\|",
    "⌋": r"\rfloor",
    "⌉": r"\rceil",
    "〉": r"\rangle",
    "⟧": r"\rrbracket",
    "": "",
}

# Known function names
_MATH_FUNCTIONS: set[str] = {
    "sin", "cos", "tan", "csc", "sec", "cot",
    "arcsin", "arccos", "arctan",
    "sinh", "cosh", "tanh", "csch", "sech", "coth",
    "ln", "log", "lg", "exp",
    "lim", "limsup", "liminf", "sup", "inf",
    "max", "min", "argmax", "argmin",
    "det", "gcd", "lcm", "mod",
    "ker", "deg", "dim", "hom",
    "Pr", "Re", "Im",
}


def omml_to_latex(elem) -> str:
    """Convert an OMML math element to LaTeX.

    Args:
        elem: An lxml Element, either m:oMathPara or m:oMath.

    Returns:
        LaTeX math string wrapped in $...$ or $$...$$.
    """
    tag = _localname(elem.tag)
    if tag == "oMathPara":
        return _convert_oMathPara(elem)
    elif tag == "oMath":
        return _convert_oMath(elem)
    else:
        content = _convert_element(elem)
        return f"${content}$"


def _convert_oMathPara(elem) -> str:
    """Convert display math paragraph to $$...$$."""
    parts = []
    for child in elem:
        tag = _localname(child.tag)
        if tag == "oMath":
            parts.append(_convert_element(child))
    body = r"\\".join(parts)
    return f"$$\n{body}\n$$"


def _convert_oMath(elem) -> str:
    """Convert inline math to $...$."""
    content = _convert_element(elem)
    return f"${content}$"


def _convert_element(elem) -> str:
    """Recursively convert an OMML element to LaTeX."""
    tag = _localname(elem.tag)

    if tag == "r":
        return _convert_run(elem)
    elif tag == "f":
        return _convert_fraction(elem)
    elif tag == "func":
        return _convert_function(elem)
    elif tag == "sSup":
        return _convert_sSup(elem)
    elif tag == "sSub":
        return _convert_sSub(elem)
    elif tag == "sSubSup":
        return _convert_sSubSup(elem)
    elif tag == "sPre":
        return _convert_sPre(elem)
    elif tag == "rad":
        return _convert_radical(elem)
    elif tag == "nary":
        return _convert_nary(elem)
    elif tag == "acc":
        return _convert_accent(elem)
    elif tag == "bar":
        return _convert_bar(elem)
    elif tag == "d":
        return _convert_delimiter(elem)
    elif tag == "m":
        return _convert_matrix(elem)
    elif tag == "eqArr":
        return _convert_eqArray(elem)
    elif tag == "groupChr":
        return _convert_groupChr(elem)
    elif tag == "limLow":
        return _convert_limLow(elem)
    elif tag == "limUpp":
        return _convert_limUpp(elem)
    elif tag == "box":
        return _convert_box(elem)
    elif tag == "borderBox":
        return _convert_borderBox(elem)
    elif tag == "phant":
        return _convert_phantom(elem)
    elif tag in ("e", "num", "den", "sup", "sub", "deg"):
        children = [_convert_element(c) for c in elem]
        return "".join(children)
    elif tag == "oMath":
        children = [_convert_element(c) for c in elem]
        return "".join(children)
    else:
        children = [_convert_element(c) for c in elem]
        return "".join(children)


def _convert_run(elem) -> str:
    """Convert m:r (math run) to LaTeX text."""
    texts = []
    for child in elem:
        tag = _localname(child.tag)
        if tag == "t":
            text = child.text or ""
            texts.append(text)
        elif tag == "br":
            texts.append(" ")
    return _escape_latex("".join(texts))


def _convert_fraction(elem) -> str:
    """Convert m:f to \\frac{num}{den}."""
    num = ""
    den = ""
    for child in elem:
        tag = _localname(child.tag)
        if tag == "num":
            num = _convert_element(child)
        elif tag == "den":
            den = _convert_element(child)
    return rf"\frac{{{num}}}{{{den}}}"


def _convert_function(elem) -> str:
    """Convert m:func to \\sin, \\cos, etc."""
    func_name = ""
    base = ""
    for child in elem:
        tag = _localname(child.tag)
        if tag == "funcName":
            # Extract function name text
            func_name = _extract_text(child)
        elif tag == "e":
            base = _convert_element(child)
    if func_name.lower() in _MATH_FUNCTIONS:
        return rf"\{func_name} {base}"
    elif func_name:
        return rf"\operatorname{{{func_name}}} {base}"
    return base


def _convert_sSup(elem) -> str:
    """Convert m:sSup to base^{sup}."""
    base = ""
    sup = ""
    for child in elem:
        tag = _localname(child.tag)
        if tag == "e":
            base = _convert_element(child)
        elif tag == "sup":
            sup = _convert_element(child)
    return f"{{{base}}}^{{{sup}}}"


def _convert_sSub(elem) -> str:
    """Convert m:sSub to base_{sub}."""
    base = ""
    sub = ""
    for child in elem:
        tag = _localname(child.tag)
        if tag == "e":
            base = _convert_element(child)
        elif tag == "sub":
            sub = _convert_element(child)
    return f"{{{base}}}_{{{sub}}}"


def _convert_sSubSup(elem) -> str:
    """Convert m:sSubSup to base_{sub}^{sup}."""
    base = ""
    sub = ""
    sup = ""
    for child in elem:
        tag = _localname(child.tag)
        if tag == "e":
            base = _convert_element(child)
        elif tag == "sub":
            sub = _convert_element(child)
        elif tag == "sup":
            sup = _convert_element(child)
    result = f"{{{base}}}"
    if sub:
        result += f"_{{{sub}}}"
    if sup:
        result += f"^{{{sup}}}"
    return result


def _convert_sPre(elem) -> str:
    """Convert m:sPre to pre-sub-superscript: {pre}_{sub}^{sup} base."""
    base = ""
    sub = ""
    sup = ""
    pre = ""
    for child in elem:
        tag = _localname(child.tag)
        if tag == "e":
            base = _convert_element(child)
        elif tag == "sub":
            sub = _convert_element(child)
        elif tag == "sup":
            sup = _convert_element(child)
        elif tag == "pre":
            pre = _convert_element(child)
    result = ""
    if pre:
        result = f"{{{pre}}}"
    if sub:
        result += f"_{{{sub}}}"
    if sup:
        result += f"^{{{sup}}}"
    result += f"{{{base}}}"
    return result


def _convert_radical(elem) -> str:
    """Convert m:rad to \\sqrt or \\sqrt[n]."""
    deg = ""
    base = ""
    for child in elem:
        tag = _localname(child.tag)
        if tag == "deg":
            deg = _convert_element(child)
        elif tag == "e":
            base = _convert_element(child)
    if deg:
        return rf"\sqrt[{deg}]{{{base}}}"
    return rf"\sqrt{{{base}}}"


def _convert_nary(elem) -> str:
    """Convert m:nary to \\sum_{sub}^{sup}, \\int, etc."""
    nary_char = ""
    sub = ""
    sup = ""
    base = ""
    for child in elem:
        tag = _localname(child.tag)
        if tag == "chr":
            nary_char = _get_char_val(child)
        elif tag == "sub":
            sub = _convert_element(child)
        elif tag == "sup":
            sup = _convert_element(child)
        elif tag == "e":
            base = _convert_element(child)

    cmd = _NARY_CHAR_MAP.get(nary_char, r"\sum")
    result = cmd
    if sub:
        result += f"_{{{sub}}}"
    if sup:
        result += f"^{{{sup}}}"
    if base:
        result += f" {{{base}}}"
    return result


def _convert_accent(elem) -> str:
    """Convert m:acc to \\hat, \\tilde, etc."""
    accent_char = ""
    base = ""
    for child in elem:
        tag = _localname(child.tag)
        if tag == "chr":
            accent_char = _get_char_val(child)
        elif tag == "e":
            base = _convert_element(child)

    cmd = _ACCENT_CHAR_MAP.get(accent_char, r"\hat")
    return f"{cmd}{{{base}}}"


def _convert_bar(elem) -> str:
    """Convert m:bar to \\overline or \\underline."""
    pos = elem.get(f"{{{M_NS}}}pos", "top")
    base = ""
    for child in elem:
        tag = _localname(child.tag)
        if tag == "e":
            base = _convert_element(child)
    cmd = r"\overline" if pos == "top" else r"\underline"
    return f"{cmd}{{{base}}}"


def _convert_delimiter(elem) -> str:
    """Convert m:d to \\left( ... \\right)."""
    open_char = ""
    close_char = ""
    base = ""
    for child in elem:
        tag = _localname(child.tag)
        if tag == "dPr":
            open_char = _get_delim_char(child, "begChr")
            close_char = _get_delim_char(child, "endChr")
        elif tag == "e":
            base = _convert_element(child)

    left = _DELIM_OPEN_MAP.get(open_char, r"\left" + "(")
    right = _DELIM_CLOSE_MAP.get(close_char, r"\right" + ")")

    # Special case: |...| should be \left| ... \right|
    if open_char == "|":
        left = r"\left|"
    if close_char == "|":
        right = r"\right|"

    return f"{left} {base} {right}"


def _get_delim_char(elem, child_tag: str) -> str:
    """Extract delimiter character value from a dPr child element."""
    for child in elem:
        if _localname(child.tag) == child_tag:
            return child.get(f"{{{M_NS}}}val", "") or ""
    return ""


def _convert_matrix(elem) -> str:
    """Convert m:m to \\begin{matrix}...\\end{matrix}."""
    rows = []
    for child in elem:
        if _localname(child.tag) == "mr":
            cells = []
            for cell in child:
                if _localname(cell.tag) == "e":
                    cells.append(_convert_element(cell))
            rows.append(" & ".join(cells))
    body = r" \\ ".join(rows)
    return rf"\begin{{matrix}}{body}\end{{matrix}}"


def _convert_eqArray(elem) -> str:
    """Convert m:eqArr to aligned equations."""
    rows = []
    for child in elem:
        if _localname(child.tag) == "e":
            rows.append(_convert_element(child))
    body = r" \\ ".join(rows)
    return body  # Raw content; caller wraps in display math


def _convert_groupChr(elem) -> str:
    """Convert m:groupChr to \\overbrace or \\underbrace."""
    chr_char = ""
    pos = "bottom"
    base = ""
    for child in elem:
        tag = _localname(child.tag)
        if tag == "groupChrPr":
            chr_char = _get_delim_char(child, "chr") or chr_char
            pos = child.get(f"{{{M_NS}}}pos", pos)
        elif tag == "e":
            base = _convert_element(child)
    # Default: use overbrace/underbrace based on position
    if chr_char == "⏞" or pos == "bottom":
        return rf"\underbrace{{{base}}}"
    else:
        return rf"\overbrace{{{base}}}"


def _convert_limLow(elem) -> str:
    """Convert m:limLow to base_{limit}."""
    base = ""
    lim = ""
    for child in elem:
        tag = _localname(child.tag)
        if tag == "e":
            base = _convert_element(child)
        elif tag == "lim":
            lim = _convert_element(child)
    return f"{{{base}}}_{{{lim}}}"


def _convert_limUpp(elem) -> str:
    """Convert m:limUpp to base^{limit}."""
    base = ""
    lim = ""
    for child in elem:
        tag = _localname(child.tag)
        if tag == "e":
            base = _convert_element(child)
        elif tag == "lim":
            lim = _convert_element(child)
    return f"{{{base}}}^{{{lim}}}"


def _convert_box(elem) -> str:
    """Convert m:box — just pass through content."""
    for child in elem:
        if _localname(child.tag) == "e":
            return _convert_element(child)
    return ""


def _convert_borderBox(elem) -> str:
    """Convert m:borderBox to \\boxed{...}."""
    base = ""
    for child in elem:
        if _localname(child.tag) == "e":
            base = _convert_element(child)
    return rf"\boxed{{{base}}}"


def _convert_phantom(elem) -> str:
    """Convert m:phant to \\phantom or empty."""
    show = elem.get(f"{{{M_NS}}}show", "1")
    base = ""
    for child in elem:
        if _localname(child.tag) == "e":
            base = _convert_element(child)
    if show == "0":
        return ""
    return base


def _extract_text(elem) -> str:
    """Extract all text from m:t children recursively."""
    texts = []
    for child in elem.iter(f"{{{M_NS}}}t"):
        if child.text:
            texts.append(child.text)
    return "".join(texts)


def _get_char_val(elem) -> str:
    """Get the val attribute of an OMML element."""
    return elem.get(f"{{{M_NS}}}val", "") or ""


def _localname(tag: str) -> str:
    """Extract local name from a fully qualified XML tag."""
    if "}" in tag:
        return tag.rsplit("}", 1)[1]
    return tag


def _escape_latex(text: str) -> str:
    """Escape special LaTeX characters in plain text."""
    chars = {
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
        "\\": r"\textbackslash{}",
    }
    for ch, repl in chars.items():
        text = text.replace(ch, repl)
    return text


def has_math(paragraph_element) -> tuple[bool, str]:
    """Check if a paragraph contains OMML math elements.

    Args:
        paragraph_element: A python-docx paragraph._element (lxml).

    Returns:
        (has_math, math_type) where math_type is 'display', 'inline', or ''.
    """
    for child in paragraph_element.iter(f"{{{M_NS}}}oMathPara"):
        return (True, "display")
    for child in paragraph_element.iter(f"{{{M_NS}}}oMath"):
        return (True, "inline")
    return (False, "")


def convert_paragraph_math(paragraph_element) -> str | None:
    """Convert all math in a paragraph to LaTeX.

    For display math (oMathPara), returns the full $$...$$ block.
    For inline math (oMath), returns the paragraph text with math inline
    as $...$.

    Returns None if no math found.
    """
    has_m, mtype = has_math(paragraph_element)
    if not has_m:
        return None

    if mtype == "display":
        result_parts = []
        for child in paragraph_element:
            tag = _localname(child.tag)
            if tag == "oMathPara":
                result_parts.append(omml_to_latex(child))
        return "\n".join(result_parts) if result_parts else None

    # Inline math: build text with $...$ in place of oMath
    result_parts = []
    for child in paragraph_element:
        tag = _localname(child.tag)
        if tag == "oMath":
            latex = omml_to_latex(child)
            result_parts.append(latex)
        elif tag == "r":
            texts = []
            for t in child.iter(f"{{{M_NS}}}t"):
                if t.text:
                    texts.append(t.text)
            if texts:
                result_parts.append(_escape_latex("".join(texts)))
        else:
            if child.text:
                result_parts.append(child.text)
    return "".join(result_parts)
