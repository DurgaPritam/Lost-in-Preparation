import { describe, expect, it } from 'vitest';
import * as G from '@/lib/data/generated';
import * as L from '@/lib/data/load';
import { bestState, breakdowns, auditView } from '@/lib/data/selectors/audit';
import { caseView } from '@/lib/data/selectors/caseStudy';
import { mostSevere, sourceConfidence, toxicityCategory } from '@/lib/data/selectors/common';
import { compactProfile, driverOf, expandProfile, familyOfKey, toSpeciesProfile } from '@/lib/data/selectors/compare';
import { coverage, reportingGap } from '@/lib/data/selectors/home';
import { modernLabel, toHypothesis } from '@/lib/data/selectors/hypotheses';
import { toValidation } from '@/lib/data/selectors/methods';
import { extractedFields, illegibleSpans, nameResolution, preparationOf, recipeSlug, toRecipe } from '@/lib/data/selectors/recipes';

const recipes = L.loadRecipes();
const species = L.loadSpecies();
const index = L.loadProfileIndex();
const metrics = L.loadMetrics();

describe('contract validation', () => {
  it('every site-data file validates', () => {
    const v = L.validateAll();
    expect(v['recipes.json']).toBe(recipes.length);
    expect(Object.keys(v).length).toBeGreaterThan(9);
  });
  it('a mismatch is rejected (unknown field, wrong enum, missing field)', () => {
    const r = structuredClone(recipes[0]) as Record<string, unknown>;
    expect(G.recipes.schema.safeParse([{ ...r, extra: 1 }]).success).toBe(false);
    expect(G.recipes.schema.safeParse([{ ...r, heat: 'scorching' }]).success).toBe(false);
    const { provenance: _p, ...missing } = r;
    expect(G.recipes.schema.safeParse([missing]).success).toBe(false);
  });
});

describe('source confidence and toxicity come from data', () => {
  it('per source, never merged; Pliny lower from its disputed share', () => {
    const p = sourceConfidence('pliny_nh', metrics.nameResolution);
    const c = sourceConfidence('culpeper_1652', metrics.nameResolution);
    expect(p.level).toBe('lower');
    expect(c.level).toBe('higher');
    expect(p.disputedShare).toBe(metrics.nameResolution['disputedShare:pliny']?.value);
    expect(sourceConfidence('pliny_nh', {}).level).toBe('unknown');
  });
  it('deprecated flags map forward; the most severe flag wins', () => {
    expect(toxicityCategory('known_toxic')).toBe('toxic_reported');
    expect(toxicityCategory('none_known')).toBe('no_toxicity_reported');
    expect(toxicityCategory(null)).toBe('unknown');
    expect(mostSevere([{ category: 'unknown', sources: [] }, { category: 'concern', sources: [] }]).category).toBe('concern');
  });
});

describe('recipes', () => {
  const pliny = recipes.find((r) => r.id === 'pliny-nh:b22:c011:001#r01')!;
  it('unknown stays null, never false or 0', () => {
    const p = preparationOf(pliny);
    expect(p.heat).toBeNull();
    expect(p.filtered).toBeNull();
    expect(p.vehicle).toBe('unknown');
  });
  it('overlapping quotes are drawn once; the indication is never drawn inline', () => {
    const fields = extractedFields(pliny, 'provisional');
    const drawn = fields.filter((f) => f.inline);
    for (const a of drawn) for (const b of drawn) if (a !== b) expect(a.end <= b.start || b.end <= a.start).toBe(true);
    expect(fields.some((f) => f.kind === 'indication' && f.inline)).toBe(false);
    for (const f of fields.filter((x) => x.start >= 0)) expect(pliny.passage.text.slice(f.start, f.end)).toBe(f.quote);
  });
  it('illegible markers are kept as spans', () => {
    const spans = illegibleSpans('a ⟦?⟧ b ⟦foreign⟧ c');
    expect(spans.map((s) => [s.at, s.end])).toEqual([[2, 5], [8, 17]]);
  });
  it('name states: unresolved without candidates, disputed when flagged', () => {
    expect(nameResolution(pliny, []).state).toBe('unresolved');
    const cs = species.filter((s) => s.disputed).slice(0, 1);
    expect(nameResolution(pliny, cs.map((c) => ({ ...c, recipeId: pliny.id }))).state).toBe('disputed');
  });
  it('corrections are carried and slugs are unique', () => {
    const r = toRecipe(pliny, { species, index, sources: L.loadSources() });
    expect(r.corrections.map((c) => c.field)).toEqual(['part', 'solvent', 'heat', 'process', 'filtered']);
    expect(r.evidence).toBe('provisional');
    expect(new Set(recipes.map((x) => recipeSlug(x.id))).size).toBe(recipes.length);
  });
});

describe('compare', () => {
  it('drivers print the model multiplier; heuristic flags come from the profile', () => {
    expect(driverOf('heat', 0.23, true)).toMatchObject({ effect: 'lowers', strength: 'strong', heuristic: true, note: 'Model multiplier ×0.23' });
    expect(driverOf('solvent', 1, false).effect).toBe('neutral');
    expect(familyOfKey('unknown|unknown|methanol|cold|yes')).toBe('modern');
    expect(familyOfKey('unknown|unknown|water|boiled|yes')).toBe('historical');
  });
  it('the compact file expands to the same profile', () => {
    const e = index[0];
    const ps = L.loadProfile(e.file);
    const full = toSpeciesProfile(e, ps);
    const back = expandProfile(JSON.parse(JSON.stringify(compactProfile(e, ps))));
    expect(back.preparations.map((p) => p.estimates.length)).toEqual(full.preparations.map((p) => p.estimates.length));
    expect(back.preparations[0].estimates[0].likelihood).toEqual(full.preparations[0].estimates[0].likelihood);
  });
});

describe('audit', () => {
  it('best outcome: any match matches; all-known-differ differs; no-analogue is never differs', () => {
    expect(bestState(['mismatch', 'match'])).toBe('matches');
    expect(bestState(['mismatch', 'mismatch'])).toBe('differs');
    expect(bestState(['mismatch', 'unknown'])).toBe('not_stated');
    expect(bestState(['no_analogue', 'no_analogue'])).toBe('no_analogue');
    expect(bestState(['no_analogue', 'mismatch'])).toBe('differs');
  });
  it('v2 units reproduce the frozen v2 counts', () => {
    const v = auditView(L.loadAuditV2(), (id) => id);
    const s = v.units.map((u) => u.state.overall);
    const av2 = metrics.auditV2!;
    expect(s.filter((x) => x === 'not_stated').length).toBe(av2.unknownUnits);
    expect(s.filter((x) => x === 'no_analogue').length).toBe(av2.noModernAnalogueUnits);
    expect(v.units.length).toBe(av2.units);
    for (const b of breakdowns(v.units)) expect(Object.values(b.vehicle).reduce((a, x) => a + x, 0)).toBe(b.studies);
  });
});

describe('hypotheses, home, methods, case study', () => {
  const hs = L.loadHypotheses();
  it('modern preparation is read from the trail and is always the modern family; toxic plants get no Compare link', () => {
    const h = hs[0];
    expect(modernLabel(h)).toBe('modern methanol extract');
    const e = index.find((x) => x.speciesId === h.speciesId)!;
    const v = toHypothesis(h, { index, audit: L.loadAudit(), profiles: L.loadProfile(e.file), rankedOf: hs.length });
    expect(v.modern?.preparation.family).toBe('modern');
    expect(v.gap).toEqual({ low: h.profileGap.low, high: h.profileGap.high, point: h.profileGap.value });
    if (v.toxicity.category === 'toxic_reported') expect(v.trail.flatMap((s) => s.refs ?? []).some((r) => r.href?.startsWith('/compare'))).toBe(false);
  });
  it('reporting gap: n, CI and the inflated-solvent flag', () => {
    const g = reportingGap(metrics);
    const sol = g.prepared.vars.find((r) => r.key.endsWith(':solvent'))!;
    expect(sol.inflated).toBe(true);
    expect(g.prepared.vars.filter((r) => r.inflated)).toHaveLength(1);
    expect(g.retrieved.vars.some((r) => r.inflated)).toBe(false);
    for (const r of g.prepared.vars) expect(r.k).toBe(Math.round(r.value! * r.n!));
    expect(g.v3.n).toBeGreaterThan(0);
  });
  it('coverage counts every name once by evidence status', () => {
    const c = coverage(species, recipes, 1);
    expect(c.nameResolutions.validated + c.nameResolutions.provisional + c.nameResolutions.pending).toBe(new Set(species.map((s) => s.id.split('|')[1])).size);
  });
  it('a metric without an interval never shows a point', () => {
    const v = toValidation(metrics);
    for (const m of v.metrics) if (m.value.low == null || m.value.high == null) expect(m.value.low == null && m.value.high == null).toBe(true);
    expect(v.comparisons[0].methods).toHaveLength(2);
  });
  it('case study lists every logged correction of its recipes', () => {
    const c = L.loadCaseStudies()[0];
    const cv = caseView(c, recipes);
    expect(cv.corrections.length).toBe(c.correctedRecipeIds.reduce((n, id) => n + (recipes.find((r) => r.id === id)?.corrections.length ?? 0), 0));
  });
});
