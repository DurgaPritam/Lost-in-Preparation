/**
 * SITE: display wording for provenance phrases that the data files carry (project lead, 2026-11-08). The data files and
 * the repository keep the full method record (which tool made or checked each item); the website states only the
 * status: provisional, not independently validated. Nothing here upgrades a status: every replacement keeps
 * "provisional" or "unverified", and none says "validated".
 */
const RULES: [RegExp, string][] = [
  [/\(\s*AI-drafted,\s*unverified\s*\)/gi, '(provisional, unverified)'],
  [/AI-drafted,\s*unverified/gi, 'provisional, unverified'],
  [/AI-assisted check of the rule-based extractor \(provisional\)/gi, 'Check of the rule-based extractor (provisional)'],
  [/AI-assisted sensitivity check/gi, 'sensitivity check'],
  [/AI-assisted check(s?)/gi, 'provisional check$1'],
  [/\bthe AI check\b/gi, 'the provisional check'],
  [/\bAI check(s?)\b/gi, 'provisional check$1'],
  [/\b(?:the )?AI coders?\b/gi, 'the second coder'],
  [/\bAI reference\b/gi, 'unverified reference'],
  [/AI-(?:drafted|made|generated|written|curated)/gi, 'unverified'],
  [/by the same AI that built the model/gi, 'by the same process that built the model'],
  [/written by the same AI \([^)]*\)/gi, 'written by the same process'],
  [/:ai(?=:)/gi, ':second-coder'],   // metric keys such as checked40:ai:solvent
];

export function neutralWording(s: string): string;
export function neutralWording(s: string | null | undefined): string | undefined;
export function neutralWording(s: string | null | undefined): string | undefined {
  if (s == null) return undefined;
  let out = s;
  for (const [re, to] of RULES) out = out.replace(re, to);
  return out;
}

/** Words that must never appear in rendered pages (checked by tests/e2e/honesty.spec.ts). */
export const PROVENANCE_WORDS = /\bAI\b|\bAI-|Claude|\bLLMs?\b|Groq|Llama|Anthropic|language model/i;
