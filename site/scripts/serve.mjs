/** Minimal static server for the exported site (out/), used by Playwright, Lighthouse and screenshots. No dependencies.
 *  Text responses are brotli/gzip-compressed, as Vercel serves them, so Lighthouse measures the deployed transfer sizes. */
import { createServer } from 'node:http';
import { readFile, stat } from 'node:fs/promises';
import path from 'node:path';
import { brotliCompressSync, gzipSync, constants } from 'node:zlib';

const COMPRESSIBLE = new Set(['.html', '.js', '.css', '.json', '.svg', '.txt']);
const cache = new Map();

const root = path.resolve(process.argv[2] ?? 'out');
const port = Number(process.argv[3] ?? 4517);
const TYPES = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json',
  '.woff2': 'font/woff2', '.svg': 'image/svg+xml', '.txt': 'text/plain; charset=utf-8', '.ico': 'image/x-icon', '.png': 'image/png' };

createServer(async (req, res) => {
  let p = decodeURIComponent(new URL(req.url ?? '/', 'http://x').pathname);
  let file = path.join(root, p);
  if (!file.startsWith(root)) { res.writeHead(403).end(); return; }
  try {
    if ((await stat(file)).isDirectory()) file = path.join(file, 'index.html');
  } catch {
    if (!path.extname(file)) file = `${file}.html`;
  }
  try {
    let body = await readFile(file);
    const ext = path.extname(file);
    const headers = { 'content-type': TYPES[ext] ?? 'application/octet-stream', vary: 'accept-encoding',
      'cache-control': ext === '.html' || p.startsWith('/data/') ? 'no-cache' : 'public, max-age=31536000, immutable' };
    const accept = String(req.headers['accept-encoding'] ?? '');
    const enc = !COMPRESSIBLE.has(ext) ? null : /\bbr\b/.test(accept) ? 'br' : /\bgzip\b/.test(accept) ? 'gzip' : null;
    if (enc) {
      const key = `${enc}:${file}`;
      if (!cache.has(key)) cache.set(key, enc === 'br' ? brotliCompressSync(body, { params: { [constants.BROTLI_PARAM_QUALITY]: 5 } }) : gzipSync(body, { level: 6 }));
      body = cache.get(key);
      headers['content-encoding'] = enc;
    }
    res.writeHead(200, headers);
    res.end(body);
  } catch {
    const nf = await readFile(path.join(root, '404.html')).catch(() => Buffer.from('Not found'));
    res.writeHead(404, { 'content-type': 'text/html; charset=utf-8' }).end(nf);
  }
}).listen(port, () => console.log(`serving ${root} on http://localhost:${port}`));
