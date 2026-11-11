// About page: what the project is, how the web version relates to the Python, how to run both, credits.
import { route, app, api, isStatic, esc } from './core.js';

route('about', async () => {
  const info = await api('/info');
  const missing = info.effects.filter(e => !e.implemented).map(e => e.label);
  app().innerHTML = `<p class="kicker">About</p><h1>Dot Matrix Art</h1>
    <p class="lead">${esc(info.description)}</p>
    <h2>How a photo becomes dots</h2>
    <ol><li>Optional noise reduction (Pillow <code>SMOOTH</code>), edge enhancement (<code>EDGE_ENHANCE</code>) and an artistic effect.</li>
      <li>The image is resampled (LANCZOS) to the matrix size, e.g. 45 × 19, and converted to brightness.</li>
      <li>Each cell gets a dot whose radius is <span class="eq">r = r<sub>max</sub> · (1 − brightness / 255)</span>, with
        r<sub>max</sub> = half the smaller cell side × spacing. Dots smaller than 0.5 px are skipped.</li>
      <li>With a palette, each cell takes the nearest palette colour (squared RGB distance); otherwise dots are black.</li>
      <li>"Animated effects" scale every dot by 0.8 + 0.4 · sin(0.1·frame + 0.2·x + 0.2·y), a travelling wave.</li></ol>
    ${missing.length ? `<p class="small mute">The effect menu of the desktop app also lists ${esc(missing.join(', '))}; the Python code does not
      implement them yet, so they leave the image unchanged, here as there.</p>` : ''}
    <h2>Browser version vs Python</h2>
    <p>The static site cannot run Python, so the conversion was ported to JavaScript, including the Pillow operations it
      relies on (3×3 filters, contrast/colour enhancement, Gaussian blur, LANCZOS and BICUBIC resampling). A node test runs
      the port on a generated test image and compares it with the repo's Python: every effect image, brightness matrix,
      palette colour, dot position and radius, the SVG export and the shape geometry agree exactly. Drawing differs a
      little: the browser anti-aliases shapes, Pillow does not, and stipple scatter uses a different random generator.</p>
    <p>${isStatic() ? 'On this site your photo stays in your browser.' : 'In this local app the preview uses the same JS port, and "Render with Python" runs the real converter on this computer.'}</p>
    <h2>Run it yourself</h2>
    <pre>git clone https://github.com/gddickinson/dotMatrix_art
cd dotMatrix_art
pip install -r requirements.txt
python app.py                      # desktop app (Tkinter): camera, batch, projects, dual display

pip install -r requirements-web.txt
python run_web.py                  # web app at http://127.0.0.1:8157</pre>
    <p class="small mute">The desktop app also has camera capture, face detection (OpenCV), batch processing, project
      save/load and a dual display window; those are not part of the web version.</p>
    <h2>Credits</h2>
    <p>By George Dickinson (<a href="https://github.com/gddickinson/dotMatrix_art">gddickinson/dotMatrix_art</a>), MIT licence.
      Built with AI assistance from Claude (Anthropic).</p>`;
});
