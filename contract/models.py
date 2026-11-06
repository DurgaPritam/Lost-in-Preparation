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

CONTRACT_VERSION = "1.6"
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
    basis: str = Field(description="silver_ai_reference | ai_drafted_unverified | ai_curated_literature_reference")
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
}
ARRAY_FILES = {k for k in FILE_MODELS if k != "metrics.json"}
