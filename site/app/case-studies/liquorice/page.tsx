import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { LiquoriceCase } from '@/features/case/LiquoriceCase';
import { toxicityFromIndex } from '@/lib/data/selectors/common';
import { confidences, getCase } from '@/lib/data/site';

export const metadata: Metadata = { title: 'Case study: liquorice “juice”' };
export default function Page() {
  const c = getCase();
  if (!c) notFound();
  const tox = toxicityFromIndex(c.toxicity ? { speciesId: c.study.speciesId, acceptedName: c.taxon, toxicityFlag: c.toxicity.flag, toxicityNote: c.toxicity.note, toxicityEvidence: c.toxicity.ev } : undefined);
  return (
    <LiquoriceCase view={{ study: c.study, corrections: c.corrections }} taxon={c.taxon} toxicity={tox} hypothesisHref={c.hypothesisHref}
                   compareHref={c.compareHref} beforeCompareHref={c.beforeCompareHref} confidences={confidences()} />
  );
}
