"""Compound descriptors and SMARTS flags for the preparation model (M4).

Descriptors (RDKit): Crippen logP, TPSA, MW, H-bond donors/acceptors, heavy atoms.
HEURISTIC flags (labelled as such everywhere they appear):
  basic_nitrogen   aliphatic amines (not amides, anilines, sulfonamides, imides), amidines, guanidines
  heat:endoperoxide / heat:peroxide   O–O bonds (ring / any)
  heat:labile_ester   esters of tertiary or phenolic alcohols, and lactones of allylic/tertiary type
  heat:glucosinolate, heat:cyanogenic_glycoside   selected heat-labile glycosides
  volatile         small, non-H-bonding molecules (MW < 250, HBD <= 1, TPSA < 40): steam-volatile, lost on open boiling
Coarse class (HEURISTIC): alkaloid-like / glycoside-like / phenolic / terpenoid-like / other.
"""
from __future__ import annotations

from functools import lru_cache

from rdkit import Chem
from rdkit.Chem import Crippen, Descriptors, Lipinski, rdMolDescriptors

SMARTS = {
    "basic_nitrogen": "[NX3;!$(N-C=[O,S,N]);!$(N-a);!$(N-[SX4]);!$(N-N=O);!$(N#*);!$(N=*);!$([N]-[O])]",
    "amidine_guanidine": "[CX3](=[NX2;!a])[NX3]",
    "heat:endoperoxide": "[OX2;R][OX2;R]",
    "heat:peroxide": "[OX2][OX2]",
    "heat:labile_ester": "[CX3](=O)[OX2][$([CX4;H0]),$(c)]",
    "heat:glucosinolate": "S[CX3]=N[OX2]S(=O)(=O)[O,OX1-]",
    "heat:cyanogenic_glycoside": "N#C[CX4][OX2][CX4;R]",
}
_PAT = {k: Chem.MolFromSmarts(v) for k, v in SMARTS.items()}
_SUGAR = Chem.MolFromSmarts("[OX2;R1]1[CX4;R1][CX4;R1]([OX2H1,OX2])[CX4;R1]([OX2H1,OX2])[CX4;R1]([OX2H1,OX2])[CX4;R1]1")
_PHENOL = Chem.MolFromSmarts("c[OX2H1]")


@lru_cache(maxsize=200_000)
def describe(smiles: str) -> dict | None:
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    flags = sorted(k for k, p in _PAT.items() if mol.HasSubstructMatch(p))
    if "heat:endoperoxide" in flags and "heat:peroxide" in flags:
        flags.remove("heat:peroxide")
    basic = "basic_nitrogen" in flags or "amidine_guanidine" in flags
    mw = Descriptors.MolWt(mol)
    hbd, tpsa = Lipinski.NumHDonors(mol), rdMolDescriptors.CalcTPSA(mol)
    volatile = mw < 250 and hbd <= 1 and tpsa < 40
    heat_flags = [f for f in flags if f.startswith("heat:")]
    if basic:
        cls = "alkaloid-like"
    elif mol.HasSubstructMatch(_SUGAR):
        cls = "glycoside-like"
    elif mol.HasSubstructMatch(_PHENOL):
        cls = "phenolic"
    elif all(a.GetSymbol() in ("C", "O", "H") for a in mol.GetAtoms()) and mol.GetNumAtoms() >= 10:
        cls = "terpenoid-like"
    else:
        cls = "other"
    return {
        "logP": round(Crippen.MolLogP(mol), 3), "tpsa": round(tpsa, 2), "mw": round(mw, 2),
        "hbd": int(hbd), "hba": int(Lipinski.NumHAcceptors(mol)), "heavyAtoms": mol.GetNumHeavyAtoms(),
        "basicN": bool(basic), "heatFlags": heat_flags, "volatile": bool(volatile), "class": cls,
    }
