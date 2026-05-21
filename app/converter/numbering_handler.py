"""Extract list numbering definitions from Word OOXML.

Word stores list numbering in the numbering part (numbering.xml).
This module parses the definitions to retrieve starting values
and number formats for ordered lists.
"""

from lxml import etree

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


class NumberingHandler:
    """Parses Word numbering definitions for list start values."""

    def __init__(self, python_docx_document):
        self._start_map: dict[tuple[int, int], int] = {}
        self._numfmt_map: dict[tuple[int, int], str] = {}
        self._abstract_nums: dict[int, etree.Element] = {}
        self._parse(python_docx_document)

    def _parse(self, doc) -> None:
        try:
            numbering_part = doc.part.numbering_part
        except AttributeError:
            return
        if numbering_part is None:
            return
        numbering_elem = numbering_part.element

        for abstract_num in numbering_elem.findall(f"{{{W_NS}}}abstractNum"):
            an_id = int(abstract_num.get(f"{{{W_NS}}}abstractNumId"))
            self._abstract_nums[an_id] = abstract_num

        for num_elem in numbering_elem.findall(f"{{{W_NS}}}num"):
            num_id = int(num_elem.get(f"{{{W_NS}}}numId"))
            an_ref = num_elem.find(f"{{{W_NS}}}abstractNumId")
            if an_ref is None:
                continue
            an_id = int(an_ref.get(f"{{{W_NS}}}val"))
            overrides = {}
            for ovr in num_elem.findall(f"{{{W_NS}}}lvlOverride"):
                ilvl = int(ovr.get(f"{{{W_NS}}}ilvl"))
                start_ovr = ovr.find(f"{{{W_NS}}}startOverride")
                if start_ovr is not None:
                    overrides[ilvl] = int(start_ovr.get(f"{{{W_NS}}}val"))

            if an_id not in self._abstract_nums:
                continue
            abstract_elem = self._abstract_nums[an_id]
            for lvl_elem in abstract_elem.findall(f"{{{W_NS}}}lvl"):
                ilvl = int(lvl_elem.get(f"{{{W_NS}}}ilvl"))
                key = (num_id, ilvl)
                # Check for level override first
                if ilvl in overrides:
                    self._start_map[key] = overrides[ilvl]
                else:
                    start_elem = lvl_elem.find(f"{{{W_NS}}}start")
                    if start_elem is not None:
                        self._start_map[key] = int(start_elem.get(f"{{{W_NS}}}val"))
                numfmt_elem = lvl_elem.find(f"{{{W_NS}}}numFmt")
                if numfmt_elem is not None:
                    self._numfmt_map[key] = numfmt_elem.get(f"{{{W_NS}}}val", "decimal")

    def get_start(self, num_id: int, ilvl: int) -> int:
        """Return the starting number for a given numId and ilvl.

        Defaults to 1 if not found.
        """
        return self._start_map.get((num_id, ilvl), 1)

    def get_numfmt(self, num_id: int, ilvl: int) -> str:
        """Return the number format (decimal, upperRoman, lowerLetter, etc.)."""
        return self._numfmt_map.get((num_id, ilvl), "decimal")

    @staticmethod
    def extract_num_info(paragraph_element) -> tuple[int, int] | None:
        """Extract (numId, ilvl) from a paragraph XML element.

        Returns None if the paragraph is not a numbered list item.
        """
        numPr = paragraph_element.find(f"{{{W_NS}}}pPr/{{{W_NS}}}numPr")
        if numPr is None:
            return None
        num_id_elem = numPr.find(f"{{{W_NS}}}numId")
        ilvl_elem = numPr.find(f"{{{W_NS}}}ilvl")
        if num_id_elem is None:
            return None
        num_id = int(num_id_elem.get(f"{{{W_NS}}}val"))
        ilvl = int(ilvl_elem.get(f"{{{W_NS}}}val")) if ilvl_elem is not None else 0
        return (num_id, ilvl)

    @staticmethod
    def format_num(num: int, numfmt: str) -> str:
        """Format a number according to Word's numFmt."""
        if numfmt == "upperRoman":
            return NumberingHandler._to_roman(num).upper()
        elif numfmt == "lowerRoman":
            return NumberingHandler._to_roman(num).lower()
        elif numfmt == "upperLetter":
            return chr(ord('A') + num - 1) if 1 <= num <= 26 else str(num)
        elif numfmt == "lowerLetter":
            return chr(ord('a') + num - 1) if 1 <= num <= 26 else str(num)
        else:
            return str(num)

    @staticmethod
    def _to_roman(n: int) -> str:
        vals = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
                (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
                (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]
        result = []
        for v, r in vals:
            while n >= v:
                result.append(r)
                n -= v
        return "".join(result)
