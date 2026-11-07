/**
 * PLACEHOLDER DATA SHAPES.
 * The project's JSON Schemas were not attached in Phase 1, so these types are
 * the design system's assumptions. When the schemas arrive, replace this file
 * with types generated from them (e.g. json-schema-to-typescript) and adapt
 * the small mapping functions at the top of each honesty component. Every
 * component takes these narrow props, not whole records, to keep that cheap.
 */

/** 1. Evidence status */
export type EvidenceStatus = 'validated' | 'provisional' | 'pending';

/** 2. Source confidence */
export type SourceWork = 'culpeper_1652' | 'pliny_nh';
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
export type Vehicle =
  | 'cold_infusion'
  | 'decoction'
  | 'wine'
  | 'vinegar'
  | 'oil'
  | 'ethanol_extract'
  | 'methanol_extract'
  | 'aqueous_extract'
  | 'hydrodistillation'
  /** v2 (additive): plain water at any heat, and honey (incl. oxymel-like preparations). */
  | 'water'
  | 'honey'
  | 'unknown';
export interface Preparation {
  family: PreparationFamily;
  vehicle: Vehicle;
  /** null = not stated in the source. Rendered as Unknown, never as "no". */
  filtered: boolean | null;
  /** v2 (additive, optional): acid added or inherent (vinegar). null = not stated. */
  acidified?: boolean | null;
  /** Added in Phase 2. null = not stated. */
  heat?: HeatLevel | null;
  /** Free text as normalised, e.g. "3 days". null = not stated. */
  duration?: string | null;
}

/* ───────────────────────── Phase 2 additions (still assumed) ───────────────────────── */

export type HeatLevel = 'cold' | 'warm' | 'boiled' | 'reflux';

/** A field the pipeline extracted from a passage, anchored to character offsets. */
export type ExtractedFieldKind = 'plant' | 'part' | 'vehicle' | 'quantity' | 'heat' | 'duration' | 'filtration';
export interface ExtractedField {
  id: string;
  kind: ExtractedFieldKind;
  /** [start, end) offsets into Passage.text. */
  start: number;
  end: number;
  /** Normalised value, e.g. "wine", "3 days". null = could not normalise. */
  value: string | null;
  evidence: EvidenceStatus;
}
/** A stretch of the transcription that is illegible. Rendered as ⟦?⟧. */
export interface IllegibleSpan {
  id: string;
  /** Offset where the marker is placed in Passage.text (text holds no placeholder). */
  at: number;
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
  origin: { kind: 'recipe'; recipeId: string; source: SourceWork } | { kind: 'study'; citation: string };
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
export type MatchState = 'matches' | 'differs' | 'not_stated';

/** contract: studies.json — one modern study that prepared a plant we track. */
export interface Study {
  id: string;
  /** PubMed ID. null = not indexed in PubMed. */
  pmid: string | null;
  title: string;
  year: number | null;
  taxon: string;
  plantPart: StatedField<string>;
  solvent: StatedField<string>;
  heat: StatedField<HeatLevel>;
  duration: StatedField<string>;
  filtered: StatedField<boolean>;
  /** Plant-to-solvent ratio as reported, e.g. "1:10 w/v". */
  ratio: StatedField<string>;
  /** v2 (additive, optional): fresh or dried plant material. */
  material?: StatedField<'fresh' | 'dried'>;
  /** Recipes whose historical preparation this study is compared against. */
  comparedRecipeIds: string[];
  /** How this study's preparation compares with the historical one. */
  match: { vehicle: MatchState; heat: MatchState; filtration: MatchState };
}

/** contract: audit_summary.json — per-source breakdown for the Audit page. */
export interface AuditBreakdown {
  source: SourceWork;
  plants: number;
  studies: number;
  vehicle: Record<MatchState, number>;
  heat: Record<MatchState, number>;
  filtration: Record<MatchState, number>;
}

/** contract: hypotheses.json */
export type TrailStage = 'source' | 'name' | 'preparation' | 'model' | 'audit' | 'toxicity';
export interface TrailStep {
  id: string;
  stage: TrailStage;
  title: string;
  detail: string;
  evidence: EvidenceStatus;
  /** Heuristic ids applied at this step (see heuristics.json). */
  heuristics?: string[];
  refs?: { label: string; href?: string }[];
}
export interface Hypothesis {
  id: string;
  rank: number;
  /** Ranks consistent with the uncertainty, e.g. [1, 3]. */
  rankRange: [number, number];
  taxon: string;
  compound: string;
  compoundClass: string;
  /** The preparation as the source describes it. */
  faithful: { label: string; preparation: Preparation };
  /** The preparation most modern studies used. */
  modern: { label: string; preparation: Preparation };
  historicalLikelihood: LikelihoodRange;
  modernLikelihood: LikelihoodRange;
  /** Number of recipes attesting the faithful preparation, per source. */
  attestation: { source: SourceWork; recipes: number }[];
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
  a: { label: string; preparation: Preparation; likelihood: LikelihoodRange };
  b: { label: string; preparation: Preparation; likelihood: LikelihoodRange };
  expected: string;
  outcome: 'pass' | 'fail' | 'borderline';
  explanation: string;
  evidence: EvidenceStatus;
}
export type CheckOutcome = 'pass' | 'fail' | 'borderline' | 'not_run';
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

/* ───────────────────────── v2 additions (additive; existing files unchanged) ───────────────────────── */

/** contract: reporting_gap.json — how often modern studies state each preparation detail. */
export type ReportingField = 'solvent' | 'plant_part' | 'heat' | 'duration' | 'ratio' | 'material' | 'filtration';
export interface ReportingGapRow {
  field: ReportingField;
  label: string;
  /** Studies that state this detail. */
  stated: number;
  /** Studies assessed for this detail. */
  n: number;
  /** 95% interval for the proportion stated (Wilson). null = not computed. */
  ci: [number, number] | null;
  evidence: EvidenceStatus;
}
export interface ReportingGapFile {
  headline: { field: ReportingField; text: string };
  method: string;
  rows: ReportingGapRow[];
}

/** contract: plates.json — illustration slots. Every image carries its licence. */
export interface Plate {
  taxon: string;
  /** e.g. "Glycyrrhiza glabra, from a 19th-century medicinal-plant atlas". */
  caption: string;
  /** 'to_source' = slot designed, file not chosen yet; 'confirmed' = licence checked by a person. */
  status: 'to_source' | 'sourced' | 'confirmed';
  licence: 'Public domain' | null;
  host: 'Wikimedia Commons' | null;
  /** Commons file page (for attribution and licence). */
  fileUrl: string | null;
  /** Direct image URL once sourced; null renders the drawn placeholder. */
  imageUrl: string | null;
}

/** contract: lab_plan.json — Lab Planner (placeholder until the quantum feature ships). */
export interface LabPlanItem {
  id: string;
  hypothesisId: string;
  title: string;
  compares: [string, string];
  /** What the lab would measure. null = not decided. */
  readout: string | null;
  effort: 'low' | 'medium' | 'high' | null;
  rank: number;
  rankRange: [number, number];
  /** Quantum-informed priority. Always null until the feature ships. */
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
