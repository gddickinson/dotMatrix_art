// Patterns page: the demo face in every dot pattern, and every artistic effect, rendered live by the JS port.
import { route, app, api, esc } from './core.js';
import { convert } from './dm_engine.js';
import { drawDots } from './dm_shapes.js';
import { demoImage } from './demo_image.js';

const BASE = { mw: 28, mh: 34, outW: 280, outH: 340, spacing: 1.0, effect: 'none', animate: false, frame: 0 };

function thumb(img, o) {
  const cv = document.createElement('canvas');
  cv.width = o.outW; cv.height = o.outH;
  const { dots } = convert(img, o);
  drawDots(cv.getContext('2d'), dots, o);
  return cv;
}

route('gallery', async () => {
  const [info, demo] = await Promise.all([api('/info'), demoImage()]);
  const effects = info.effects.filter(e => e.implemented && e.value !== 'none');
  const missing = info.effects.filter(e => !e.implemented).map(e => e.label);
  app().innerHTML = `<p class="kicker">Patterns</p><h1>${info.patterns.length} dot patterns</h1>
    <p class="lead">The demo face (drawn by the repo's <code>FaceGenerator</code>) as a ${BASE.mw} × ${BASE.mh} matrix in each
      pattern. Dot size follows darkness: a black pixel gives the largest dot. Click one to open it in the studio.</p>
    <div class="thumbs" id="pats"></div>
    <h2>Artistic effects</h2>
    <p>Applied before sampling, here with the Ocean Blues palette. ${missing.length ? `The desktop menu also lists
      ${esc(missing.join(', '))}, which the Python code does not implement yet (the image passes through unchanged).` : ''}</p>
    <div class="thumbs" id="effs"></div>`;
  const add = (host, label, href, cv) => {
    const a = document.createElement('a');
    a.className = 'card'; a.href = href;
    cv.setAttribute('role', 'img'); cv.setAttribute('aria-label', label);
    a.append(cv); a.insertAdjacentHTML('beforeend', `<b>${esc(label)}</b>`);
    document.getElementById(host).append(a);
  };
  for (const p of info.patterns) add('pats', p.label, `#/studio?pattern=${p.value}`, thumb(demo.img, { ...BASE, pattern: p.value }));
  for (const e of effects) {
    add('effs', e.label, '#/studio', thumb(demo.img, { ...BASE, pattern: 'circle', effect: e.value, usePalette: true,
      palette: info.palettes['Ocean Blues'], background: [12, 16, 32] }));
  }
});
