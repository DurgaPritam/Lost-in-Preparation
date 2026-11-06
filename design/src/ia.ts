/**
 * Information architecture. Seven top-level destinations, in reading order of
 * the argument: what it is → the sources → the comparison → the audit →
 * what follows → how much to trust it → what it's built on.
 * `question` is the one question each page answers; use it as the page's
 * subtitle so judges always know why they are on a page.
 */
export interface Route {
  id: 'home' | 'recipes' | 'compare' | 'audit' | 'hypotheses' | 'methods' | 'data';
  path: string;
  label: string;
  question: string;
  primaryObjects: string[];
  /** Honesty treatments this page must surface (DESIGN.md §4 numbering). */
  treatments: number[];
}

export const ROUTES: Route[] = [
  {
    id: 'home', path: '/', label: 'Home',
    question: 'What does this tool claim, and how far should I trust it?',
    primaryObjects: ['Project summary', 'Pipeline diagram', 'Coverage counts by evidence status', 'Entry points'],
    treatments: [1, 2, 5, 8],
  },
  {
    id: 'recipes', path: '/recipes', label: 'Recipe explorer',
    question: 'What did Culpeper and Pliny actually prescribe, and how was it prepared?',
    primaryObjects: ['Recipe list (filter by source, vehicle, plant, status)', 'Recipe detail drawer: passage, name resolution, preparation, predicted extraction'],
    treatments: [1, 2, 3, 4, 5, 6, 7, 8],
  },
  {
    id: 'compare', path: '/compare', label: 'Compare',
    question: 'For one plant, how does the historical preparation differ from how modern studies prepared it?',
    primaryObjects: ['Plant picker', 'Side-by-side historical vs modern preparations', 'Paired likelihood ranges per compound class'],
    treatments: [3, 4, 5, 6, 7, 8],
  },
  {
    id: 'audit', path: '/audit', label: 'Audit',
    question: 'Did modern studies test the preparation the sources described?',
    primaryObjects: ['Study-by-study preparation audit table', 'Mismatch categories (vehicle, heat, filtering, not stated)'],
    treatments: [1, 4, 7, 8],
  },
  {
    id: 'hypotheses', path: '/hypotheses', label: 'Hypotheses',
    question: 'Which preparation–compound pairs are worth re-testing, and why?',
    primaryObjects: ['Ranked hypothesis list (rank by range, not point)', 'Hypothesis detail: reasoning chain, every input’s status'],
    treatments: [1, 2, 3, 4, 5, 6, 7, 8],
  },
  {
    id: 'methods', path: '/methods', label: 'Methods & validation',
    question: 'How were names resolved and extraction estimated, and what has been checked by people?',
    primaryObjects: ['Pipeline steps', 'Heuristics register', 'Validation status counts', 'Known limitations'],
    treatments: [1, 2, 4, 5, 6],
  },
  {
    id: 'data', path: '/data', label: 'Data & licences',
    question: 'Where does every record come from, and can I reuse it?',
    primaryObjects: ['Source editions and transcriptions', 'Datasets and licences', 'Download links', 'Schema reference'],
    treatments: [2, 8],
  },
];
