"""Preparation Lab engine inputs (contract v1.7, P38): site-data/engine/ validates, matches the model config and the
published profiles, and the custom seed rule is the one the TypeScript engine uses (site/lib/engine/prep.ts)."""
import json

from contract import models as C
from lip.m4 import engine_export as E
from lip.m4 import model as M
from lip.paths import SITE_DATA

ENG = SITE_DATA / "engine"


def test_engine_files_validate_and_match_the_model_config():
    model = C.EngineModel.model_validate(json.loads((ENG / "model.json").read_text()))
    cfg = M.load_config()
    assert model.modelVersion == M.config_version(cfg)
    assert [p.label for p in model.preparations] == [p.label for p in M.GRID]
    assert [p.seedOffset for p in model.preparations] == list(range(len(M.GRID)))
    assert model.params.draws == cfg["mc"]["draws"] and model.params.seed == cfg["mc"]["seed"]
    assert model.noiseSeedOffset == 10_000_019


def test_species_inputs_follow_the_published_profiles():
    idx = json.loads((SITE_DATA / "profiles" / "index.json").read_text())
    for e in idx:
        sp = C.EngineSpecies.model_validate(json.loads((ENG / f"{e['speciesId']}.json").read_text()))
        prof = json.loads((SITE_DATA / e["file"]).read_text())
        assert [c.compoundId for c in sp.compounds] == [c["compoundId"] for c in prof[0]["compounds"]]


def test_parity_cases_are_off_grid_and_use_the_custom_seed_rule():
    grid = {(tuple(sorted(p.solvent)), p.heat, p.filtered, p.process) for p in M.GRID}
    for c in json.loads((ENG / "parity.json").read_text()):
        p = C.EngineParityCase.model_validate(c).preparation
        assert (tuple(sorted(p.solvents)), p.heat, p.filtered, p.process) not in grid
        assert p.seedOffset == E.custom_seed_offset(p.solvents, p.heat, p.filtered, p.process)


def test_fnv1a_known_values():
    # the same values are asserted in site/tests/unit/engine.test.ts
    assert E.fnv1a32("a") == 3826002220
    assert E.fnv1a32("water|cold|yes|infusion") == 611673888
