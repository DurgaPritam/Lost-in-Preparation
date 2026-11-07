import { useEffect, useState } from 'react';
import { Landing } from './Landing';
import { Lab, type Heat, type Settings, type Solvent } from './Lab';
import { Atlas, RecipePage } from './Atlas';
import { EvidenceGap } from './EvidenceGap';
import { CaseStudy } from './CaseStudy';
import { LabPlanner } from './LabPlanner';
import { Docs } from './Docs';
import { EmptyState, LinkButton, SiteShell } from '../index';
import { recipes } from '../contract';

/**
 * Hash router for local review (v2). Replace with the production router; the
 * paths are the real ones from src/ia.ts plus one child route:
 *   #/                         Landing
 *   #/lab?plant=&solvent=&heat=&strained=&acid=   Preparation Lab (params optional)
 *   #/atlas   #/recipes/:id    Recipe Atlas and a recipe page
 *   #/evidence-gap   #/case/liquorice   #/planner   #/docs?s=section
 * Old v1 paths redirect: /recipes → /atlas, /compare → /lab, /audit → /docs
 * (studies), /hypotheses → /planner, /methods and /data → /docs.
 */
type View =
  | { name: 'landing' } | { name: 'lab'; plant?: string; initial: Partial<Settings>; key: string }
  | { name: 'atlas' } | { name: 'recipe'; id: string } | { name: 'gap' } | { name: 'case' }
  | { name: 'planner' } | { name: 'docs'; section?: string } | { name: 'missing'; path: string };

const SOLVENTS: Solvent[] = ['water', 'wine', 'vinegar', 'oil', 'honey'];
const HEATS: Heat[] = ['cold', 'warm', 'boiled'];
const bool = (v: string | null) => (v === 'true' ? true : v === 'false' ? false : undefined);

export function parse(hash: string): View {
  const path = hash.replace(/^#/, '') || '/';
  // "/docs#studies" inside the hash: keep the fragment as a section.
  const [beforeFrag, frag] = path.split('#');
  const [p, q = ''] = beforeFrag.split('?');
  const qs = new URLSearchParams(q);
  if (p.startsWith('/recipes/')) return { name: 'recipe', id: decodeURIComponent(p.slice('/recipes/'.length)) };
  switch (p) {
    case '/': return { name: 'landing' };
    case '/lab': case '/compare': {
      const initial: Partial<Settings> = {};
      const s = qs.get('solvent'); if (s && (SOLVENTS as string[]).includes(s)) initial.solvent = s as Solvent;
      const h = qs.get('heat'); if (h && (HEATS as string[]).includes(h)) initial.heat = h as Heat;
      const f = bool(qs.get('strained')); if (f !== undefined) initial.filtered = f;
      const a = bool(qs.get('acid')); if (a !== undefined) initial.acidified = a;
      const plant = qs.get('plant') ?? qs.get('species') ?? undefined;
      return { name: 'lab', plant, initial, key: beforeFrag };
    }
    case '/atlas': case '/recipes': return { name: 'atlas' };
    case '/evidence-gap': return { name: 'gap' };
    case '/case/liquorice': return { name: 'case' };
    case '/planner': case '/hypotheses': return { name: 'planner' };
    case '/docs': return { name: 'docs', section: frag ?? qs.get('s') ?? undefined };
    case '/audit': return { name: 'docs', section: 'studies' };
    case '/methods': case '/data': return { name: 'docs' };
    default: return { name: 'missing', path: p };
  }
}

export default function App() {
  const [view, setView] = useState<View>(() => parse(location.hash));
  useEffect(() => {
    const on = () => { setView(parse(location.hash)); window.scrollTo(0, 0); };
    window.addEventListener('hashchange', on);
    return () => window.removeEventListener('hashchange', on);
  }, []);
  useEffect(() => {
    if (view.name !== 'docs' || !view.section) return;
    const id = view.section;
    requestAnimationFrame(() => document.getElementById(id)?.scrollIntoView({ block: 'start' }));
  }, [view]);
  const nav = (path: string) => { location.hash = path; };

  switch (view.name) {
    case 'lab': return <Lab key={view.key} onNavigate={nav} initialPlant={view.plant} initial={view.initial} />;
    case 'atlas': return <Atlas onNavigate={nav} />;
    case 'recipe': {
      const r = recipes.find((x) => x.id === view.id);
      if (!r) return <Missing path={`/recipes/${view.id}`} nav={nav} />;
      return <RecipePage key={r.id} recipe={r} onNavigate={nav} />;
    }
    case 'gap': return <EvidenceGap onNavigate={nav} />;
    case 'case': return <CaseStudy onNavigate={nav} />;
    case 'planner': return <LabPlanner onNavigate={nav} />;
    case 'docs': return <Docs onNavigate={nav} />;
    case 'missing': return <Missing path={view.path} nav={nav} />;
    default: return <Landing onNavigate={nav} />;
  }
}

function Missing({ path, nav }: { path: string; nav: (p: string) => void }) {
  return (
    <SiteShell current="landing" onNavigate={nav}>
      <EmptyState
        title="No page at this address"
        body={<>Nothing lives at <code className="font-mono">{path}</code>.</>}
        action={<LinkButton href="/" onClick={(e) => { e.preventDefault(); nav('/'); }}>Back to the start</LinkButton>}
      />
    </SiteShell>
  );
}
