/**
 * Preparation Lab: settings, the URL that shares them, the mapping onto the engine's preparations, and the engine's
 * estimates as the design's CompoundEstimate. Pure and browser-safe.
 *
 * Settings are solvent, heat, filtration and acidity, kept separate (non-negotiable 4). The model represents acidity
 * only through vinegar (basic nitrogen in an acid vehicle), so "acidified" with any other solvent has NO estimate: the
 * Lab shows its no-data state and never invents one.
 */
import type { EngineEstimate, EngineModel, EnginePrep, PrepChoice } from '../../engine';
import { preparationFor } from '../../engine/prep';
import type { CompoundEstimate, Driver, DriverId, Preparation } from '../../types';

export type LabSolvent = 'water' | 'wine' | 'vinegar' | 'oil' | 'honey';
export type LabHeat = 'cold' | 'warm' | 'boiled';
export interface LabSettings { solvent: LabSolvent; heat: LabHeat; filtered: boolean; acidified: boolean }
export interface LabQuery extends LabSettings { plant: string | null; modern: boolean }

export const SOLVENTS: { value: LabSolvent; label: string }[] = [
  { value: 'water', label: 'Water' }, { value: 'wine', label: 'Wine' }, { value: 'vinegar', label: 'Vinegar' }, { value: 'oil', label: 'Oil' }, { value: 'honey', label: 'Honey' },
];
export const HEATS: { value: LabHeat; label: string }[] = [{ value: 'cold', label: 'Cold' }, { value: 'warm', label: 'Warm' }, { value: 'boiled', label: 'Boiled' }];
export const DEFAULT_SETTINGS: LabSettings = { solvent: 'water', heat: 'cold', filtered: true, acidified: false };

const bool = (v: string | null) => (v === 'true' ? true : v === 'false' ? false : undefined);

/** /lab/?plant=&solvent=&heat=&strained=&acid=&modern= (design v2 HANDOFF §1; `modern` added for the comparison). */
export function parseLabQuery(qs: URLSearchParams): LabQuery {
  const s = qs.get('solvent');
  const h = qs.get('heat');
  const out: LabQuery = {
    ...DEFAULT_SETTINGS,
    plant: qs.get('plant') ?? qs.get('species'),
    modern: bool(qs.get('modern')) ?? false,
  };
  if (s && SOLVENTS.some((x) => x.value === s)) out.solvent = s as LabSolvent;
  if (h && HEATS.some((x) => x.value === h)) out.heat = h as LabHeat;
  const f = bool(qs.get('strained'));
  if (f !== undefined) out.filtered = f;
  const a = bool(qs.get('acid'));
  if (a !== undefined) out.acidified = a;
  if (out.solvent === 'vinegar') out.acidified = true; // vinegar is acidic
  return out;
}

export function labQueryString(q: LabQuery): string {
  const p = new URLSearchParams();
  if (q.plant) p.set('plant', q.plant);
  p.set('solvent', q.solvent);
  p.set('heat', q.heat);
  p.set('strained', String(q.filtered));
  p.set('acid', String(q.acidified));
  if (q.modern) p.set('modern', 'true');
  return p.toString();
}
export const labHref = (q: Partial<LabQuery> & { plant: string }) => `/lab/?${labQueryString({ ...DEFAULT_SETTINGS, modern: false, ...q })}`;

/** The engine choice for the settings, or null when the model has no estimate (acidified without vinegar). */
export function choiceOf(s: LabSettings): PrepChoice | null {
  if (s.acidified && s.solvent !== 'vinegar') return null;
  // process only names the preparation (and its seed); the model reads distillation, powder and expression only
  const process = s.heat === 'boiled' ? 'decoction' : s.solvent === 'water' ? 'infusion' : 'maceration';
  return { solvents: [s.solvent], heat: s.heat, filtered: s.filtered ? 'yes' : 'no', process };
}
export const engineQueryKey = (speciesId: string, prep: EnginePrep) => `${speciesId}|${prep.seedOffset}|${prep.key}|${prep.process ?? ''}`;

export function prepFor(model: EngineModel, s: LabSettings): EnginePrep | null {
  const c = choiceOf(s);
  return c ? preparationFor(model, c) : null;
}
/** The modern lab method the Lab compares against: the pipeline's modern methanol extract. */
export const modernPrep = (model: EngineModel) => model.preparations.find((p) => p.label === 'modern methanol extract') ?? null;

export function settingsLabel(s: LabSettings): string {
  const solvent = SOLVENTS.find((x) => x.value === s.solvent)!.label.toLowerCase();
  return `${solvent}, ${s.heat}, ${s.filtered ? 'strained' : 'unstrained'}${s.acidified ? ', acidified' : ''}`;
}
export const preparationOfSettings = (s: LabSettings): Preparation => ({ family: 'historical', vehicle: s.solvent, heat: s.heat, filtered: s.filtered, acidified: s.acidified });
export const MODERN_PREPARATION: Preparation = { family: 'modern', vehicle: 'methanol', heat: 'cold', filtered: true, acidified: false };

/**
 * A driver is the model's multiplier for one factor. Direction and strength are a display binning of that number; the
 * multiplier itself is printed in the note, so the binning hides nothing.
 */
export function driverOf(id: DriverId, m: number, heuristic: boolean): Driver {
  const effect = m > 1.02 ? 'raises' : m < 0.98 ? 'lowers' : 'neutral';
  const strength = effect === 'neutral' ? null
    : effect === 'lowers' ? (m < 0.5 ? 'strong' : m < 0.8 ? 'moderate' : 'weak')
    : (m > 2 ? 'strong' : m > 1.25 ? 'moderate' : 'weak');
  return { id, effect, strength, heuristic, note: `Model multiplier ×${m.toFixed(2)}` };
}

export interface LabCompound { compoundId: string; name: string; compoundClass: string; heatFlags: string[]; volatile: boolean; basicN: boolean }

/** Engine estimates → the design's CompoundEstimate. Heuristic drivers: heat (alerts, volatile loss), acidity, filtration
 *  carry-over; the solvent window is not a heuristic (logP descriptor validated against experiment). */
export function toEstimates(compounds: LabCompound[], est: EngineEstimate[], s: LabSettings | null): CompoundEstimate[] {
  return est.map((e, i) => {
    const c = compounds[i];
    const heatHeuristic = c.heatFlags.length > 0 || c.volatile;
    return {
      compound: c.name, compoundClass: c.compoundClass,
      likelihood: { low: e.low, high: e.high, point: e.likelihood },
      drivers: [
        driverOf('solvent', e.drivers.solvent, false),
        driverOf('heat', e.drivers.heat, heatHeuristic),
        driverOf('filtration', e.drivers.filtration, s ? !s.filtered : true),
        driverOf('acidity', e.drivers.acidity, true),
      ],
    };
  });
}
