"""GFN2-xTB solvation free energies (xtb 6.7.1, ALPB implicit solvation), cached by InChIKey.

Protocol per compound:
 1. RDKit: add H, one 3D conformer with ETKDGv3 (fixed seed), MMFF94 pre-optimisation.
 2. xtb --gfn 2 --opt (gas phase, optimisation level 'normal').
 3. Single points on the optimised geometry with --alpb <solvent> for each solvent in SOLVENTS;
    Gsolv is read from the xtb output. Solvents supported by the installed xtb (checked 2026-11-05):
    ALPB: water, hexane, hexadecane, octanol, woctanol, methanol, ethanol. Used here: water,
    hexadecane (oil proxy), ethanol (alcohol), woctanol (water-saturated octanol, for logP validation).
 4. log K(solvent/water) = (Gsolv_water - Gsolv_solvent) / (2.303 RT); logP_xtb = log K(woctanol/water).
Exploratory: Wiberg bond orders from the gas-phase run, recorded for O–O bonds (heat-flagged).
Single conformer and implicit solvent: these are approximations (stated in METHODS.md).
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile

from rdkit import Chem
from rdkit.Chem import AllChem

from ..paths import ROOT

XTB = ROOT / ".tools" / "xtb-env" / "bin" / "xtb"
CACHE = ROOT / "data" / "cache" / "xtb"
SOLVENTS = ["water", "hexadecane", "ethanol", "woctanol"]
SEED = 20261105
EH_TO_KCAL = 627.5095
LN10RT = 2.302585 * 0.0019872043 * 298.15  # kcal/mol
MAX_HEAVY = 50
TIMEOUT = 900


def version() -> str | None:
    if not XTB.exists():
        return None
    out = subprocess.run([str(XTB), "--version"], capture_output=True, text=True).stdout
    m = re.search(r"xtb version (\S+)", out)
    return m.group(1) if m else None


def _run(args: list[str], cwd: str) -> str:
    env = {**os.environ, "OMP_NUM_THREADS": "1", "OMP_STACKSIZE": "1G", "MKL_NUM_THREADS": "1"}
    p = subprocess.run([str(XTB), *args], cwd=cwd, capture_output=True, text=True, timeout=TIMEOUT, env=env)
    if "normal termination of xtb" not in (p.stdout + p.stderr):
        raise RuntimeError("xtb failed: " + (p.stdout + p.stderr)[-400:])
    return p.stdout


def _gsolv(out: str) -> float:
    m = re.findall(r"Gsolv\s+(-?\d+\.\d+)\s+Eh", out)
    if not m:
        raise RuntimeError("no Gsolv in output")
    return float(m[-1])


def compute(inchikey: str, smiles: str, force: bool = False) -> dict:
    cp = CACHE / f"{inchikey}.json"
    if cp.exists() and not force:
        return json.loads(cp.read_text())
    res = {"inchikey": inchikey, "smiles": smiles, "xtbVersion": version(), "method": "GFN2-xTB/ALPB", "seed": SEED}
    try:
        mol = Chem.AddHs(Chem.MolFromSmiles(smiles))
        if mol.GetNumHeavyAtoms() > MAX_HEAVY:
            raise RuntimeError(f"skipped: {mol.GetNumHeavyAtoms()} heavy atoms > {MAX_HEAVY}")
        p = AllChem.ETKDGv3()
        p.randomSeed = SEED
        if AllChem.EmbedMolecule(mol, p) != 0:
            raise RuntimeError("ETKDG embedding failed")
        AllChem.MMFFOptimizeMolecule(mol, maxIters=2000)
        charge = Chem.GetFormalCharge(mol)
        d = tempfile.mkdtemp(prefix="xtb_")
        try:
            Chem.MolToXYZFile(mol, os.path.join(d, "in.xyz"))
            out = _run(["in.xyz", "--gfn", "2", "--opt", "normal", "--chrg", str(charge)], d)
            res["energyGas"] = float(re.findall(r"TOTAL ENERGY\s+(-?\d+\.\d+)\s+Eh", out)[-1])
            wbo = os.path.join(d, "wbo")
            sym = [a.GetSymbol() for a in mol.GetAtoms()]
            oo = []
            if os.path.exists(wbo):
                for line in open(wbo):
                    i, j, b = line.split()
                    i, j = int(i) - 1, int(j) - 1
                    if sym[i] == "O" and sym[j] == "O":
                        oo.append(round(float(b), 3))
            res["wiberg_OO"] = oo
            shutil.copy(os.path.join(d, "xtbopt.xyz"), os.path.join(d, "opt.xyz"))
            g = {}
            for s in SOLVENTS:
                g[s] = _gsolv(_run(["opt.xyz", "--gfn", "2", "--alpb", s, "--chrg", str(charge)], d))
            res["gsolv_Eh"] = g
            res["logK"] = {s: round((g["water"] - g[s]) * EH_TO_KCAL / LN10RT, 3) for s in SOLVENTS if s != "water"}
            res["logP_xtb"] = res["logK"]["woctanol"]
            res["status"] = "ok"
        finally:
            shutil.rmtree(d, ignore_errors=True)
    except Exception as e:  # noqa: BLE001 - recorded, never imputed
        res["status"] = f"failed: {str(e)[:200]}"
    CACHE.mkdir(parents=True, exist_ok=True)
    cp.write_text(json.dumps(res, indent=1))
    return res
