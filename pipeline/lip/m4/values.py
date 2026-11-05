"""Table-cell number parsing for FUTURE registered checks (v4 onwards). v3 keeps its registered parser
(prereg_v3.value_of) and is NOT re-scored.

Rules:
  - not detected (nd, n.d., ND, <LOD, <LOQ, bdl, tr, traces, a lone dash) -> 0.0;
  - the first number in the cell is used (the mean of "mean ± SD");
  - thousands separators are recognised when the grouping is unambiguous:
        "1,234.5" / "12,345" with a dot elsewhere -> comma groups are thousands;
        "1.234,5" -> dot groups are thousands, comma is the decimal mark;
        "1 234.5" / "1 234,5" (space or thin space between groups of 3) -> thousands;
  - a single comma followed by 1-2 or 4+ digits is a decimal comma ("10,5" -> 10.5);
  - a single dot is always a decimal point ("1.234" -> 1.234; PMC tables use English conventions);
  - "1,234" alone (one comma, exactly three digits after it) is AMBIGUOUS (thousands in English, a decimal
    comma elsewhere) -> None, i.e. missing, never guessed;
  - scientific notation ("2.1e-3", "2.1 × 10−3") is supported;
  - anything else -> None (missing).
"""
from __future__ import annotations

import html
import re

ND = re.compile(r"^\s*(?:n\.?\s?d\.?|ND|<\s*LO[DQ]|bdl|BDL|tr\.?|traces?|[-–−])\s*[a-z*†‡]{0,2}\s*$", re.I)
NUM = re.compile(r"(?<![\w.,])(\d{1,3}(?:[   ]\d{3})+(?:[.,]\d+)?|\d+(?:[.,]\d+)*)"
                 r"(?:\s*(?:[eE]|[×x]\s*10\^?)\s*([-+−–]?\d+))?")


class AmbiguousNumber(ValueError):
    pass


def _to_float(tok: str) -> float:
    t = tok.replace(" ", " ").replace(" ", " ")
    if " " in t:                                     # space-grouped thousands
        t = t.replace(" ", "")
        return float(t.replace(",", "."))
    dots, commas = t.count("."), t.count(",")
    if dots and commas:                              # both: the LAST one is the decimal mark
        if t.rfind(".") > t.rfind(","):
            if not re.fullmatch(r"\d{1,3}(?:,\d{3})+\.\d+", t):
                raise AmbiguousNumber(tok)
            return float(t.replace(",", ""))
        if not re.fullmatch(r"\d{1,3}(?:\.\d{3})+,\d+", t):
            raise AmbiguousNumber(tok)
        return float(t.replace(".", "").replace(",", "."))
    sep = "," if commas else "." if dots else None
    if sep is None:
        return float(t)
    parts = t.split(sep)
    if len(parts) > 2:                               # "1,234,567" or "1.234.567": groups of three
        if all(len(p) == 3 for p in parts[1:]) and 1 <= len(parts[0]) <= 3:
            return float("".join(parts))
        raise AmbiguousNumber(tok)
    if sep == "," and len(parts[1]) == 3:            # "1,234": thousands or decimal comma?
        raise AmbiguousNumber(tok)
    return float(t.replace(",", "."))


def parse_cell(cell: str) -> float | None:
    s = html.unescape(cell or "").strip()
    if not s:
        return None
    if ND.match(s):
        return 0.0
    m = NUM.search(s)
    if not m:
        return None
    try:
        v = _to_float(m.group(1))
    except AmbiguousNumber:
        return None
    if m.group(2):
        v *= 10 ** int(m.group(2).replace("−", "-").replace("–", "-"))
    return v
