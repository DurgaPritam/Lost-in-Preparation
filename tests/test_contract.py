"""Contract freeze guard: committed JSON Schemas must equal what contract/models.py generates."""
from __future__ import annotations

import json

from contract import models as C
from lip.contract_gen import SCHEMA_DIR, schemas


def test_schemas_match_models():
    for name, schema in schemas().items():
        on_disk = json.loads((SCHEMA_DIR / name).read_text())
        assert on_disk == schema, f"{name} differs from contract/models.py — regenerate with `python -m lip contract`"


def test_contract_version_frozen():
    assert C.CONTRACT_VERSION == "1.8"


def test_recipe_defaults_are_unknown():
    r = C.Recipe(id="x", sourceId="s",
                 passage=C.PassageRef(passageId="p", text="t", location=C.PassageLocation(part="herbal", lineStart=1, lineEnd=1)),
                 provenance=C.Provenance(method="human", createdAt="2026-01-01"))
    d = r.model_dump()
    for f in ("plantNameAsWritten", "part", "freshOrDried", "heat", "heatText", "durationText", "filtered",
              "process", "form", "indicationAsWritten", "recipeType"):
        assert d[f] == "unknown", f
    assert d["solvent"] == ["unknown"] and d["mock"] is False


def test_sources_json_validates():
    data = json.loads(open("site-data/sources.json").read())
    recs = [C.Source.model_validate(r) for r in data]
    assert {r.workId for r in recs} == {"culpeper-english-physitian", "culpeper-complete-herbal", "pliny-natural-history"}
    assert all(r.files and len(r.files[0].sha256) == 64 for r in recs)
