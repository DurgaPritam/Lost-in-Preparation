/** One function per page, assembling validated contract data through the selectors. Imported by the server-only facade
 *  (site.ts) for pages, and by scripts/prepare-data.ts for the files that pages load on demand. */
import type {
  CompoundEstimate, DownloadFile, LikelihoodRange, NameResolution, Plate, Recipe, SourceConfidence, SourceRecord, SourceWork, SourcesFile,
  ToxicityRecord,
} from '../types';
import { compareRanges } from './format';
import { HEURISTICS } from './heuristics';
import * as L from './load';
import { plantKeyOf } from './selectors/atlas';
import { auditView, breakdowns } from './selectors/audit';
import { caseView } from './selectors/caseStudy';
import { mostSevere, sourceConfidence, toxicityCategory, toxicityFromIndex } from './selectors/common';
import { toReportingGap } from './selectors/gap';
import { coverage } from './selectors/home';
import { hypothesisId, toHypothesis } from './selectors/hypotheses';
import { labHref, type LabHeat, type LabSolvent } from './selectors/lab';
import { toValidation } from './selectors/methods';
import { quantumSummary, toPanelView } from './selectors/labPanel';
import { plateFor, toPlate } from './selectors/plates';
import { groupSpecies, recipeSlug, toRecipe, toSummary } from './selectors/recipes';

export type Confidences = Record<SourceWork, SourceConfidence>;
export function confidences(): Confidences {
  const nr = L.loadMetrics().nameResolution;
  return { culpeper_1652: sourceConfidence('culpeper_1652', nr), culpeper_1850: sourceConfidence('culpeper_1850', nr), pliny_nh: sourceConfidence('pliny_nh', nr) };
}
const speciesName = () => {
  const m = new Map(L.loadProfileIndex().map((e) => [e.speciesId, e.acceptedName]));
  for (const s of L.loadSpecies()) if (s.wfoId && s.acceptedName && !m.has(s.wfoId)) m.set(s.wfoId, s.acceptedName);
  return (id: string) => m.get(id) ?? id;
};
export const plates = (): Plate[] => L.loadPlates().map(toPlate);

/* ───────── Lab ───────── */

export interface LabPlant { speciesId: string; taxon: string; compounds: number; toxicity: ToxicityRecord; plate: Plate | null }
/** The Lab opens on this species unless the URL names another: no toxicity reported, a sourced plate, and volatile oils,
 *  so cold water and a decoction differ visibly. (Liquorice, the design's default, has toxicity reported here.) */
export const LAB_DEFAULT_TAXON = 'Salvia sclarea';
export function labPlants(): LabPlant[] {
  const ps = plates();
  return L.loadProfileIndex().map((e) => ({
    speciesId: e.speciesId, taxon: e.acceptedName, compounds: e.compounds, toxicity: toxicityFromIndex(e), plate: plateFor(ps, e.acceptedName),
  })).sort((a, b) => a.taxon.localeCompare(b.taxon));
}
/** Genus-only names in the recipes: the Lab's "no species-level profile" state names them. */
export function genusOnlyNames(): string[] {
  return [...new Set(recipes().filter((r) => r.name.state === 'genus_only').map((r) => r.name.candidates[0]?.taxon).filter((x): x is string => !!x))].sort();
}
export function getLab() {
  const plants = labPlants();
  return { plants, genusOnly: genusOnlyNames(), heuristics: HEURISTICS, defaultTaxon: plants.some((p) => p.taxon === LAB_DEFAULT_TAXON) ? LAB_DEFAULT_TAXON : plants[0]?.taxon ?? '' };
}

/* ───────── Recipes / Atlas ───────── */

let _recipes: Recipe[] | null = null;
function recipes(): Recipe[] {
  if (!_recipes) {
    const inp = { species: L.loadSpecies(), index: L.loadProfileIndex(), sources: L.loadSources() };
    const by = groupSpecies(inp.species);
    _recipes = L.loadRecipes().map((r) => toRecipe(r, inp, by));
    const slugs = new Set(_recipes.map((r) => recipeSlug(r.id)));
    if (slugs.size !== _recipes.length) throw new Error('recipe slugs are not unique');
  }
  return _recipes;
}
export const recipeSlugs = () => recipes().map((r) => recipeSlug(r.id));
export const getRecipeSummaries = () => recipes().map(toSummary);


export interface AtlasRecipeLink { slug: string; source: SourceWork; vehicle: string }
export interface AtlasPlant {
  key: string; name: NameResolution; recipes: Record<SourceWork, number>; toxicity: ToxicityRecord; plate: Plate | null;
  href: string; links: AtlasRecipeLink[]; total: number; disputed: boolean;
}
/** Plant cards for the Atlas's first screen; the recipe list used by search and filters loads with the page's data. */
export function atlasPlants(): AtlasPlant[] {
  const ps = plates();
  const groups = new Map<string, Recipe[]>();
  for (const r of recipes()) { const k = plantKeyOf(r.name); groups.set(k, [...(groups.get(k) ?? []), r]); }
  return [...groups.entries()].map(([key, rs]) => {
    const r0 = rs[0];
    const count = (w: SourceWork) => rs.filter((x) => x.source === w).length;
    return {
      key, name: r0.name, recipes: { culpeper_1652: count('culpeper_1652'), culpeper_1850: count('culpeper_1850'), pliny_nh: count('pliny_nh') },
      toxicity: mostSevere(rs.map((x) => x.toxicity)), plate: r0.name.state === 'disputed' ? null : plateFor(ps, r0.name.candidates[0]?.taxon),
      href: `/recipes/${recipeSlug(r0.id)}/`, links: rs.map((x) => ({ slug: recipeSlug(x.id), source: x.source, vehicle: x.preparation.vehicle })),
      total: rs.length, disputed: r0.name.state === 'disputed',
    };
  }).sort((a, b) => b.total - a.total || a.key.localeCompare(b.key));
}
export const getAtlas = () => ({ plants: atlasPlants(), total: recipes().length, confidences: confidences() });

/** A recipe page: the recipe, its plate, its source confidence, and Lab links built only from stated fields, one per
 *  species candidate that has a profile; none for a plant with toxicity reported (acceptance check 5). */
export function getRecipe(slug: string) {
  const r = recipes().find((x) => recipeSlug(x.id) === slug);
  if (!r) return null;
  const plants = labPlants();
  const p = r.preparation;
  const solvent = (['water', 'wine', 'vinegar', 'oil', 'honey'] as const).find((s) => s === p.vehicle);
  const heat = p.heat === 'cold' || p.heat === 'warm' || p.heat === 'boiled' ? (p.heat as LabHeat) : undefined;
  const labLinks = r.name.state === 'unresolved' ? [] : r.name.candidates.flatMap((c, i) => {
    const plant = plants.find((x) => x.taxon === c.taxon);
    if (!plant || plant.toxicity.category === 'toxic_reported' || r.toxicity.category === 'toxic_reported' || c.rank !== 'species') return [];
    const q: Parameters<typeof labHref>[0] = { plant: c.taxon };
    if (solvent) { q.solvent = solvent as LabSolvent; q.acidified = solvent === 'vinegar'; }
    if (heat) q.heat = heat;
    if (p.filtered === true || p.filtered === false) q.filtered = p.filtered;
    return [{ taxon: c.taxon, href: labHref(q), index: i + 1, of: r.name.candidates.length, stated: { solvent: !!solvent, heat: !!heat, filtered: p.filtered === true || p.filtered === false } }];
  });
  return { recipe: r, plate: r.name.state === 'disputed' ? null : plateFor(plates(), r.name.candidates[0]?.taxon), confidence: confidences()[r.source], labLinks };
}

/* ───────── Evidence gap ───────── */

export type AuditVersion = 'v1' | 'v2';
const auditOf = (v: AuditVersion) => auditView(v === 'v1' ? L.loadAudit() : L.loadAuditV2(), speciesName());
/** Study rows per audit version: written to public/data/audit-studies-<v>.json and loaded when the table is shown. */
export const getAuditStudies = (v: AuditVersion) => auditOf(v).rows;
export function getAudit() {
  const v1 = auditOf('v1');
  const v2 = auditOf('v2');
  const m = L.loadMetrics();
  return { v1: { breakdowns: breakdowns(v1.units), units: v1.units.length, rows: v1.rows.length },
           v2: { breakdowns: breakdowns(v2.units), units: v2.units.length, rows: v2.rows.length },
           headline: m.headlineMatchRate, auditV2: m.auditV2 ?? null, confidences: confidences() };
}
export function getGap() {
  return { gap: toReportingGap(L.loadMetrics()), audit: getAudit() };
}

/* ───────── Hypotheses, Planner ───────── */

export function getHypotheses() {
  const hs = [...L.loadHypotheses()].sort((a, b) => a.rank - b.rank);
  const idx = L.loadProfileIndex();
  return hs.map((h) => {
    const e = idx.find((x) => x.speciesId === h.speciesId);
    return toHypothesis(h, { index: idx, audit: L.loadAudit(), profiles: e ? L.loadProfile(e.file) : [], rankedOf: hs.length });
  });
}
/** SITE: the Planner shows the re-test panel (lab_panel.json, P40 + v2), not the hypothesis list (design proposal approved 2026-11-07). */
export function getPanel() {
  const lp = L.loadLabPanel();
  if (!lp) return null;
  const idx = L.loadProfileIndex();
  const ids = new Set(recipes().map((r) => r.id));
  return toPanelView(lp, (speciesId) => toxicityFromIndex(idx.find((x) => x.speciesId === speciesId)),
    (rid) => (ids.has(rid) ? `/recipes/${recipeSlug(rid)}/` : null));
}
export function getPlanner() {
  return { panel: getPanel(), heuristics: HEURISTICS };
}

/* ───────── Case study ───────── */

export interface CaseFigure { label: string; compareLabel: string; shown: number; total: number; rows: { compound: string; compoundClass: string; a: LikelihoodRange; b: LikelihoodRange }[] }
/** Compounds of two published profiles side by side: the `n` whose ranges separate most (largest gap between the
 *  ranges; overlapping ranges rank last). The figure says how many it shows of how many. */
function figure(sid: string, aLabel: string, bLabel: string, n = 5): CaseFigure | null {
  const e = L.loadProfileIndex().find((x) => x.speciesId === sid);
  if (!e) return null;
  const ps = L.loadProfile(e.file);
  const a = ps.find((p) => p.preparationLabel === aLabel);
  const b = ps.find((p) => p.preparationLabel === bLabel);
  if (!a || !b) return null;
  const rows = a.compounds.map((c, i) => {
    const d = b.compounds[i];
    const ra = { low: c.low, high: c.high, point: c.likelihood };
    const rb = { low: d.low, high: d.high, point: d.likelihood };
    const v = compareRanges(ra, rb);
    const sep = v === 'a' ? c.low - d.high : v === 'b' ? d.low - c.high : -1;
    return { compound: c.name, compoundClass: c.class, a: ra, b: rb, sep };
  }).sort((x, y) => y.sep - x.sep || x.compound.localeCompare(y.compound));
  return { label: aLabel, compareLabel: bLabel, shown: Math.min(n, rows.length), total: rows.length, rows: rows.slice(0, n).map(({ sep: _s, ...r }) => r) };
}

export function getCase() {
  const c = L.loadCaseStudies()[0];
  if (!c) return null;
  const hs = getHypotheses();
  const h = hs.find((x) => x.speciesId === c.speciesId && x.indication === c.indication.label) ?? null;
  const e = L.loadProfileIndex().find((x) => x.speciesId === c.speciesId);
  const rec = recipes().find((r) => r.id === c.primaryRecipeId) ?? null;
  const panel = getPanel();
  return {
    ...caseView(c, L.loadRecipes()), taxon: e?.acceptedName ?? c.speciesId, toxicity: toxicityFromIndex(e),
    plate: plateFor(plates(), e?.acceptedName), recipe: rec, recipeHref: rec ? `/recipes/${recipeSlug(rec.id)}/` : null,
    confidence: rec ? confidences()[rec.source] : null, hypothesis: h,
    plannerRank: panel?.sizes.find((z) => z.k === panel.defaultK)?.entries.find((x) => x.speciesId === c.speciesId)?.position ?? null,
    withheldFromPlanner: !!panel?.excludedToxic.some((x) => x.species === e?.acceptedName),
    before: figure(c.speciesId, c.before.faithful, c.before.modern),
    after: figure(c.speciesId, c.after.faithful, c.after.modern),
    toxicReported: toxicityCategory(e?.toxicityFlag) === 'toxic_reported',
  };
}

/* ───────── Landing ───────── */

export function getLanding() {
  const plants = labPlants();
  const demo = plants.find((p) => p.taxon === LAB_DEFAULT_TAXON) ?? plants.find((p) => p.toxicity.category === 'no_toxicity_reported') ?? plants[0];
  const ps = plates();
  const c = L.loadCaseStudies()[0];
  // The three "ways in" cards show sourced plates of plants with no toxicity reported, so no card pictures a toxic plant
  // next to an invitation.
  const calm = plants.filter((p) => p.plate?.image && p.toxicity.category === 'no_toxicity_reported');
  return {
    demo, gap: toReportingGap(L.loadMetrics()), confidences: confidences(),
    pathPlates: [calm[1] ?? calm[0], demo, calm[2] ?? calm[0]].map((p) => (p ? { taxon: p.taxon, plate: p.plate } : null)),
    caseTitle: c?.title ?? null, plateCount: ps.filter((p) => p.image).length,
  };
}

/* ───────── Docs ───────── */

export const getValidation = () => toValidation(L.loadMetrics());

const DOWNLOADS: Omit<DownloadFile, 'licence'>[] = [
  { file: 'recipes.json', contract: 'recipes.schema.json', description: 'Every extracted recipe, with verbatim quotes, provenance and logged corrections.', format: 'json' },
  { file: 'species.json', contract: 'species.schema.json', description: 'Species candidates for each recipe’s plant name, with confidence, basis and disputed flags.', format: 'json' },
  { file: 'profiles/index.json', contract: 'profiles.index.schema.json', description: 'The species with predicted extraction profiles, with their toxicity entries.', format: 'json' },
  { file: 'audit.json', contract: 'audit.schema.json', description: 'Audit v1, as pre-registered: how modern studies prepared each plant for each use.', format: 'json' },
  { file: 'audit_v2.json', contract: 'audit_v2.schema.json', description: 'Audit v2, the pre-registered re-analysis after v1’s design flaw.', format: 'json' },
  { file: 'hypotheses.json', contract: 'hypotheses.schema.json', description: 'Ranked hypotheses worth re-testing, with caveats and evidence trails.', format: 'json' },
  { file: 'case_studies.json', contract: 'case_studies.schema.json', description: 'Documented extraction corrections and their effect on the ranking.', format: 'json' },
  { file: 'metrics.json', contract: 'metrics.schema.json', description: 'Every metric with its interval, n and source file, including the reporting gap.', format: 'json' },
  { file: 'sources.json', contract: 'sources.schema.json', description: 'The digitised historical sources, with checksums and licences.', format: 'json' },
  { file: 'engine/model.json', contract: 'engine.model.schema.json', description: 'The preparation model’s parameters and uncertainty settings, for the in-browser engine.', format: 'json' },
  { file: 'plates.json', contract: 'plates.schema.json', description: 'Botanical plates: Commons file, author, date and licence as stated on Commons.', format: 'json' },
];
export function getSources(): SourcesFile {
  const sources: SourceRecord[] = L.loadSources().map((s) => ({
    id: s.id, title: s.title, role: s.translator ? 'translation' : 'historical text', edition: `${s.author}${s.translator ? `, trans. ${s.translator}` : ''}`,
    year: String(s.editionYear), licence: s.licence, licenceEvidence: s.licenceVerified ? 'provisional' : 'pending', url: s.url, note: s.licenceNote ?? undefined,
  }));
  return { sources, downloads: DOWNLOADS.map((d) => ({ ...d, licence: d.file === 'plates.json' ? 'Public domain images; record CC BY 4.0' : 'CC BY 4.0 (LICENSE-DATA), with the exceptions listed there' })) };
}
export function getDocs() {
  const studies = new Set(L.loadAudit().flatMap((r) => r.studies.map((s) => s.pmid))).size;
  return {
    validation: getValidation(), sources: getSources(), audit: getAudit(), heuristics: HEURISTICS, confidences: confidences(),
    hypothesesCount: L.loadHypotheses().length,
    quantum: (() => { const p = getPanel(); return p ? { ...quantumSummary(p), winners: p.winners, noise: p.noise, hardware: p.hardware, noiseModel: p.noiseModel } : null; })(),
    coverage: coverage(L.loadSpecies(), L.loadRecipes(), studies), modelledSpecies: L.loadProfileIndex().length,
  };
}

/* ───────── Credits ───────── */

export function getCredits() {
  return { plates: L.loadPlates() };
}

export type { CompoundEstimate };
export { hypothesisId };
