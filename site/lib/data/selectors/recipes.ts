/** Contract recipes (+ species candidates, profile index, sources) → the design's Recipe / RecipeSummary. */
import type { ExtractedField, ExtractedFieldKind, IllegibleSpan, NameResolution, Preparation, Recipe, RecipeSummary, SpeciesCandidate } from '../../types';
import { vehicleLabel } from '../format';
import type { ContractProfileIndex, ContractRecipe, ContractSource, ContractSpecies } from '../load';
import { candidateEvidence, mostSevere, recipeEvidence, sourceWork, toxicityFromIndex } from './common';

/** Contract evidence key → extracted-field kind, and how its normalised value is read from the recipe. */
const FIELD_OF: { key: string; kind: ExtractedFieldKind; value: (r: ContractRecipe) => string | null }[] = [
  { key: 'plantNameAsWritten', kind: 'plant', value: (r) => known(r.plantNameAsWritten) },
  { key: 'part', kind: 'part', value: (r) => human(r.part) },
  { key: 'freshOrDried', kind: 'freshOrDried', value: (r) => human(r.freshOrDried) },
  { key: 'solvent', kind: 'vehicle', value: (r) => vehicleLabel(r.solvent.join('+')) },
  { key: 'heat', kind: 'heat', value: (r) => human(r.heat) },
  { key: 'durationText', kind: 'duration', value: (r) => known(r.durationText) },
  { key: 'filtered', kind: 'filtration', value: (r) => human(r.filtered) },
  { key: 'process', kind: 'process', value: (r) => human(r.process) },
  { key: 'form', kind: 'form', value: (r) => human(r.form) },
  { key: 'indicationAsWritten', kind: 'indication', value: (r) => known(r.indicationAsWritten) },
];
const known = (v: string | null | undefined) => (v == null || v === 'unknown' ? null : v);
const human = (v: string | null | undefined) => (known(v) == null ? null : (v as string).replace(/_/g, ' '));

export function preparationOf(r: Pick<ContractRecipe, 'solvent' | 'heat' | 'filtered' | 'durationText'>): Preparation {
  const vehicles = r.solvent.filter((s) => s !== 'unknown');
  return {
    family: 'historical',
    vehicle: vehicles.length ? vehicles.join('+') : 'unknown',
    heat: r.heat === 'unknown' ? null : (r.heat as Preparation['heat']),
    filtered: r.filtered === 'yes' ? true : r.filtered === 'no' ? false : r.filtered === 'not_applicable' ? 'not_applicable' : null,
    duration: known(r.durationText),
  };
}

/** Illegible or non-transcribed stretches: the transcription keeps markers like ⟦?⟧ / ⟦??⟧ / ⟦foreign⟧ in the text. */
export function illegibleSpans(text: string): IllegibleSpan[] {
  const out: IllegibleSpan[] = [];
  for (const m of text.matchAll(/⟦([^⟧]*)⟧/g)) {
    const inner = m[1];
    out.push({ id: `ill-${m.index}`, at: m.index!, end: m.index! + m[0].length, estChars: null,
               note: /^\?+$/.test(inner) ? 'Marked as illegible in the transcription.' : `Not transcribed in the source text (${inner}).` });
  }
  return out;
}

/** Fields with verbatim offsets. Spans that overlap one already drawn are kept for the table but not drawn inline. */
export function extractedFields(r: ContractRecipe, evidence: ExtractedField['evidence']): ExtractedField[] {
  const raw: ExtractedField[] = [];
  for (const f of FIELD_OF) {
    const v = f.value(r);
    const quotes = (r.evidence[f.key] ?? []) as { quote: string; start: number; end: number; inHeading?: boolean }[];
    if (v == null || !quotes.length) continue;
    quotes.forEach((q, i) => raw.push({
      id: `${f.key}-${i}`, kind: f.kind, start: q.inHeading ? -1 : q.start, end: q.inHeading ? -1 : q.end, value: v, evidence,
      // SITE: the long use-as-written span is listed in the table, not drawn: a span button cannot wrap inline.
      inline: !q.inHeading && f.kind !== 'indication', quote: q.quote,
    }));
  }
  const taken: [number, number][] = [];
  const byStart = [...raw].filter((f) => f.inline).sort((a, b) => a.start - b.start || b.end - a.end);
  for (const f of byStart) {
    if (taken.some(([s, e]) => f.start < e && s < f.end)) { f.inline = false; continue; }
    taken.push([f.start, f.end]);
  }
  return raw;
}

export interface RecipeInputs {
  species: ContractSpecies[];
  index: ContractProfileIndex[];
  sources: ContractSource[];
}

export function nameResolution(r: ContractRecipe, cands: ContractSpecies[]): NameResolution {
  const sorted = [...cands].sort((a, b) => a.id.localeCompare(b.id));
  const candidates: SpeciesCandidate[] = sorted.map((c) => ({
    taxon: c.acceptedName ?? 'Unresolved', rank: 'species', confidence: { low: null, high: null, point: c.confidence }, evidence: candidateEvidence(c.basis),
  }));
  const state: NameResolution['state'] = !candidates.length ? 'unresolved' : sorted.some((c) => c.disputed) ? 'disputed' : 'resolved';
  return { historicalName: r.plantNameAsWritten, source: sourceWork(r.sourceId), state, candidates };
}

function editionOf(sourceId: string, sources: ContractSource[]): string {
  const s = sources.find((x) => x.id === sourceId);
  if (!s) return sourceId;
  return `${s.author}, ${s.title}${s.translator ? `, translated by ${s.translator}` : ''} (${s.editionYear} edition)`;
}
function locatorOf(r: ContractRecipe): string {
  const l = r.passage.location;
  const where = l.book != null ? `Book ${l.book}, chapter ${l.chapter ?? '?'}` : l.entry ? `Entry “${l.entry}”` : l.part;
  const sub = l.book != null && l.entry ? ` · ${l.entry}` : l.subsection ? ` · ${l.subsection}` : '';
  return `${where}${sub} · lines ${l.lineStart}–${l.lineEnd} · passage ${r.passage.passageId}`;
}

export function toRecipe(r: ContractRecipe, inp: RecipeInputs, byRecipe = groupSpecies(inp.species)): Recipe {
  const cands = byRecipe.get(r.id) ?? [];
  const idx = new Map(inp.index.map((e) => [e.speciesId, e]));
  const evidence = recipeEvidence(r.provenance.method);
  const tox = mostSevere(cands.map((c) => toxicityFromIndex(c.wfoId ? idx.get(c.wfoId) : undefined, c.toxicityFlag, c.toxicityNote)));
  return {
    id: r.id, source: sourceWork(r.sourceId), name: nameResolution(r, cands), preparation: preparationOf(r),
    passage: { text: r.passage.text, edition: editionOf(r.sourceId, inp.sources), locator: locatorOf(r), fields: extractedFields(r, evidence),
               illegible: illegibleSpans(r.passage.text) },
    toxicity: tox, evidence, indication: known(r.indicationAsWritten), recipeType: r.recipeType as Recipe['recipeType'],
    excludedFromHeadline: r.excludedFromHeadline, recipeQuote: r.evidence.recipe?.[0]?.quote ?? '',
    provenance: [r.provenance.provider ?? r.provenance.method, r.provenance.model, r.provenance.promptVersion].filter(Boolean).join(' · '),
    corrections: (r.corrections ?? []).map((c) => ({ ...c, from: c.from })),
  };
}

export const groupSpecies = (species: ContractSpecies[]) => {
  const m = new Map<string, ContractSpecies[]>();
  for (const s of species) m.set(s.recipeId, [...(m.get(s.recipeId) ?? []), s]);
  return m;
};

export function toSummary(rec: Recipe): RecipeSummary {
  return {
    id: rec.id, source: rec.source, name: rec.name, preparation: rec.preparation, toxicity: { ...rec.toxicity, sources: [] },
    evidence: rec.evidence, indication: rec.indication, corrected: rec.corrections.length > 0,
    search: [rec.name.historicalName, ...rec.name.candidates.map((c) => c.taxon), rec.indication ?? '', rec.recipeQuote].join(' ').toLowerCase(),
  };
}

/** URL-safe id for a recipe page (recipe ids contain ':' and '#'). */
export { recipeSlug } from './recipeSlug';
