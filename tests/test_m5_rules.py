"""M5 rule-based method extractor: lexicon v1 on constructed sentences (no network, no LLM)."""
from __future__ import annotations

import pytest

from lip.m5 import rules as R


def one(text, **want):
    ps = R.extract(text)
    assert len(ps) == 1, [p.solvent for p in ps]
    p = ps[0]
    for k, v in want.items():
        assert getattr(p, k) == v, (k, getattr(p, k), v)
    for e in p.evidence:                                    # every value is backed by the verbatim matched text
        assert text[e["start"]:e["end"]] == e["quote"] and getattr(p, e["field"]) != "unknown"
    return p


def by_solvent(text):
    return {p.solvent: p for p in R.extract(text)}


def test_version_records_lexicon_hash():
    v = R.lexicon().version
    assert v.startswith("m5_rules/v1:") and len(v.split(":")[1]) == 10


def test_hydroethanolic_with_fraction_and_cold_and_dried_leaf():
    p = one("Shade-dried leaves were extracted with 70% ethanol at room temperature for 72 h, then filtered.",
            solvent="hydroethanolic", heat="cold", part="leaf", freshOrDried="dried", filtered="yes")
    assert p.ethanolFraction == 0.7 and p.solventText == "70% ethanol" and p.unknownFields == []


def test_95_percent_ethanol_is_coded_ethanol():
    one("The roots were macerated in 96% ethanol.", solvent="ethanol", part="root")


def test_decoction_is_water_and_boiled():
    one("A decoction of the aerial parts was prepared.", solvent="water", heat="boiled", part="aerial_parts")


def test_infusion_in_boiling_water_is_warm_not_boiled():
    one("An infusion was prepared by steeping the flowers; infusion in boiling water lasted 10 min.", solvent="water", heat="warm",
        part="flower")


def test_unstated_is_unknown_never_guessed():
    p = one("The methanolic extract of the plant showed antioxidant activity.", solvent="methanol")
    assert set(p.unknownFields) == {"heat", "part", "freshOrDried", "filtered"}


def test_no_preparation_described():
    p = one("Hyoscyamine was quantified in plasma samples of 20 patients.")
    assert p.unknownFields == R.FIELDS and p.flags == ["no preparation described"]


@pytest.mark.parametrize("text", [
    "Ethanol-induced gastric ulcers were reduced by the extract.",           # disease model, not a solvent
    "The extract was partitioned with ethyl acetate fraction collected.",   # a fraction
    "Green tea extract was used as a positive control.",                     # a beverage of another plant
])
def test_exclusion_contexts(text):
    s = by_solvent(text)
    assert "ethanol" not in s and "ethyl_acetate" not in s and "water" not in s


def test_solvent_needs_an_extraction_cue_sentence():
    ps = R.extract("Samples were dissolved in methanol for HPLC. No plant extract was tested.")
    assert [p.solvent for p in ps] == ["unknown"]


def test_several_solvents_give_several_preparations_and_conflicting_heat_is_unknown():
    s = by_solvent("Hexane and methanol extracts of the seeds were obtained by Soxhlet extraction. "
                   "An aqueous extract was prepared at room temperature and by reflux.")
    assert set(s) == {"hexane", "methanol", "water"}
    assert s["hexane"].heat == "boiled" and s["methanol"].heat == "boiled" and s["hexane"].part == "seed"
    assert s["water"].heat == "unknown" and "conflicting heat cues" in s["water"].flags


def test_temperature_bands_ignore_evaporation_and_drying():
    one("The leaves were extracted with water at 80 °C.", solvent="water", heat="warm")
    p = one("The leaves were extracted with water and concentrated under reduced pressure at 40 °C.", solvent="water")
    assert p.heat == "unknown"
    one("The fruits were extracted with water at 100 °C for 1 h.", solvent="water", heat="boiled", part="fruit")


def test_several_parts_is_unknown_and_fresh_vs_dried_conflict():
    p = one("Leaves and roots were extracted with acetone. Fresh leaves and dried roots were used.", solvent="acetone")
    assert p.part == "unknown" and "several plant parts named" in p.flags
    assert p.freshOrDried == "unknown" and "both fresh and dried material named" in p.flags


def test_dried_extract_is_not_dried_material():
    p = one("Fresh flowers were extracted with chloroform; the extract was freeze-dried.", solvent="chloroform", freshOrDried="fresh")
    assert p.part == "flower"


def test_essential_oil_is_other_and_hydrodistillation_boiled():
    one("The essential oil was obtained from the aerial parts by hydrodistillation in a Clevenger apparatus.", solvent="other",
        heat="boiled", part="aerial_parts")


def test_supercritical_co2():
    one("Seeds were subjected to supercritical CO2 extraction.", solvent="co2", part="seed")


def test_lexicon_is_documented_and_marked_heuristic():
    raw = R.LEX_PATH.read_text()
    assert "HEURISTIC" in raw and "NOTHING IS INFERRED" in raw and 'version = "v1"' in raw


def test_partitioning_solvents_are_not_preparations():
    s = by_solvent("Two fractions were obtained by partitioning the methanol (MeOH) extract of licorice roots with ethyl acetate (EtOAc).")
    assert set(s) == {"methanol"} and s["methanol"].part == "root"
