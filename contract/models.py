"""Shared data contract — v1.3 (frozen; v1.1–v1.3 are additive or layout-only, see CHANGELOG).

One pydantic model per site-data/ file. JSON Schemas in contract/schemas/ are generated from
these models (`python -m lip contract`); never edit the schemas by hand.

Includes accepted proposals P1–P29 (see contract/CHANGELOG.md). Changes after the freeze must
be proposed in CHANGELOG.md first.

Conventions
- `unknown` is a value, never an error. Free-text fields use the literal string "unknown".
- Every record has `mock: bool` (default false). Mock data must set it to true.
- Heuristic-derived values are flagged as heuristic (rule 5).
- Solvent, heat and filtration are separate fields everywhere (rule 4).
"""
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

CONTRACT_VERSION = "1.9"
UNKNOWN = "unknown"


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=True)


class _Record(_Model):
    mock: bool = False


# --- shared enumerations ------------------------------------------------------------------

class Solvent(str, Enum):  # historical vehicles (P8 list, P9 none)
    water = "water"
    wine = "wine"
    vinegar = "vinegar"
    oil = "oil"
    honey = "honey"
    none = "none"
    other = "other"
    unknown = "unknown"


class ModernSolvent(str, Enum):  # P2
    methanol = "methanol"
    ethanol = "ethanol"
    hydroethanolic = "hydroethanolic"
    hexane = "hexane"
    chloroform = "chloroform"
    ethyl_acetate = "ethyl_acetate"
    dichloromethane = "dichloromethane"
    acetone = "acetone"
    co2 = "co2"
    water = "water"
    other = "other"
    unknown = "unknown"


class Heat(str, Enum):  # `cold` = no applied heat / ambient (P13)
    cold = "cold"
    warm = "warm"
    boiled = "boiled"
    unknown = "unknown"


class Filtered(str, Enum):  # P12
    yes = "yes"
    no = "no"
    not_applicable = "not_applicable"
    unknown = "unknown"


class Process(str, Enum):  # P10
    infusion = "infusion"
    decoction = "decoction"
    maceration = "maceration"
    distillation = "distillation"
    expression = "expression"
    powder = "powder"
    other = "other"
    unknown = "unknown"


class Part(str, Enum):  # P11
    leaf = "leaf"
    root = "root"
    rhizome = "rhizome"
    seed = "seed"
    fruit = "fruit"
    flower = "flower"
    bark = "bark"
    stem = "stem"
    aerial_parts = "aerial_parts"
    whole_plant = "whole_plant"
    resin = "resin"
    juice = "juice"
    other = "other"
    unknown = "unknown"


class FreshOrDried(str, Enum):  # P11
    fresh = "fresh"
    dried = "dried"
    unknown = "unknown"


class Form(str, Enum):  # P11
    drink = "drink"
    poultice = "poultice"
    ointment = "ointment"
    plaster = "plaster"
    gargle = "gargle"
    inhalation = "inhalation"
    other = "other"
    unknown = "unknown"


class RecipeType(str, Enum):  # P27
    single_plant = "single_plant"
    compound = "compound"
    unknown = "unknown"


class IngredientRole(str, Enum):  # P27
    principal = "principal"
    co_ingredient = "co_ingredient"
    unknown = "unknown"


class IngredientKind(str, Enum):  # P27 detail (decides single_plant vs compound)
    plant = "plant"
    animal = "animal"
    mineral = "mineral"
    other = "other"
    unknown = "unknown"


class MatchCode(str, Enum):  # P5
    match = "match"
    mismatch = "mismatch"
    unknown = "unknown"
    no_analogue = "no_analogue"  # v1.6 (P37c): audit v2 only; the historical vehicle has no modern analogue (never unfaithful)


class ToxicityFlag(str, Enum):  # P18; v1.4 (P34): values describe what the cited SOURCE says
    toxic_reported = "toxic_reported"            # poisoning, toxic effects or toxic constituents reported
    concern_reported = "concern_reported"        # a specific risk, contraindication or warning
    no_toxicity_reported = "no_toxicity_reported"  # NOT evidence of safety
    data_lacking = "data_lacking"                # the source says safety / toxicity data are missing
    unknown = "unknown"                          # no source located; NOT evidence of safety
    known_toxic = "known_toxic"                  # deprecated in v1.4 (screen-list value); kept for compatibility
    none_known = "none_known"                    # deprecated in v1.4; never emitted (absence is not safety)


class ToxicityEvidence(_Model):  # v1.4 (P34)
    source: str
    url: str
    quote: str = Field(description="one verbatim sentence, re-checked against the fetched source")
    licence: str
    basis: str = Field(description="e.g. ai_drafted_unverified")
    verifiedBy: str = ""


class SpeciesBasis(str, Enum):  # commentary_19c: candidate only, never ground truth (P29)
    scholarly = "scholarly"
    database = "database"
    model = "model"
    commentary_19c = "commentary_19c"


class MetricStatus(str, Enum):  # P7
    computed = "computed"
    not_computed = "not_computed"


class ProvenanceMethod(str, Enum):  # P21
    llm = "llm"
    human = "human"
    adjudicated = "adjudicated"


# --- sources.json -------------------------------------------------------------------------

class SourceFile(_Model):
    url: str
    sha256: str


class Source(_Record):
    id: str
    workId: str = Field(description="Groups volumes/editions of one work (P25)")
    title: str
    author: str
    translator: str | None = None  # P20
    originalYear: int | None = Field(None, description="Year of composition/first publication; may be approximate (P24)")
    originalYearApprox: bool = False
    editionYear: int = Field(description="Year of the edition actually digitised (P24)")
    language: str
    edition: str
    licence: str
    licenceVerified: bool  # P20
    licenceNote: str | None = None
    editorialNote: str | None = Field(None, description="Later editorial additions etc. (P26)")
    url: str
    files: list[SourceFile] = []  # P25


# --- recipes.json -------------------------------------------------------------------------

class Quote(_Model):
    """A verbatim span of the passage's cleaned text (P28). Offsets index into passage.text.

    inHeading=True: the quote comes from the entry heading (plant names only); start=end=-1.
    """
    quote: str
    start: int
    end: int
    inHeading: bool = False


class PassageLocation(_Model):
    part: str
    book: int | None = None
    chapter: str | None = None
    entry: str | None = None
    subsection: str | None = None
    lineStart: int
    lineEnd: int


class PassageRef(_Model):
    passageId: str
    text: str
    location: PassageLocation
    translation: str | None = None  # P19
    translationSource: str | None = None


class Ingredient(_Model):  # P27
    plantNameAsWritten: str
    part: Part = Part.unknown
    role: IngredientRole = IngredientRole.unknown
    kind: IngredientKind = IngredientKind.unknown
    evidence: list[Quote] = []


class Provenance(_Model):  # P21; provider fields added in v1.1 (P30)
    method: ProvenanceMethod
    provider: str | None = None  # groq | ollama | anthropic
    model: str | None = None
    modelVersion: str | None = Field(None, description="e.g. Ollama model digest")
    decoding: dict[str, Any] | None = Field(None, description="temperature, seed, context length, quantisation, effort...")
    promptVersion: str | None = None
    annotator: str | None = None
    createdAt: str


class RecipeCorrection(_Model):  # v1.6 (P37a): a logged field correction (config/m1_corrections.csv)
    field: str
    from_: str = Field(alias="from", description="the extracted value (solvent lists joined with '+')")
    to: str
    reason: str
    evidence: str
    requestedBy: str
    appliedBy: str
    date: str

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class Recipe(_Record):
    id: str
    sourceId: str
    passage: PassageRef
    recipeType: RecipeType = RecipeType.unknown
    ingredients: list[Ingredient] = []
    plantNameAsWritten: str = UNKNOWN  # principal plant
    part: Part = Part.unknown
    freshOrDried: FreshOrDried = FreshOrDried.unknown
    solvent: list[Solvent] = Field(default_factory=lambda: [Solvent.unknown], min_length=1)  # P8
    heat: Heat = Heat.unknown
    heatText: str = UNKNOWN  # P13
    durationText: str = UNKNOWN
    filtered: Filtered = Filtered.unknown
    process: Process = Process.unknown  # P10
    form: Form = Form.unknown
    indicationAsWritten: str = UNKNOWN
    indicationNormalized: "MeshTerm | None" = None  # P17; not produced by M1
    fieldConfidence: dict[str, float] = Field(
        default_factory=dict, description="Model self-reported 0-1 confidence per field; uncalibrated")
    evidence: dict[str, list[Quote]] = Field(
        default_factory=dict, description="Verbatim quotes supporting each non-unknown field; key 'recipe' = whole recipe span (P28)")
    attributionCaveat: str | None = None  # P26
    excludedFromHeadline: bool = Field(False, description="True for compound recipes (P27 decision)")
    provenance: Provenance
    corrections: list[RecipeCorrection] = Field(
        default_factory=list, description="v1.6 (P37a): logged corrections; the fields above stay as extracted")


# --- species.json -------------------------------------------------------------------------

class SpeciesCandidate(_Record):
    id: str  # P3
    recipeId: str
    speciesId: str | None = Field(None, description="= wfoId; null if unresolved (P3)")
    nameAsWritten: str
    acceptedName: str | None = None
    wfoId: str | None = None
    confidence: float
    basis: SpeciesBasis
    basisRef: str | None = Field(None, description="e.g. footnote passage id for commentary_19c")
    disputed: bool
    toxicityFlag: ToxicityFlag = ToxicityFlag.unknown  # P18
    toxicityNote: str | None = None


# --- profiles.json ------------------------------------------------------------------------

class Drivers(_Model):  # P6 per-factor multipliers, kept separate (rule 4)
    solvent: float
    heat: float
    filtration: float
    acidity: float


class HeuristicFlags(_Model):  # rule 5
    heat: bool = True
    acidity: bool = True
    filtration: bool = True


class CompoundLikelihood(_Model):
    compoundId: str = Field(description="InChIKey (P14)")
    name: str
    compoundClass: str = Field(alias="class")
    smiles: str
    sourceDb: str
    sourceRecordId: str
    likelihood: float
    low: float
    high: float
    drivers: Drivers
    heuristic: HeuristicFlags = HeuristicFlags()
    heuristicFlags: list[str] = []

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class Profile(_Record):
    speciesId: str
    preparationKey: str = Field(description="part|freshOrDried|solvent(+joined)|heat|filtered (P4)")
    process: Process | None = Field(None, description="v1.2 (P32): process, e.g. distillation, which the key cannot express")
    preparationLabel: str | None = None
    compounds: list[CompoundLikelihood]
    coverageNote: str


class ProfileIndexEntry(_Record):  # v1.3 (P33): site-data/profiles/index.json
    speciesId: str
    acceptedName: str
    file: str = Field(description="path relative to site-data/, e.g. profiles/wfo-0000134589.json")
    preparations: int
    compounds: int
    toxicityFlag: ToxicityFlag = ToxicityFlag.unknown
    toxicityNote: str | None = None
    toxicityEvidence: ToxicityEvidence | None = None  # v1.4 (P34)


# --- engine/ (v1.7, P38: Preparation Lab, the in-browser M4 engine) -----------------------
# Everything the browser needs to recompute M4 for any combination of solvent, heat, filtration and acidity:
# the model parameters and uncertainty settings (engine/model.json), each species' per-compound model inputs
# (engine/<speciesId>.json, loaded on demand), and Python reference results for combinations outside the
# 13-preparation grid (engine/parity.json). All values are MODEL INPUTS or MODEL ESTIMATES, never measurements;
# acidity, heat alerts, volatility, filtration carry-over and the size penalty are HEURISTICS (rule 5).

class EngineSolventWindow(_Model):
    upper: list[float] | None = Field(None, description="[low, high] of the upper logP edge (too lipophilic to dissolve)")
    lower: list[float] | None = Field(None, description="[low, high] of the lower logP edge (too polar to dissolve)")
    ethanolFraction: list[float] | None = Field(None, description="wine only: ethanol volume fraction range")
    ethanolShift: list[float] | None = Field(None, description="wine only: window shift per unit ethanol fraction")


class EngineHeatRange(_Model):
    warm: list[float]
    boiled: list[float]


class EngineParams(_Model):
    draws: int
    seed: int
    steepness: list[float]
    solvents: dict[str, EngineSolventWindow]
    acidityLogdShift: list[float] = Field(description="HEURISTIC: logD shift for basic nitrogen in vinegar")
    heat: dict[str, EngineHeatRange] = Field(description="HEURISTIC: degradation fraction per alert (and volatile loss) per heat level")
    distillationVolatileCarried: list[float]
    distillationNonvolatileCarried: list[float]
    unfilteredSuspended: list[float] = Field(description="HEURISTIC: suspended material carried by an unfiltered preparation")
    appliedWholeSuspended: list[float] = Field(description="HEURISTIC: material in contact when applied whole (not_applicable)")
    mwPenaltyAbove: float
    mwPenalty: list[float] = Field(description="HEURISTIC: size penalty above mwPenaltyAbove")


class EngineDescriptorError(_Model):
    descriptor: str
    mae: float
    sd: float = Field(description="Normal SD added to logP for the reported 5th–95th range (sigma = MAE * sqrt(pi/2))")
    source: str


class EnginePreparation(_Model):
    seedOffset: int = Field(description="added to params.seed for this preparation's random stream")
    key: str
    label: str
    solvents: list[str]
    heat: Heat
    filtered: Filtered
    process: Process | None = None


class EngineModel(_Record):  # site-data/engine/model.json
    modelVersion: str = Field(description="hash of config/prep_model.toml (prep-model:<sha256[:10]>)")
    rng: str = Field(description="random-number generation, so a port can reproduce the draws exactly")
    noiseSeedOffset: int = Field(description="descriptor-error stream: params.seed + seedOffset + noiseSeedOffset")
    customSeedRule: str = Field(description="seedOffset for a preparation outside the grid")
    params: EngineParams
    descriptorError: list[EngineDescriptorError]
    preparations: list[EnginePreparation] = Field(description="the 13 pipeline preparations, in grid order")
    heuristics: list[str]
    note: str


class EngineCompound(_Model):
    compoundId: str = Field(description="InChIKey")
    name: str
    compoundClass: str = Field(description="coarse class (heuristic)")
    descriptor: str = Field(description="lipophilicity descriptor used: rdkit (Crippen logP) or xtb")
    lipophilicity: float
    basicN: bool = Field(description="HEURISTIC SMARTS flag: basic nitrogen")
    heatFlags: list[str] = Field(description="HEURISTIC SMARTS heat alerts")
    volatile: bool = Field(description="HEURISTIC: MW < 250, HBD <= 1, TPSA < 40")
    mw: float


class EngineSpecies(_Record):  # site-data/engine/<speciesId>.json
    speciesId: str
    acceptedName: str
    modelVersion: str
    compounds: list[EngineCompound] = Field(description="same compounds, in the same order, as profiles/<speciesId>.json")


class EngineEstimate(_Model):
    compoundId: str
    likelihood: float
    low: float
    high: float
    rangeModelOnly: list[float]
    drivers: Drivers


class EngineParityCase(_Record):  # site-data/engine/parity.json
    speciesId: str
    preparation: EnginePreparation
    expected: list[EngineEstimate] = Field(description="Python (pipeline/lip/m4/model.py) estimates, one per compound, in species order")


# --- plates.json (v1.8, P39: botanical plates for the site) ------------------------------
# One record per modelled species: a public-domain 19th-century plate from Wikimedia Commons, or status "to_source"
# with no image. Written by `python -m lip plates`; the licence, author and date are as stated on Commons.

class PlateImage(_Model):
    avif: str = Field(description="srcset of the AVIF copies served by the site")
    webp: str = Field(description="srcset of the WebP copies served by the site")
    src: str = Field(description="largest WebP copy (img fallback)")
    width: int
    height: int


class PlateAiCheck(_Model):  # v1.8 (P39 amendment): an AI agent's reading of the Commons page; never human confirmation
    basis: str = Field(description="ai_assisted_check")
    statement: str = Field(description="'checked by AI agent on <date>; awaiting human confirmation'")
    checkedOn: str
    checkedBy: str
    pageRevisionId: int | None = None
    licenceTemplates: list[str] = Field(default_factory=list, description="licence templates as written on the page")
    publication: str | None = Field(None, description="the page's Source field and plate-series categories, as written")
    publicationDate: str | None = Field(None, description="the page's Date field, as written (may be an upload date)")
    flags: list[str] = Field(default_factory=list, description="mechanical observations for the human reviewer")


class PlateRecord(_Record):  # site-data/plates.json
    speciesId: str
    taxon: str
    caption: str
    status: str = Field(description="to_source (no image) | sourced (licence read from Commons by script) | confirmed (checked by a person)")
    licence: str | None = Field(None, description="Commons LicenseShortName, e.g. 'Public domain'")
    licenceDetail: str | None = Field(None, description="Commons UsageTerms")
    host: str | None = None
    fileUrl: str | None = Field(None, description="Commons file description page")
    sourceUrl: str | None = Field(None, description="the image URL that was downloaded once (never hotlinked)")
    author: str | None = None
    date: str | None = None
    work: str | None = Field(None, description="the plate series")
    matchedName: str | None = Field(None, description="the name the file is titled with (accepted name or a WFO synonym)")
    sha256: str | None = None
    retrievedAt: str | None = None
    image: PlateImage | None = None
    aiCheck: PlateAiCheck | None = Field(None, description="v1.8 P39 amendment: AI-assisted licence check (provisional); status stays 'sourced' until a person confirms")


# --- audit.json ---------------------------------------------------------------------------

class MeshTerm(_Model):  # P17
    meshId: str
    label: str


class StudyMatch(_Model):  # P5
    solvent: MatchCode
    heat: MatchCode
    filtration: MatchCode
    part: MatchCode
    freshOrDried: MatchCode
    overall: MatchCode


class Study(_Model):
    pmid: str
    doi: str | None = None
    title: str
    year: int | None = None
    solvent: ModernSolvent  # P2
    solventText: str
    ethanolFraction: float | None = None
    heat: Heat
    part: Part
    freshOrDried: FreshOrDried
    filtered: Filtered  # P1
    match: StudyMatch
    unknownFields: list[str]
    evidenceSource: str = Field(description="abstract | pmc_fulltext (P15)")
    methodsSnippet: str | None = None


class Rate(_Model):  # P16
    value: float | None
    nKnown: int
    nUnknown: int


class AuditRecord(_Record):
    speciesId: str
    indication: MeshTerm | None
    indicationAsWritten: str
    historicalPreparation: str = Field(description="preparationKey")
    historicalRecipeIds: list[str]
    studies: list[Study]
    matchRate: Rate


# --- hypotheses.json ----------------------------------------------------------------------

class Interval(_Model):
    value: float
    low: float
    high: float


class EvidenceItem(_Model):
    kind: str  # recipe | study | profile | species
    ref: str
    note: str | None = None


class GapRanking(_Model):  # v1.5 (P35)
    rule: str = Field(description="the ranking rule, e.g. rank by the 5th percentile of the gap over coupled draws")
    gapP5: float = Field(description="profile gap exceeded in 95% of draws (the ranking key)")
    gapThreshold: float
    pGapAboveThreshold: float
    compoundsUsed: int
    compoundsExcludedWide: int = Field(description="compounds left out: 5th–95th range wider than the rule's limit")
    rankByMedianGap: int | None = Field(None, description="comparison only; not used for ranking")


class Hypothesis(_Record):
    rank: int
    speciesId: str
    indication: MeshTerm | None
    indicationAsWritten: str
    faithfulPreparation: str = Field(description="preparationKey")
    faithfulPreparationText: str
    attestationCount: int
    profileGap: Interval  # P22: 1 - cosine similarity, in [0,1]; v1.5 (P35): value = median, low/high = 5th/95th of coupled draws
    gapRanking: GapRanking | None = None  # v1.5 (P35): the robust ranking rule's inputs
    neverTestedFaithfully: bool
    toxicityFlag: ToxicityFlag  # P18
    toxicityNote: str | None = None
    caveats: list[str]
    evidenceTrail: list[EvidenceItem]


# --- metrics.json -------------------------------------------------------------------------

class Metric(_Model):  # P7
    status: MetricStatus
    value: float | None = None
    low: float | None = None
    high: float | None = None
    n: int | None = None
    sourceFile: str | None = None
    note: str | None = None


def not_computed(note: str) -> Metric:
    return Metric(status=MetricStatus.not_computed, note=note)


class PRF(_Model):
    precision: Metric
    recall: Metric
    f1: Metric


class ExtractionRun(_Model):  # v1.1 (P30)
    provider: str
    model: str
    modelVersion: str | None = None
    decoding: dict[str, Any] = {}
    promptVersion: str


class ExtractionMetrics(_Model):
    run: ExtractionRun | None = Field(None, description="the LLM run the metrics describe; null until a run exists")
    overall: dict[str, PRF] = Field(description="per field, all strata")
    bySource: dict[str, dict[str, PRF]] = Field(description="stratum -> field -> PRF")
    recipeDetection: dict[str, PRF] = Field(description="stratum or 'overall' -> PRF")
    spanRejectionRate: Metric


class CheckResult(_Model):
    status: MetricStatus
    result: str | None = None  # pass | fail
    explanation: str | None = None
    sourceFile: str | None = None


class ProvisionalSection(_Model):  # v1.2 (P31): never human-validated
    basis: str = Field(description="silver_ai_reference | ai_drafted_unverified | ai_curated_literature_reference | ai_assisted_check")
    label: str
    extraction: ExtractionMetrics | None = None
    metrics: dict[str, Metric] = {}


class AuditV2Section(_Model):  # v1.6 (P37c)
    label: str
    protocol: str
    overallFidelity: Metric
    overallNotFaithfulShare: Metric
    perVariableFidelity: dict[str, Metric]
    solventWineCutoffSensitivity: dict[str, Metric]
    units: int
    unknownUnits: int
    noModernAnalogueUnits: int
    eligibleStudies: int
    pairsWithRecords: int
    pairs: int


class CaseStage(_Model):  # v1.6 (P37d)
    faithful: str
    modern: str
    rank: int
    rankedOf: int
    gap: Interval


class CaseEvidence(_Model):  # v1.6 (P37d)
    passageId: str
    sourceId: str
    citation: str
    text: str


class CaseStudy(_Record):  # v1.6 (P37d): site-data/case_studies.json
    id: str
    title: str
    speciesId: str
    indication: MeshTerm
    primaryRecipeId: str
    recipeQuote: str
    extractedAs: dict[str, str]
    correctedTo: dict[str, str]
    correctedRecipeIds: list[str]
    evidence: list[CaseEvidence]
    before: CaseStage
    after: CaseStage
    label: str


class Metrics(_Model):
    contractVersion: str = CONTRACT_VERSION
    generatedAt: str
    pipelineVersion: str
    mock: bool = False
    extraction: ExtractionMetrics
    interAnnotatorAgreement: dict[str, Metric] = Field(description="field -> Cohen's kappa")
    nameResolution: dict[str, Metric]  # top1, top3, disputedShare
    logPError: dict[str, Metric]  # rdkit, xtb
    headlineMatchRate: Metric
    artemisininCheck: CheckResult
    reportingGap: dict[str, Metric] = Field(
        default_factory=dict, description="v1.6 (P37b): descriptive reporting-gap shares (not hypothesis tests), Wilson 95% CI")
    auditV2: "AuditV2Section | None" = Field(None, description="v1.6 (P37c): audit v2, pre-registered re-analysis after v1's design flaw")
    provisional: dict[str, ProvisionalSection] = Field(
        default_factory=dict, description="v1.2: PROVISIONAL results against AI-made references; never gold")


Recipe.model_rebuild()

Metrics.model_rebuild()

# --- lab_panel.json (v1.9, P40 approved 2026-11-07; v2 amendment): the recommended re-test panel and the Phase 8 benchmark --------------------

class PanelGap(_Model):
    p5: float
    p50: float
    p95: float


class PanelCandidate(_Model):
    position: int
    candidateId: str = Field(description="<speciesId>|<historical preparation>|<modern comparator>")
    speciesId: str
    species: str
    historicalPreparation: str = Field(description="M4 preparation label (heuristic map from the recipe fields)")
    modernComparator: str
    modernComparatorBasis: str = Field(description="studies (most frequent among the pairs' studies) | default (most frequent across all coded studies)")
    indication: MeshTerm
    indications: list[str] = Field(description="every MeSH id attested for the candidate's recipes")
    gap: PanelGap = Field(description="profile gap (1 - cosine similarity) percentiles over coupled Monte Carlo draws (M6)")
    value: float = Field(description="gap.p5 / the largest gap.p5 in the pool")
    compoundsLikelyToDiffer: int
    compoundClasses: list[str]
    toxicity: str
    caveats: list[str]
    evidenceTrail: list[EvidenceItem]


class PanelAlternative(_Model):
    toxicRule: str = Field(description="exclude | at_most_one")
    k: int
    perSpecies: int | None = Field(None, description="at most this many entries per species (v2); null = no limit (v1)")
    poolSize: int
    objective: float
    candidateIds: list[str]
    coverage: dict[str, int] = Field(description="distinct attributes covered per family (class, indication, prep)")
    panel: list[PanelCandidate] = Field(default_factory=list, description="P40 amendment: the full entries, so the Planner can show any panel size")


class PanelSensitivity(_Model):
    weight: str
    factor: float
    value: float
    jaccardWithDefault: float
    added: list[str]
    removed: list[str]


class BenchmarkRow(_Model):
    n: int
    k: int
    solver: str = Field(description="exact | greedy | anneal | random | qaoa-penalty | qaoa-xy")
    p: int | None = Field(None, description="QAOA depth")
    instances: int
    meanApproximationRatio: float | None = Field(None, description="classical: of the returned panel; QAOA: expected over the feasible probability mass")
    pOptimum: float | None = Field(None, description="mean probability of sampling an optimal panel (QAOA, exact statevector)")
    feasibility: float | None = Field(None, description="mean probability of exactly k selected and the toxic rule met (QAOA)")
    meanSeconds: float | None = None
    twoQubitGatesAllToAll: int | None = None
    twoQubitGatesHeavyHex: int | None = None
    depthAllToAll: int | None = None


class NoiseRow(_Model):
    variant: str
    p: int
    twoQubitError: float
    oneQubitError: float
    readoutError: float
    pOptimum: float
    feasibility: float
    meanArFeasible: float | None = None


class PanelExcluded(_Model):  # P40 amendment (v2): a candidate left out of the displayed panel, and why
    candidateId: str
    species: str
    historicalPreparation: str
    modernComparator: str
    reason: str


class PanelOriginal(_Model):  # P40 amendment (v2): the original v1 result, kept visible beside v2
    ruleVersion: str
    k: int
    toxicRule: str
    objective: float
    configSha256: str
    panel: list[PanelCandidate]
    notes: list[str] = Field(description="plain notes on the v1 result, generated from its data (e.g. entries chosen on coverage alone)")


class LabPanel(_Record):  # site-data/lab_panel.json
    basis: str = Field(description="exact_optimisation_of_model_outputs: the panel is the exact optimum of a fixed objective over model predictions; hypotheses worth re-testing, never claims")
    label: str
    ruleVersion: str = Field(description="v2 (docs/QUBO_v2_RULE.md, pre-registered) for the displayed panel")
    ruleDoc: str
    toxicRule: str
    perSpecies: int | None = None
    k: int
    weights: dict[str, float]
    penaltyMargin: float
    configSha256: str
    poolSize: int
    panel: list[PanelCandidate]
    alternatives: list[PanelAlternative]
    perSpeciesSensitivity: list[PanelAlternative] = Field(description="v2 with at most two entries per species (ILP only), k = 4, 6, 8")
    ineligible: list[PanelExcluded] = Field(description="candidates failing the v2 eligibility rule")
    excludedToxic: list[PanelExcluded] = Field(description="eligible candidates left out because toxicity is reported for the species")
    original: PanelOriginal | None = Field(None, description="the original v1 result, shown beside v2")
    sensitivity: list[PanelSensitivity]
    benchmark: list[BenchmarkRow]
    winnerBySize: dict[str, str] = Field(description="n -> which method wins at that size (k = 4): the fastest classical method that returned the optimum on every instance, and QAOA's best P(optimum) against a uniform random feasible panel")
    noise: list[NoiseRow]
    noiseModel: str
    hardware: dict[str, str]
    versions: dict[str, str]
    seeds: dict[str, str]
    generatedAt: str


FILE_MODELS = {
    "sources.json": Source,
    "recipes.json": Recipe,
    "species.json": SpeciesCandidate,
    "profiles.index.json": ProfileIndexEntry,      # site-data/profiles/index.json
    "profiles.species.json": Profile,              # site-data/profiles/<speciesId>.json (array of Profile)
    "audit.json": AuditRecord,
    "audit_v2.json": AuditRecord,                  # v1.6 (P37c)
    "case_studies.json": CaseStudy,                # v1.6 (P37d)
    "hypotheses.json": Hypothesis,
    "metrics.json": Metrics,
    "engine.model.json": EngineModel,              # v1.7 (P38) site-data/engine/model.json
    "engine.species.json": EngineSpecies,          # v1.7 (P38) site-data/engine/<speciesId>.json
    "engine.parity.json": EngineParityCase,        # v1.7 (P38) site-data/engine/parity.json
    "plates.json": PlateRecord,                    # v1.8 (P39) site-data/plates.json
    "lab_panel.json": LabPanel,                    # v1.9 (P40) site-data/lab_panel.json
}
ARRAY_FILES = {k for k in FILE_MODELS if k not in ("metrics.json", "engine.model.json", "engine.species.json", "lab_panel.json")}
