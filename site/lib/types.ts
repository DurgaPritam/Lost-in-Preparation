/**
 * VIEW-MODEL TYPES (from design/v2 src/types.ts; the v1 adaptations are kept).
 * The contract types are GENERATED from the JSON Schemas into lib/data/generated/ and validated with Zod at build
 * time. These are the narrow props the design's components take; lib/data/selectors/ maps contract records onto
 * them. Changes from the design's assumed shapes are marked "SITE:" and listed in site/CHANGES.md.
 */

/** 1. Evidence status */
export type EvidenceStatus = 'validated' | 'provisional' | 'pending';

/** 2. Source confidence */
/** SITE: the real corpus has a third source, Culpeper's 1850 Complete Herbal (never merged with 1652 or Pliny). */
export type SourceWork = 'culpeper_1652' | 'culpeper_1850' | 'pliny_nh';
export type SourceConfidenceLevel = 'higher' | 'lower' | 'unknown';
export interface SourceConfidence {
  source: SourceWork;
  level: SourceConfidenceLevel;
  /** Share of resolved names that are disputed, 0–1. null = unknown. */
  disputedShare: number | null;
  note?: string;
}

/** 4. Uncertainty: every likelihood is a range on 0–1. null = unknown. */
export interface LikelihoodRange {
  low: number | null;
  high: number | null;
  /** Point estimate. Secondary; may be absent. */
  point?: number | null;
}

/** 3. Disputed names */
export type TaxonRank = 'species' | 'genus';
export interface SpeciesCandidate {
  taxon: string;
  rank: TaxonRank;
  authority?: string;
  /** SITE: M2 gives a heuristic match score with no interval: low/high are null and the score is `point`. */
  confidence: LikelihoodRange;
  evidence: EvidenceStatus;
}
export type ResolutionState = 'resolved' | 'disputed' | 'genus_only' | 'unresolved';
export interface NameResolution {
  historicalName: string;
  source: SourceWork;
  state: ResolutionState;
  candidates: SpeciesCandidate[];
}

/** 6. Heuristics */
export interface Heuristic {
  id: 'acidity' | 'heat_sensitivity' | string;
  label: string;
  rule: string;
}

/** 7. Toxicity */
export type ToxicityCategory =
  | 'toxic_reported'
  | 'concern'
  | 'no_toxicity_reported'
  | 'data_lacking'
  | 'unknown';
export interface ToxicitySource {
  label: string;
  href?: string;
}
export interface ToxicityRecord {
  category: ToxicityCategory;
  sources: ToxicitySource[];
  note?: string;
}

/** Preparations */
export type PreparationFamily = 'historical' | 'modern';
/**
 * SITE: the contract keeps solvent, heat and process separate (non-negotiable 4), so the vehicle is the solvent alone:
 * a historical vehicle (water, wine, vinegar, oil, honey, none, other) or a modern solvent (methanol, ethanol,
 * hydroethanolic, hexane, ...). Several vehicles are joined with "+", e.g. "honey+vinegar". See vehicleLabel().
 */
export type Vehicle = string;
export interface Preparation {
  family: PreparationFamily;
  vehicle: Vehicle;
  /** null = not stated in the source. Rendered as Unknown, never as "no".
   *  SITE: 'not_applicable' (ointments, poultices, amulets ...) is a real contract value and prints as such. */
  filtered: boolean | null | 'not_applicable';
  /** v2 (additive): acid added or inherent (vinegar). null = not stated. */
  acidified?: boolean | null;
  /** Added in Phase 2. null = not stated. */
  heat?: HeatLevel | null;
  /** Free text as normalised, e.g. "3 days". null = not stated. */
  duration?: string | null;
}

/* ───────────────────────── Phase 2 additions (still assumed) ───────────────────────── */

export type HeatLevel = 'cold' | 'warm' | 'boiled' | 'reflux';

/** A field the pipeline extracted from a passage, anchored to character offsets. */
/** SITE: the fields M1 actually extracts. It never extracts quantity, so quantity is not listed as not stated. */
export type ExtractedFieldKind = 'plant' | 'part' | 'freshOrDried' | 'vehicle' | 'heat' | 'duration' | 'filtration' | 'process' | 'form' | 'indication';
export interface ExtractedField {
  id: string;
  kind: ExtractedFieldKind;
  /** [start, end) offsets into Passage.text. */
  start: number;
  end: number;
  /** Normalised value, e.g. "wine", "3 days". null = could not normalise. */
  value: string | null;
  evidence: EvidenceStatus;
  /** SITE: false when the quote overlaps a span already drawn in the passage (it is still listed in the table),
   *  or comes from the entry heading (start = end = -1). */
  inline: boolean;
  /** SITE: the verbatim quote (the heading text when the quote is from the heading). */
  quote: string;
}
/** A stretch of the transcription that is illegible. Rendered as ⟦?⟧. */
export interface IllegibleSpan {
  id: string;
  /** Offset where the marker is placed in Passage.text. SITE: the transcription keeps its marker in the text,
   *  so the span runs from `at` to `end` and is drawn in place of those characters. */
  at: number;
  end: number;
  /** Estimated length in characters; null = unknown. */
  estChars: number | null;
  note?: string;
}
export interface Passage {
  text: string;
  edition: string;
  locator: string;
  fields: ExtractedField[];
  illegible: IllegibleSpan[];
}

export interface Recipe {
  id: string;
  source: SourceWork;
  name: NameResolution;
  preparation: Preparation;
  passage: Passage;
  toxicity: ToxicityRecord;
  evidence: EvidenceStatus;
  /** SITE additions from the contract. */
  indication: string | null;
  recipeType: 'single_plant' | 'compound' | 'unknown';
  excludedFromHeadline: boolean;
  recipeQuote: string;
  provenance: string;
  corrections: RecipeCorrectionView[];
}
/** SITE: a logged field correction (contract v1.6, P37a). The recipe's fields stay as extracted. */
export interface RecipeCorrectionView {
  field: string;
  from: string;
  to: string;
  reason: string;
  evidence: string;
  requestedBy: string;
  appliedBy: string;
  date: string;
}
/** SITE: the recipe explorer list carries a summary, not the whole passage. */
export interface RecipeSummary {
  id: string;
  source: SourceWork;
  name: NameResolution;
  preparation: Preparation;
  toxicity: ToxicityRecord;
  evidence: EvidenceStatus;
  indication: string | null;
  search: string;
  corrected: boolean;
}

/** Compare view: one species' predicted extraction under one preparation. */
export type DriverId = 'solvent' | 'heat' | 'filtration' | 'acidity';
export type DriverEffect = 'raises' | 'lowers' | 'neutral' | 'unknown';
export interface Driver {
  id: DriverId;
  effect: DriverEffect;
  strength: 'strong' | 'moderate' | 'weak' | null;
  /** True for rule-of-thumb drivers (acidity, heat sensitivity). */
  heuristic: boolean;
  note?: string;
}
export interface CompoundEstimate {
  compound: string;
  compoundClass: string;
  likelihood: LikelihoodRange;
  drivers: Driver[];
}
export interface PreparationProfile {
  id: string;
  label: string;
  preparation: Preparation;
  /** Where this preparation comes from: a recipe or a modern study. */
  /** SITE: the M4 profiles are model presets for a species ('model'), not tied to one recipe or study. */
  origin: { kind: 'recipe'; recipeId: string; source: SourceWork } | { kind: 'study'; citation: string } | { kind: 'model'; note: string };
  estimates: CompoundEstimate[];
}
export interface SpeciesProfile {
  taxon: string;
  /** If the species came from a disputed name, which candidate this is. */
  fromName?: { historicalName: string; candidateIndex: number; candidateCount: number };
  toxicity: ToxicityRecord;
  preparations: PreparationProfile[];
}

/* ───────────────────────── Phase 3 additions (still assumed) ───────────────────────── */

/** A value extracted from a paper. value null = the paper does not state it. */
export interface StatedField<T> {
  value: T | null;
  evidence: EvidenceStatus;
}
/** SITE: 'no_analogue' (audit v2 only): the historical vehicle has no modern analogue; never counted as differs. */
export type MatchState = 'matches' | 'differs' | 'not_stated' | 'no_analogue';

/** SITE: one coded modern study row (from audit.json / audit_v2.json). A study coded with several preparations has one
 *  row per preparation. Duration and ratio are not coded by the rule-based extractor, so they are not shown. */
export interface Study {
  id: string;
  pmid: string | null;
  title: string;
  year: number | null;
  taxon: string;
  indication: string;
  plantPart: StatedField<string>;
  solvent: StatedField<string>;
  heat: StatedField<HeatLevel>;
  freshOrDried: StatedField<string>;
  filtered: StatedField<boolean | 'not_applicable'>;
  evidenceSource: string;
  methodsSnippet: string | null;
  comparedRecipeIds: string[];
  match: { vehicle: MatchState; heat: MatchState; filtration: MatchState; part: MatchState; freshOrDried: MatchState; overall: MatchState };
}

/** Per-source breakdown for the Audit page. SITE: no_analogue appears only under audit v2. */
export interface AuditBreakdown {
  source: SourceWork;
  plants: number;
  studies: number;
  vehicle: Record<MatchState, number>;
  heat: Record<MatchState, number>;
  filtration: Record<MatchState, number>;
}

/** SITE: hypotheses are species-level profile gaps (contract Hypothesis), not compound-level likelihood pairs. */
export type TrailStage = 'source' | 'name' | 'preparation' | 'model' | 'audit' | 'toxicity';
export interface TrailStep {
  id: string;
  stage: TrailStage;
  title: string;
  detail: string;
  evidence: EvidenceStatus;
  heuristics?: string[];
  refs?: { label: string; href?: string }[];
}
export interface Hypothesis {
  id: string;
  rank: number;
  rankedOf: number;
  rankByMedianGap: number | null;
  taxon: string;
  speciesId: string;
  indication: string;
  indicationAsWritten: string;
  faithful: { label: string; preparation: Preparation; key: string };
  modern: { label: string; preparation: Preparation } | null;
  /** 1 - cosine similarity of the two predicted compound profiles: median (point), 5th and 95th percentiles. */
  gap: LikelihoodRange;
  gapThreshold: number | null;
  pGapAboveThreshold: number | null;
  compoundsUsed: number | null;
  compoundsExcludedWide: number | null;
  rule: string | null;
  attestation: { source: SourceWork; recipes: number }[];
  attestationCount: number;
  caveats: string[];
  toxicity: ToxicityRecord;
  evidence: EvidenceStatus;
  trail: TrailStep[];
}

/** contract: validation.json */
export interface PipelineStage {
  id: string;
  name: string;
  does: string;
  tool: string | null;
  validation: EvidenceStatus;
}
export interface MetricValue {
  point: number | null;
  low: number | null;
  high: number | null;
  unit: string;
}
export interface Metric {
  id: string;
  stage: string;
  name: string;
  value: MetricValue;
  n: number | null;
  evidence: EvidenceStatus;
  note?: string;
}
export interface MethodComparison {
  id: string;
  question: string;
  /** The pre-registered check this comparison answers (PreregisteredCheck.id), if any. */
  preregisteredId?: string;
  /** "lower is better" or "higher is better" — drawn on the chart. */
  direction: 'lower_better' | 'higher_better';
  methods: { name: string; value: MetricValue }[];
  finding: string;
  decision: string;
  evidence: EvidenceStatus;
}
export interface PositiveControl {
  id: string;
  preregisteredId?: string;
  taxon: string;
  compound: string;
  /** SITE: optional; the contract's artemisinin check carries no structured ranges, so none are drawn. */
  a?: { label: string; preparation: Preparation; likelihood: LikelihoodRange };
  b?: { label: string; preparation: Preparation; likelihood: LikelihoodRange };
  expected: string;
  outcome: CheckOutcome;
  explanation: string;
  evidence: EvidenceStatus;
}
/** SITE: 'reported' = a result exists in site-data but is not graded pass/fail there. */
export type CheckOutcome = 'pass' | 'fail' | 'borderline' | 'not_run' | 'reported';
export interface PreregisteredCheck {
  id: string;
  /** ISO date the criterion was fixed. null = unknown. */
  registeredOn: string | null;
  criterion: string;
  outcome: CheckOutcome;
  detail: string;
  evidence: EvidenceStatus;
}
export interface Validation {
  pipeline: PipelineStage[];
  metrics: Metric[];
  comparisons: MethodComparison[];
  positiveControls: PositiveControl[];
  preregistered: PreregisteredCheck[];
  limitations: string[];
}

/** contract: sources.json */
export type SourceRole = 'historical text' | 'translation' | 'taxonomy' | 'literature' | 'chemistry' | 'toxicity' | 'software';
export interface SourceRecord {
  id: string;
  title: string;
  role: SourceRole;
  edition: string | null;
  year: string | null;
  licence: string | null;
  /** Has a person checked the licence terms? */
  licenceEvidence: EvidenceStatus;
  url: string | null;
  note?: string;
}
export interface DownloadFile {
  file: string;
  contract: string;
  description: string;
  format: 'json' | 'csv';
  licence: string | null;
}
export interface SourcesFile {
  sources: SourceRecord[];
  downloads: DownloadFile[];
}

/* ───────────────────────── v2 additions ───────────────────────── */

/** Evidence gap: how often modern studies state each preparation detail.
 *  SITE: built from metrics.reportingGap (contract v1.6, P37b), not a separate file. The fields are the audit's five
 *  coded variables; `inflated` marks the solvent share, which is inflated by construction in the prepared set. */
export type ReportingField = 'solvent' | 'part' | 'heat' | 'freshOrDried' | 'filtration';
export interface ReportingGapRow {
  field: ReportingField;
  label: string;
  stated: number;
  n: number;
  /** 95% Wilson interval for the share stated. null = not computed. */
  ci: [number, number] | null;
  evidence: EvidenceStatus;
  inflated: boolean;
  note: string | null;
}
export interface ReportingGapView {
  headline: { field: ReportingField; text: string };
  method: string;
  rows: ReportingGapRow[];
  /** SITE: the share stating none of the five details (same set). */
  none: ReportingGapRow | null;
  /** SITE: the other study sets (all retrieved studies; heat by coding source) and the v3 screening. */
  extra: { label: string; stated: number; n: number; ci: [number, number] | null; note: string | null }[];
}

/** Botanical plate (contract v1.8, P39: site-data/plates.json).
 *  SITE: the image is a set of optimised, locally served files (AVIF + WebP at several widths, explicit size), never a
 *  hotlinked Commons URL; author, date and the Commons licence travel with it. */
export interface PlateImage {
  avif: string;
  webp: string;
  src: string;
  width: number;
  height: number;
}
export interface Plate {
  taxon: string;
  caption: string;
  /** 'sourced' = file chosen and its licence read from Commons by script; 'confirmed' = a person checked it. */
  status: 'to_source' | 'sourced' | 'confirmed';
  licence: string | null;
  host: 'Wikimedia Commons' | null;
  fileUrl: string | null;
  imageUrl: string | null;
  author: string | null;
  date: string | null;
  work: string | null;
  image: PlateImage | null;
}

/** Lab Planner (placeholder until the quantum feature ships). SITE: derived from hypotheses.json; rankRange is null
 *  because the ranking records no rank interval, and readout/effort are not decided anywhere in the data. */
export interface LabPlanItem {
  id: string;
  hypothesisId: string;
  title: string;
  compares: [string, string];
  readout: string | null;
  effort: 'low' | 'medium' | 'high' | null;
  rank: number;
  rankRange: [number, number] | null;
  quantumScore: LikelihoodRange | null;
}
export interface LabPlanFile {
  feature: { name: string; status: 'coming_soon' | 'available'; release: string | null; description: string };
  items: LabPlanItem[];
}

/** contract: coverage.json — Home counts. */
export interface Coverage {
  nameResolutions: Record<EvidenceStatus, number>;
  recipes: number;
  studies: number;
}
