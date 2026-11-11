# Dot Matrix Art

A photo-to-dot-matrix converter with a full-featured Tkinter GUI. Transform any image into dot matrix art using a variety of dot patterns, artistic effects, and export options.

![Dot Matrix Example](examples/dot_matrix_example.png)

## Features

- **11 dot pattern types**: circle, square, diamond, hexagon, star, cross, heart, triangle, halftone, stipple, ASCII
- **Artistic effects** with configurable parameters
- **Real-time preview** in the GUI
- **Camera capture** support (requires OpenCV)
- **Face detection** for intelligent cropping (requires OpenCV)
- **Batch processing** and export
- **Project save/load** via JSON
- **Multi-threaded** processing for responsive UI

## Requirements

- Python 3.7+
- Pillow (PIL)
- NumPy
- tkinter (included with Python)
- OpenCV (optional, for camera and face detection)

```bash
pip install Pillow numpy opencv-python
```

## Usage

```bash
# Run the desktop app (modular package dot_matrix/)
python app.py

# The original single-file v3 app still works too
python photo_to_dot_matrix_v3.py
```

### Workflow

1. Load an image via the GUI file dialog
2. Choose a dot pattern type
3. Adjust dot size, spacing, and artistic effects
4. Preview the result in real time
5. Export the dot matrix art (PNG/JPEG, SVG, high-resolution PNG, animation frames)

Note: the effect menu also lists Watercolor, Comic, Sepia and Depth 3D, which are not implemented yet
(they leave the image unchanged).

## Versions

| File | Description |
|------|-------------|
| `_archive/photo_to_dot_matrix_v1.py` | Original version |
| `_archive/photo_to_dot_matrix_v2.py` | Added more patterns and effects |
| `photo_to_dot_matrix_v3.py` | Full GUI with camera, face detection, batch processing (single file, kept for compatibility) |
| `app.py` + `dot_matrix/` | The v3 app split into modules (current) |

## Project Structure

```
dotMatrix_art/
├── app.py                      # Entry point: launches the Tkinter GUI
├── dot_matrix/                 # Package: models, patterns, effects, camera, batch, project_io, gui_*
├── photo_to_dot_matrix_v3.py   # Legacy single-file v3 app
├── test_patterns.py            # Tests (pytest)
├── _archive/                   # v1 and v2
├── examples/
│   └── dot_matrix_example.png  # Example output
└── README.md
```

Projects and gallery images are saved to `dot_matrix_projects/` (created at run time). See `INTERFACE.md` for a
module map.

---
*Built with AI assistance from [Claude (Anthropic)](https://claude.com/).*
