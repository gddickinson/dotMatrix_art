// JS port of the conversion in dot_matrix/patterns.py + effects.py + models.py (no DOM; runs in node for tests).
// preprocess() = AdvancedDotMatrixConverter.preprocess_image (noise reduction, edge enhancement, artistic effect),
// sampleMatrix() = sample_matrix (LANCZOS to the matrix size, brightness, palette colours),
// computeDots() = the dot loop of convert_image_advanced (the "circle data" the desktop app exports as SVG),
// extractDominantColors() = ColorPalette.extract_dominant_colors.
import {
  makeImage, toL, toRGB, filter3x3, contrast, color, invert, lighter, gaussianBlur, resample, resizeNearest,
} from './pil_ops.js';

// effects.py ArtisticProcessor.apply_artistic_effect. Effects not handled there return the image unchanged.
export const EFFECTS = {
  vintage(im) {
    const c = contrast(im, 0.8), d = c.data, out = new Uint8Array(d.length);
    const M = [[0.393, 0.769, 0.189], [0.349, 0.686, 0.168], [0.272, 0.534, 0.131]];
    for (let i = 0; i < d.length; i += 3) {
      for (let ch = 0; ch < 3; ch++) {
        const v = d[i] * M[ch][0] + d[i + 1] * M[ch][1] + d[i + 2] * M[ch][2];
        out[i + ch] = v <= 0 ? 0 : v >= 255 ? 255 : Math.trunc(v);
      }
    }
    return makeImage(im.w, im.h, 3, out);
  },
  neon: im => color(contrast(filter3x3(im, 'EDGE_ENHANCE_MORE'), 1.5), 2.0),
  sketch(im) {
    const gray = toL(im);
    const invBlurred = invert(gaussianBlur(invert(gray), 5));
    return toRGB(lighter(gray, invBlurred));
  },
  crosshatch: im => toRGB(contrast(filter3x3(toL(im), 'FIND_EDGES'), 2.0)),
  mosaic(im) {
    const small = resizeNearest(im, Math.max(1, Math.floor(im.w / 20)), Math.max(1, Math.floor(im.h / 20)));
    return resizeNearest(small, im.w, im.h);
  },
  emboss: im => filter3x3(im, 'EMBOSS'),
};

export const isImplemented = effect => effect === 'none' || effect in EFFECTS;

export function applyEffect(im, effect) {
  return EFFECTS[effect] ? EFFECTS[effect](im) : im;
}

// Same order as the Python: SMOOTH, then EDGE_ENHANCE, then the effect. Input RGB.
export function preprocess(im, { effect = 'none', edgeEnhance = false, noiseReduce = false } = {}) {
  let work = im.c === 3 ? im : toRGB(im);
  if (noiseReduce) work = filter3x3(work, 'SMOOTH');
  if (edgeEnhance) work = filter3x3(work, 'EDGE_ENHANCE');
  if (effect !== 'none') work = applyEffect(work, effect);
  return work;
}

// _map_to_palette: nearest palette colour by squared RGB distance (first one wins ties, like Python's min()).
export function mapToPalette(rgb, palette) {
  const n = rgb.w * rgb.h, out = new Uint8Array(n * 3);
  for (let i = 0; i < n; i++) {
    const r = rgb.data[3 * i], g = rgb.data[3 * i + 1], b = rgb.data[3 * i + 2];
    let best = 0, bestD = Infinity;
    for (let k = 0; k < palette.length; k++) {
      const p = palette[k], d = (p[0] - r) ** 2 + (p[1] - g) ** 2 + (p[2] - b) ** 2;
      if (d < bestD) { bestD = d; best = k; }
    }
    out.set(palette[best].slice(0, 3), 3 * i);
  }
  return out;
}

// Returns { brightness: Uint8Array(mw*mh), colors: Uint8Array(mw*mh*3) | null }.
export function sampleMatrix(work, mw, mh, palette = null) {
  if (palette && palette.length) {
    const resized = resample(work, mw, mh, 'lanczos');
    return { brightness: toL(resized).data, colors: mapToPalette(resized, palette) };
  }
  return { brightness: resample(toL(work), mw, mh, 'lanczos').data, colors: null };
}

// Dot list as in convert_image_advanced: [{x, y, r, color, i, j}], color 'black' or [r, g, b].
export function computeDots(matrix, { mw, mh, outW, outH, spacing = 1.0, animate = false, frame = 0 }) {
  const cellW = outW / mw, cellH = outH / mh;
  const maxR = Math.min(cellW, cellH) / 2 * spacing;
  const dots = [];
  for (let y = 0; y < mh; y++) {
    for (let x = 0; x < mw; x++) {
      const b = matrix.brightness[y * mw + x];
      const base = maxR * (1 - b / 255.0);
      const r = animate ? base * (0.8 + 0.4 * Math.sin(frame * 0.1 + x * 0.2 + y * 0.2)) : base;
      if (r > 0.5) {
        const k = 3 * (y * mw + x);
        const col = matrix.colors ? [matrix.colors[k], matrix.colors[k + 1], matrix.colors[k + 2]] : 'black';
        dots.push({ x: (x + 0.5) * cellW, y: (y + 0.5) * cellH, r, color: col, i: x, j: y });
      }
    }
  }
  return dots;
}

// One call for everything (the static site caches preprocess/sampleMatrix itself for speed).
export function convert(im, o) {
  const work = preprocess(im, o);
  const matrix = sampleMatrix(work, o.mw, o.mh, o.usePalette ? o.palette : null);
  return { work, matrix, dots: computeDots(matrix, o) };
}

// ColorPalette.extract_dominant_colors: BICUBIC to 150x150, round channels down to multiples of 32, most common first.
export function extractDominantColors(im, num = 5) {
  const small = resample(im.c === 3 ? im : toRGB(im), 150, 150, 'bicubic');
  const counts = new Map();
  for (let i = 0; i < small.data.length; i += 3) {
    const key = ((small.data[i] >> 5) << 16) | ((small.data[i + 1] >> 5) << 8) | (small.data[i + 2] >> 5);
    counts.set(key, (counts.get(key) || 0) + 1);
  }
  return [...counts.entries()].sort((a, b) => b[1] - a[1]).slice(0, num)
    .map(([k]) => [((k >> 16) & 255) * 32, ((k >> 8) & 255) * 32, (k & 255) * 32]);
}
