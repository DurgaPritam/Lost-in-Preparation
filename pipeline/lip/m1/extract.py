"""M1 LLM extraction (provider-agnostic).

Per passage: one structured-output request with the strict JSON schema. Every recipe is
span-checked; if any check fails the model is shown the errors and asked again (up to
MAX_RETRIES). Recipes still failing after that are REJECTED (dropped and logged), never repaired.

Responses are cached on disk per (provider, model, model digest, decoding, promptVersion,
passage), so re-runs are free and reproducible.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from datetime import datetime, timezone

import pandas as pd
from pydantic import ValidationError

from contract import models as C

from ..paths import INTERIM, load_sources
from .prompt import Prompt, build, heading_of, render_user
from .schema import LLMRecipe, LLMResponse
from .spans import check_recipe

MAX_RETRIES = 2
OUT = INTERIM / "m1"

CULPEPER_1850_CAVEAT = {
    "later_addition_candidate": "1850 Kelly edition; this herbal entry has no matching heading in the 1652 text "
                                "(heuristic crosswalk), so it may be a later editorial addition.",
    "probable_1652": "1850 Kelly edition; probable (not certain) match to a 1652 entry.",
    "in_1652": "1850 Kelly edition; heading matches the 1652 text, but wording may differ.",
    None: "1850 Kelly edition, which includes later editorial additions; this part has no 1652 counterpart.",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def source_titles() -> tuple[tuple[str, str], ...]:
    return tuple((s["id"], s["title"]) for s in load_sources())


class Extractor:
    def __init__(self, provider, cache: bool = True):
        self.provider = provider
        self.cache = cache
        self.prompt: Prompt = build(source_titles())
        self.titles = dict(source_titles())
        self.run = provider.info()

    def _cache_path(self, pid: str):
        k = json.dumps([self.run.provider, self.run.model, self.run.modelVersion, self.run.decoding,
                        self.prompt.version, pid], sort_keys=True, default=str)
        return OUT / "raw" / f"{hashlib.sha256(k.encode()).hexdigest()[:24]}.json"

    def extract(self, row) -> dict:
        """Returns {passageId, recipes: [C.Recipe dict], rejections, attempts, usage, run}."""
        cp = self._cache_path(row.passage_id)
        if self.cache and cp.exists():
            return json.loads(cp.read_text())

        heading = heading_of(row)
        messages: list[dict] = [{"role": "user", "content": render_user(row, self.titles.get(row.source_id, ""))}]
        usage: dict[str, int] = {}
        attempts, accepted, failures, stop = 0, [], [], None

        for attempt in range(MAX_RETRIES + 1):
            attempts = attempt + 1
            comp = self.provider.complete(self.prompt.system, messages, self.prompt.schema)
            for k, v in comp.usage.items():
                usage[k] = usage.get(k, 0) + v
            stop = comp.stop
            if stop in ("refusal", "max_tokens"):
                failures = [{"recipe": None, "errors": [f"stop={stop}"]}]
                break
            try:
                parsed = LLMResponse.model_validate_json(comp.text)
            except ValidationError as e:
                failures = [{"recipe": None, "errors": [f"schema: {e.errors()[:3]}"]}]
                feedback = "Your JSON did not validate against the schema. Return the full corrected JSON."
            else:
                checks = [(r, check_recipe(r, row.text_clean, heading)) for r in parsed.recipes]
                accepted = [(r, c) for r, c in checks if c.ok]
                failures = [{"recipe": r.model_dump(), "errors": c.errors} for r, c in checks if not c.ok]
                if not failures:
                    break
                feedback = (
                    "Some recipes broke the quoting rules:\n"
                    + "\n".join(f"- recipe {i + 1}: " + "; ".join(f["errors"]) for i, f in enumerate(failures))
                    + "\nReturn the full corrected JSON for the whole passage. Copy quotes exactly from the passage."
                )
            messages.append(comp.assistant_message)  # append-only history
            messages.append({"role": "user", "content": feedback})

        result = {
            "passageId": row.passage_id,
            "recipes": [self.to_contract(row, r, c, i) for i, (r, c) in enumerate(accepted)],
            "rejections": failures,
            "attempts": attempts,
            "stop": stop,
            "usage": usage,
            "run": asdict(self.run),
            "promptVersion": self.prompt.version,
        }
        if self.cache:
            cp.parent.mkdir(parents=True, exist_ok=True)
            cp.write_text(json.dumps(result, ensure_ascii=False, indent=1, default=str))
        return result

    def to_contract(self, row, r: LLMRecipe, check, i: int) -> dict:
        text, heading = row.text_clean, heading_of(row)

        def quotes(field: str, fallback: list[str]) -> list[C.Quote]:
            return [C.Quote(quote=text[s:e] if not h else q.strip(), start=s, end=e, inHeading=h)
                    for (s, e, h), q in zip(check.offsets.get(field, []), fallback)]

        evidence = {"recipe": quotes("recipe", [r.recipeQuote])}
        for f in ("plantNameAsWritten", "heatText", "durationText", "indicationAsWritten"):
            if getattr(r, f) != C.UNKNOWN:
                evidence[f] = quotes(f, [getattr(r, f)])
        ev_quotes: dict[str, list[str]] = {}
        for ev in r.evidence:
            ev_quotes.setdefault(ev.field, []).append(ev.quote)
        for f, qs in ev_quotes.items():
            evidence[f] = quotes(f, qs)
        ing_q = quotes("ingredients", [g.plantNameAsWritten for g in r.ingredients])
        ingredients = [C.Ingredient(plantNameAsWritten=g.plantNameAsWritten, part=g.part, role=g.role, kind=g.kind,
                                    evidence=[q] if q else [])
                       for g, q in zip(r.ingredients, ing_q + [None] * len(r.ingredients))]
        caveat = None
        if row.source_id == "culpeper-1850":
            status = getattr(row, "addition_status", None)
            caveat = CULPEPER_1850_CAVEAT.get(None if pd.isna(status) else status, CULPEPER_1850_CAVEAT[None])
        rec = C.Recipe(
            id=f"{row.passage_id}#r{i:02d}",
            sourceId=row.source_id,
            passage=C.PassageRef(
                passageId=row.passage_id, text=text,
                location=C.PassageLocation(
                    part=row.part, book=None if pd.isna(row.book) else int(row.book),
                    chapter=None if pd.isna(row.chapter) else row.chapter, entry=heading or None,
                    subsection=None if pd.isna(row.subsection) else row.subsection,
                    lineStart=int(row.line_start), lineEnd=int(row.line_end))),
            recipeType=r.recipeType, ingredients=ingredients, plantNameAsWritten=r.plantNameAsWritten,
            part=r.part, freshOrDried=r.freshOrDried, solvent=r.solvent, heat=r.heat, heatText=r.heatText,
            durationText=r.durationText, filtered=r.filtered, process=r.process, form=r.form,
            indicationAsWritten=r.indicationAsWritten, indicationNormalized=None,
            fieldConfidence={c.field: c.confidence for c in r.fieldConfidence},
            evidence=evidence, attributionCaveat=caveat,
            excludedFromHeadline=r.recipeType != C.RecipeType.single_plant.value,
            provenance=C.Provenance(method=C.ProvenanceMethod.llm, provider=self.run.provider, model=self.run.model,
                                    modelVersion=self.run.modelVersion, decoding=self.run.decoding,
                                    promptVersion=self.prompt.version, createdAt=_now()),
        )
        return rec.model_dump(by_alias=True)


def run(provider, rows: pd.DataFrame, scope: str, cache: bool = True) -> dict:
    provider.check()
    ex = Extractor(provider, cache=cache)
    OUT.mkdir(parents=True, exist_ok=True)
    results = [ex.extract(row) for row in rows.itertuples()]
    recipes = [r for res in results for r in res["recipes"]]
    rejected = [dict(passageId=res["passageId"], **f) for res in results for f in res["rejections"]]
    (OUT / f"predictions_{scope}.json").write_text(json.dumps(recipes, ensure_ascii=False, indent=1))
    with (OUT / f"rejections_{scope}.jsonl").open("w") as fh:
        for rj in rejected:
            fh.write(json.dumps(rj, ensure_ascii=False) + "\n")
    n_rej = sum(1 for rj in rejected if rj["recipe"] is not None)
    usage: dict[str, int] = {}
    for res in results:
        for k, v in res["usage"].items():
            usage[k] = usage.get(k, 0) + v
    summary = {
        "scope": scope, "run": asdict(ex.run), "promptVersion": ex.prompt.version,
        "passages": len(results), "recipesAccepted": len(recipes), "recipesRejected": n_rej,
        "recipesReturned": len(recipes) + n_rej,
        "passagesFailedWhole": sum(1 for rj in rejected if rj["recipe"] is None),
        "retriesUsed": sum(res["attempts"] - 1 for res in results), "usage": usage, "generatedAt": _now(),
    }
    (OUT / f"run_{scope}.json").write_text(json.dumps(summary, indent=2, default=str))
    return summary
