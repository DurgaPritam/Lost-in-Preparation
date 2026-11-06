"""Resolver v3 footnote rule: hedged or contradicted footnote binomials are not used as identifications."""
from __future__ import annotations

import json

import pandas as pd
import pytest

from lip.m2.resolve import footnote_binomials, footnote_trigger

P = pd.read_parquet("data/interim/passages.parquet").set_index("passage_id")


def fn(pid: str) -> str:
    return P.loc[pid, "text_clean"]


@pytest.mark.parametrize("footnote,binomial,expect", [
    # Pliny "CENTAURION OR CHIRONION": Fée considers it the greater centaury; Littré names Centaurea centaurium
    ("pliny-nh-bohn-v5:fn638", "Centaurea centaureum", "competing authorities: Fée, Littré"),
    # "TIPHYON": a single Sprengel conjecture
    ("pliny-nh-bohn-v4:fn2089", "Lavandula spica", "takes this to be"),
    # "CENTAURIS TRIORCHIS": "Fée is probably right in his conjecture"
    ("pliny-nh-bohn-v5:fn646", "Centaurea centaureum", "is probably right"),
    # "SYMPHYTON PETRÆON": Fée says the rock symphytum is a totally different plant from comfrey
    ("pliny-nh-bohn-v5:fn1787", "Symphytum officinale", "totally different"),
    # "NEP": "Fée thinks"
    ("pliny-nh-bohn-v4:fn1577", "Melissa altissima", "competing authorities"),
])
def test_cases_from_review_are_triggered(footnote, binomial, expect):
    text = fn(footnote)
    t = footnote_trigger(text, binomial, len(footnote_binomials(text)))
    assert t is not None and expect.lower() in t.lower()


def test_competing_authorities_trigger():
    text = fn("pliny-nh-bohn-v5:fn1786")  # Desfontaines vs Fée vs Lobel vs Cæsalpinus on "symphyton petræon"
    t = footnote_trigger(text, "Symphytum officinale", len(footnote_binomials(text)))
    assert t and ("competing authorities" in t or "considers" in t)


@pytest.mark.parametrize("text,binomial", [
    ("Identified by Desfontaines with the Symphytum officinale, or Great comfrey.", "Symphytum officinale"),
    ("The Crocus sativus of Linnæus.", "Crocus sativus"),
])
def test_plain_identifications_are_not_triggered(text, binomial):
    assert footnote_trigger(text, binomial, 1) is None


def test_resolver_output_marks_and_logs_triggers():
    c = pd.read_parquet("data/interim/m2/name_candidates.parquet")
    top = c[c["rank"] == 1].set_index("nameId")
    for nid in ("pliny-nh:b25:c030:n0", "pliny-nh:b21:c039:n1", "pliny-nh:b25:c032:n0", "pliny-nh:b27:c024:n0", "pliny-nh:b20:c056:n0"):
        trig = json.loads(top.loc[nid, "footnoteTriggers"])
        assert top.loc[nid, "disputed"] and trig and all(t["trigger"] for t in trig), nid
    trig_any = top.footnoteTriggers.map(lambda x: bool(json.loads(x)))
    assert top[trig_any].disputed.all()  # every triggered name is disputed
    for r in top[trig_any].itertuples():  # triggered binomials only ever carry the reduced weight
        for e in json.loads(r.evidence):
            if "not used as identification" in e["how"]:
                assert e["weight"] <= 0.4 + 1e-9


def test_hedge_word_in_own_sentence():
    text = fn("pliny-nh-bohn-v4:fn1577")
    assert footnote_trigger(text, "Menta silvestris", len(footnote_binomials(text))) == "thinks"
    text = fn("pliny-nh-bohn-v5:fn638")
    assert footnote_trigger(text, "Panaces centaurion", len(footnote_binomials(text))) == "considers"
