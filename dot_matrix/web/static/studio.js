// Studio page: pick your own photo (or the demo face), set every option the desktop app has, preview live and download.
// The preview always runs the JS port in the browser (the image is never uploaded on the static site). In the local app
// "Render with Python" sends the image to this computer's server, which runs the repo's AdvancedDotMatrixConverter.
import { route, app, api, esc, isStatic, needsServer, onLeave, download } from './core.js';
import { extractDominantColors } from './dm_engine.js';
import { fileToRGB } from './image_io.js';
import { render, downloadPNG, downloadSVG, runPython } from './studio_render.js';

const state = { src: null, img: null, s: null, palettes: null, last: null, extracted: 0 };

function defaults(info) {
  const d = info.defaults;
  return { pattern: d.pattern, effect: d.effect, edge: d.edge_enhance, noise: d.noise_reduce, usePalette: d.use_palette,
    palette: d.palette, useBg: false, bg: '#000000', mw: d.matrix_width, mh: d.matrix_height, outW: d.output_width,
    outH: d.output_height, spacing: d.spacing, animate: false, frame: 0, seed: 1 };
}

const opt = (v, label, sel) => `<option value="${esc(v)}" ${v === sel ? 'selected' : ''}>${esc(label)}</option>`;
const num = (id, label, v, min, max, step = 1) =>
  `<div><label for="${id}">${label}</label><input id="${id}" type="number" min="${min}" max="${max}" step="${step}" value="${v}"></div>`;
const chk = (id, label, on) => `<label class="check" for="${id}"><input id="${id}" type="checkbox" ${on ? 'checked' : ''}> ${label}</label>`;

function swatches(colors) { return colors.map(c => `<i style="background:rgb(${c.join(',')})" title="rgb(${c.join(',')})"></i>`).join(''); }

route('studio', async (args, query) => {
  const info = await api('/info');
  if (!state.palettes) state.palettes = JSON.parse(JSON.stringify(info.palettes));
  if (!state.s) state.s = defaults(info);
  const s = state.s, L = info.limits;
  if (query.pattern && info.patterns.some(p => p.value === query.pattern)) s.pattern = query.pattern;
  const engine = isStatic()
    ? 'Conversion runs <b>in your browser</b> with a JavaScript port of the Python converter (tested to give the same dots as the Python). Your image is never uploaded.'
    : 'The preview runs the JavaScript port in your browser; <b>Render with Python</b> sends the image to this computer\'s server, which runs the repo\'s own converter.';
  app().innerHTML = `<p class="kicker">Studio</p><h1>Make dot matrix art</h1>
    <div class="callout a small">${engine}</div>
    <div class="studio"><div>
      <div class="panel"><h3>1 · Image</h3>
        <label for="f-file">Your photo (JPEG, PNG, GIF, WebP...)</label><input id="f-file" type="file" accept="image/*">
        <button id="b-demo" class="alt" type="button">Use the demo face</button>
        <p id="src" class="small mute"></p></div>
      <div class="panel"><h3>2 · Pattern & effect</h3>
        <label for="s-pattern">Dot pattern</label><select id="s-pattern">${info.patterns.map(p => opt(p.value, p.label, s.pattern)).join('')}</select>
        <label for="s-effect">Artistic effect</label><select id="s-effect">${info.effects.map(e => opt(e.value, e.implemented ? e.label : `${e.label} (no change: not implemented in the Python)`, s.effect)).join('')}</select>
        ${chk('s-edge', 'Edge enhancement', s.edge)}${chk('s-noise', 'Noise reduction', s.noise)}</div>
      <div class="panel"><h3>3 · Colour</h3>
        ${chk('s-usepal', 'Use palette (otherwise black dots)', s.usePalette)}
        <label for="s-palette">Palette</label><select id="s-palette"></select><div id="sw" class="swatches"></div>
        <button id="b-extract" class="alt" type="button">Extract palette from image</button>
        ${chk('s-usebg', 'Custom background', s.useBg)}
        <label for="s-bg">Background colour</label><input id="s-bg" type="color" value="${s.bg}"></div>
      <div class="panel"><h3>4 · Matrix</h3>
        <div class="pair">${num('s-mw', 'Matrix width (dots)', s.mw, ...L.matrix)}${num('s-mh', 'Matrix height', s.mh, ...L.matrix)}</div>
        <div class="pair">${num('s-ow', 'Output width (px)', s.outW, ...L.output)}${num('s-oh', 'Output height', s.outH, ...L.output)}</div>
        <label for="s-sp">Spacing (dot size) <b id="sp-v">${s.spacing.toFixed(2)}</b></label>
        <input id="s-sp" type="range" min="${info.spacing_range[0]}" max="${info.spacing_range[1]}" step="0.01" value="${s.spacing}"></div>
      <div class="panel"><h3>5 · Animation</h3>
        ${chk('s-anim', 'Animated effects (dots pulse in a wave)', s.animate)}
        <label for="s-frame">Animation frame <b id="fr-v">${s.frame}</b></label><input id="s-frame" type="range" min="0" max="240" step="1" value="${s.frame}">
        <button id="b-play" class="alt" type="button">Play</button></div>
    </div><div>
      <div class="preview"><canvas id="cv" width="900" height="380" role="img" aria-label="Dot matrix preview"></canvas></div>
      <p id="status" class="small status" role="status"></p>
      <div class="panel"><h3>Download</h3>
        <button id="d-png" type="button">PNG</button><button id="d-png4" class="alt" type="button">PNG ×4 (print)</button>
        <button id="d-svg" class="alt" type="button">SVG (circles, as the desktop app)</button>
        <button id="d-svgs" class="alt" type="button">SVG (pattern shapes)</button>
        <button id="b-seed" class="alt" type="button">New stipple scatter</button>
        <p class="small mute">The desktop app's SVG export writes every dot as a circle; "pattern shapes" is a web extra.
          Browser PNGs are anti-aliased, Pillow's are not, so edges look slightly softer.</p></div>
      <div class="panel pybox"><h3>Python converter</h3>${isStatic() ? needsServer('Rendering with the real Python converter')
        : '<button id="b-py" type="button">Render with Python</button> <span id="py-status" class="small" role="status"></span><div id="py-out"></div>'}</div>
    </div></div>`;

  const $ = id => document.getElementById(id), cv = $('cv');
  const fillPalettes = () => {
    $('s-palette').innerHTML = Object.keys(state.palettes).map(k => opt(k, k, s.palette)).join('');
    $('sw').innerHTML = swatches(state.palettes[s.palette] || []);
  };
  fillPalettes();
  const srcNote = () => {
    $('src').innerHTML = state.src ? `<b>${esc(state.src.name)}</b>: ${state.img.w} × ${state.img.h} px${state.src.demo
      ? '. Synthetic face drawn by the repo\'s <code>FaceGenerator</code>.' : ''}` : 'No image yet.';
  };

  let timer = 0;
  const redraw = (delay = 60) => {
    clearTimeout(timer);
    timer = setTimeout(() => {
      if (!state.img) { $('status').textContent = 'Choose a photo or the demo face.'; return; }
      $('status').textContent = 'Working...';
      setTimeout(() => {
        try {
          state.last = render(state.img, s, state.palettes, cv);
          $('status').textContent = `${state.last.dots.length} dots · ${s.mw} × ${s.mh} matrix · ${s.outW} × ${s.outH} px · ${Math.round(state.last.ms)} ms`;
        } catch (e) { console.error(e); $('status').innerHTML = `<span class="err">${esc(e.message)}</span>`; }
      }, 0);
    }, delay);
  };

  async function load(src) {
    $('status').textContent = 'Reading image...';
    try {
      state.img = await fileToRGB(src.file || await (await fetch(src.url)).blob());
      state.src = src; srcNote(); redraw(0);
    } catch (e) { $('status').innerHTML = `<span class="err">Could not read that image: ${esc(e.message)}</span>`; }
  }
  $('f-file').onchange = e => { const f = e.target.files[0]; if (f) load({ file: f, name: f.name }); };
  $('b-demo').onclick = async () => { const d = await api('/demo'); load({ url: d.png, name: d.name, demo: true }); };

  const bind = (id, key, conv, ev = 'change') => $(id).addEventListener(ev, () => { s[key] = conv($(id)); redraw(); });
  const intIn = (lo, hi) => el => { const v = Math.round(+el.value); return Math.min(hi, Math.max(lo, Number.isFinite(v) ? v : lo)); };
  bind('s-pattern', 'pattern', el => el.value); bind('s-effect', 'effect', el => el.value);
  bind('s-edge', 'edge', el => el.checked); bind('s-noise', 'noise', el => el.checked);
  bind('s-usepal', 'usePalette', el => el.checked); bind('s-usebg', 'useBg', el => el.checked);
  bind('s-bg', 'bg', el => el.value, 'input'); bind('s-anim', 'animate', el => el.checked);
  $('s-palette').addEventListener('change', () => { s.palette = $('s-palette').value; $('sw').innerHTML = swatches(state.palettes[s.palette]); redraw(); });
  bind('s-mw', 'mw', intIn(...L.matrix)); bind('s-mh', 'mh', intIn(...L.matrix));
  bind('s-ow', 'outW', intIn(...L.output)); bind('s-oh', 'outH', intIn(...L.output));
  bind('s-sp', 'spacing', el => { $('sp-v').textContent = (+el.value).toFixed(2); return +el.value; }, 'input');
  bind('s-frame', 'frame', el => { $('fr-v').textContent = el.value; return +el.value; }, 'input');

  $('b-extract').onclick = () => {
    if (!state.img) { $('status').textContent = 'Load an image first.'; return; }
    const name = `Extracted ${++state.extracted}`;
    state.palettes[name] = extractDominantColors(state.img, 6);   // 6 colours, as the desktop button
    s.palette = name; s.usePalette = true; $('s-usepal').checked = true; fillPalettes(); redraw();
  };

  let play = 0;
  const stop = () => { clearInterval(play); play = 0; $('b-play') && ($('b-play').textContent = 'Play'); };
  $('b-play').onclick = () => {
    if (play) { stop(); return; }
    s.animate = true; $('s-anim').checked = true; $('b-play').textContent = 'Stop';
    play = setInterval(() => {   // 150 ms per frame, as the desktop animation timer
      s.frame = (s.frame + 1) % 241; $('s-frame').value = s.frame; $('fr-v').textContent = s.frame;
      if (state.img) { state.last = render(state.img, s, state.palettes, cv); }
    }, 150);
  };
  onLeave(stop);

  const need = () => { if (!state.last) { $('status').textContent = 'Nothing to download yet.'; return false; } return true; };
  const base = () => (state.src ? state.src.name.replace(/\.[^.]+$/, '') : 'dotmatrix');
  $('d-png').onclick = () => need() && downloadPNG(state.last.dots, state.last.o, base());
  $('d-png4').onclick = () => need() && downloadPNG(state.last.dots, state.last.o, base(), 4);
  $('d-svg').onclick = () => need() && downloadSVG(state.last.dots, state.last.o, base());
  $('d-svgs').onclick = () => need() && downloadSVG(state.last.dots, state.last.o, base(), true);
  $('b-seed').onclick = () => { s.seed = (s.seed % 9973) + 1; redraw(0); };

  if (!isStatic()) $('b-py').onclick = async () => {
    if (!state.src) { $('py-status').textContent = 'Load an image first.'; return; }
    $('b-py').disabled = true; $('py-status').textContent = 'Python is converting...';
    try {
      const r = await runPython(s, state.src, state.palettes), js = state.last ? state.last.dots : [];
      const same = js.length === r.dots.length && r.dots.every((d, k) => Math.abs(d.r - js[k].r) < 1e-9);
      $('py-status').innerHTML = `${r.dots.length} dots from Python · browser preview: ${js.length} dots, ${same ? '<span class="ok">identical dot list</span>' : 'differs slightly (browsers and Pillow decode some files, e.g. JPEG, a little differently)'}`;
      $('py-out').innerHTML = `<img src="${r.png}" alt="Dot matrix art rendered by the Python converter" width="${r.width}" height="${r.height}">
        <button id="py-png" type="button">Python PNG</button><button id="py-svg" class="alt" type="button">Python SVG</button>`;
      $('py-png').onclick = async () => download(`${base()}_${s.pattern}_python.png`, await (await fetch(r.png)).blob());
      $('py-svg').onclick = () => download(`${base()}_python.svg`, r.svg, 'image/svg+xml');
    } catch (e) { $('py-status').innerHTML = `<span class="err">${esc(e.message)}</span>`; }
    $('b-py').disabled = false;
  };

  srcNote();
  if (!state.img) { const d = await api('/demo'); await load({ url: d.png, name: d.name, demo: true }); } else redraw(0);
});
