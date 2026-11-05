"""site-data/metrics.json is assembled section by section: each module updates only its own part."""
from __future__ import annotations

import json
from datetime import datetime, timezone

from contract import models as C

from . import PIPELINE_VERSION
from .paths import SITE_DATA

PATH = SITE_DATA / "metrics.json"


def _later(phase: str) -> C.Metric:
    return C.not_computed(f"computed in {phase}")


def skeleton() -> C.Metrics:
    nc = C.not_computed("not computed yet")
    prf = C.PRF(precision=nc, recall=nc, f1=nc)
    return C.Metrics(
        generatedAt=datetime.now(timezone.utc).isoformat(timespec="seconds"), pipelineVersion=PIPELINE_VERSION,
        extraction=C.ExtractionMetrics(overall={}, bySource={}, recipeDetection={"overall": prf}, spanRejectionRate=nc),
        interAnnotatorAgreement={},
        nameResolution={"top1": _later("M2 evaluation"), "top3": _later("M2 evaluation"), "disputedShare": _later("M2")},
        logPError={"rdkit": _later("M4"), "xtb": _later("M4")},
        headlineMatchRate=_later("M5/M6"),
        artemisininCheck=C.CheckResult(status="not_computed", explanation="computed in M4"),
    )


def load() -> C.Metrics:
    if PATH.exists():
        return C.Metrics.model_validate_json(PATH.read_text())
    return skeleton()


def update(**sections) -> C.Metrics:
    m = load()
    data = m.model_dump(by_alias=True)
    for k, v in sections.items():
        data[k] = v.model_dump(by_alias=True) if hasattr(v, "model_dump") else \
            {kk: (vv.model_dump(by_alias=True) if hasattr(vv, "model_dump") else vv) for kk, vv in v.items()}
    data["generatedAt"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    data["pipelineVersion"] = PIPELINE_VERSION
    m = C.Metrics.model_validate(data)
    PATH.parent.mkdir(parents=True, exist_ok=True)
    PATH.write_text(m.model_dump_json(indent=2, by_alias=True) + "\n")
    return m


def write_json(path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, default=str) + "\n")
