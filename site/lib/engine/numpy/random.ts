/**
 * An exact port of the parts of NumPy 2.4.6's random module that the preparation model (M4) uses, so the browser
 * reproduces the pipeline's Monte Carlo draws bit for bit:
 *
 *   numpy.random.default_rng(seed)   SeedSequence(seed) -> generate_state(4, uint64) -> PCG64 (XSL-RR 128/64)
 *   Generator.uniform(lo, hi, n)     lo + (hi - lo) * next_double          next_double = (next_uint64 >> 11) * 2^-53
 *   Generator.random(n)              next_double
 *   Generator.choice(3 items, n)     integers(0, 3): Lemire's bounded method on next_uint32 (buffered halves)
 *   Generator.normal(loc, sd, n)     loc + sd * ziggurat standard normal (NumPy's tables, zigguratTables.ts)
 *
 * Sources: numpy/random/bit_generator.pyx (SeedSequence), numpy/random/src/pcg64/pcg64.{h,c}, numpy/random/_pcg64.pyx,
 * numpy/random/src/distributions/distributions.c, numpy/random/_common.pxd (BSD-3-Clause, see zigguratTables.ts).
 *
 * Every model draw for one preparation reads the same stream (the pipeline reseeds per compound with the same seed),
 * so a stream is generated once (BigInt arithmetic) and cached as 32-bit halves; each compound reads it through a
 * fresh Cursor.
 */
import { fma } from './fma';
import { FI_DOUBLE, KI_DOUBLE, WI_DOUBLE, ZIGGURAT_NOR_INV_R, ZIGGURAT_NOR_R } from './zigguratTables';

const MASK64 = (1n << 64n) - 1n;
const MASK128 = (1n << 128n) - 1n;
const PCG_MULT = (2549297995355413924n << 64n) | 4865540595714422341n; // PCG_DEFAULT_MULTIPLIER_128
const TWO_POW_M53 = 1 / 9007199254740992;

/** SeedSequence(entropy).generate_state(n64, uint64), pool size 4, no spawn key. */
export function seedSequenceState(entropy: number | bigint, n64 = 4): bigint[] {
  let e = BigInt(entropy);
  if (e < 0n) throw new Error('expected non-negative entropy');
  const ent: number[] = [];
  if (e === 0n) ent.push(0);
  while (e > 0n) { ent.push(Number(e & 0xffffffffn)); e >>= 32n; }
  const pool = new Uint32Array(4);
  let hashA = 0x43b0d7e5;
  const hashmix = (value: number): number => {
    let v = (value ^ hashA) >>> 0;
    hashA = Math.imul(hashA, 0x931e8875) >>> 0;
    v = Math.imul(v, hashA) >>> 0;
    return (v ^ (v >>> 16)) >>> 0;
  };
  const mix = (x: number, y: number): number => {
    const r = (Math.imul(0xca01f9dd, x) - Math.imul(0x4973f715, y)) >>> 0;
    return (r ^ (r >>> 16)) >>> 0;
  };
  for (let i = 0; i < 4; i++) pool[i] = hashmix(i < ent.length ? ent[i] : 0);
  for (let s = 0; s < 4; s++) for (let d = 0; d < 4; d++) if (s !== d) pool[d] = mix(pool[d], hashmix(pool[s]));
  for (let s = 4; s < ent.length; s++) for (let d = 0; d < 4; d++) pool[d] = mix(pool[d], hashmix(ent[s]));
  let hashB = 0x8b51f9dd;
  const words: number[] = [];
  for (let i = 0; i < n64 * 2; i++) {
    let v = (pool[i % 4] ^ hashB) >>> 0;
    hashB = Math.imul(hashB, 0x58f38ded) >>> 0;
    v = Math.imul(v, hashB) >>> 0;
    words.push((v ^ (v >>> 16)) >>> 0);
  }
  const out: bigint[] = [];
  for (let k = 0; k < n64; k++) out.push((BigInt(words[2 * k + 1]) << 32n) | BigInt(words[2 * k])); // little-endian view
  return out;
}

/** PCG64 bit generator as numpy seeds it from an integer. */
export class PCG64 {
  private state = 0n;
  private readonly inc: bigint;
  constructor(seed: number | bigint) {
    const v = seedSequenceState(seed, 4);
    const initstate = (v[0] << 64n) | v[1]; // pcg64_set_seed: seed[0] is the high word
    const initseq = (v[2] << 64n) | v[3];
    this.inc = ((initseq << 1n) | 1n) & MASK128;
    this.step();
    this.state = (this.state + initstate) & MASK128;
    this.step();
  }
  private step(): void { this.state = (this.state * PCG_MULT + this.inc) & MASK128; }
  /** next_uint64 (pcg_setseq_128_xsl_rr_64_random_r) */
  next64(): bigint {
    this.step();
    const s = this.state;
    const x = ((s >> 64n) ^ s) & MASK64;
    const rot = BigInt(Number(s >> 122n));
    return ((x >> rot) | (x << ((64n - rot) & 63n))) & MASK64;
  }
}

/** The raw uint64 stream of one seed, generated on demand and cached as (hi, lo) 32-bit halves. */
export class RawStream {
  private gen: PCG64;
  hi = new Uint32Array(0);
  lo = new Uint32Array(0);
  length = 0;
  /** Uniform draws by range, position by position (fma(range, next_double[pos], lo)): every compound of a preparation
   *  reads the same stream, so each value is computed once. */
  private uniforms = new Map<string, { values: Float64Array; filled: number }>();
  constructor(readonly seed: number) { this.gen = new PCG64(seed); }
  uniformAt(lo: number, range: number, pos: number, n: number): Float64Array {
    const key = `${lo}:${range}`;
    let u = this.uniforms.get(key);
    if (!u) { u = { values: new Float64Array(0), filled: 0 }; this.uniforms.set(key, u); }
    const end = pos + n;
    if (end > u.filled) {
      this.ensure(end);
      if (end > u.values.length) {
        const grown = new Float64Array(Math.max(end, u.values.length * 2, 4096));
        grown.set(u.values.subarray(0, u.filled));
        u.values = grown;
      }
      for (let i = u.filled; i < end; i++) u.values[i] = fma(range, (this.hi[i] * 2097152 + (this.lo[i] >>> 11)) * TWO_POW_M53, lo);
      u.filled = end;
    }
    return u.values.subarray(pos, end);
  }
  ensure(n: number): void {
    if (n <= this.length) return;
    const cap = Math.max(n, this.length * 2, 4096);
    if (cap > this.hi.length) {
      const hi = new Uint32Array(cap); hi.set(this.hi.subarray(0, this.length));
      const lo = new Uint32Array(cap); lo.set(this.lo.subarray(0, this.length));
      this.hi = hi; this.lo = lo;
    }
    for (let i = this.length; i < cap; i++) {
      const r = this.gen.next64();
      this.hi[i] = Number(r >> 32n);
      this.lo[i] = Number(r & 0xffffffffn);
    }
    this.length = cap;
  }
}

/** A Generator's position in a stream: next_double, the buffered next_uint32, and the fill methods M4 calls. */
export class Cursor {
  pos = 0;
  private hasU32 = false;
  private u32 = 0;
  constructor(private readonly s: RawStream) {}
  nextDouble(): number {
    if (this.pos >= this.s.length) this.s.ensure(this.pos + 1);
    const i = this.pos++;
    return (this.s.hi[i] * 2097152 + (this.s.lo[i] >>> 11)) * TWO_POW_M53; // (u64 >> 11) * 2^-53, exact
  }
  /** pcg64_next32: low half first, the high half is buffered for the next call. */
  nextUint32(): number {
    if (this.hasU32) { this.hasU32 = false; return this.u32; }
    if (this.pos >= this.s.length) this.s.ensure(this.pos + 1);
    const i = this.pos++;
    this.hasU32 = true;
    this.u32 = this.s.hi[i];
    return this.s.lo[i];
  }
  /** Generator.uniform(lo, hi, n) into out (random_uniform: lo + range * next_double, range = hi - lo, computed as
   *  one fused multiply-add as in NumPy's arm64 build; see fma.ts). */
  uniform(range: readonly number[], n: number): Float64Array {
    const v = this.s.uniformAt(range[0], range[1] - range[0], this.pos, n); // a read-only view of the cached draws
    this.pos += n;
    return v;
  }
  /** Generator.random(n) */
  random(n: number, out: Float64Array = new Float64Array(n)): Float64Array {
    for (let i = 0; i < n; i++) out[i] = this.nextDouble();
    return out;
  }
  /** Generator.integers(0, high) for high <= 2^32 - 1 (random_bounded_uint64_fill -> buffered_bounded_lemire_uint32). */
  integers(high: number, n: number, out: Int32Array = new Int32Array(n)): Int32Array {
    const rng = high - 1;
    const excl = rng + 1;
    const threshold = (0xffffffff - rng) % excl;
    for (let i = 0; i < n; i++) {
      let m = this.nextUint32() * excl; // < 2^53: exact
      let leftover = m % 4294967296;
      if (leftover < excl) {
        while (leftover < threshold) { m = this.nextUint32() * excl; leftover = m % 4294967296; }
      }
      out[i] = Math.floor(m / 4294967296);
    }
    return out;
  }
}

/** default_rng(seed).normal(0.0, 1.0, n): NumPy's ziggurat (random_standard_normal). */
export function standardNormals(seed: number, n: number): Float64Array {
  const s = new RawStream(seed);
  const c = new Cursor(s);
  const out = new Float64Array(n);
  for (let k = 0; k < n; k++) {
    for (;;) {
      if (c.pos >= s.length) s.ensure(c.pos + 1);
      const i = c.pos++;
      const hi = s.hi[i];
      const lo = s.lo[i];
      const idx = lo & 0xff;
      const sign = (lo >>> 8) & 1;
      const rabs = (lo >>> 9) + (hi & 0x1fffffff) * 8388608; // (r >> 9) & (2^52 - 1)
      let x = rabs * WI_DOUBLE[idx];
      if (sign) x = -x;
      if (rabs < KI_DOUBLE[idx]) { out[k] = x; break; }
      if (idx === 0) {
        let done = false;
        while (!done) {
          const xx = -ZIGGURAT_NOR_INV_R * Math.log1p(-c.nextDouble());
          const yy = -Math.log1p(-c.nextDouble());
          if (yy + yy > xx * xx) {
            out[k] = Math.floor(rabs / 256) % 2 ? -(ZIGGURAT_NOR_R + xx) : ZIGGURAT_NOR_R + xx;
            done = true;
          }
        }
        break;
      }
      if (fma(FI_DOUBLE[idx - 1] - FI_DOUBLE[idx], c.nextDouble(), FI_DOUBLE[idx]) < Math.exp(-0.5 * x * x)) { out[k] = x; break; }
    }
  }
  return out;
}

