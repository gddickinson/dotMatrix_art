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
| `project_io.py` | Save/load, export, undo, threading | `ProjectManager`, `AdvancedExporter`, `UndoRedoManager`, `ThreadSafeImageProcessor` |
| `gui_main.py` | Main Tkinter application class | `MasterDotMatrixStudio` |
| `gui_tabs.py` | Tab setup methods (mixin) | `TabSetupMixin` |
| `gui_display.py` | Dual display window | `DualDisplayWindow` |

## Tests
- `test_patterns.py` -- Smoke tests for patterns, effects, palettes, undo/redo, SVG export

## Archive
- `_archive/` -- Old v1 and v2 files

## Module Dependencies
```
app.py --> gui_main.py --> gui_tabs.py, gui_display.py
                       --> patterns.py --> effects.py --> models.py
                       --> camera.py --> models.py
                       --> batch.py --> models.py
                       --> project_io.py --> models.py
```
