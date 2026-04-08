# Dot Matrix Art — Roadmap

## Current State
A photo-to-dot-matrix converter with three version files totaling ~4,170 lines. The latest version (`photo_to_dot_matrix_v3.py`, 2,372 lines) is a full-featured Tkinter GUI application with 11 dot patterns, artistic effects, camera capture, face detection, batch processing, and project save/load. Code is functional but monolithic — the entire v3 app lives in a single file. Older versions (v1 at 449 lines, v2 at 1,349 lines) are kept alongside the latest.

## Short-term Improvements
- [x] Split `photo_to_dot_matrix_v3.py` (2,372 lines) into modules: `app.py` (GUI), `patterns.py` (dot pattern rendering), `effects.py` (artistic effects), `camera.py` (capture/face detection), `batch.py` (batch processing), `project_io.py` (save/load)
- [x] Move v1 and v2 into an `archive/` directory — they add confusion about which file to run
- [x] Add `requirements.txt` with Pillow, numpy, opencv-python
- [ ] Add input validation for dot size, spacing, and image dimensions
- [x] Add error handling for missing OpenCV when camera features are selected
- [ ] Add type hints to core conversion functions
- [x] Add unit tests for pattern generation (circle, square, diamond, etc.) — these are deterministic and testable

## Feature Enhancements
- [ ] Add SVG export support — dot matrix art is inherently vector-friendly
- [ ] Add color palette modes: monochrome, duotone, full-color, custom palette
- [ ] Add dithering algorithms (Floyd-Steinberg, Atkinson) as alternative to simple thresholding
- [ ] Add preview at multiple resolutions simultaneously (thumbnail grid)
- [ ] Add undo/redo for parameter changes
- [ ] Add drag-and-drop image loading
- [ ] Add PDF export for print-ready output with configurable DPI
- [ ] Add a "randomize" button that generates interesting parameter combinations

## Long-term Vision
- [ ] Create a web version using Flask/FastAPI + HTML5 Canvas for broader accessibility
- [ ] Add video-to-dot-matrix mode — process video frames and export as animated GIF or MP4
- [ ] Add AI-powered auto-parameter selection based on image content (portraits vs landscapes vs text)
- [ ] Publish as a pip-installable CLI tool: `dotmatrix convert --pattern hexagon input.jpg output.png`
- [ ] Add a gallery/sharing feature that saves parameter presets alongside output images
- [ ] Support tiled/poster output for large-format printing

## Technical Debt
- [x] `photo_to_dot_matrix_v3.py` is a single 2,372-line file — the top refactoring priority
- [x] `photo_to_dot_matrix_v2.py` (1,349 lines) shares code with v3 but is not a dependency — dead code
- [ ] Pattern rendering likely uses per-pixel loops in Python — profile and optimize with numpy vectorization
- [x] Camera/face detection is tightly coupled to the GUI — should be usable independently
- [x] No `.gitignore` — gallery images and project files may get committed
- [ ] Threading in the GUI lacks proper cancellation and error propagation
