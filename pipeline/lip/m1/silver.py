"""Silver reference set (PROVISIONAL, NOT GOLD): build and validate data/silver/silver_v1.json.

basis = "silver_ai_reference". Labels were written by an AI (Claude Code) directly from the
annotation guidelines, passage by passage, in data/silver/silver_v1_spec.py. This module only
expands that notation and checks it: every quote must occur verbatim in the passage (or, for
plant names marked H:, in the entry heading). It never generates labels itself.

The output uses the same shape as the annotation tool's export, so the evaluator can read it,
but it is written to data/silver/ and is never read as gold.
"""
from __future__ import annotations

import importlib.util
import json
from datetime import datetime, timezone

from ..paths import ROOT
from .sample import SAMPLE_PATH
from .schema import CATEGORICAL_FIELDS

BASIS = "silver_ai_reference"
LABEL = "AI reference labels (provisional; not human-validated)"
SPEC = ROOT / "data" / "silver" / "silver_v1_spec.py"
OUT = ROOT / "data" / "silver" / "silver_v1.json"
UNK = "unknown"


class SilverError(ValueError):
    pass


def _load_spec() -> dict:
    spec = importlib.util.spec_from_file_location("silver_v1_spec", SPEC)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.S


def _q(quote: str, text: str, heading: str, where: str, heading_ok: bool = False) -> dict:
    i = text.find(quote)
    if i >= 0:
        return {"quote": quote, "start": i, "end": i + len(quote), "inHeading": False}
    if heading_ok and quote in heading:
        return {"quote": quote, "start": -1, "end": -1, "inHeading": True}
    raise SilverError(f"{where}: quote not verbatim: {quote!r}")


def _vq(v: str) -> tuple[str, str | None]:
    if "@" not in v:
        raise SilverError(f"enum value without evidence quote: {v!r}")
    val, quote = v.split("@", 1)
    return val, quote


def expand(pid: str, r: dict, text: str, heading: str) -> dict:
    where = f"{pid}"
    ev: dict[str, list] = {}
    span = _q(r["s"], text, heading, where + " span")
    plant = r.get("p", UNK)
    in_head = plant.startswith("H:")
    plant = plant[2:] if in_head else plant
    if plant != UNK:
        ev["plantNameAsWritten"] = [_q(plant, text, heading, where + " plant", heading_ok=in_head)]
    rec = {f: UNK for f in CATEGORICAL_FIELDS}
    rec.update(recipeSpan={k: span[k] for k in ("quote", "start", "end")}, plantNameAsWritten=plant, solvent=[UNK],
               heatText=r.get("ht", UNK), durationText=r.get("dur", UNK), indicationAsWritten=r.get("i", UNK),
               notes=r.get("note", ""), basis=BASIS)
    for f in ("heatText", "durationText", "indicationAsWritten"):
        if rec[f] != UNK:
            ev[f] = [_q(rec[f], text, heading, f"{where} {f}")]
    for f in ("part", "freshOrDried", "heat", "filtered", "process", "form"):
        if f in r:
            val, quote = _vq(r[f])
            rec[f] = val
            ev[f] = [_q(quote, text, heading, f"{where} {f}")]
    if "solvent" in r:
        val, quote = _vq(r["solvent"])
        rec["solvent"] = val.split(",")
        ev["solvent"] = [_q(quote, text, heading, f"{where} solvent")]
    ingredients = []
    if plant != UNK:
        ingredients.append({"plantNameAsWritten": plant, "part": rec["part"], "role": "principal", "kind": "plant",
                            "inHeading": in_head})
    for c in r.get("co", []):
        name, kind = c.split("|")
        _q(name, text, heading, f"{where} co-ingredient")
        ingredients.append({"plantNameAsWritten": name, "part": UNK, "role": "co_ingredient", "kind": kind, "inHeading": False})
    rec["ingredients"] = ingredients
    if r.get("co"):
        rec["recipeType"] = "compound"
        if "ev_type" in r:
            ev["recipeType"] = [_q(r["ev_type"], text, heading, f"{where} recipeType")]
    elif len(ingredients) == 1:
        rec["recipeType"] = "single_plant"
    rec["evidence"] = ev
    return rec


def build() -> dict:
    sample = json.loads(SAMPLE_PATH.read_text())
    spec = _load_spec()
    ids = [p["passageId"] for p in sample["passages"]]
    missing, extra = set(ids) - set(spec), set(spec) - set(ids)
    if missing or extra:
        raise SilverError(f"spec/sample mismatch: missing={sorted(missing)} extra={sorted(extra)}")
    passages = {}
    for p in sample["passages"]:
        recipes = [expand(p["passageId"], r, p["text"], p["heading"] or "") for r in spec[p["passageId"]]]
        passages[p["passageId"]] = {"done": True, "recipes": recipes, "notes": "", "basis": BASIS}
    out = {
        "annotator": "claude-code (AI reference)", "basis": BASIS, "label": LABEL, "mode": "silver",
        "sampleVersion": sample["version"], "guidelinesVersion": "v1",
        "caveat": "Not human validation. The same AI also wrote the guidelines and the extractor's few-shot examples, "
                  "so agreement with this set may be inflated by shared conventions.",
        "createdAt": datetime.now(timezone.utc).isoformat(timespec="seconds"), "passages": passages,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    n = sum(len(v["recipes"]) for v in passages.values())
    return {"passages": len(passages), "recipes": n, "passagesWithoutRecipe": sum(1 for v in passages.values() if not v["recipes"]),
            "compound": sum(1 for v in passages.values() for r in v["recipes"] if r["recipeType"] == "compound"), "path": str(OUT.relative_to(ROOT))}
