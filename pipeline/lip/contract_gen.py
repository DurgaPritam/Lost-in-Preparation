"""Generate contract/schemas/*.schema.json from contract/models.py (never edit schemas by hand).

Writes ONLY under contract/schemas/. It never writes into prompts/: prompt versions are frozen once used. The M1
response schema is built in code (m1/schema.py) and hashed into every promptVersion (m1/prompt.py); its documented copy
is the frozen prompts/m1_extract/v1/response.schema.json (see prompts/m1_extract/CHANGELOG.md).
"""
from __future__ import annotations

import json

from contract.models import ARRAY_FILES, CONTRACT_VERSION, FILE_MODELS

from .paths import ROOT

SCHEMA_DIR = ROOT / "contract" / "schemas"
FROZEN = ROOT / "prompts"


def _target(path):
    """Every file this module writes goes through here: inside contract/schemas/, never inside prompts/."""
    path = path.resolve()
    if path.is_relative_to(FROZEN.resolve()) or not path.is_relative_to(SCHEMA_DIR.resolve()):
        raise PermissionError(f"contract generator may write only under {SCHEMA_DIR.relative_to(ROOT)}/, not {path}")
    return path


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
        _target(SCHEMA_DIR / name).write_text(json.dumps(s, indent=2, ensure_ascii=False) + "\n")
        written.append(str((SCHEMA_DIR / name).relative_to(ROOT)))
    return written
