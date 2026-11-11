// Home page: hero, counts read from the API, a live sample and links to the pages.
import { route, app, api, isStatic, animate } from './core.js';
import { convert, computeDots } from './dm_engine.js';
import { drawDots } from './dm_shapes.js';
import { demoImage } from './demo_image.js';

route('home', async () => {
  const [info, demo] = await Promise.all([api('/info'), demoImage()]);
  const nEff = info.effects.filter(e => e.implemented && e.value !== 'none').length;
  app().innerHTML = `<section class="hero"><p class="kicker">Photo to dot matrix converter</p>
    <h1 class="glow">Dot Matrix Art</h1>
    <p class="lead">${info.description} ${isStatic() ? 'Everything runs in your browser: your photo is never uploaded.' : ''}</p>
    <a class="btn" href="#/studio">Open the studio</a> <a class="btn alt" href="#/gallery">See the patterns</a></section>
    <div class="tiles">
      <div class="tile"><b>${info.patterns.length}</b><span>dot patterns</span></div>
      <div class="tile"><b>${nEff}</b><span>artistic effects</span></div>
      <div class="tile"><b>${Object.keys(info.palettes).length}</b><span>colour palettes</span></div>
      <div class="tile"><b>PNG · SVG</b><span>downloads</span></div></div>
    <div class="two"><div class="preview"><canvas id="hero-cv" role="img" aria-label="The demo face as animated hexagon dots"></canvas></div>
    <div class="grid" style="grid-template-columns:1fr">
      <a class="card" href="#/studio"><b>Studio</b><small>your own photo</small><span>Every option of the desktop app: matrix and output size, spacing, pattern, effect, palette, background, animation.</span></a>
      <a class="card" href="#/gallery"><b>Patterns</b><small>${info.patterns.length} shapes · ${nEff} effects</small><span>Circle, square, diamond, hexagon, star, cross, heart, triangle, halftone, stipple and ASCII.</span></a>
      <a class="card" href="#/about"><b>About</b><small>how it works · run it locally</small><span>The desktop Tkinter app, the local web app and how the browser version was checked against the Python.</span></a>
    </div></div>`;
  const cv = document.getElementById('hero-cv');
  const o = { mw: 30, mh: 36, outW: 300, outH: 360, spacing: 1.15, pattern: 'hexagon', effect: 'none', animate: true, frame: 0,
    usePalette: true, palette: info.palettes['Neon Cyberpunk'], background: [5, 6, 12] };
  cv.width = o.outW; cv.height = o.outH;
  const { matrix } = convert(demo.img, o);
  const frame = f => drawDots(cv.getContext('2d'), computeDots(matrix, { ...o, frame: f }), o);
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) { frame(0); return; }
  let last = -1e9, f = 0;
  animate(t => { if (t - last >= 150) { frame(f++); last = t; } });
});
