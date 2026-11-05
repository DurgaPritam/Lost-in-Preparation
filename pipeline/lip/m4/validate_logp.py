"""Validate the solvent descriptor: RDKit Crippen logP vs GFN2-xTB/ALPB logP against experiment.

Reference: SangsterLogP dataset (Zenodo record 19387552, CC BY 4.0), sheet 'SangsterLogP'.
Selection (fixed seed): ionisation-based class 'N' (neutral), measured logP present, SMILES parses,
single fragment, no formal charge, elements C H N O S F Cl Br only, 6–30 heavy atoms; 150 compounds
drawn stratified by experimental-logP quintile (30 per quintile).
Metrics: MAE, RMSE, Spearman rho, each with a 95% bootstrap CI (B = 2000, paired resampling).
Caveat: Crippen's atom contributions were fitted to public experimental logP data that likely overlaps
this set, which favours RDKit; xTB has no logP fitting.
The method with the lower MAE becomes the model default (config/prep_model.toml records the choice).
"""
from __future__ import annotations

import json
import random
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import Crippen
from scipy.stats import spearmanr

from ..paths import INTERIM, ROOT
from . import xtb

SRC = ROOT / "data" / "raw" / "logp" / "SangsterLogP_Datasets.xlsx"
OUT = INTERIM / "m4"
SEED, N_PER_BIN, BINS = 20261105, 30, 5
ALLOWED = set("C H N O S F Cl Br".split())


SRC_URL = "https://zenodo.org/api/records/19387552/files/Datasets.xlsx/content"
SRC_SHA256 = "a5f998a690ff48d820afe11b23d2522e95ff11764f6d13c773749750f3ea8d42"


def ensure_source() -> None:
    """Download the SangsterLogP workbook (CC BY 4.0) if missing and verify its checksum."""
    import hashlib
    import urllib.request
    if not SRC.exists():
        SRC.parent.mkdir(parents=True, exist_ok=True)
        SRC.write_bytes(urllib.request.urlopen(SRC_URL, timeout=300).read())
    sha = hashlib.sha256(SRC.read_bytes()).hexdigest()
    if sha != SRC_SHA256:
        raise RuntimeError(f"SangsterLogP checksum mismatch: {sha}")


def select() -> pd.DataFrame:
    ensure_source()
    d = pd.read_excel(SRC, sheet_name="SangsterLogP (N=23,520)")
    d = d[(d["Ionisation-based class"] == "N") & d.logP.notna()].copy()
    keep = []
    for r in d.itertuples():
        m = Chem.MolFromSmiles(str(r.SMILES))
        if m is None or len(Chem.GetMolFrags(m)) != 1 or Chem.GetFormalCharge(m) != 0:
            continue
        if not {a.GetSymbol() for a in m.GetAtoms()} <= ALLOWED or not 6 <= m.GetNumHeavyAtoms() <= 30:
            continue
        keep.append({"id": r.ID, "smiles": Chem.MolToSmiles(m), "inchikey": Chem.MolToInchiKey(m),
                     "logP_exp": float(r.logP), "source": r.Source})
    k = pd.DataFrame(keep).drop_duplicates("inchikey")
    k["bin"] = pd.qcut(k.logP_exp, BINS, labels=False)
    return pd.concat([g.sample(n=min(N_PER_BIN, len(g)), random_state=SEED) for _, g in k.groupby("bin")]).reset_index(drop=True)


def _boot(y, a, fn, b=2000):
    rng = random.Random(SEED)
    n, vals = len(y), []
    for _ in range(b):
        idx = [rng.randrange(n) for _ in range(n)]
        vals.append(fn(y[idx], a[idx]))
    vals = np.sort(np.array(vals))
    return float(vals[int(0.025 * b)]), float(vals[int(0.975 * b) - 1])


def metrics(y, pred) -> dict:
    y, pred = np.asarray(y), np.asarray(pred)
    mae = lambda a, b: float(np.mean(np.abs(a - b)))  # noqa: E731
    rmse = lambda a, b: float(np.sqrt(np.mean((a - b) ** 2)))  # noqa: E731
    rho = lambda a, b: float(spearmanr(a, b).statistic)  # noqa: E731
    return {name: {"value": round(f(y, pred), 4), "ci": [round(x, 4) for x in _boot(y, pred, f)]}
            for name, f in (("mae", mae), ("rmse", rmse), ("spearman", rho))} | {"n": int(len(y))}


def run(workers: int = 8) -> dict:
    s = select()
    s["logP_rdkit"] = [round(Crippen.MolLogP(Chem.MolFromSmiles(x)), 3) for x in s.smiles]
    with ThreadPoolExecutor(max_workers=workers) as ex:
        res = list(ex.map(lambda r: xtb.compute(r[0], r[1]), zip(s.inchikey, s.smiles)))
    s["xtb_status"] = [r["status"] for r in res]
    s["logP_xtb"] = [r.get("logP_xtb") for r in res]
    s["logK_hexadecane_xtb"] = [r.get("logK", {}).get("hexadecane") for r in res]
    ok = s[s.xtb_status == "ok"]
    out = {
        "reference": "SangsterLogP (Zenodo 19387552, CC BY 4.0), neutral subset",
        "selection": {"seed": SEED, "perQuintile": N_PER_BIN, "selected": int(len(s)), "xtbOk": int(len(ok)),
                      "xtbFailed": s[s.xtb_status != "ok"].xtb_status.str[:60].value_counts().to_dict()},
        "rdkit_all": metrics(s.logP_exp, s.logP_rdkit),
        "rdkit_paired": metrics(ok.logP_exp, ok.logP_rdkit),
        "xtb_paired": metrics(ok.logP_exp, ok.logP_xtb),
        "xtbVersion": xtb.version(),
    }
    out["default"] = "rdkit" if out["rdkit_paired"]["mae"]["value"] <= out["xtb_paired"]["mae"]["value"] else "xtb"
    OUT.mkdir(parents=True, exist_ok=True)
    s.to_csv(OUT / "logp_validation.csv", index=False)
    (OUT / "logp_validation.json").write_text(json.dumps(out, indent=2))
    return out
