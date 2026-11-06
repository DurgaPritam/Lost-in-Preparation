/**
 * Writes one JSON file per contract file into mock-data/ (the deliverable)
 * and public/data/ (served at /data/*.json by Vite for the download links).
 * Run: npm run mock-data
 */
import { mkdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { CONTRACT_FILES } from '../src/contract';

for (const dir of ['mock-data', join('public', 'data')]) {
  const out = join(process.cwd(), dir);
  mkdirSync(out, { recursive: true });
  for (const [file, data] of Object.entries(CONTRACT_FILES)) {
    writeFileSync(join(out, file), JSON.stringify(data, null, 2) + '\n');
  }
  console.log(`wrote ${Object.keys(CONTRACT_FILES).length} files to ${dir}/`);
}
