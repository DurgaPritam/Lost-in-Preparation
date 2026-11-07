"""Write public/fonts/fraunces-latin-opsz-{normal,italic}.woff2 from the design's files with the optical-size axis pinned
at 144 (the weight axis is kept whole).

Why: the site sets Fraunces only through `.font-display`, which always applies `font-variation-settings: 'opsz' 144`
(styles/globals.css, from the design), and nothing else references --f-display. Every glyph the site renders is therefore
the opsz-144 instance, so pinning the axis changes no rendering and roughly halves the two files (the largest fonts on
the light theme's first screen). The licence (SIL OFL 1.1) permits modified versions; the file keeps its name because
the design's fonts.css refers to it, and the OFL's reserved-name clause is not triggered (Fraunces declares no reserved
font name; see public/fonts/LICENSE-Fraunces.txt).

Run from site/ with a Python that has fontTools and brotli:  python scripts/pin-fraunces-opsz.py
"""
from pathlib import Path

from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

SRC = Path("../design/v2/lost-in-preparation-handoff/assets/fonts")
OUT = Path("public/fonts")

for style in ("normal", "italic"):
    name = f"fraunces-latin-opsz-{style}.woff2"
    font = TTFont(SRC / name)
    pinned = instancer.instantiateVariableFont(font, {"opsz": 144})
    pinned.flavor = "woff2"
    pinned.save(OUT / name)
    print(name, (SRC / name).stat().st_size // 1024, "KB ->", (OUT / name).stat().st_size // 1024, "KB")
