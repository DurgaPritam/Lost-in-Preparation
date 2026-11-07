"""Write styles/font-fallbacks.css: metric-matched fallback faces for the v2 web fonts (the technique next/font uses).

Each fallback renders a local font (Times New Roman / Liberation Serif, Arial / Liberation Sans, Courier New /
Liberation Mono; the Liberation fonts are metric-compatible with them) scaled to the web face, so text keeps its size
and line breaks while the web face loads (font-display: swap) and does not shift when it arrives.

  size-adjust      = web face's average advance / reference font's average advance, weighted by English letter
                     frequency (space and lowercase letters), both per em;
  ascent/descent/line-gap overrides = the web face's hhea metrics per em, divided by size-adjust.

Fraunces is variable: it is measured at wght 400 and opsz 144, the setting `.font-display` uses.
Run from site/ with a Python that has fontTools and brotli (needed to read woff2):
    python scripts/font-fallbacks.py [--ref-dir /System/Library/Fonts/Supplemental]
The reference fonts are read only for their metrics; nothing is copied.
"""
import argparse
import io
from pathlib import Path

from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

FREQ = {  # English letter frequency (%), plus space; used to weight the average advance
    " ": 18.0, "e": 10.2, "t": 7.5, "a": 6.5, "o": 6.2, "i": 5.7, "n": 5.7, "s": 5.3, "h": 5.0, "r": 4.9, "d": 3.4,
    "l": 3.3, "c": 2.3, "u": 2.3, "m": 2.0, "w": 2.0, "f": 1.8, "g": 1.6, "y": 1.6, "p": 1.6, "b": 1.3, "v": 0.8,
    "k": 0.6, "j": 0.1, "x": 0.2, "q": 0.1, "z": 0.1,
}

REF = {  # reference family -> {(weight>=600, italic): (file, local() names)}
    "serif": {
        (False, False): ("Times New Roman.ttf", ["Times New Roman", "TimesNewRomanPSMT", "Liberation Serif", "LiberationSerif"]),
        (False, True): ("Times New Roman Italic.ttf", ["Times New Roman Italic", "TimesNewRomanPS-ItalicMT", "Liberation Serif Italic", "LiberationSerif-Italic"]),
    },
    "sans": {
        (False, False): ("Arial.ttf", ["Arial", "ArialMT", "Liberation Sans", "LiberationSans"]),
        (True, False): ("Arial Bold.ttf", ["Arial Bold", "Arial-BoldMT", "Liberation Sans Bold", "LiberationSans-Bold"]),
        (False, True): ("Arial Italic.ttf", ["Arial Italic", "Arial-ItalicMT", "Liberation Sans Italic", "LiberationSans-Italic"]),
    },
    "mono": {
        (False, False): ("Courier New.ttf", ["Courier New", "CourierNewPSMT", "Liberation Mono", "LiberationMono"]),
    },
}

# (fallback family, web font file, weight, style, reference kind). One face per weight and style the site uses.
FACES = [
    ("Fraunces Fallback", "fraunces-latin-opsz-normal", 400, "normal", "serif"),
    ("Fraunces Fallback", "fraunces-latin-opsz-italic", 400, "italic", "serif"),
    ("Instrument Sans Fallback", "instrument-sans-latin-400-normal", 400, "normal", "sans"),
    ("Instrument Sans Fallback", "instrument-sans-latin-500-normal", 500, "normal", "sans"),
    ("Instrument Sans Fallback", "instrument-sans-latin-600-normal", 600, "normal", "sans"),
    ("Instrument Sans Fallback", "instrument-sans-latin-400-italic", 400, "italic", "sans"),
    ("JetBrains Mono Fallback", "jetbrains-mono-latin-400-normal", 400, "normal", "mono"),
    ("JetBrains Mono Fallback", "jetbrains-mono-latin-500-normal", 500, "normal", "mono"),
    ("Instrument Serif Fallback", "instrument-serif-latin-400-normal", 400, "normal", "serif"),
    ("Instrument Serif Fallback", "instrument-serif-latin-400-italic", 400, "italic", "serif"),
    ("Hanken Grotesk Fallback", "hanken-grotesk-latin-400-normal", 400, "normal", "sans"),
    ("Hanken Grotesk Fallback", "hanken-grotesk-latin-500-normal", 500, "normal", "sans"),
    ("Hanken Grotesk Fallback", "hanken-grotesk-latin-600-normal", 600, "normal", "sans"),
    ("DM Mono Fallback", "dm-mono-latin-400-normal", 400, "normal", "mono"),
    ("DM Mono Fallback", "dm-mono-latin-500-normal", 500, "normal", "mono"),
]

# The design's stacks (tokens.css), with the fallback family inserted right after the web font. Nothing else changes.
LIGHT = {
    "--f-display": "'Fraunces', 'Fraunces Fallback', 'Iowan Old Style', Georgia, serif",
    "--f-sans": "'Instrument Sans', 'Instrument Sans Fallback', 'Segoe UI', system-ui, sans-serif",
    "--f-mono": "'JetBrains Mono', 'JetBrains Mono Fallback', ui-monospace, Menlo, monospace",
}
DARK = {
    "--f-display": "'Instrument Serif', 'Instrument Serif Fallback', 'Iowan Old Style', Georgia, serif",
    "--f-sans": "'Hanken Grotesk', 'Hanken Grotesk Fallback', 'Segoe UI', system-ui, sans-serif",
    "--f-mono": "'DM Mono', 'DM Mono Fallback', ui-monospace, Menlo, monospace",
}


def avg_advance(font: TTFont) -> float:
    cmap = font.getBestCmap()
    hmtx = font["hmtx"]
    upm = font["head"].unitsPerEm
    total = weight = 0.0
    for ch, f in FREQ.items():
        g = cmap.get(ord(ch))
        if g is None:
            raise SystemExit(f"{font} has no glyph for {ch!r}")
        total += hmtx[g][0] / upm * f
        weight += f
    return total / weight


def load_web(path: Path) -> TTFont:
    font = TTFont(path)
    if "fvar" in font:
        axes = {a.axisTag for a in font["fvar"].axes}
        loc = {k: v for k, v in {"wght": 400, "opsz": 144}.items() if k in axes}
        font = instancer.instantiateVariableFont(font, loc)
        buf = io.BytesIO()
        font.flavor = None
        font.save(buf)
        font = TTFont(io.BytesIO(buf.getvalue()))
    return font


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref-dir", default="/System/Library/Fonts/Supplemental")
    ap.add_argument("--fonts", default="public/fonts")
    ap.add_argument("--out", default="styles/font-fallbacks.css")
    a = ap.parse_args()
    ref_dir = Path(a.ref_dir)

    lines = [
        "/*",
        " * SITE (see CHANGES.md): metric-matched fallback faces for the v2 web fonts. Written by scripts/font-fallbacks.py;",
        " * do not edit by hand. Each face renders a local Times New Roman / Arial / Courier New (or the metric-compatible",
        " * Liberation font) scaled to the web face, so text does not shift when the web face arrives (font-display: swap).",
        " * The token stacks below are the design's (tokens.css) with the fallback family inserted after the web font.",
        " */",
    ]
    for family, file, wght, style, kind in FACES:
        web = load_web(Path(a.fonts) / f"{file}.woff2")
        refs = REF[kind]
        italic = style == "italic"
        # the closest reference face that exists: same boldness and style, then regular in that style, then regular
        key = next(k for k in [(wght >= 600, italic), (False, italic), (False, False)] if k in refs)
        ref_file, names = refs[key]
        ref = TTFont(ref_dir / ref_file)
        size = avg_advance(web) / avg_advance(ref)
        hhea, upm = web["hhea"], web["head"].unitsPerEm
        asc, desc, gap = hhea.ascent / upm / size, abs(hhea.descent) / upm / size, hhea.lineGap / upm / size
        src = ", ".join(f"local('{n}')" for n in names)
        lines.append(
            f"@font-face {{ font-family: '{family}'; font-weight: {wght}; font-style: {style}; src: {src};\n"
            f"  size-adjust: {size * 100:.2f}%; ascent-override: {asc * 100:.2f}%; descent-override: {desc * 100:.2f}%; line-gap-override: {gap * 100:.2f}%; }}"
        )

    def block(sel: str, stacks: dict, indent: str = "") -> list[str]:
        return [f"{indent}{sel} {{"] + [f"{indent}  {k}: {v};" for k, v in stacks.items()] + [f"{indent}}}"]

    lines += [""] + block(":root", LIGHT)
    lines += ["@media (prefers-color-scheme: dark) {"] + block(':root:not([data-theme="light"])', DARK, "  ") + ["}"]
    lines += block(':root[data-theme="dark"]', DARK)
    Path(a.out).write_text("\n".join(lines) + "\n")
    print(a.out, len(FACES), "faces")


if __name__ == "__main__":
    main()
