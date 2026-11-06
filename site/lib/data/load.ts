/**
 * Typed, validated loaders for ../site-data (build time only; the site never reads anything else).
 * Every file is parsed with the Zod schema generated from the contract JSON Schema; any mismatch throws, which fails
 * `next build` (and scripts/prepare-data.ts runs the same checks before the build starts).
 */
import { readFileSync } from 'node:fs';
import path from 'node:path';
import type { z } from 'zod';
import * as G from './generated';

export const SITE_DATA = process.env.SITE_DATA_DIR ?? path.resolve(process.cwd(), '..', 'site-data');

const cache = new Map<string, unknown>();
function parse<S extends z.ZodTypeAny>(file: string, schema: S): z.infer<S> {
  if (!cache.has(file)) {
    const raw = JSON.parse(readFileSync(path.join(SITE_DATA, file), 'utf8'));
    const r = schema.safeParse(raw);
    if (!r.success) {
      const issues = r.error.issues.slice(0, 5).map((i) => `${i.path.join('.')}: ${i.message}`).join('; ');
      throw new Error(`site-data/${file} does not match contract ${G.CONTRACT_VERSION}: ${issues}`);
    }
    cache.set(file, r.data);
  }
  return cache.get(file) as z.infer<S>;
}

export type ContractRecipe = z.infer<typeof G.recipes.schema>[number];
export type ContractSpecies = z.infer<typeof G.species.schema>[number];
export type ContractProfileIndex = z.infer<typeof G.profilesIndex.schema>[number];
export type ContractProfile = z.infer<typeof G.profilesSpecies.schema>[number];
export type ContractAudit = z.infer<typeof G.audit.schema>[number];
export type ContractHypothesis = z.infer<typeof G.hypotheses.schema>[number];
export type ContractMetrics = z.infer<typeof G.metrics.schema>;
export type ContractMetric = ContractMetrics['logPError'][string];
export type ContractSource = z.infer<typeof G.sources.schema>[number];
export type ContractCase = z.infer<typeof G.caseStudies.schema>[number];

export const loadSources = () => parse('sources.json', G.sources.schema);
export const loadRecipes = () => parse('recipes.json', G.recipes.schema);
export const loadSpecies = () => parse('species.json', G.species.schema);
export const loadProfileIndex = () => parse('profiles/index.json', G.profilesIndex.schema);
export const loadProfile = (file: string) => parse(file, G.profilesSpecies.schema);
export const loadAudit = () => parse('audit.json', G.audit.schema);
export const loadAuditV2 = () => parse('audit_v2.json', G.auditV2.schema);
export const loadHypotheses = () => parse('hypotheses.json', G.hypotheses.schema);
export const loadMetrics = () => parse('metrics.json', G.metrics.schema);
export const loadCaseStudies = () => parse('case_studies.json', G.caseStudies.schema);
// v1.7 (P38): Preparation Lab engine inputs
export const loadEngineModel = () => parse('engine/model.json', G.engineModel.schema);
export const loadEngineSpecies = (speciesId: string) => parse(`engine/${speciesId}.json`, G.engineSpecies.schema);
export const loadEngineParity = () => parse('engine/parity.json', G.engineParity.schema);

/** Every contract file, for the pre-build validation script and the unit tests. */
export function validateAll(): Record<string, number> {
  const out: Record<string, number> = {
    'sources.json': loadSources().length, 'recipes.json': loadRecipes().length, 'species.json': loadSpecies().length,
    'profiles/index.json': loadProfileIndex().length, 'audit.json': loadAudit().length, 'audit_v2.json': loadAuditV2().length,
    'hypotheses.json': loadHypotheses().length, 'case_studies.json': loadCaseStudies().length, 'metrics.json': loadMetrics() ? 1 : 0,
  };
  for (const e of loadProfileIndex()) out[e.file] = loadProfile(e.file).length;
  out['engine/model.json'] = loadEngineModel().preparations.length;
  for (const e of loadProfileIndex()) out[`engine/${e.speciesId}.json`] = loadEngineSpecies(e.speciesId).compounds.length;
  out['engine/parity.json'] = loadEngineParity().length;
  return out;
}
