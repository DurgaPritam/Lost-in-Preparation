/**
 * Botanical name formatting (Phase 4). Genus and epithet are italic; rank
 * markers and qualifiers ("sp.", "spp.", "var.", "subsp.", "cf.", "aff.")
 * and authorities are roman, as in a journal. "Mentha sp." → <i>Mentha</i> sp.
 */
const ROMAN = new Set(['sp.', 'spp.', 'var.', 'subsp.', 'ssp.', 'cf.', 'aff.', 'f.']);

export function Taxon({ name, authority }: { name: string; authority?: string }) {
  const parts = name.split(/\s+/);
  return (
    <span>
      {parts.map((p, i) => (
        <span key={i}>
          {i > 0 && ' '}
          {ROMAN.has(p) ? <span className="not-italic">{p}</span> : <i>{p}</i>}
        </span>
      ))}
      {authority && <span className="not-italic text-ink-subtle"> {authority}</span>}
    </span>
  );
}
