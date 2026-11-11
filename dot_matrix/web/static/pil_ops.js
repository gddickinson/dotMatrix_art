// Pure-JS port of the Pillow 13 operations the converter uses (no DOM): RGB->L, 3x3 kernel filters, blend/enhance,
// Gaussian blur (extended box blur), LANCZOS/BICUBIC resampling and NEAREST resize. Images are
// { w, h, c, data: Uint8Array } with c = 3 (RGB) or 1 (L). Ported from Pillow's C sources (Filter.c, Blend.c,
// BoxBlur.c, Resample.c, Geometry.c, Convert.c); float32 steps use Math.fround like the C code.
// Tested against Pillow output in dm_engine.test.mjs.

const f32 = Math.fround;

export function makeImage(w, h, c, data) { return { w, h, c, data: data || new Uint8Array(w * h * c) }; }
export function copyImage(im) { return makeImage(im.w, im.h, im.c, new Uint8Array(im.data)); }

// RGB -> L, ITU-R 601-2 luma in fixed point (Convert.c L24).
export function toL(im) {
  if (im.c === 1) return copyImage(im);
  const n = im.w * im.h, out = new Uint8Array(n), d = im.data;
  for (let i = 0, j = 0; i < n; i++, j += 3) out[i] = (d[j] * 19595 + d[j + 1] * 38470 + d[j + 2] * 7471 + 0x8000) >>> 16;
  return makeImage(im.w, im.h, 1, out);
}

export function toRGB(im) {
  if (im.c === 3) return copyImage(im);
  const n = im.w * im.h, out = new Uint8Array(n * 3);
  for (let i = 0; i < n; i++) out[3 * i] = out[3 * i + 1] = out[3 * i + 2] = im.data[i];
  return makeImage(im.w, im.h, 3, out);
}

// ImageFilter built-in 3x3 kernels: [scale, offset, kernel].
export const KERNELS = {
  SMOOTH: [13, 0, [1, 1, 1, 1, 5, 1, 1, 1, 1]],
  EDGE_ENHANCE: [2, 0, [-1, -1, -1, -1, 10, -1, -1, -1, -1]],
  EDGE_ENHANCE_MORE: [1, 0, [-1, -1, -1, -1, 9, -1, -1, -1, -1]],
  FIND_EDGES: [1, 0, [-1, -1, -1, -1, 8, -1, -1, -1, -1]],
  EMBOSS: [1, 128, [-1, 0, 0, 0, 1, 0, 0, 0, 0]],
};

const clip8f = v => (v < 0 ? 0 : v > 255 ? 255 : Math.trunc(v));

// ImagingFilter3x3: border pixels copied; kernel rows 0..2 apply to image rows y+1, y, y-1 (as in Filter.c).
export function filter3x3(im, name) {
  const [scale, off, kern] = KERNELS[name];
  const k = kern.map(v => f32(f32(v) / f32(scale)));
  const offset = f32(f32(off) + 0.5);
  const { w, h, c } = im, src = im.data, out = new Uint8Array(src);
  if (w < 3 || h < 3) return makeImage(w, h, c, out);   // Pillow returns a copy when the image is smaller than the kernel
  const row = (x, y, ch, k0) => f32(f32(f32(src[((y * w) + x - 1) * c + ch] * k[k0]) + f32(src[(y * w + x) * c + ch] * k[k0 + 1]))
    + f32(src[(y * w + x + 1) * c + ch] * k[k0 + 2]));
  for (let y = 1; y < h - 1; y++) {
    for (let x = 1; x < w - 1; x++) {
      for (let ch = 0; ch < c; ch++) {
        let ss = offset;
        ss = f32(ss + row(x, y + 1, ch, 0));
        ss = f32(ss + row(x, y, ch, 3));
        ss = f32(ss + row(x, y - 1, ch, 6));
        out[(y * w + x) * c + ch] = clip8f(ss);
      }
    }
  }
  return makeImage(w, h, c, out);
}

// Image.blend(im1, im2, alpha) (Blend.c), alpha as float32.
export function blend(a, b, alpha) {
  const al = f32(alpha), n = a.data.length, out = new Uint8Array(n), A = a.data, B = b.data;
  const inside = al >= 0 && al <= 1;
  for (let i = 0; i < n; i++) {
    const t = f32(A[i] + al * (B[i] - A[i]));   // one rounding (fused multiply-add, as in the arm64 build)
    out[i] = inside ? Math.trunc(t) : (t <= 0 ? 0 : t >= 255 ? 255 : Math.trunc(t));
  }
  return makeImage(a.w, a.h, a.c, out);
}

// ImageEnhance.Contrast: blend with a flat image of the mean luminance (rounded).
export function contrast(im, factor) {
  const L = toL(im).data;
  let sum = 0;
  for (let i = 0; i < L.length; i++) sum += L[i];
  const mean = Math.trunc(sum / L.length + 0.5);
  const deg = makeImage(im.w, im.h, im.c, new Uint8Array(im.data.length).fill(mean));
  return blend(deg, im, factor);
}

// ImageEnhance.Color: blend with the grayscale version.
export function color(im, factor) { return blend(im.c === 1 ? copyImage(im) : toRGB(toL(im)), im, factor); }

export function invert(im) { return makeImage(im.w, im.h, im.c, im.data.map(v => 255 - v)); }

export function lighter(a, b) {
  const out = new Uint8Array(a.data.length);
  for (let i = 0; i < out.length; i++) out[i] = Math.max(a.data[i], b.data[i]);
  return makeImage(a.w, a.h, a.c, out);
}

// --- Gaussian blur (BoxBlur.c) ----------------------------------------------------------------------------------
function gaussianBoxRadius(radius, passes) {
  const sigma2 = f32(f32(radius * radius) / passes);
  const L = f32(Math.sqrt(12.0 * sigma2 + 1.0));
  const l = f32(Math.floor((L - 1.0) / 2.0));
  let a = f32(f32(2 * l + 1) * f32(f32(l * f32(l + 1)) - f32(3 * sigma2)));
  a = f32(a / f32(6 * f32(sigma2 - f32(f32(l + 1) * f32(l + 1)))));
  return f32(l + a);
}

// One line of the extended box blur; line has `c` interleaved channels, `get(x, ch)` / `set(x, ch, v)` accessors.
function boxLine(get, set, c, lastx, radius, edgeA, edgeB, ww, fw) {
  const SH = 16777216;
  for (let ch = 0; ch < c; ch++) {
    let acc = get(0, ch) * (radius + 1);
    for (let x = 0; x < edgeA - 1; x++) acc += get(x, ch);
    acc += get(lastx, ch) * (radius - edgeA + 1);
    const out = [];
    const step = (x, sub, add, left, right) => {
      acc += get(add, ch) - get(sub, ch);
      const bulk = acc * ww + (get(left, ch) + get(right, ch)) * fw;
      out[x] = Math.floor((bulk + 8388608) / SH) & 255;
    };
    if (edgeA <= edgeB) {
      for (let x = 0; x < edgeA; x++) step(x, 0, x + radius, 0, x + radius + 1);
      for (let x = edgeA; x < edgeB; x++) step(x, x - radius - 1, x + radius, x - radius - 1, x + radius + 1);
      for (let x = edgeB; x <= lastx; x++) step(x, x - radius - 1, lastx, x - radius - 1, lastx);
    } else {
      for (let x = 0; x < edgeB; x++) step(x, 0, x + radius, 0, x + radius + 1);
      for (let x = edgeB; x < edgeA; x++) step(x, 0, lastx, 0, lastx);
      for (let x = edgeA; x <= lastx; x++) step(x, x - radius - 1, lastx, x - radius - 1, lastx);
    }
    for (let x = 0; x <= lastx; x++) set(x, ch, out[x]);
  }
}

function boxPass(data, w, h, c, floatRadius, horizontal) {
  const radius = Math.trunc(floatRadius);
  const ww = Math.trunc(f32(16777216 / f32(f32(floatRadius * 2) + 1)));
  const fw = Math.trunc((16777216 - (radius * 2 + 1) * ww) / 2);
  const len = horizontal ? w : h, lines = horizontal ? h : w;
  const edgeA = Math.min(radius + 1, len), edgeB = Math.max(len - radius - 1, 0);
  for (let l = 0; l < lines; l++) {
    const idx = horizontal ? (x, ch) => (l * w + x) * c + ch : (y, ch) => (y * w + l) * c + ch;
    boxLine((x, ch) => data[idx(x, ch)], (x, ch, v) => { data[idx(x, ch)] = v; }, c, len - 1, radius, edgeA, edgeB, ww, fw);
  }
}

export function gaussianBlur(im, radius, passes = 3) {
  const r = gaussianBoxRadius(f32(radius), passes);
  const data = new Uint8Array(im.data);
  if (r !== 0) {
    for (let i = 0; i < passes; i++) boxPass(data, im.w, im.h, im.c, r, true);
    for (let i = 0; i < passes; i++) boxPass(data, im.w, im.h, im.c, r, false);
  }
  return makeImage(im.w, im.h, im.c, data);
}

// --- Resampling (Resample.c) ------------------------------------------------------------------------------------
const sinc = x => { if (x === 0) return 1; x *= Math.PI; return Math.sin(x) / x; };
export const FILTERS = {
  lanczos: { support: 3, f: x => (-3 <= x && x < 3 ? sinc(x) * sinc(x / 3) : 0) },
  bicubic: { support: 2, f: x => { const a = -0.5; if (x < 0) x = -x;
    if (x < 1) return ((a + 2) * x - (a + 3)) * x * x + 1; if (x < 2) return (((x - 5) * x + 8) * x - 4) * a; return 0; } },
};
const PREC = 22;

function coeffs(inSize, outSize, filter) {
  const scale = inSize / outSize, filterscale = Math.max(scale, 1);
  const support = filter.support * filterscale, ksize = Math.ceil(support) * 2 + 1, inv = 1 / filterscale;
  const bounds = new Int32Array(outSize * 2), kk = new Int32Array(outSize * ksize);
  for (let xx = 0; xx < outSize; xx++) {
    const center = (xx + 0.5) * scale;
    const xmin = Math.max(Math.trunc(center - support + 0.5), 0);
    const xmax = Math.min(Math.trunc(center + support + 0.5), inSize) - xmin;
    const k = new Float64Array(xmax);
    let ww = 0;
    for (let x = 0; x < xmax; x++) { k[x] = filter.f((x + xmin - center + 0.5) * inv); ww += k[x]; }
    for (let x = 0; x < xmax; x++) {
      const v = ww !== 0 ? k[x] / ww : k[x];
      kk[xx * ksize + x] = v < 0 ? Math.trunc(-0.5 + v * (1 << PREC)) : Math.trunc(0.5 + v * (1 << PREC));
    }
    bounds[2 * xx] = xmin; bounds[2 * xx + 1] = xmax;
  }
  return { bounds, kk, ksize };
}

const clipPrec = ss => { const v = Math.floor(ss / 4194304); return v < 0 ? 0 : v > 255 ? 255 : v; };

function passH(im, outW, filter) {
  const { w, h, c } = im, { bounds, kk, ksize } = coeffs(w, outW, filter), out = new Uint8Array(outW * h * c);
  for (let y = 0; y < h; y++) for (let xx = 0; xx < outW; xx++) {
    const xmin = bounds[2 * xx], xmax = bounds[2 * xx + 1], k0 = xx * ksize;
    for (let ch = 0; ch < c; ch++) {
      let ss = 1 << (PREC - 1);
      for (let x = 0; x < xmax; x++) ss += im.data[(y * w + x + xmin) * c + ch] * kk[k0 + x];
      out[(y * outW + xx) * c + ch] = clipPrec(ss);
    }
  }
  return makeImage(outW, h, c, out);
}

function passV(im, outH, filter) {
  const { w, h, c } = im, { bounds, kk, ksize } = coeffs(h, outH, filter), out = new Uint8Array(w * outH * c);
  for (let yy = 0; yy < outH; yy++) {
    const ymin = bounds[2 * yy], ymax = bounds[2 * yy + 1], k0 = yy * ksize;
    for (let x = 0; x < w; x++) for (let ch = 0; ch < c; ch++) {
      let ss = 1 << (PREC - 1);
      for (let y = 0; y < ymax; y++) ss += im.data[((y + ymin) * w + x) * c + ch] * kk[k0 + y];
      out[(yy * w + x) * c + ch] = clipPrec(ss);
    }
  }
  return makeImage(w, outH, c, out);
}

// Image.resize(size, LANCZOS | BICUBIC): separable passes, each rounded to 8 bits; vertical pass first when the
// height shrinks by more than twice as much as the width (Pillow 13 ordering).
export function resample(im, outW, outH, filterName = 'lanczos') {
  if (outW === im.w && outH === im.h) return copyImage(im);
  const filter = FILTERS[filterName];
  const needH = outW !== im.w, needV = outH !== im.h;
  const hFirst = !((im.h - outH) > 0 && (im.h - outH) > (im.w - outW) * 2);
  let cur = im;
  if (hFirst) { if (needH) cur = passH(cur, outW, filter); if (needV) cur = passV(cur, outH, filter); }
  else { if (needV) cur = passV(cur, outH, filter); if (needH) cur = passH(cur, outW, filter); }
  return cur;
}

// Image.resize(size, NEAREST) via ImagingScaleAffine (positions accumulated in doubles).
export function resizeNearest(im, outW, outH) {
  if (outW === im.w && outH === im.h) return copyImage(im);
  const { w, h, c } = im, a0 = w / outW, a4 = h / outH, out = new Uint8Array(outW * outH * c);
  const xin = new Int32Array(outW);
  let xo = a0 * 0.5;
  for (let x = 0; x < outW; x++) { xin[x] = Math.min(xo < 0 ? 0 : Math.trunc(xo), w - 1); xo += a0; }
  let yo = a4 * 0.5;
  for (let y = 0; y < outH; y++) {
    const yi = Math.min(yo < 0 ? 0 : Math.trunc(yo), h - 1);
    for (let x = 0; x < outW; x++) for (let ch = 0; ch < c; ch++) out[(y * outW + x) * c + ch] = im.data[(yi * w + xin[x]) * c + ch];
    yo += a4;
  }
  return makeImage(outW, outH, c, out);
}
