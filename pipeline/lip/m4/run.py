"""Phase 4 runner: descriptor choice, known-case test (artemisinin), profiles, metrics."""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pandas as pd

from contract import models as C

from .. import metrics_store
from ..paths import INTERIM, ROOT, SITE_DATA
from . import chem, literature, prereg_literature, xtb
from . import model as M

OUT = INTERIM / "m4"
ARTEMISININ = {"name": "artemisinin", "inchikey": "BLUAFEHZUWYNDE-NNWCWBAJSA-N",
               "smiles": "C[C@@H]1CC[C@H]2[C@H](C(=O)O[C@H]3[C@@]24[C@H]1CC[C@](O3)(OO4)C)C"}


def choose_descriptor(cfg: dict) -> tuple[str, dict]:
    val = json.loads((OUT / "logp_validation.json").read_text())
    want = cfg["descriptor"]["default"]
    return (val["default"] if want == "auto" else want), val


def lipophilicity(smiles: str, inchikey: str, descriptor: str) -> tuple[float, str]:
    d = chem.describe(smiles)
    if descriptor == "xtb":
        r = xtb.compute(inchikey, smiles)
        if r.get("status") == "ok":
            return r["logP_xtb"], "xtb"
    return d["logP"], "rdkit"


def known_case(cfg: dict, descriptor: str) -> dict:
    a = ARTEMISININ
    d = chem.describe(a["smiles"])
    h, used = lipophilicity(a["smiles"], a["inchikey"], descriptor)
    c = M.Compound(a["inchikey"], h, d["basicN"], d["heatFlags"], d["volatile"], d["mw"])
    preps = [M.BY_LABEL[l] for l in ("cold water infusion", "decoction in water", "low-temperature nonpolar extract (hexane)",
                                     "modern methanol extract")]
    # sensitivity: cold water without straining (soaked and wrung out), to show the suspension assumption's effect
    preps.insert(1, M.Prep("unknown|unknown|water|cold|no", "cold water, unfiltered (soaked and wrung out)", ("water",), "cold", "no", "infusion"))
    res = {p.label: M.simulate(c, p, cfg) for p in preps}
    thr = cfg["artemisinin_check"]
    checks = {
        "heat flag fires": "heat:endoperoxide" in d["heatFlags"],
        f"cold water median < {thr['cold_water_max']}": res["cold water infusion"]["likelihood"] < thr["cold_water_max"],
        f"low-temperature nonpolar median > {thr['nonpolar_cold_min']}":
            res["low-temperature nonpolar extract (hexane)"]["likelihood"] > thr["nonpolar_cold_min"],
    }
    cw, nc = res["cold water infusion"], res["low-temperature nonpolar extract (hexane)"]
    borderline = (cw["high"] >= thr["cold_water_max"]) or (nc["low"] <= thr["nonpolar_cold_min"])
    x = xtb.compute(a["inchikey"], a["smiles"])
    expl = (f"Descriptor {used} (logP {h:.2f}). Endoperoxide heat flag: {checks['heat flag fires']}. "
            f"Cold water {res['cold water infusion']['likelihood']:.2f} [{res['cold water infusion']['low']:.2f}–{res['cold water infusion']['high']:.2f}]; "
            f"decoction {res['decoction in water']['likelihood']:.2f} (heat factor {res['decoction in water']['drivers']['heat']:.2f}); "
            f"low-temperature hexane {res['low-temperature nonpolar extract (hexane)']['likelihood']:.2f} "
            f"[{res['low-temperature nonpolar extract (hexane)']['low']:.2f}–{res['low-temperature nonpolar extract (hexane)']['high']:.2f}]. "
            f"Pre-registered thresholds: cold water < {thr['cold_water_max']}, nonpolar > {thr['nonpolar_cold_min']}. "
            f"Exploratory xTB Wiberg bond order of the O–O bond: {max(x.get('wiberg_OO') or [float('nan')]):.3f}.")
    result = ("borderline pass" if borderline else "pass") if all(checks.values()) else "fail"
    drivers = {lab: r["drivers"] for lab, r in res.items()}
    expl += (" BORDERLINE: the 5th–95th percentile range crosses a threshold (cold water "
             f"{cw['low']:.2f}–{cw['high']:.2f} vs < {thr['cold_water_max']}; nonpolar {nc['low']:.2f}–{nc['high']:.2f} vs > {thr['nonpolar_cold_min']})."
             if borderline else "")
    expl += (" Cold water is filtered (filtration factor 1.00): its value comes from the solvent factor alone. "
             f"Without straining, the suspension assumption raises it to {res['cold water, unfiltered (soaked and wrung out)']['likelihood']:.2f} "
             f"(filtration factor {res['cold water, unfiltered (soaked and wrung out)']['drivers']['filtration']:.2f}).")
    out = {"result": result, "drivers": drivers, "checks": checks, "predictions": res, "descriptor": used,
           "lipophilicity": h, "flags": d, "xtb": {k: x.get(k) for k in ("logP_xtb", "logK", "wiberg_OO", "status")},
           "explanation": expl}
    (OUT / "artemisinin_check.json").write_text(json.dumps(out, indent=2, default=str))
    return out


def profiles(cfg: dict, descriptor: str) -> dict:
    prop = pd.read_csv(INTERIM / "m3" / "study_set_proposal.csv")
    prop = prop[prop.proposed]
    occ = pd.read_parquet(INTERIM / "m3" / "occurrences.parquet")
    comp = pd.read_parquet(INTERIM / "m3" / "compounds.parquet").drop_duplicates("inchikey").set_index("inchikey")
    cov = pd.read_csv(INTERIM / "m3" / "coverage.csv").set_index("acceptedName")
    records, rows = [], []
    for sp in prop.itertuples():
        o = occ[occ.acceptedName == sp.acceptedName]
        cpds = []
        for r in o.itertuples():
            if r.inchikey not in comp.index:
                continue
            cr = comp.loc[r.inchikey]
            d = chem.describe(cr.smiles)
            if d is None:
                continue
            h, used = lipophilicity(cr.smiles, r.inchikey, descriptor)
            cpds.append((r, cr, d, M.Compound(r.inchikey, h, d["basicN"], d["heatFlags"], d["volatile"], d["mw"]), used))
        for j, prep in enumerate(M.GRID):
            entries = []
            for r, cr, d, c, used in cpds:
                s = M.simulate(c, prep, cfg, seed_offset=j)
                entries.append(C.CompoundLikelihood(
                    compoundId=r.inchikey, name=cr.label if isinstance(cr.label, str) else r.inchikey, compoundClass=f"{d['class']} (heuristic)",
                    smiles=cr.smiles, sourceDb="LOTUS via Wikidata", sourceRecordId=(list(r.wikidataIds) or [""])[0],
                    likelihood=s["likelihood"], low=s["low"], high=s["high"], drivers=C.Drivers(**s["drivers"]),
                    heuristicFlags=s["heuristicFlags"]))
                rows.append({"speciesId": sp.wfoId, "acceptedName": sp.acceptedName, "preparation": prep.label,
                             "preparationKey": prep.key, "inchikey": r.inchikey, "name": cr.label if isinstance(cr.label, str) else None, "class": d["class"],
                             "lipophilicity": c.h, "descriptor": used, **{k: s[k] for k in ("likelihood", "low", "high")},
                             **{f"driver_{k}": v for k, v in s["drivers"].items()}, "flags": ";".join(s["heuristicFlags"])})
            note = cov.loc[sp.acceptedName].coverageNote if sp.acceptedName in cov.index else "no coverage record"
            records.append(C.Profile(speciesId=sp.wfoId, preparationKey=prep.key.split("#")[0], process=prep.process,
                                     preparationLabel=prep.label, compounds=entries,
                                     coverageNote=f"{note}; model estimates, not measurements"))
    # v1.3 layout: one file per species + index (the site loads them on demand); full file in the data release
    import gzip
    pdir = SITE_DATA / "profiles"
    pdir.mkdir(parents=True, exist_ok=True)
    for old in pdir.glob("*.json"):
        old.unlink()
    (SITE_DATA / "profiles.json").unlink(missing_ok=True)
    tox = dict(zip(prop.acceptedName, zip(prop.get("toxicity", ["unknown"] * len(prop)), prop.get("toxicityNote", [None] * len(prop)))))
    index = []
    for sp in prop.itertuples():
        recs = [p for p in records if p.speciesId == sp.wfoId]
        f = pdir / f"{sp.wfoId}.json"
        f.write_text(json.dumps([p.model_dump(by_alias=True) for p in recs], ensure_ascii=False, separators=(",", ":")) + "\n")
        flag, note = tox.get(sp.acceptedName, ("unknown", None))
        index.append(C.ProfileIndexEntry(speciesId=sp.wfoId, acceptedName=sp.acceptedName, file=f"profiles/{f.name}",
                                         preparations=len(recs), compounds=len(recs[0].compounds) if recs else 0,
                                         toxicityFlag=flag if isinstance(flag, str) else "unknown",
                                         toxicityNote=note if isinstance(note, str) else None).model_dump())
    (pdir / "index.json").write_text(json.dumps(index, indent=1, ensure_ascii=False) + "\n")
    rel = ROOT / "data" / "release"
    rel.mkdir(parents=True, exist_ok=True)
    with gzip.open(rel / "profiles_full.json.gz", "wt", encoding="utf-8") as fh:
        json.dump([p.model_dump(by_alias=True) for p in records], fh, ensure_ascii=False, separators=(",", ":"))
    pd.DataFrame(rows).to_parquet(OUT / "profiles_long.parquet", index=False)
    return {"species": int(prop.acceptedName.nunique()), "preparations": len(M.GRID), "profiles": len(records),
            "compoundEntries": len(rows)}


def main() -> dict:
    cfg = M.load_config()
    descriptor, val = choose_descriptor(cfg)
    case = known_case(cfg, descriptor)
    prof = profiles(cfg, descriptor)
    lp = {}
    for key, block in (("rdkit", "rdkit_paired"), ("xtb", "xtb_paired")):
        b = val[block]
        lp[key] = C.Metric(status="computed", value=b["mae"]["value"], low=b["mae"]["ci"][0], high=b["mae"]["ci"][1], n=b["n"],
                           sourceFile="data/interim/m4/logp_validation.json",
                           note=f"MAE vs experimental logP (SangsterLogP neutral subset); RMSE {b['rmse']['value']}, "
                                f"Spearman {b['spearman']['value']} [{b['spearman']['ci'][0]}, {b['spearman']['ci'][1]}]")
        lp[f"{key}Spearman"] = C.Metric(status="computed", value=b["spearman"]["value"], low=b["spearman"]["ci"][0],
                                        high=b["spearman"]["ci"][1], n=b["n"], sourceFile="data/interim/m4/logp_validation.json",
                                        note="Spearman rho vs experimental logP")
    lp["defaultDescriptor"] = C.Metric(status="computed", note=f"default = {descriptor} (lower MAE on paired set)")
    metrics_store.update(
        logPError=lp,
        artemisininCheck=C.CheckResult(status="computed", result=case["result"], explanation=case["explanation"],
                                       sourceFile="data/interim/m4/artemisinin_check.json"))
    metrics_store.drop_provisional("prepModelVsLiterature")  # superseded by _exploratory / _preregistered
    lit = literature.evaluate(cfg)
    from ..m2.evaluate import wilson
    lo, hi = wilson(lit["agree"], lit["n"])
    metrics_store.update_provisional("prepModelVsLiterature_exploratory", C.ProvisionalSection(
        basis=literature.BASIS, label=literature.LABEL,
        metrics={"agreement": C.Metric(status="computed", value=round(lit["agree"] / lit["n"], 4), low=round(lo, 4),
                                       high=round(hi, 4), n=lit["n"], sourceFile="data/interim/m4/literature_check.json",
                                       note=f"{literature.LABEL}; {lit['agree']}/{lit['n']} rows agree under pre-registered "
                                            f"thresholds; Wilson 95% CI; table chosen by the same AI that built the model")}))
    pre = prereg_literature.evaluate(cfg)
    if pre["rowsFound"]:
        plo, phi = wilson(pre["agree"], pre["rowsFound"])
        pm = C.Metric(status="computed", value=round(pre["agree"] / pre["rowsFound"], 4), low=round(plo, 4), high=round(phi, 4),
                      n=pre["rowsFound"], sourceFile="data/interim/m4/literature_prereg.json",
                      note=(f"PRE-REGISTERED (docs/PREREGISTRATION.md, commit 35b7c0d); {pre['agree']}/{pre['rowsFound']} rows agree; "
                            f"target was 30, rule not relaxed; by preparation: {pre['byPreparation']}; Wilson 95% CI"))
    else:
        pm = C.not_computed("no rows met the pre-registered rule")
    metrics_store.update_provisional("prepModelVsLiterature_preregistered", C.ProvisionalSection(
        basis=literature.BASIS, label="PRE-REGISTERED literature check, provisional; AI-written rule and code, not human-curated",
        metrics={"agreement": pm}))
    summary = {"descriptor": descriptor, "literatureAgreementExploratory": f"{lit['agree']}/{lit['n']}",
               "literatureAgreementPreregistered": f"{pre['agree']}/{pre['rowsFound']}", "modelVersion": M.config_version(cfg), "xtbVersion": xtb.version(),
               "artemisinin": case["result"], "profiles": prof, "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    (OUT / "m4_summary.json").write_text(json.dumps(summary, indent=2))
    return summary
