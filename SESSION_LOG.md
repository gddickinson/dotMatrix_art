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
- Open questions were answered by George the same day (see next entry).

## 2026-11-11 (later): follow-up fixes approved by George
- Implemented the four menu effects that did nothing (Python effects.py + JS dm_engine.js, fixture extended, node test
  4563/4563 exact): Sepia (sepia matrix), Watercolor (Gaussian blur 2, posterize 4 bits, colour x1.3), Comic
  (smoothed 2-bit poster colours x black ink mask where FIND_EDGES >= 48), Depth 3D (red/cyan anaglyph, shift 1% of
  width). Vintage now shares the sepia helper (identical output).
- EXIF orientation: new `dot_matrix/image_loader.py` `open_image` (ImageOps.exif_transpose) used by the GUI (load,
  gallery viewer), batch mode and the web upload. Browser already used createImageBitmap 'from-image'; new
  `tests/test_browser.py` (Playwright) checks a generated Orientation-6 JPEG decodes upright. Note: current Chrome
  applies EXIF even with imageOrientation 'none', so that test guards the result, not the option value.
- FaceGenerator.create_test_face works at any size (margins shrink below 40 px; 40 px and up pixel-identical).
- Each fix in its own "Fix ..." commit with regression tests. All KIT checks re-run: pytest 30 passed
  (tests/ + test_patterns.py), screenshots static + local all ok, Python render = browser dot list.
- Still pre-existing: dot_matrix/gui_main.py is 835 lines (over the 500-line budget; not split here).
