/**
 * Shared mapping rules from contract records to the design's view models. Every honesty treatment is driven by a
 * data field here, never hard-coded in a component:
 *
 *  Evidence status (DESIGN.md §4.1)
 *    validated   a person checked it against an independent reference (human annotation, scholarly basis,
 *                experimental logP reference)
 *    provisional not yet independently validated (the M1 session extraction; unverified references)
 *    pending     produced by a rule or model and not yet assessed (M2 database/model matches, rule-based audit coding)
 *  Source confidence (§4.2): per source from metrics.nameResolution["disputedShare:<source>"]; the level is "lower"
 *    when at least half of that source's resolved names are disputed (display rule, stated in the tooltip note).
 *  Toxicity (§4.7): the contract's source-based flags; deprecated values map to their successors.
 */
import { neutralWording } from '../wording';
import type { EvidenceStatus, SourceConfidence, SourceWork, ToxicityCategory, ToxicityRecord } from '../../types';

export const sourceWork = (sourceId: string): SourceWork =>
  sourceId === 'culpeper-1652' ? 'culpeper_1652' : sourceId === 'culpeper-1850' ? 'culpeper_1850' : 'pliny_nh';

export const recipeEvidence = (method: string): EvidenceStatus =>
  method === 'human' || method === 'adjudicated' ? 'validated' : 'provisional';

export const candidateEvidence = (basis: string): EvidenceStatus => (basis === 'scholarly' ? 'validated' : 'pending');

interface ShareMetric { status: string; value?: number | null; n?: number | null }
export const DISPUTED_LOWER_AT = 0.5;
export function sourceConfidence(work: SourceWork, nameResolution: Record<string, ShareMetric | undefined>): SourceConfidence {
  const key = work === 'pliny_nh' ? 'disputedShare:pliny' : 'disputedShare:culpeper';
  const m = nameResolution[key];
  const share = m && m.status === 'computed' && m.value != null ? m.value : null;
  const level = share == null ? 'unknown' : share >= DISPUTED_LOWER_AT ? 'lower' : 'higher';
  const note = [
    work === 'culpeper_1850' ? 'Names in the 1850 edition are resolved through their 1652 entry.' : null,
    work === 'pliny_nh' ? 'A 19th-century English translation (Bostock & Riley) of a 1st-century Latin text.' : null,
    share != null && m?.n != null ? `Disputed share over ${m.n} resolved names. Shown as lower confidence when at least half are disputed.` : null,
  ].filter(Boolean).join(' ');
  return { source: work, level, disputedShare: share, note: note || undefined };
}

export function toxicityCategory(flag: string | null | undefined): ToxicityCategory {
  switch (flag) {
    case 'toxic_reported': case 'known_toxic': return 'toxic_reported';
    case 'concern_reported': return 'concern';
    case 'no_toxicity_reported': case 'none_known': return 'no_toxicity_reported';
    case 'data_lacking': return 'data_lacking';
    default: return 'unknown';
  }
}
const SEVERITY: ToxicityCategory[] = ['toxic_reported', 'concern', 'data_lacking', 'no_toxicity_reported', 'unknown'];
/** The most severe of several records (a disputed name keeps every candidate's flag; the strongest one shows). */
export function mostSevere(records: ToxicityRecord[]): ToxicityRecord {
  if (!records.length) return { category: 'unknown', sources: [] };
  return [...records].sort((a, b) => SEVERITY.indexOf(a.category) - SEVERITY.indexOf(b.category))[0];
}

export interface IndexEntryLike {
  speciesId: string; acceptedName: string; toxicityFlag?: string | null; toxicityNote?: string | null;
  toxicityEvidence?: { source: string; url: string; quote: string; licence: string; basis: string; verifiedBy?: string } | null;
}
export function toxicityFromIndex(e: IndexEntryLike | undefined, flag?: string | null, note?: string | null): ToxicityRecord {
  const category = toxicityCategory(e?.toxicityFlag ?? flag);
  const ev = e?.toxicityEvidence;
  return {
    category,
    sources: ev ? [{ label: `${ev.source} (${ev.basis === 'ai_drafted_unverified' ? 'provisional, unverified' : neutralWording(ev.basis)})`, href: ev.url }] : [],
    note: neutralWording((e?.toxicityNote ?? note) || undefined),
  };
}
