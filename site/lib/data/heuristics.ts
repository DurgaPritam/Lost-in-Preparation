/** The model's heuristics (METHODS.md §9), as text. Whether one applies to a value is read from the data (profile
 *  `heuristic` flags); these entries only describe the rule. No numbers here. */
import type { Heuristic } from '../types';

export const HEURISTICS: Heuristic[] = [
  { id: 'heat_sensitivity', label: 'Heat sensitivity', rule: 'Heat is treated as lowering compounds flagged as heat-labile or volatile, with an assumed range; it is not fitted to data.' },
  { id: 'acidity', label: 'Acidity', rule: 'Acidic vehicles (vinegar, wine) are treated as favouring basic nitrogen compounds, which form salts; a rule of thumb with an assumed range.' },
  { id: 'filtration_carryover', label: 'Filtration carry-over', rule: 'Unfiltered preparations are treated as carrying some undissolved material; filtration lowers what is carried over.' },
  { id: 'likely_differ', label: 'Compounds likely to differ', rule: 'A compound counts when the 5th–95th range of its predicted difference between the two preparations excludes zero and the median difference reaches an assumed threshold (differ_delta in config/m8_qubo_v2.toml); not fitted to data.' },
  { id: 'compound_class', label: 'Compound class', rule: 'Compound classes come from simple structure rules, labelled “(heuristic)” in the data.' },
];
export const heuristic = (id: string) => HEURISTICS.find((h) => h.id === id);
