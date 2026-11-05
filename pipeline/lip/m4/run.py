"""Phase 4 runner: descriptor choice, known-case test (artemisinin), profiles, metrics."""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pandas as pd

from contract import models as C

from .. import metrics_store
from ..paths import INTERIM, ROOT, SITE_DATA
from . import chem, literature, xtb
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
    res = {lab: M.simulate(c, M.BY_LABEL[lab], cfg) for lab in
           ("cold water infusion", "decoction in water", "low-temperature nonpolar extract (hexane)", "modern methanol extract")}
    thr = cfg["artemisinin_check"]
    checks = {
        "heat flag fires": "heat:endoperoxide" in d["heatFlags"],
        f"cold water median < {thr['cold_water_max']}": res["cold water infusion"]["likelihood"] < thr["cold_water_max"],
        f"low-temperature nonpolar median > {thr['nonpolar_cold_min']}":
            res["low-temperature nonpolar extract (hexane)"]["likelihood"] > thr["nonpolar_cold_min"],
    }
    x = xtb.compute(a["inchikey"], a["smiles"])
    expl = (f"Descriptor {used} (logP {h:.2f}). Endoperoxide heat flag: {checks['heat flag fires']}. "
            f"Cold water {res['cold water infusion']['likelihood']:.2f} [{res['cold water infusion']['low']:.2f}–{res['cold water infusion']['high']:.2f}]; "
            f"decoction {res['decoction in water']['likelihood']:.2f} (heat factor {res['decoction in water']['drivers']['heat']:.2f}); "
            f"low-temperature hexane {res['low-temperature nonpolar extract (hexane)']['likelihood']:.2f} "
            f"[{res['low-temperature nonpolar extract (hexane)']['low']:.2f}–{res['low-temperature nonpolar extract (hexane)']['high']:.2f}]. "
            f"Pre-registered thresholds: cold water < {thr['cold_water_max']}, nonpolar > {thr['nonpolar_cold_min']}. "
            f"Exploratory xTB Wiberg bond order of the O–O bond: {max(x.get('wiberg_OO') or [float('nan')]):.3f}.")
    out = {"result": "pass" if all(checks.values()) else "fail", "checks": checks, "predictions": res, "descriptor": used,
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
    SITE_DATA.mkdir(parents=True, exist_ok=True)
    (SITE_DATA / "profiles.json").write_text(json.dumps([p.model_dump(by_alias=True) for p in records], ensure_ascii=False,
                                                        separators=(",", ":")) + "\n")
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
    lit = literature.evaluate(cfg)
    from ..m2.evaluate import wilson
    lo, hi = wilson(lit["agree"], lit["n"])
    metrics_store.update_provisional("prepModelVsLiterature", C.ProvisionalSection(
        basis=literature.BASIS, label=literature.LABEL,
        metrics={"agreement": C.Metric(status="computed", value=round(lit["agree"] / lit["n"], 4), low=round(lo, 4),
                                       high=round(hi, 4), n=lit["n"], sourceFile="data/interim/m4/literature_check.json",
                                       note=f"{literature.LABEL}; {lit['agree']}/{lit['n']} rows agree under pre-registered "
                                            f"thresholds; Wilson 95% CI; table chosen by the same AI that built the model")}))
    summary = {"descriptor": descriptor, "literatureAgreement": f"{lit['agree']}/{lit['n']}", "modelVersion": M.config_version(cfg), "xtbVersion": xtb.version(),
               "artemisinin": case["result"], "profiles": prof, "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    (OUT / "m4_summary.json").write_text(json.dumps(summary, indent=2))
    return summary
