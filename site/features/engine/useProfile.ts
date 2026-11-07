'use client';

/**
 * Runs the preparation engine in its Web Worker (lib/engine/worker.ts) and keeps the page responsive:
 * - the previous profile stays visible, marked `updating`, until the new one arrives (same species only: a different
 *   species' bars are never shown as if they were this one's);
 * - finished profiles are cached here and in the worker, per (species, preparation), so switching back is instant;
 * - a newer request on the same channel cancels the older one in the worker, and a stale answer is ignored here.
 */
import { useEffect, useState } from 'react';
import type { EngineEstimate, EnginePrep } from '@/lib/engine';
import type { CompoundMeta } from '@/lib/engine/worker';

export type ProfileStatus = 'idle' | 'loading' | 'updating' | 'ready' | 'error';
export interface ProfileState {
  status: ProfileStatus;
  speciesId: string | null;
  key: string | null;
  estimates: EngineEstimate[] | null;
  compounds: CompoundMeta[] | null;
  ms: number | null;
  error: string | null;
}
const EMPTY: ProfileState = { status: 'idle', speciesId: null, key: null, estimates: null, compounds: null, ms: null, error: null };

type Out = { type: 'result'; id: number; key: string; estimates: EngineEstimate[]; compounds: CompoundMeta[]; ms: number }
  | { type: 'cancelled'; id: number } | { type: 'error'; id: number; message: string };

let worker: Worker | null = null;
let nextId = 1;
const listeners = new Map<number, (m: Out) => void>();
const cache = new Map<string, { estimates: EngineEstimate[]; compounds: CompoundMeta[] }>();

function getWorker(): Worker {
  if (!worker) {
    worker = new Worker(new URL('../../lib/engine/worker.ts', import.meta.url));
    worker.onmessage = (e: MessageEvent<Out>) => {
      const l = listeners.get(e.data.id);
      if (l) { listeners.delete(e.data.id); l(e.data); }
    };
  }
  return worker;
}

export const profileKey = (speciesId: string, p: EnginePrep) => `${speciesId}|${p.seedOffset}|${p.key}|${p.process ?? ''}`;

export function useProfile(channel: string, speciesId: string | null, prep: EnginePrep | null): ProfileState {
  const [state, setState] = useState<ProfileState>(EMPTY);
  const key = speciesId && prep ? profileKey(speciesId, prep) : null;
  useEffect(() => {
    if (!speciesId || !prep || !key) { setState((s) => ({ ...s, status: 'idle' })); return; }
    const hit = cache.get(key);
    if (hit) { setState({ status: 'ready', speciesId, key, ...hit, ms: 0, error: null }); return; }
    setState((s) => (s.speciesId === speciesId && s.estimates
      ? { ...s, status: 'updating', error: null }
      : { ...EMPTY, status: 'loading', speciesId }));
    const id = nextId++;
    listeners.set(id, (m) => {
      if (m.type === 'result') {
        cache.set(m.key, { estimates: m.estimates, compounds: m.compounds });
        setState({ status: 'ready', speciesId, key: m.key, estimates: m.estimates, compounds: m.compounds, ms: m.ms, error: null });
      } else if (m.type === 'error') {
        setState((s) => ({ ...s, status: 'error', error: m.message }));
      }
    });
    getWorker().postMessage({ type: 'compute', id, channel, speciesId, prep, base: '/data/engine/' });
    return () => { listeners.delete(id); };
    // prep is identified by its key
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [channel, key]);
  return state;
}
