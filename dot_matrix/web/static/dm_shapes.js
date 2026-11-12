// Dot shapes of patterns.py (_draw_circle ... _draw_ascii_dot) as drawing primitives, plus canvas and SVG output.
// shapePrimitives() returns the same ellipse/rectangle/polygon/text calls the Python makes on ImageDraw (tested in
// dm_engine.test.mjs). svgShapes() reproduces the desktop SVG export (AdvancedExporter.export_svg with the pattern,
// dot_matrix/svg_export.py) byte for byte except for stipple's random scatter; svgCircles() reproduces the
// circles-only format (export_svg without a pattern).

const rad = d => d * (Math.PI / 180);   // math.radians

// Seeded RNG (mulberry32) for the stipple pattern (the Python uses the unseeded `random` module).
export function rng(seed = 1) {
  let a = seed >>> 0;
  return () => { a |= 0; a = (a + 0x6D2B79F5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
}

export function asciiChar(r) { return r > 5 ? '@' : r > 3 ? '#' : r > 2 ? '*' : r > 1 ? '+' : '.'; }

// Primitives: {t:'ellipse'|'rect', box:[x0,y0,x1,y1]}, {t:'poly', pts:[[x,y],...]}, {t:'text', x, y, ch, size}.
export function shapePrimitives(pattern, cx, cy, r, rand = Math.random) {
  const ell = (rr, x = cx, y = cy) => ({ t: 'ellipse', box: [x - rr, y - rr, x + rr, y + rr] });
  const poly = pts => ({ t: 'poly', pts });
  switch (pattern) {
    case 'square': return [{ t: 'rect', box: [cx - r, cy - r, cx + r, cy + r] }];
    case 'diamond': return [poly([[cx, cy - r], [cx + r, cy], [cx, cy + r], [cx - r, cy]])];
    case 'hexagon': return [poly([0, 1, 2, 3, 4, 5].map(i => [cx + r * Math.cos(rad(60 * i - 30)), cy + r * Math.sin(rad(60 * i - 30))]))];
    case 'star': return [poly([...Array(10).keys()].map(i => {
      const a = rad(36 * i - 90), rr = i % 2 === 0 ? r : r * 0.4;
      return [cx + rr * Math.cos(a), cy + rr * Math.sin(a)];
    }))];
    case 'cross': { const w = r * 0.3;
      return [{ t: 'rect', box: [cx - w, cy - r, cx + w, cy + r] }, { t: 'rect', box: [cx - r, cy - w, cx + r, cy + w] }]; }
    case 'heart': return [poly([...Array(50).keys()].map(i => {
      const t = rad(i * 360 / 50);
      const x = r * 0.5 * (16 * Math.sin(t) ** 3) / 16;
      const y = -r * 0.5 * (13 * Math.cos(t) - 5 * Math.cos(2 * t) - 2 * Math.cos(3 * t) - Math.cos(4 * t)) / 16;
      return [cx + x, cy + y];
    }))];
    case 'triangle': return [poly([[cx, cy - r], [cx - r * 0.866, cy + r * 0.5], [cx + r * 0.866, cy + r * 0.5]])];
    case 'halftone': return r > 3 ? [ell(r), ell(r * 0.6)] : [ell(r)];
    case 'stipple': {
      const n = Math.max(1, Math.trunc(r * 2)), dr = Math.max(0.5, r / 4), out = [];
      for (let k = 0; k < n; k++) {
        const dx = -r + 2 * r * rand(), dy = -r + 2 * r * rand();
        if (dx * dx + dy * dy <= r * r) out.push(ell(dr, cx + dx, cy + dy));
      }
      return out;
    }
    case 'ascii_dot': return [{ t: 'text', x: cx - r / 2, y: cy - r / 2, ch: asciiChar(r), size: Math.max(8, Math.trunc(r * 1.5)) }];
    default: return [ell(r)];
  }
}

export const cssColor = c => (typeof c === 'string' ? c : `rgb(${c[0]},${c[1]},${c[2]})`);
export const hexToRgb = h => { const m = /^#?([0-9a-f]{6})$/i.exec(h || ''); if (!m) return null;
  const v = parseInt(m[1], 16); return [(v >> 16) & 255, (v >> 8) & 255, v & 255]; };

// Draw onto a 2D context of size outW x outH (scale > 1 renders a sharper, larger copy).
export function drawDots(ctx, dots, { pattern, outW, outH, background = null, seed = 1, scale = 1 }) {
  ctx.save();
  ctx.setTransform(scale, 0, 0, scale, 0, 0);
  ctx.fillStyle = background ? cssColor(background) : '#ffffff';
  ctx.fillRect(0, 0, outW, outH);
  const rand = rng(seed);
  for (const d of dots) {
    ctx.fillStyle = cssColor(d.color);
    for (const p of shapePrimitives(pattern, d.x, d.y, d.r, rand)) {
      if (p.t === 'rect') {   // ImageDraw rectangles include the far edge pixel
        ctx.fillRect(p.box[0], p.box[1], p.box[2] - p.box[0] + 1, p.box[3] - p.box[1] + 1);
      } else if (p.t === 'ellipse') {
        const rx = (p.box[2] - p.box[0]) / 2 + 0.5, ry = (p.box[3] - p.box[1]) / 2 + 0.5;
        ctx.beginPath(); ctx.ellipse((p.box[0] + p.box[2]) / 2 + 0.5, (p.box[1] + p.box[3]) / 2 + 0.5, rx, ry, 0, 0, 2 * Math.PI); ctx.fill();
      } else if (p.t === 'poly') {
        ctx.beginPath(); p.pts.forEach(([x, y], k) => (k ? ctx.lineTo(x + 0.5, y + 0.5) : ctx.moveTo(x + 0.5, y + 0.5))); ctx.closePath(); ctx.fill();
      } else {
        ctx.font = `${p.size}px Arial, Helvetica, sans-serif`; ctx.textBaseline = 'top'; ctx.fillText(p.ch, p.x, p.y);
      }
    }
  }
  ctx.restore();
}

// Python's str() of a float: integral values keep ".0".
export const pyFloat = v => (Number.isInteger(v) ? v.toFixed(1) : String(v));

function svgHead(outW, outH, background) {
  const bg = background ? `rgb(${background[0]},${background[1]},${background[2]})` : 'white';
  return '<?xml version="1.0" encoding="UTF-8"?>\n'
    + `<svg width="${outW}" height="${outH}" xmlns="http://www.w3.org/2000/svg">\n`
    + `<rect width="${outW}" height="${outH}" fill="${bg}"/>\n`;
}

// svg_export.circles_svg: every dot as a full-precision <circle>, whatever the pattern.
export function svgCircles(dots, outW, outH, background = null) {
  let s = svgHead(outW, outH, background);
  for (const d of dots) s += `<circle cx="${pyFloat(d.x)}" cy="${pyFloat(d.y)}" r="${pyFloat(d.r)}" fill="${cssColor(d.color)}"/>\n`;
  return s + '</svg>';
}

// The chosen pattern's shapes as SVG elements (svg_export.shapes_svg; numbers as String(+v.toFixed(3))).
export function svgShapes(dots, { pattern, outW, outH, background = null, seed = 1 }) {
  const rand = rng(seed), f = v => +v.toFixed(3);
  let s = svgHead(outW, outH, background);
  for (const d of dots) {
    const fill = cssColor(d.color);
    for (const p of shapePrimitives(pattern, d.x, d.y, d.r, rand)) {
      if (p.t === 'rect') s += `<rect x="${f(p.box[0])}" y="${f(p.box[1])}" width="${f(p.box[2] - p.box[0])}" height="${f(p.box[3] - p.box[1])}" fill="${fill}"/>\n`;
      else if (p.t === 'ellipse') s += `<circle cx="${f((p.box[0] + p.box[2]) / 2)}" cy="${f((p.box[1] + p.box[3]) / 2)}" r="${f((p.box[2] - p.box[0]) / 2)}" fill="${fill}"/>\n`;
      else if (p.t === 'poly') s += `<polygon points="${p.pts.map(([x, y]) => `${f(x)},${f(y)}`).join(' ')}" fill="${fill}"/>\n`;
      else s += `<text x="${f(p.x)}" y="${f(p.y)}" font-family="Arial, sans-serif" font-size="${p.size}" dominant-baseline="hanging" fill="${fill}">${p.ch}</text>\n`;
    }
  }
  return s + '</svg>';
}
