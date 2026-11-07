/**
 * SITE: copied from design/v2 src/ia.ts; paths carry the trailing slash the static export serves (/lab/ etc.).
 *
 * Information architecture v2 — a product, not a report.
 * The front door is the promise and a live demo; Methods & data is a
 * documentation section reached last. `question` is what each page answers.
 */
export interface Route {
  id: 'landing' | 'lab' | 'atlas' | 'gap' | 'case' | 'planner' | 'docs';
  path: string;
  label: string;
  question: string;
  /** Honesty treatments the page must surface (DESIGN.md §4 numbering). */
  treatments: number[];
  /** Shown in the top navigation. */
  nav: boolean;
}

export const ROUTES: Route[] = [
  { id: 'landing', path: '/', label: 'Home', question: 'Historical remedies were recipes, not just plants. What does each preparation actually extract?', treatments: [4, 5, 7, 8], nav: false },
  { id: 'lab', path: '/lab/', label: 'Preparation Lab', question: 'If I change the solvent, heat, filtration or acidity, what happens to the compound profile?', treatments: [1, 2, 4, 5, 6, 7, 8], nav: true },
  { id: 'atlas', path: '/atlas/', label: 'Recipe Atlas', question: 'What did Culpeper and Pliny prescribe, and how was it prepared?', treatments: [1, 2, 3, 7, 8], nav: true },
  { id: 'gap', path: '/evidence-gap/', label: 'Evidence gap', question: 'How often do modern studies say how they prepared the plant?', treatments: [1, 4, 8], nav: true },
  { id: 'case', path: '/case/liquorice/', label: 'Case study', question: 'What changes when a liquorice recipe is read as a recipe?', treatments: [1, 4, 5, 6, 7], nav: true },
  { id: 'planner', path: '/planner/', label: 'Lab Planner', question: 'Which experiments should a lab run first?', treatments: [1, 4, 7, 8], nav: true },
  { id: 'docs', path: '/docs/', label: 'Methods & data', question: 'How was all of this produced, how far has it been checked, and can I reuse it?', treatments: [1, 2, 4, 5, 6, 8], nav: true },
];
