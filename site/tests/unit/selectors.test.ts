import { describe, expect, it } from 'vitest';
import * as G from '@/lib/data/generated';
import * as L from '@/lib/data/load';
import { bestState, breakdowns, auditView } from '@/lib/data/selectors/audit';
import { caseView } from '@/lib/data/selectors/caseStudy';
import { mostSevere, sourceConfidence, toxicityCategory } from '@/lib/data/selectors/common';
import { ATLAS_CHIPS, plantKeyOf, recipeMatches } from '@/lib/data/selectors/atlas';
import { toReportingGap } from '@/lib/data/selectors/gap';
import { coverage } from '@/lib/data/selectors/home';
import { choiceOf, driverOf, labQueryString, parseLabQuery, toEstimates } from '@/lib/data/selectors/lab';
import { getPanel } from '@/lib/data/assemble';
import { labLinkFor } from '@/lib/data/selectors/labPanel';
import { toPlate } from '@/lib/data/selectors/plates';
import { familyOfKey, labHrefOfKey } from '@/lib/data/selectors/prepKey';
import { getRecipeSummaries } from '@/lib/data/assemble';
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

describe('Lab', () => {
  it('drivers print the model multiplier; direction and strength are a display binning of it', () => {
    expect(driverOf('heat', 0.23, true)).toMatchObject({ effect: 'lowers', strength: 'strong', heuristic: true, note: 'Model multiplier ×0.23' });
    expect(driverOf('solvent', 1, false).effect).toBe('neutral');
    expect(driverOf('filtration', 1.4, true)).toMatchObject({ effect: 'raises', strength: 'moderate' });
    expect(familyOfKey('unknown|unknown|methanol|cold|yes')).toBe('modern');
    expect(familyOfKey('unknown|unknown|water|boiled|yes')).toBe('historical');
  });
  it('acidity without vinegar has no estimate; vinegar is always acidic', () => {
    expect(choiceOf({ solvent: 'water', heat: 'cold', filtered: true, acidified: true })).toBeNull();
    expect(choiceOf({ solvent: 'vinegar', heat: 'cold', filtered: true, acidified: true })).toMatchObject({ solvents: ['vinegar'], filtered: 'yes' });
    expect(parseLabQuery(new URLSearchParams('solvent=vinegar&acid=false')).acidified).toBe(true);
  });
  it('the URL carries the plant and every setting, and round-trips', () => {
    const q = parseLabQuery(new URLSearchParams('plant=Salvia sclarea&solvent=wine&heat=boiled&strained=false&acid=false&modern=true'));
    expect(q).toMatchObject({ plant: 'Salvia sclarea', solvent: 'wine', heat: 'boiled', filtered: false, acidified: false, modern: true });
    expect(parseLabQuery(new URLSearchParams(labQueryString(q)))).toEqual(q);
    expect(parseLabQuery(new URLSearchParams('solvent=mercury&heat=reflux'))).toMatchObject({ solvent: 'water', heat: 'cold' });
  });
  it('engine estimates become ranges with the median as the point; only heat, acidity and unfiltered carry-over are heuristic', () => {
    const [e] = toEstimates([{ compoundId: 'X', name: 'x', compoundClass: 'c (heuristic)', heatFlags: [], volatile: false, basicN: false }],
      [{ compoundId: 'X', likelihood: 0.4, low: 0.2, high: 0.6, rangeModelOnly: [0.25, 0.55], drivers: { solvent: 0.4, heat: 1, filtration: 1, acidity: 1 } }],
      { solvent: 'water', heat: 'cold', filtered: true, acidified: false });
    expect(e.likelihood).toEqual({ low: 0.2, high: 0.6, point: 0.4 });
    expect(e.drivers.map((d) => [d.id, d.heuristic])).toEqual([['solvent', false], ['heat', false], ['filtration', false], ['acidity', true]]);
  });
  it('a Lab link is made only for a preparation the Lab represents exactly', () => {
    expect(labHrefOfKey('Raphanus sativus', 'unknown|unknown|wine|boiled|yes')).toContain('solvent=wine&heat=boiled&strained=true');
    expect(labHrefOfKey('X y', 'unknown|unknown|wine+honey|boiled|yes')).toBeNull();
    expect(labHrefOfKey('X y', 'unknown|unknown|water|unknown|yes')).toBeNull();
  });
});

describe('v2 pages: evidence gap, planner, plates, atlas', () => {
  it('reporting gap: counts, intervals and n from metrics; only the prepared solvent row is inflated', () => {
    const g = toReportingGap(metrics);
    expect(g.rows.map((r) => r.field).sort()).toEqual(['filtration', 'freshOrDried', 'heat', 'part', 'solvent']);
    expect(g.rows.filter((r) => r.inflated).map((r) => r.field)).toEqual(['solvent']);
    for (const r of g.rows) {
      const m = metrics.reportingGap![`prepared:all:${r.field}`];
      expect([r.stated, r.n, r.ci]).toEqual([Math.round(m.value! * m.n!), m.n, [m.low, m.high]]);
    }
    expect(g.none?.n).toBe(g.rows[0].n);
    expect(g.extra.some((x) => x.label.includes('v3'))).toBe(true);
  });
  it('reporting gap: the AI-assisted sensitivity sits beside the frozen share and never replaces it', () => {
    const g = toReportingGap(metrics);
    const sec = metrics.provisional.reportingGapSensitivity;
    for (const r of g.rows) {
      const m = metrics.reportingGap![`prepared:all:${r.field}`];
      expect(r.stated).toBe(Math.round(m.value! * m.n!)); // frozen number unchanged
      if (!sec) { expect(r.sensitivity).toBeNull(); continue; }
      expect(sec.basis).toBe('ai_assisted_check');
      const s = sec.metrics[`prepared:all:${r.field}`];
      if (r.field === 'filtration') expect(r.sensitivity && 'notComputed' in r.sensitivity).toBe(true); // not in the AI check
      else expect(r.sensitivity && !('notComputed' in r.sensitivity) ? r.sensitivity.point : null).toBe(s.value);
    }
  });
  it('planner: the displayed panel (v2) never plans a toxic-reported plant, lists the excluded ones, one entry per plant', () => {
    const v = getPanel();
    expect(v).not.toBeNull();
    const lp = L.loadLabPanel()!;
    expect(v!.ruleVersion).toBe('v2');
    for (const z of v!.sizes) {
      expect(z.entries.some((e) => e.toxicity.category === 'toxic_reported')).toBe(false);
      expect(new Set(z.entries.map((e) => e.speciesId)).size).toBe(z.entries.length);      // at most one per plant
      expect(z.entries.every((e) => (e.gap.low ?? 0) > 0 && e.differs >= 1)).toBe(true);   // v2 eligibility
      expect(z.entries.map((e) => e.position)).toEqual(z.entries.map((_, i) => i + 1));
    }
    expect(v!.excludedToxic.length).toBe(lp.excludedToxic.length);
    expect(v!.sizes.map((z) => z.k)).toEqual([4, 6, 8]);
    // the original v1 result stays visible, and its coverage-only entries are flagged from the data
    expect(v!.original!.entries.filter((e) => e.coverageOnly).map((e) => e.id)).toEqual(lp.original!.panel.filter((c) => c.compoundsLikelyToDiffer === 0).map((c) => c.candidateId));
    expect(labLinkFor('Glycyrrhiza glabra', 'decoction in water', true)).toBeNull();   // acceptance check 5
    expect(v!.benchmark.every((r) => r.ar == null || (r.ar >= 0 && r.ar <= 1 + 1e-9))).toBe(true);
  });
  it('plates: an image only when sourced, with licence and host; status never claims a person confirmed it', () => {
    for (const p of L.loadPlates().map(toPlate)) {
      if (p.image) expect([p.status, p.host, p.licence && /^public domain/i.test(p.licence)]).toEqual(['sourced', 'Wikimedia Commons', true]);
      else expect(p.status).toBe('to_source');
    }
  });
  it('atlas: a disputed name is filed under its historical name; source chips never merge Culpeper editions', () => {
    const rs = getRecipeSummaries();
    const d = rs.find((r) => r.name.state === 'disputed')!;
    expect(plantKeyOf(d.name)).toBe(`“${d.name.historicalName}”`);
    expect(ATLAS_CHIPS.filter((c) => c.id.startsWith('culpeper')).length).toBe(2);
    const only1850 = rs.filter((r) => recipeMatches(r, '', ['culpeper_1850']));
    expect(only1850.length).toBeGreaterThan(0);
    expect(only1850.every((r) => r.source === 'culpeper_1850')).toBe(true);
    expect(rs.filter((r) => recipeMatches(r, 'VINEGAR', [])).length).toBe(rs.filter((r) => recipeMatches(r, 'vinegar', [])).length);
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
  it('modern preparation is read from the trail and is always the modern family; toxic plants get no Lab link', () => {
    const h = hs[0];
    expect(modernLabel(h)).toBe('modern methanol extract');
    const e = index.find((x) => x.speciesId === h.speciesId)!;
    const v = toHypothesis(h, { index, audit: L.loadAudit(), profiles: L.loadProfile(e.file), rankedOf: hs.length });
    expect(v.modern?.preparation.family).toBe('modern');
    expect(v.gap).toEqual({ low: h.profileGap.low, high: h.profileGap.high, point: h.profileGap.value });
    if (v.toxicity.category === 'toxic_reported') expect(v.trail.flatMap((s) => s.refs ?? []).some((r) => r.href?.startsWith('/lab'))).toBe(false);
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
  it('four statuses: AI-assisted checks are never validated, and logP is validated against external data (2026-11-07)', () => {
    const v = toValidation(metrics);
    const prov = v.metrics.filter((m) => m.id.startsWith('prov-'));
    expect(prov.length).toBeGreaterThan(0);
    for (const m of prov) expect(m.evidence === 'provisional' || m.evidence === 'pending').toBe(true);
    // the logP descriptor check is against measured, published values: external data, not a person's check
    for (const id of ['m4-rdkit', 'm4-xtb']) {
      const m = v.metrics.find((x) => x.id === id)!;
      expect(m.evidence).toBe(metrics.logPError[id === 'm4-rdkit' ? 'rdkit' : 'xtb']?.status === 'computed' ? 'external' : 'pending');
    }
    if (v.comparisons[0]) expect(v.comparisons[0].evidence).toBe('external');
    // nothing is human-validated unless a human reference was computed
    if (metrics.extraction.overall?.part?.f1?.status !== 'computed' && metrics.nameResolution.top1?.status !== 'computed' && metrics.interAnnotatorAgreement.heat?.status !== 'computed')
      expect(v.metrics.filter((m) => m.evidence === 'validated')).toEqual([]);
    // a stage is human-validated only when its human reference has been computed
    const stage = (id: string) => v.pipeline.find((p) => p.id === id)!.validation;
    expect(['validated', 'external']).not.toContain(stage('m4'));
    if (metrics.extraction.overall?.part?.f1?.status !== 'computed') expect(stage('m1')).not.toBe('validated');
    if (metrics.nameResolution.top1?.status !== 'computed') expect(stage('m2')).not.toBe('validated');
    if (metrics.provisional.m5ExtractorAiCheck) expect(stage('m5')).toBe('provisional');
  });
  it('case study lists every logged correction of its recipes', () => {
    const c = L.loadCaseStudies()[0];
    const cv = caseView(c, recipes);
    expect(cv.corrections.length).toBe(c.correctedRecipeIds.reduce((n, id) => n + (recipes.find((r) => r.id === id)?.corrections.length ?? 0), 0));
  });
});
