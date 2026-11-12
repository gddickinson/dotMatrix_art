# Dot Matrix Art Studio -- Interface Map

## Entry Points
- `app.py` -- Main entry point; configures logging and launches the GUI
- `photo_to_dot_matrix_v3.py` -- Legacy monolithic file (kept for backward compatibility)

## Package: `dot_matrix/`

| File | Purpose | Key Classes/Functions |
|---|---|---|
| `__init__.py` | Package init; re-exports public API | -- |
| `models.py` | Data models, enums, settings | `DotPattern`, `ArtisticEffect`, `ExportFormat`, `ProjectSettings`, `ColorPalette` |
| `patterns.py` | Dot pattern rendering engine | `AdvancedDotMatrixConverter` |
| `effects.py` | Artistic image effects | `ArtisticProcessor`, `FaceGenerator` |
| `camera.py` | Camera capture and face detection | `FaceDetector`, `CameraCapture`, `CV2_AVAILABLE` |
| `batch.py` | Batch image processing | `BatchProcessor` |
| `svg_export.py` | SVG text: pattern shapes (byte-identical to the web) or circles only | `shapes_svg`, `circles_svg`, `svg_number`, `ShapeRecorder` |
| `image_loader.py` | Open images upright (EXIF orientation applied); used by GUI, batch and web | `open_image` |
| `project_io.py` | Save/load, export, undo, threading | `ProjectManager`, `AdvancedExporter`, `UndoRedoManager`, `ThreadSafeImageProcessor` |
| `gui_main.py` | Main Tkinter application class | `MasterDotMatrixStudio` |
| `gui_tabs.py` | Tab setup methods (mixin) | `TabSetupMixin` |
| `gui_display.py` | Dual display window | `DualDisplayWindow` |

`patterns.py` also exposes the two halves of the conversion used by the web app and its tests:
`AdvancedDotMatrixConverter.preprocess_image` (RGB normalisation, smoothing, edge enhancement, effect) and
`sample_matrix` (LANCZOS to the matrix size, brightness, palette colours).

## Web interface: `dot_matrix/web/` (no GUI imports)

| File | Purpose |
|---|---|
| `web/app.py` | FastAPI app: front end, `GET /api/info`, `/api/demo`, `POST /api/convert`, `/api/palette`; `STATIC_ENDPOINTS` |
| `web/convert_api.py` | Parameter parsing/validation and JSON encoding around the real converter (`parse_params`, `convert`, `svg_text`, `info`, `demo`) |
| `web/static/index.html`, `style.css`, `style_app.css`, `core.js`, `main.js` | Page shell, shared kit theme + project colours, router, entry point |
| `web/static/pil_ops.js` | JS port of the Pillow ops used (RGB->L, 3x3 filters, blend/enhance, Gaussian blur, posterize, point, multiply, LANCZOS/BICUBIC/NEAREST resize) |
| `web/static/dm_engine.js` | JS port of preprocess/effects, `sampleMatrix`, `computeDots`, `extractDominantColors` |
| `web/static/dm_shapes.js` | Pattern shapes as draw primitives, canvas drawing, SVG (pattern shapes as the desktop export, circles only) |
| `web/static/dm_engine.test.mjs` | Node test: JS port vs `tests/fixtures/dm_fixture.json` |
| `web/static/studio.js`, `studio_render.js` | Studio page (UI) and its cached pipeline, downloads, Python render call |
| `web/static/home.js`, `gallery.js`, `about.js` | Other pages |
| `web/static/image_io.js`, `demo_image.js`, `static_api.js` | Image decoding, demo face, static-site data layer |

- `run_web.py` -- starts the web app on http://127.0.0.1:8157
- `scripts/build_static.py` -- exports the static GitHub Pages site to `site/`
- `scripts/make_dm_fixture.py` -- writes the Python-vs-JS fixture
- `scripts/screenshots.py` -- browser smoke test and README screenshots (`docs/img/`)
- `.github/workflows/pages.yml` -- tests, builds and publishes the static site on push to `main`

## Tests
- `test_patterns.py` -- Smoke tests for patterns, effects, palettes, undo/redo, SVG export, non-RGB inputs, EXIF, small faces
- `tests/test_web.py` -- Web API, static build, fixture currency, and the node JS-engine test
- `tests/test_browser.py` -- Playwright check that the browser decodes an EXIF-rotated JPEG upright (skipped without Playwright)
- `tests/exif_sample.py` -- builds the rotated test JPEG used by both

## Archive
- `_archive/` -- Old v1 and v2 files

## Module Dependencies
```
app.py --> gui_main.py --> gui_tabs.py, gui_display.py
                       --> patterns.py --> effects.py --> models.py
                       --> camera.py --> models.py
                       --> batch.py --> models.py
                       --> project_io.py --> models.py, svg_export.py (--> patterns.py)
run_web.py --> web/app.py --> web/convert_api.py --> patterns.py, effects.py, models.py, project_io.py
```
