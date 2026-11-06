/** One function per page, assembling validated contract data through the selectors. Imported by the server-only facade
 *  (site.ts) for pages, and by scripts/prepare-data.ts for the files that pages load on demand. */
import type { DownloadFile, SourceConfidence, SourceRecord, SourceWork, SourcesFile } from '../types';
import * as L from './load';
import { auditView, breakdowns } from './selectors/audit';
import { caseView } from './selectors/caseStudy';
import { sourceConfidence, toxicityCategory } from './selectors/common';
import { prepId } from './selectors/compare';
import { coverage, reportingGap } from './selectors/home';
import { compareHref, hypothesisId, modernLabel, toHypothesis } from './selectors/hypotheses';
import { toValidation } from './selectors/methods';
import { emptySelection, facetOptions } from './selectors/recipeFacets';
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

let _recipes: ReturnType<typeof toRecipe>[] | null = null;
function recipes() {
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
export const getRecipe = (slug: string) => recipes().find((r) => recipeSlug(r.id) === slug) ?? null;
export const getRecipeSummaries = () => recipes().map(toSummary);
/** The explorer's first screen, rendered statically; the full list (public/data/recipe-index.json) loads after it. */
export function getRecipeExplorer(first: number) {
  const all = getRecipeSummaries();
  return { initial: all.slice(0, first), total: all.length, initialOptions: facetOptions(all, '', emptySelection()), confidences: confidences() };
}

export function getHome() {
  const a1 = L.loadAudit();
  const studies = new Set(a1.flatMap((r) => r.studies.map((s) => s.pmid))).size;
  return { coverage: coverage(L.loadSpecies(), L.loadRecipes(), studies), confidences: confidences(), gap: reportingGap(L.loadMetrics()) };
}

export function getCompareIndex() {
  const idx = L.loadProfileIndex();
  // Default: the top-ranked hypothesis whose plant is not toxic_reported (a toxic plant is never offered as a Compare entry point).
  const top = [...L.loadHypotheses()].sort((a, b) => a.rank - b.rank)
    .find((h) => toxicityCategory(idx.find((x) => x.speciesId === h.speciesId)?.toxicityFlag ?? h.toxicityFlag) !== 'toxic_reported');
  let def: { species: string; a?: string; b?: string } = { species: idx[0]?.speciesId ?? '' };
  if (top) {
    const e = idx.find((x) => x.speciesId === top.speciesId);
    if (e) {
      const ps = L.loadProfile(e.file);
      const a = ps.find((p) => p.preparationLabel === top.faithfulPreparationText);
      const b = ps.find((p) => p.preparationLabel === modernLabel(top));
      def = { species: e.speciesId, a: a ? prepId(a) : undefined, b: b ? prepId(b) : undefined };
    }
  }
  return { species: idx.map((e) => ({ speciesId: e.speciesId, taxon: e.acceptedName })).sort((x, y) => x.taxon.localeCompare(y.taxon)), default: def };
}

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

export function getHypotheses() {
  const hs = [...L.loadHypotheses()].sort((a, b) => a.rank - b.rank);
  const idx = L.loadProfileIndex();
  return hs.map((h) => {
    const e = idx.find((x) => x.speciesId === h.speciesId);
    return toHypothesis(h, { index: idx, audit: L.loadAudit(), profiles: e ? L.loadProfile(e.file) : [], rankedOf: hs.length });
  });
}
export const hypothesisIds = () => L.loadHypotheses().map(hypothesisId);
export const getHypothesis = (id: string) => getHypotheses().find((h) => h.id === id) ?? null;

export const getValidation = () => toValidation(L.loadMetrics());

const DOWNLOADS: Omit<DownloadFile, 'licence'>[] = [
  { file: 'recipes.json', contract: 'recipes.schema.json', description: 'Every extracted recipe, with verbatim quotes, provenance and logged corrections.', format: 'json' },
  { file: 'species.json', contract: 'species.schema.json', description: 'Species candidates for each recipe’s plant name, with confidence, basis and disputed flags.', format: 'json' },
  { file: 'profiles/index.json', contract: 'profiles.index.schema.json', description: 'The species with predicted extraction profiles, with their toxicity entries.', format: 'json' },
  { file: 'audit.json', contract: 'audit.schema.json', description: 'Audit v1, as pre-registered: how modern studies prepared each plant for each use.', format: 'json' },
  { file: 'audit_v2.json', contract: 'audit_v2.schema.json', description: 'Audit v2, the pre-registered re-analysis after v1’s design flaw.', format: 'json' },
  { file: 'hypotheses.json', contract: 'hypotheses.schema.json', description: 'Ranked hypotheses worth re-testing, with caveats and evidence trails.', format: 'json' },
  { file: 'case_studies.json', contract: 'case_studies.schema.json', description: 'Documented extraction corrections and their effect on the ranking.', format: 'json' },
  { file: 'metrics.json', contract: 'metrics.schema.json', description: 'Every metric with its interval, n and source file.', format: 'json' },
  { file: 'sources.json', contract: 'sources.schema.json', description: 'The digitised historical sources, with checksums and licences.', format: 'json' },
];
export function getSources(): SourcesFile {
  const sources: SourceRecord[] = L.loadSources().map((s) => ({
    id: s.id, title: s.title, role: s.translator ? 'translation' : 'historical text', edition: `${s.author}${s.translator ? `, trans. ${s.translator}` : ''}`,
    year: String(s.editionYear), licence: s.licence, licenceEvidence: s.licenceVerified ? 'provisional' : 'pending', url: s.url, note: s.licenceNote ?? undefined,
  }));
  return { sources, downloads: DOWNLOADS.map((d) => ({ ...d, licence: null })) };
}

export function getCase() {
  const c = L.loadCaseStudies()[0];
  if (!c) return null;
  const h = L.loadHypotheses().find((x) => x.speciesId === c.speciesId && x.indication?.meshId === c.indication.meshId);
  const e = L.loadProfileIndex().find((x) => x.speciesId === c.speciesId);
  return { ...caseView(c, L.loadRecipes()), hypothesisHref: h ? `/hypotheses/${hypothesisId(h)}/` : null, taxon: e?.acceptedName ?? c.speciesId,
           toxicity: e ? { flag: e.toxicityFlag, note: e.toxicityNote, ev: e.toxicityEvidence } : null,
           // Acceptance check 5: no Compare link for a toxic_reported plant.
           compareHref: h && e && toxicityCategory(e.toxicityFlag) !== 'toxic_reported' ? compareHref(c.speciesId, L.loadProfile(e.file), c.after.faithful, c.after.modern) : null,
           beforeCompareHref: h && e && toxicityCategory(e.toxicityFlag) !== 'toxic_reported' ? compareHref(c.speciesId, L.loadProfile(e.file), c.before.faithful, c.before.modern) : null };
}
