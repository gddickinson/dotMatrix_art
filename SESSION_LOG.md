# Session log

## 2026-11-11: web interface and static site (branch `web-interface`)
- Added `dot_matrix/web/` (FastAPI app + ES-module front end, port 8157), `run_web.py`, `requirements-web.txt`,
  `scripts/build_static.py`, `scripts/screenshots.py`, `.github/workflows/pages.yml` (GitHub Pages on push to main).
- Static site converts the user's own photo in the browser with a JS port (`pil_ops.js`, `dm_engine.js`,
  `dm_shapes.js`) of the converter and the Pillow operations it uses. Node test against a Python fixture
  (`scripts/make_dm_fixture.py` -> `tests/fixtures/dm_fixture.json`): all effects, brightness matrices, palette colours,
  dot lists, SVG text and shape geometry agree exactly (Pillow 13.0.0, macOS arm64; Pillow's blend uses a fused
  multiply-add there, which the port reproduces; the test allows 1 grey level for other builds).
- Local app adds "Render with Python" (POST /api/convert runs AdvancedDotMatrixConverter); the demo image is the repo's
  FaceGenerator test face.
- Small refactor: `AdvancedDotMatrixConverter.preprocess_image` / `sample_matrix` split out of
  `convert_image_advanced` (same results) so the web app and fixture use the real code path.
- Bugs fixed (separate commits, regression tests in test_patterns.py):
  - Non-RGB images (PNG with alpha, grayscale, palette GIF) failed with Vintage, palettes, and (for GIF) Neon,
    Emboss, edge enhancement and noise reduction; the converter now normalises to RGB.
  - Mosaic crashed on images under 20 px.
  - SVG export ignored the custom background colour.
  - `__pycache__/*.pyc` were tracked in git; untracked and ignored.
- Docs: README usage/structure corrected (app.py + dot_matrix/, v1/v2 in _archive/); noted that Watercolor, Comic,
  Sepia and Depth 3D effects are listed but not implemented.
- Open for George: implement or remove the four no-op effects; desktop app does not apply EXIF orientation (phone
  photos may appear sideways; the web app does apply it); `FaceGenerator.create_test_face` fails for sizes below
  about 40 px (not reachable from the GUI).
