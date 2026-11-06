/**
 * Pre-build step (npm run prebuild): validate EVERY ../site-data file against the generated Zod schemas (exit 1 on any
 * mismatch, which fails the build), then write public/data/:
 *   - the contract files themselves, for the Data & licences downloads;
 *   - compare/<speciesId>.json: each species' profiles in compact form (selectors/compare.ts), loaded on demand by Compare;
 *   - recipe-index.json: every recipe summary, loaded by the explorer after its first screen;
 *   - audit-studies-v1.json / -v2.json: the audit study rows, loaded when the Audit table is shown;
 *   - engine/model.json and engine/<speciesId>.json: Preparation Lab inputs (contract v1.7, P38), loaded on demand.
 *     engine/parity.json is a build-time test fixture (scripts/engine-parity.ts) and is not published.
 */
import { copyFileSync, mkdirSync, rmSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { SITE_DATA, loadProfile, loadProfileIndex, validateAll } from '../lib/data/load';
import { compactProfile } from '../lib/data/selectors/compare';
import { getAuditStudies, getRecipeSummaries } from '../lib/data/assemble';

const OUT = path.resolve(__dirname, '..', 'public', 'data');
let counts: Record<string, number>;
try {
  counts = validateAll();
} catch (e) {
  console.error(`\nsite-data validation FAILED: ${(e as Error).message}\n`);
  process.exit(1);
}
rmSync(OUT, { recursive: true, force: true });
mkdirSync(path.join(OUT, 'compare'), { recursive: true });
mkdirSync(path.join(OUT, 'profiles'), { recursive: true });
mkdirSync(path.join(OUT, 'engine'), { recursive: true });
for (const f of ['sources.json', 'recipes.json', 'species.json', 'audit.json', 'audit_v2.json', 'hypotheses.json', 'case_studies.json', 'metrics.json', 'profiles/index.json']) {
  copyFileSync(path.join(SITE_DATA, f), path.join(OUT, f));
}
copyFileSync(path.join(SITE_DATA, 'engine', 'model.json'), path.join(OUT, 'engine', 'model.json'));
for (const e of loadProfileIndex()) copyFileSync(path.join(SITE_DATA, 'engine', `${e.speciesId}.json`), path.join(OUT, 'engine', `${e.speciesId}.json`));
for (const e of loadProfileIndex()) {
  writeFileSync(path.join(OUT, 'compare', `${e.speciesId}.json`), JSON.stringify(compactProfile(e, loadProfile(e.file))));
}
writeFileSync(path.join(OUT, 'recipe-index.json'), JSON.stringify(getRecipeSummaries()));
for (const v of ['v1', 'v2'] as const) writeFileSync(path.join(OUT, `audit-studies-${v}.json`), JSON.stringify(getAuditStudies(v)));
console.log(`validated ${Object.keys(counts).length} site-data files (${Object.values(counts).reduce((a, b) => a + b, 0)} records); wrote public/data/`);
