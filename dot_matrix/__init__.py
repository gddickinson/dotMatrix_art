"""
Dot Matrix Art Studio - Modular package.

Submodules:
    models      - Data models, enums, and settings (DotPattern, ArtisticEffect, etc.)
    patterns    - Dot pattern rendering (AdvancedDotMatrixConverter)
    effects     - Artistic image effects (ArtisticProcessor, FaceGenerator)
    camera      - Camera capture and face detection (CameraCapture, FaceDetector)
    batch       - Batch processing (BatchProcessor)
    project_io  - Project save/load and export (ProjectManager, AdvancedExporter, UndoRedoManager)
    gui         - Tkinter GUI (MasterDotMatrixStudio, DualDisplayWindow)
"""

from dot_matrix.models import (
    DotPattern, ArtisticEffect, ExportFormat, ProjectSettings, ColorPalette,
)
from dot_matrix.patterns import AdvancedDotMatrixConverter
from dot_matrix.effects import ArtisticProcessor, FaceGenerator
from dot_matrix.camera import FaceDetector, CameraCapture
from dot_matrix.batch import BatchProcessor
from dot_matrix.project_io import (
    ProjectManager, AdvancedExporter, UndoRedoManager, ThreadSafeImageProcessor,
)

__all__ = [
    "DotPattern", "ArtisticEffect", "ExportFormat", "ProjectSettings", "ColorPalette",
    "AdvancedDotMatrixConverter",
    "ArtisticProcessor", "FaceGenerator",
    "FaceDetector", "CameraCapture",
    "BatchProcessor",
    "ProjectManager", "AdvancedExporter", "UndoRedoManager", "ThreadSafeImageProcessor",
]
