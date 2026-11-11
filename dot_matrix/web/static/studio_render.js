// Studio pipeline: runs the JS port with caching (effects and resampling only re-run when their inputs change),
// draws the preview, builds downloads, and (local app only) asks the Python converter for the same settings.
import { api, download } from './core.js';
import { preprocess, sampleMatrix, computeDots } from './dm_engine.js';
import { drawDots, svgCircles, svgShapes, hexToRgb } from './dm_shapes.js';
import { canvasBlob, dataUrlToBlob } from './image_io.js';

const cache = { img: null, workKey: '', work: null, matKey: '', matrix: null };

// Settings object (s) -> engine options.
export function engineOptions(s, palettes) {
  return {
    effect: s.effect, edgeEnhance: s.edge, noiseReduce: s.noise,
    mw: s.mw, mh: s.mh, outW: s.outW, outH: s.outH, spacing: s.spacing,
    animate: s.animate, frame: s.animate ? s.frame : 0,
    usePalette: s.usePalette, palette: palettes[s.palette], pattern: s.pattern,
    background: s.useBg ? hexToRgb(s.bg) : null, seed: s.seed,
  };
}

// Returns { dots, ms } and draws into canvas `cv`.
export function render(img, s, palettes, cv) {
  const t0 = performance.now(), o = engineOptions(s, palettes);
  if (cache.img !== img) { cache.img = img; cache.workKey = cache.matKey = ''; }
  const workKey = [o.effect, o.edgeEnhance, o.noiseReduce].join('|');
  if (workKey !== cache.workKey) { cache.work = preprocess(img, o); cache.workKey = workKey; cache.matKey = ''; }
  const matKey = [workKey, o.mw, o.mh, o.usePalette ? JSON.stringify(o.palette) : '-'].join('|');
  if (matKey !== cache.matKey) { cache.matrix = sampleMatrix(cache.work, o.mw, o.mh, o.usePalette ? o.palette : null); cache.matKey = matKey; }
  const dots = computeDots(cache.matrix, o);
  cv.width = o.outW; cv.height = o.outH;
  drawDots(cv.getContext('2d'), dots, o);
  return { dots, o, ms: performance.now() - t0 };
}

export async function downloadPNG(dots, o, name, scale = 1) {
  const cv = document.createElement('canvas');
  cv.width = Math.round(o.outW * scale); cv.height = Math.round(o.outH * scale);
  drawDots(cv.getContext('2d'), dots, { ...o, scale });
  download(`${name}_${o.pattern}${scale > 1 ? `_x${scale}` : ''}.png`, await canvasBlob(cv));
}

export function downloadSVG(dots, o, name, shapes = false) {
  const text = shapes ? svgShapes(dots, o) : svgCircles(dots, o.outW, o.outH, o.background);
  download(`${name}_${o.pattern}${shapes ? '_shapes' : ''}.svg`, text, 'image/svg+xml');
}

// Form fields for POST /api/convert (names as in convert_api.parse_params).
export function pythonForm(s, file, palettes = {}) {
  const fd = new FormData();
  fd.append('file', file);
  const f = {
    pattern: s.pattern, effect: s.effect, matrix_width: s.mw, matrix_height: s.mh, output_width: s.outW,
    output_height: s.outH, spacing: s.spacing, use_palette: s.usePalette ? 1 : 0, palette: s.palette,
    edge_enhance: s.edge ? 1 : 0, noise_reduce: s.noise ? 1 : 0, animate: s.animate ? 1 : 0, frame: s.frame,
    background: s.useBg ? s.bg : '',
  };
  if (s.usePalette && palettes[s.palette]) f.palette_colors = JSON.stringify(palettes[s.palette]);
  for (const [k, v] of Object.entries(f)) fd.append(k, v);
  return fd;
}

export async function sourceBlob(src) {
  return src.file || dataUrlToBlob(src.url);
}

export async function runPython(s, src, palettes) {
  return api(`/convert?seed=${s.seed}`, { body: pythonForm(s, await sourceBlob(src), palettes) });
}
