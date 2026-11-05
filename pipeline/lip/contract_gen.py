"""Generate contract/schemas/*.schema.json from contract/models.py (never edit schemas by hand)."""
from __future__ import annotations

import json

from contract.models import ARRAY_FILES, CONTRACT_VERSION, FILE_MODELS

from .m1.prompt import PROMPT_DIR
from .m1.schema import response_schema
from .paths import ROOT

SCHEMA_DIR = ROOT / "contract" / "schemas"


def schemas() -> dict[str, dict]:
    out = {}
    for fname, model in FILE_MODELS.items():
        s = model.model_json_schema(by_alias=True, mode="serialization")
        if fname in ARRAY_FILES:
            defs = s.pop("$defs", {})
            s = {"type": "array", "items": s, "$defs": defs} if defs else {"type": "array", "items": s}
        s = {"$schema": "https://json-schema.org/draft/2020-12/schema",
             "$id": f"lost-in-preparation/contract/{CONTRACT_VERSION}/{fname}",
             "title": fname, **s}
        out[fname.replace(".json", ".schema.json")] = s
    return out


def write() -> list[str]:
    SCHEMA_DIR.mkdir(parents=True, exist_ok=True)
    written = []
    for name, s in schemas().items():
        (SCHEMA_DIR / name).write_text(json.dumps(s, indent=2, ensure_ascii=False) + "\n")
        written.append(str((SCHEMA_DIR / name).relative_to(ROOT)))
    (PROMPT_DIR / "response.schema.json").write_text(json.dumps(response_schema(), indent=2) + "\n")
    written.append(str((PROMPT_DIR / "response.schema.json").relative_to(ROOT)))
    return written
