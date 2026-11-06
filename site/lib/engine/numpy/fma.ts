/**
 * Correctly rounded fused multiply-add, fma(a, b, c) = RN(a * b + c), in plain double arithmetic.
 *
 * Why: NumPy's C sampling code computes `lower + range * next_double` (random_uniform) and the ziggurat accept test
 * `(fi[i-1] - fi[i]) * next_double + fi[i]`; the macOS arm64 build that produced the pipeline's results contracts these
 * into hardware FMA (one rounding). JavaScript has no FMA, and an unfused a * b + c differs in the last bit in about
 * 4.5% of uniform draws, so the port emulates it.
 *
 * Algorithm: Boldo & Melquiond, "Emulation of FMA and correctly rounded sums: proved algorithms using rounding to odd",
 * IEEE Trans. Computers 57(4), 2008, Algorithm 5.4: (uh, ul) = ExactMult(a, b); (th, tl) = TwoSum(c, uh);
 * v = RO(tl + ul) (rounded to odd); result = RN(th + v). ExactMult is Dekker's product with Veltkamp splitting.
 * Valid without overflow or underflow, which holds for the model's values (|a|, |b|, |c| well inside [2^-500, 2^500]).
 */
const SPLIT = 134217729; // 2^27 + 1
const f64 = new Float64Array(1);
const u64 = new BigUint64Array(f64.buffer);
const i32 = new Uint32Array(f64.buffer); // little-endian: i32[0] is the low word

/** Round a + b to odd: the exact sum if representable, else the neighbour (of RN(a + b)) whose last mantissa bit is 1. */
function roundToOdd(a: number, b: number): number {
  const s = a + b;
  const bb = s - a;
  const err = (a - (s - bb)) + (b - bb); // TwoSum error: a + b = s + err exactly
  if (err === 0 || s === 0) return s;
  f64[0] = s;
  if ((i32[0] & 1) === 1) return s; // already odd
  // even and inexact: the true value lies on err's side of s; step one ulp toward it (stays within the same binade
  // except at a power of two, where the step toward zero lands on an odd significand as well)
  const towardZero = (s > 0) !== (err > 0);
  u64[0] = towardZero ? u64[0] - 1n : u64[0] + 1n;
  return f64[0];
}

export function fma(a: number, b: number, c: number): number {
  // ExactMult (Dekker): uh + ul = a * b
  const uh = a * b;
  let t = SPLIT * a;
  const ah = t - (t - a);
  const al = a - ah;
  t = SPLIT * b;
  const bh = t - (t - b);
  const bl = b - bh;
  const ul = al * bl - (((uh - ah * bh) - al * bh) - ah * bl);
  // TwoSum: th + tl = c + uh
  const th = c + uh;
  const z = th - c;
  const tl = (c - (th - z)) + (uh - z);
  return th + roundToOdd(tl, ul);
}
