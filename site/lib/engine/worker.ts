/// <reference lib="webworker" />
/**
 * The preparation engine in a Web Worker, so the page never blocks while a profile is computed.
 *
 *   in:  { type: 'compute', id, channel, speciesId, prep, base }
 *   out: { type: 'result', id, channel, key, estimates, compounds, ms, cached } | { type: 'cancelled', id, channel } | { type: 'error', ... }
 *        `compounds` (name, class, heuristic flags) is aligned with `estimates`, so the page needs no second fetch.
 *
 * - Cached: every finished profile is kept per (species, preparation), so switching back is instant.
 * - Cancellable: requests carry a channel ("lab", "lab-modern", ...). A computation yields between chunks of compounds;
 *   when a newer request has arrived on its channel it stops and reports `cancelled`, so a stale profile never lands.
 * - The model and species files come from /data/engine/ (validated against the contract at build time). The numbers are
 *   the engine's, which the parity gate holds equal to the Python pipeline.
 */
import { estimate, Streams } from './model';
import type { EngineEstimate, EngineModel, EnginePrep, EngineSpecies } from './types';

declare const self: DedicatedWorkerGlobalScope;

interface ComputeMsg { type: 'compute'; id: number; channel: string; speciesId: string; prep: EnginePrep; base: string }

const CHUNK = 24;
const latest = new Map<string, number>();
const results = new Map<string, EngineEstimate[]>();
const meta = new Map<string, CompoundMeta[]>();
export interface CompoundMeta { compoundId: string; name: string; compoundClass: string; heatFlags: string[]; volatile: boolean; basicN: boolean }
let model: Promise<EngineModel> | null = null;
let streams: Streams | null = null;
const species = new Map<string, Promise<EngineSpecies>>();

const getJson = async <T,>(url: string): Promise<T> => {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${url}: HTTP ${r.status}`);
  return (await r.json()) as T;
};
const keyOf = (speciesId: string, p: EnginePrep) => `${speciesId}|${p.seedOffset}|${p.key}|${p.process ?? ''}`;
/** Let queued messages (a newer request) be delivered before continuing. A MessageChannel task, not setTimeout:
 *  nested timeouts are clamped to 4 ms, which made the yields (not the model) most of a large species' time. */
const tick = new MessageChannel();
const waiting: (() => void)[] = [];
tick.port1.onmessage = () => waiting.shift()?.();
const breathe = () => new Promise<void>((resolve) => { waiting.push(resolve); tick.port2.postMessage(0); });

async function compute(m: ComputeMsg): Promise<void> {
  const t0 = performance.now();
  const key = keyOf(m.speciesId, m.prep);
  const hit = results.get(key);
  if (hit) { self.postMessage({ type: 'result', id: m.id, channel: m.channel, key, estimates: hit, compounds: meta.get(m.speciesId), ms: performance.now() - t0, cached: true }); return; }
  model ??= getJson<EngineModel>(`${m.base}model.json`);
  if (!species.has(m.speciesId)) species.set(m.speciesId, getJson<EngineSpecies>(`${m.base}${m.speciesId}.json`));
  const [md, sp] = await Promise.all([model, species.get(m.speciesId)!]);
  streams ??= new Streams(md);
  if (sp.modelVersion !== md.modelVersion) throw new Error(`model version mismatch for ${m.speciesId}`);
  if (!meta.has(m.speciesId)) {
    meta.set(m.speciesId, sp.compounds.map((c) => ({ compoundId: c.compoundId, name: c.name, compoundClass: c.compoundClass, heatFlags: c.heatFlags, volatile: c.volatile, basicN: c.basicN })));
  }
  const out: EngineEstimate[] = [];
  for (let i = 0; i < sp.compounds.length; i += CHUNK) {
    if (latest.get(m.channel) !== m.id) { self.postMessage({ type: 'cancelled', id: m.id, channel: m.channel }); return; }
    for (const c of sp.compounds.slice(i, i + CHUNK)) out.push(estimate(c, m.prep, md, streams));
    await breathe();
  }
  if (latest.get(m.channel) !== m.id) { self.postMessage({ type: 'cancelled', id: m.id, channel: m.channel }); return; }
  results.set(key, out);
  self.postMessage({ type: 'result', id: m.id, channel: m.channel, key, estimates: out, compounds: meta.get(m.speciesId), ms: performance.now() - t0, cached: false });
}

self.onmessage = (e: MessageEvent<ComputeMsg>) => {
  const m = e.data;
  if (m.type !== 'compute') return;
  latest.set(m.channel, m.id);
  compute(m).catch((err: unknown) => self.postMessage({ type: 'error', id: m.id, channel: m.channel, message: String((err as Error)?.message ?? err) }));
};
