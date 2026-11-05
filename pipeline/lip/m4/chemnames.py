"""Complete-chemical-name matching for registered literature checks (v3 onwards; v1/v2 are NOT re-scored).

The v2 collector matched compound names as whole words, which still accepted "phenol" in "total phenol
content" and "apigenin" in "Apigenin 7-O-glucoside". A name now counts only as a COMPLETE chemical name:

  1. Normalised spelling on both sides: lower case; α/β/γ/δ -> alpha/beta/gamma/delta; dash variants -> "-";
     an aglycone joined to a locant by a hyphen or space is joined by a space ("apigenin-7-O-glucoside" ->
     "apigenin 7-glucoside"); the "O-" of an O-glycoside locant is dropped ("7-O-" -> "7-").
  2. Word boundaries: no letter, digit or hyphen directly before or after the match.
  3. Not part of a longer chemical term:
       - not preceded by a pooling modifier ("total", "sum of");
       - not followed by a class, derivative or conjugate word (compounds, derivatives, glycosides, esters,
         equivalents, type, class, group, content of a class ...), a sugar or conjugate name (glucoside,
         rutinoside, glucuronide, sulfate ...), or a locant that starts a longer name ("7-glucoside", "3,4'-di...");
       - not inside a longer matched name (the longest match wins).
  4. Class nouns never count as compounds, even if a database lists a compound of that name (CLASS_WORDS).
  5. Table labels (`exact_label`): after removing footnote markers, a trailing parenthetical abbreviation or
     number, and normalising, the WHOLE label must equal one known name.
"""
from __future__ import annotations

import re

GREEK = {"α": "alpha", "β": "beta", "γ": "gamma", "δ": "delta", "ω": "omega"}
DASHES = dict.fromkeys(map(ord, "‐‑‒–—−"), "-")
SUGARS = (r"glucoside|glucosides|galactoside|rhamnoside|rutinoside|arabinoside|xyloside|glucuronide|galacturonide|"
          r"hexoside|pentoside|deoxyhexoside|glycoside|glycosides|neohesperidoside|sophoroside|apioside|malonylglucoside|"
          r"diglucoside|sulfate|sulphate|acetate|methyl ether|dimethyl ether")
AFTER_REJECT = re.compile(r"^\s*(?:(?:compounds?|derivatives?|analogues?|analogs?|conjugates?|esters?|equivalents?|"
                          r"type|types|class|classes|groups?|family|families|skeletons?|units?|moiet(?:y|ies)|residues?|"
                          r"oligomers?|polymers?|based|aglycones?)\b|(?:" + SUGARS + r")\b|\d+(?:,\d+)*['′″]*-)", re.I)
BEFORE_REJECT = re.compile(r"(?:\btotal|\bsum of)\s*$", re.I)
CLASS_WORDS = {"phenol", "phenols", "polyphenol", "polyphenols", "tannin", "tannins", "flavonoid", "flavonoids", "alkaloid",
               "alkaloids", "terpene", "terpenes", "terpenoid", "terpenoids", "saponin", "saponins", "lignin", "lignans",
               "sugar", "sugars", "protein", "proteins", "anthocyanin", "anthocyanins", "glycoside", "glycosides"}


def normalise(s: str) -> str:
    s = s.translate(DASHES)
    for g, w in GREEK.items():
        s = s.replace(g, w)
    s = s.lower()
    s = re.sub(r"(?<=[a-z])[- ](?=\d)", " ", s)           # aglycone-7-... -> aglycone 7-...
    s = re.sub(r"(\d['′″]*)-o-", r"\1-", s)               # 7-O-glucoside -> 7-glucoside
    return re.sub(r"\s+", " ", s).strip()


class Matcher:
    """names: mapping of synonym -> canonical compound name (any case/spelling; normalised here)."""

    def __init__(self, names: dict[str, str]):
        self.names: dict[str, str] = {}
        for syn, canon in names.items():
            k = normalise(syn)
            if k and k not in CLASS_WORDS:
                self.names.setdefault(k, canon)
        self._pats = sorted(self.names, key=len, reverse=True)
        self._rx = (re.compile("|".join(r"(?<![\w-])" + re.escape(p) + r"(?![\w-])" for p in self._pats))
                    if self._pats else None)

    def hits(self, text: str) -> list[str]:
        """Canonical names that occur in `text` as complete chemical names (rules 1-4), in text order."""
        t = normalise(text)
        if self._rx is None or not self._rx.search(t):
            return []
        spans = []
        for p in self._pats:
            for m in re.finditer(r"(?<![\w-])" + re.escape(p) + r"(?![\w-])", t):
                spans.append((m.start(), m.end(), p))
        keep = []
        for s, e, p in spans:
            if any(o[0] <= s and e <= o[1] and (o[1] - o[0]) > (e - s) for o in spans):
                continue  # inside a longer matched name
            if BEFORE_REJECT.search(t[:s]) or AFTER_REJECT.search(t[e:]):
                continue  # part of a longer chemical term
            keep.append((s, p))
        out = []
        for _, p in sorted(keep):
            if self.names[p] not in out:
                out.append(self.names[p])
        return out

    def exact_label(self, label: str) -> str | None:
        """Canonical name if the whole table label is one complete chemical name (rule 5), else None."""
        s = re.sub(r"<[^>]+>", "", label)
        s = re.sub(r"[*†‡§¶#]+", "", s)
        s = re.sub(r"(?<=[A-Za-z\)])\s*[a-z]{1,2}$", "", s) if re.search(r"\s[a-z]{1,2}$", s) else s  # trailing footnote letters
        s = re.sub(r"\s*\([^()]*\)\s*$", "", s)                 # trailing (abbreviation) or (number)
        s = re.sub(r"^\s*\d+[.)]?\s+", "", s)                     # leading peak number "12 " / "12. "
        k = normalise(s)
        return self.names.get(k)
