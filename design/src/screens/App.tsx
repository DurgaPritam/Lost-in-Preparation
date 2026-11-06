import { useEffect, useState } from 'react';
import { Home } from './Home';
import { RecipeExplorer } from './RecipeExplorer';
import { RecipeDetail } from './RecipeDetail';
import { Compare } from './Compare';
import { Audit } from './Audit';
import { Hypotheses } from './Hypotheses';
import { Methods } from './Methods';
import { DataLicences } from './DataLicences';
import { recipes } from '../contract';

/**
 * Hash router for local review. Replace with the production router; the
 * paths are the real ones from src/ia.ts plus two child routes:
 *   #/  #/recipes  #/recipes/:id  #/compare?species=…  #/audit  #/hypotheses  #/methods  #/data
 */
type View =
  | { name: 'home' } | { name: 'recipes' } | { name: 'recipe'; id: string } | { name: 'compare'; species?: string }
  | { name: 'audit' } | { name: 'hypotheses' } | { name: 'methods' } | { name: 'data' };

function parse(hash: string): View {
  const path = hash.replace(/^#/, '') || '/';
  const [p, q] = path.split('?');
  if (p.startsWith('/recipes/')) return { name: 'recipe', id: decodeURIComponent(p.slice('/recipes/'.length)) };
  switch (p) {
    case '/recipes': return { name: 'recipes' };
    case '/compare': return { name: 'compare', species: new URLSearchParams(q).get('species') ?? undefined };
    case '/audit': return { name: 'audit' };
    case '/hypotheses': return { name: 'hypotheses' };
    case '/methods': return { name: 'methods' };
    case '/data': return { name: 'data' };
    default: return { name: 'home' };
  }
}

export default function App() {
  const [view, setView] = useState<View>(() => parse(location.hash));
  useEffect(() => {
    const on = () => { setView(parse(location.hash)); window.scrollTo(0, 0); };
    window.addEventListener('hashchange', on);
    return () => window.removeEventListener('hashchange', on);
  }, []);
  const nav = (path: string) => { location.hash = path; };

  switch (view.name) {
    case 'recipes': return <RecipeExplorer onNavigate={nav} onOpen={(id) => nav(`/recipes/${id}`)} />;
    case 'recipe': {
      const r = recipes.find((x) => x.id === view.id) ?? recipes[0];
      return <RecipeDetail recipe={r} onNavigate={nav} onBack={() => nav('/recipes')} onCompare={(t) => nav(`/compare?species=${encodeURIComponent(t)}`)} />;
    }
    case 'compare': return <Compare key={view.species ?? ''} initialSpecies={view.species} onNavigate={nav} />;
    case 'audit': return <Audit onNavigate={nav} />;
    case 'hypotheses': return <Hypotheses onNavigate={nav} />;
    case 'methods': return <Methods onNavigate={nav} />;
    case 'data': return <DataLicences onNavigate={nav} />;
    default: return <Home onNavigate={nav} />;
  }
}
