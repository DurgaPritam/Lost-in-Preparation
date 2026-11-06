/**
 * NumPy 2.4.6's np.percentile (method 'linear') and np.median, and Python's round(x, 4), reproduced exactly.
 * Source: numpy/lib/_function_base_impl.py (_quantile, _get_indexes, _get_gamma, _lerp; _median).
 */

/** Sort a copy ascending (numeric; slice is a memory copy, unlike Float64Array.from). */
export function sorted(x: Float64Array): Float64Array {
  return x.slice().sort();
}

/** Wirth's selection: after the call a[k] is the k-th smallest of a[l..r], everything left of it is <= and everything
 *  right of it is >=. Gives exactly the values a full sort would (order statistics are unique). */
function select(a: Float64Array, l: number, r: number, k: number): void {
  while (l < r) {
    const x = a[k];
    let i = l;
    let j = r;
    do {
      while (a[i] < x) i++;
      while (x < a[j]) j--;
      if (i <= j) { const t = a[i]; a[i] = a[j]; a[j] = t; i++; j--; }
    } while (i <= j);
    if (j < k) l = i;
    if (k < i) r = j;
  }
}

let scratch = new Float64Array(0);

/** The sorted array's values at the given ranks (ascending), from a copy of x, without sorting it. A rank right after
 *  the previous one is the minimum of the elements to its right (no second selection needed). */
function orderStats(x: Float64Array, ranks: number[], inPlace = false): number[] {
  const n = x.length;
  let a = x;
  if (!inPlace) {
    if (scratch.length < n) scratch = new Float64Array(n);
    a = scratch.subarray(0, n);
    a.set(x);
  }
  const out: number[] = [];
  let l = 0;
  let prev = -2;
  for (const k of ranks) {
    if (k === prev + 1) {
      // a[k..n-1] are all >= a[prev]; the next order statistic is their minimum. Move it to position k.
      let m = k;
      for (let i = k + 1; i < n; i++) if (a[i] < a[m]) m = i;
      const t = a[k]; a[k] = a[m]; a[m] = t;
    } else {
      select(a, l, n - 1, k);
    }
    out.push(a[k]);
    prev = k;
    l = k + 1 > n - 1 ? n - 1 : k + 1;
  }
  return out;
}

interface Plan { ranks: number[]; terms: { a: number; b: number; gamma: number; last: boolean }[] }
const plans = new Map<string, Plan>();

function planFor(n: number, qs: number[]): Plan {
  const key = `${n}:${qs.join(',')}`;
  let p = plans.get(key);
  if (p) return p;
  const raw = qs.map((q) => {
    const v = (n - 1) * (q / 100); // numpy: virtual index (n - 1) * (q / 100)
    if (v >= n - 1) return { prev: n - 1, gamma: 0, last: true };
    if (v < 0) return { prev: 0, gamma: 0, last: true };
    const prev = Math.floor(v);
    return { prev, gamma: v - prev, last: false };
  });
  const ranks = [...new Set(raw.flatMap((t) => (t.last ? [t.prev] : [t.prev, t.prev + 1])))].sort((a, b) => a - b);
  p = { ranks, terms: raw.map((t) => ({ a: ranks.indexOf(t.prev), b: t.last ? -1 : ranks.indexOf(t.prev + 1), gamma: t.gamma, last: t.last })) };
  plans.set(key, p);
  return p;
}

/** np.percentile(x, qs) (method 'linear') of an unsorted array, for ascending qs. `inPlace`: x may be reordered
 *  (for temporary arrays; never for cached or shared ones). */
export function percentiles(x: Float64Array, qs: number[], inPlace = false): number[] {
  const p = planFor(x.length, qs);
  const vals = orderStats(x, p.ranks, inPlace);
  return p.terms.map((t) => {
    const a = vals[t.a];
    if (t.last) return a;
    const b = vals[t.b];
    const diff = b - a;
    return t.gamma >= 0.5 ? b - diff * (1 - t.gamma) : a + diff * t.gamma; // numpy _lerp
  });
}

/** np.median of an unsorted array; a constant array (common: factors that are 1 everywhere) needs no selection. */
export function median(x: Float64Array, inPlace = false): number {
  const v = x[0];
  let constant = true;
  for (let i = 1; i < x.length; i++) if (x[i] !== v) { constant = false; break; }
  if (constant) return v;
  const n = x.length;
  const h = n >> 1;
  if (n % 2) return orderStats(x, [h], inPlace)[0];
  const [a, b] = orderStats(x, [h - 1, h], inPlace);
  return (a + b) / 2;
}

/** np.percentile(x, q) for q in [0, 100] on an already sorted array, method 'linear'. */
export function percentileSorted(s: Float64Array, q: number): number {
  const n = s.length;
  const v = (n - 1) * (q / 100); // virtual index: (n - 1) * quantile, quantile = q / 100
  if (v >= n - 1) return s[n - 1];
  if (v < 0) return s[0];
  const prev = Math.floor(v);
  const gamma = v - prev;
  const a = s[prev];
  const b = s[prev + 1];
  const diff = b - a;
  // _lerp: a + diff * t, replaced by b - diff * (1 - t) where t >= 0.5
  return gamma >= 0.5 ? b - diff * (1 - gamma) : a + diff * gamma;
}

/** np.median on an already sorted array: the middle value, or the mean of the two middle values. */
export function medianSorted(s: Float64Array): number {
  const n = s.length;
  const h = n >> 1;
  return n % 2 ? s[h] : (s[h - 1] + s[h]) / 2;
}

/** Python round(x, 4). A tie at 4 decimals cannot occur for a binary double (x * 10^4 would need a factor 5^4), so
 *  toFixed's exact decimal rounding agrees with Python's correctly rounded result. */
export function round4(x: number): number {
  const r = Number(x.toFixed(4));
  return r === 0 ? 0 : r; // no negative zero
}
