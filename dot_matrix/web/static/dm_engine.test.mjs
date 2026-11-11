// Node test: the JS port (pil_ops.js, dm_engine.js, dm_shapes.js) against the repo's Python on the same test image.
// Fixture: tests/fixtures/dm_fixture.json, written by scripts/make_dm_fixture.py. Run: node dm_engine.test.mjs
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { makeImage } from './pil_ops.js';
import { preprocess, sampleMatrix, computeDots, extractDominantColors } from './dm_engine.js';
import { shapePrimitives, svgCircles, hexToRgb } from './dm_shapes.js';

const FIX = JSON.parse(readFileSync(fileURLToPath(new URL('../../../tests/fixtures/dm_fixture.json', import.meta.url)), 'utf8'));
const bytes = s => new Uint8Array(Buffer.from(s, 'base64'));
const img = makeImage(FIX.image.w, FIX.image.h, 3, bytes(FIX.image.rgb));
// Pixel tolerance for steps that use float32 in Pillow's C code (3x3 filters, blends): the macOS arm64 wheel may fuse
// multiply-adds, which moves a value across an integer boundary in rare cases.
const PIXEL_TOL = 1;

let failures = 0, checks = 0;
function check(ok, msg) { checks++; if (!ok) { failures++; console.log('FAIL', msg); } }

function options(p) {
  const on = k => ['1', 'true', 'on'].includes(String(p[k] ?? ''));
  return {
    effect: p.effect || 'none', edgeEnhance: on('edge_enhance'), noiseReduce: on('noise_reduce'),
    mw: +(p.matrix_width ?? 45), mh: +(p.matrix_height ?? 19), outW: +(p.output_width ?? 900), outH: +(p.output_height ?? 380),
    spacing: +(p.spacing ?? 1.0), animate: on('animate'), frame: on('animate') ? +(p.frame ?? 0) : 0,
    usePalette: on('use_palette'), palette: FIX.palettes[p.palette ?? 'Classic B&W'], background: hexToRgb(p.background),
  };
}

function diff(a, b) {
  let max = 0, n = 0;
  for (let i = 0; i < a.length; i++) { const d = Math.abs(a[i] - b[i]); if (d) { n++; max = Math.max(max, d); } }
  return { max, n };
}

// 1. Effects / preprocessing: full images.
function tile(im, n) {   // np.tile along x
  if (!n || n === 1) return im;
  const out = new Uint8Array(im.data.length * n), row = im.w * 3;
  for (let y = 0; y < im.h; y++) for (let k = 0; k < n; k++) out.set(im.data.subarray(y * row, (y + 1) * row), (y * n + k) * row);
  return makeImage(im.w * n, im.h, 3, out);
}
for (const c of FIX.effects) {
  const got = preprocess(tile(img, c.params.tile), options(c.params)).data, want = bytes(c.rgb);
  const d = diff(got, want);
  check(got.length === want.length && d.max <= PIXEL_TOL, `effect ${JSON.stringify(c.params)}: max diff ${d.max} in ${d.n} values`);
  if (d.n) console.log(`  note: effect ${JSON.stringify(c.params)} differs by ${d.max} in ${d.n}/${want.length} values`);
}

// 2. Matrices and dots.
for (const c of FIX.matrices) {
  const o = options(c.params);
  const work = preprocess(img, o);
  const m = sampleMatrix(work, o.mw, o.mh, o.usePalette ? o.palette : null);
  const db = diff(m.brightness, bytes(c.brightness));
  check(db.max <= PIXEL_TOL, `brightness ${JSON.stringify(c.params)}: max diff ${db.max} in ${db.n}`);
  const exact = db.n === 0;
  if (!exact) console.log(`  note: brightness ${JSON.stringify(c.params)} differs by ${db.max} in ${db.n}/${m.brightness.length} cells`);
  if (c.colors) {
    const dc = diff(m.colors, bytes(c.colors));
    check(exact ? dc.n === 0 : dc.n <= 3 * db.n, `palette colours ${JSON.stringify(c.params)}: ${dc.n} differ`);
  }
  if (!c.dots) continue;
  const dots = computeDots(m, o);
  if (exact) {
    check(dots.length === c.dots.length, `dot count ${dots.length} vs ${c.dots.length} for ${JSON.stringify(c.params)}`);
    let worst = 0;
    dots.forEach((d, k) => {
      const [x, y, r, col] = c.dots[k] || [NaN, NaN, NaN, null];
      worst = Math.max(worst, Math.abs(d.x - x), Math.abs(d.y - y), Math.abs(d.r - r) / Math.max(1, r));
      check(JSON.stringify(d.color) === JSON.stringify(col), `dot colour ${k} ${JSON.stringify(c.params)}`);
    });
    check(worst < 1e-9, `dot geometry ${JSON.stringify(c.params)}: worst ${worst}`);
    if (c.svg) {
      const svg = svgCircles(dots, o.outW, o.outH, o.background);
      check(svg === c.svg, `SVG text differs for ${JSON.stringify(c.params)}`);
    }
  }
}

// 3. Shapes: the ImageDraw calls of every pattern (stipple is random in the Python and not compared).
let worstShape = 0;
for (const s of FIX.shapes) {
  const got = shapePrimitives(s.pattern, s.cx, s.cy, s.r);
  check(got.length === s.calls.length, `${s.pattern} r=${s.r}: ${got.length} vs ${s.calls.length} primitives`);
  got.forEach((p, k) => {
    const q = s.calls[k] || {};
    check(p.t === q.t, `${s.pattern} primitive ${k} type ${p.t} vs ${q.t}`);
    const a = p.box || (p.pts ? p.pts.flat() : [p.x, p.y]), b = q.box || (q.pts ? q.pts.flat() : [q.x, q.y]);
    check(a.length === b.length, `${s.pattern} primitive ${k} length`);
    a.forEach((v, i) => { worstShape = Math.max(worstShape, Math.abs(v - b[i])); });
    if (p.t === 'text') check(p.ch === q.ch, `ascii char ${p.ch} vs ${q.ch}`);
  });
}
check(worstShape < 1e-9, `shape coordinates worst diff ${worstShape}`);

// 4. Dominant colours.
const dom = extractDominantColors(img, 6);
check(JSON.stringify(dom) === JSON.stringify(FIX.dominant), `dominant colours ${JSON.stringify(dom)} vs ${JSON.stringify(FIX.dominant)}`);

console.log(`${checks - failures}/${checks} checks passed; shape coordinates agree to ${worstShape.toExponential(1)}`);
process.exit(failures ? 1 : 0);
