"""Project save/load, export, undo/redo, and threading utilities."""

import json
import time
import queue
import logging
import threading
from pathlib import Path
from dataclasses import asdict
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Tuple, List, Dict

from PIL import Image

from dot_matrix.models import ProjectSettings

logger = logging.getLogger(__name__)


class ProjectManager:
    """Project management system for saving/loading settings and artworks."""

    def __init__(self):
        self.projects_dir = Path("dot_matrix_projects")
        self.projects_dir.mkdir(exist_ok=True)
        self.gallery_dir = self.projects_dir / "gallery"
        self.gallery_dir.mkdir(exist_ok=True)

    def save_project(
        self,
        settings: ProjectSettings,
        original_image: Optional[Image.Image] = None,
        result_image: Optional[Image.Image] = None,
    ) -> bool:
        """Save a project with settings and images."""
        try:
            project_dir = self.projects_dir / settings.name
            project_dir.mkdir(exist_ok=True)

            settings.modified_date = time.strftime("%Y-%m-%d %H:%M:%S")
            if not settings.created_date:
                settings.created_date = settings.modified_date

            settings_file = project_dir / "settings.json"
            with open(settings_file, "w") as f:
                json.dump(asdict(settings), f, indent=2)

            if original_image:
                original_image.save(project_dir / "original.png")

            if result_image:
                result_image.save(project_dir / "result.png")
                gallery_file = self.gallery_dir / f"{settings.name}_{int(time.time())}.png"
                result_image.save(gallery_file)

            logger.info(f"Project '{settings.name}' saved successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to save project: {e}")
            return False

    def load_project(
        self, project_name: str
    ) -> Optional[Tuple[ProjectSettings, Optional[Image.Image], Optional[Image.Image]]]:
        """Load a project with settings and images."""
        try:
            project_dir = self.projects_dir / project_name
            if not project_dir.exists():
                return None

            settings_file = project_dir / "settings.json"
            if not settings_file.exists():
                return None

            with open(settings_file, "r") as f:
                settings_dict = json.load(f)

            settings = ProjectSettings(**settings_dict)

            original_image = None
            result_image = None

            original_file = project_dir / "original.png"
            if original_file.exists():
                original_image = Image.open(original_file)

            result_file = project_dir / "result.png"
            if result_file.exists():
                result_image = Image.open(result_file)

            logger.info(f"Project '{project_name}' loaded successfully")
            return settings, original_image, result_image

        except Exception as e:
            logger.error(f"Failed to load project: {e}")
            return None

    def list_projects(self) -> List[str]:
        """List all available projects."""
        try:
            projects = []
            for item in self.projects_dir.iterdir():
                if item.is_dir() and item.name != "gallery":
                    settings_file = item / "settings.json"
                    if settings_file.exists():
                        projects.append(item.name)
            return sorted(projects)
        except Exception as e:
            logger.error(f"Failed to list projects: {e}")
            return []

    def get_gallery_images(self) -> List[Path]:
        """Get all images in the gallery."""
        try:
            images = []
            for item in self.gallery_dir.iterdir():
                if item.suffix.lower() in [".png", ".jpg", ".jpeg"]:
                    images.append(item)
            return sorted(images, key=lambda x: x.stat().st_mtime, reverse=True)
        except Exception as e:
            logger.error(f"Failed to get gallery images: {e}")
            return []


class AdvancedExporter:
    """Advanced export system with multiple formats and optimization."""

    @staticmethod
    def export_svg(
        image: Image.Image, output_path: str, circle_data: List[Dict]
    ) -> bool:
        """Export as SVG vector format."""
        try:
            width, height = image.size

            svg_content = (
                f'<?xml version="1.0" encoding="UTF-8"?>\n'
                f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">\n'
                f'<rect width="{width}" height="{height}" fill="white"/>\n'
            )

            for circle in circle_data:
                x, y, r, color = circle["x"], circle["y"], circle["r"], circle["color"]
                if isinstance(color, tuple):
                    color_str = f"rgb({color[0]},{color[1]},{color[2]})"
                else:
                    color_str = color
                svg_content += f'<circle cx="{x}" cy="{y}" r="{r}" fill="{color_str}"/>\n'

            svg_content += "</svg>"

            with open(output_path, "w") as f:
                f.write(svg_content)

            return True

        except Exception as e:
            logger.error(f"SVG export failed: {e}")
            return False

    @staticmethod
    def export_high_resolution(
        image: Image.Image, output_path: str, scale_factor: int = 4
    ) -> bool:
        """Export high-resolution version for printing."""
        try:
            new_size = (image.width * scale_factor, image.height * scale_factor)
            high_res = image.resize(new_size, Image.LANCZOS)

            if output_path.lower().endswith((".jpg", ".jpeg")):
                high_res.save(output_path, quality=95, dpi=(300, 300))
            else:
                high_res.save(output_path, dpi=(300, 300))

            return True

        except Exception as e:
            logger.error(f"High-res export failed: {e}")
            return False


class UndoRedoManager:
    """Undo/Redo system for operations."""

    def __init__(self, max_history: int = 20):
        self.history: List[Image.Image] = []
        self.current_index = -1
        self.max_history = max_history

    def add_state(self, image: Image.Image):
        """Add a new state to history."""
        self.history = self.history[: self.current_index + 1]
        self.history.append(image.copy())
        self.current_index += 1

        if len(self.history) > self.max_history:
            self.history.pop(0)
            self.current_index -= 1

    def undo(self) -> Optional[Image.Image]:
        """Undo to previous state."""
        if self.can_undo():
            self.current_index -= 1
            return self.history[self.current_index].copy()
        return None

    def redo(self) -> Optional[Image.Image]:
        """Redo to next state."""
        if self.can_redo():
            self.current_index += 1
            return self.history[self.current_index].copy()
        return None

    def can_undo(self) -> bool:
        return self.current_index > 0

    def can_redo(self) -> bool:
        return self.current_index < len(self.history) - 1

    def clear(self):
        """Clear all history."""
        self.history.clear()
        self.current_index = -1


class ThreadSafeImageProcessor:
    """Thread-safe image processing with queues."""

    def __init__(self):
        self.processing_queue: queue.Queue = queue.Queue(maxsize=5)
        self.result_queue: queue.Queue = queue.Queue(maxsize=5)
        self.processing_lock = threading.Lock()
        self.executor = ThreadPoolExecutor(max_workers=3)
        self.is_processing = False

    def submit_processing_task(self, func, *args, **kwargs):
        """Submit a processing task to the thread pool."""
        future = self.executor.submit(func, *args, **kwargs)
        return future

    def shutdown(self):
        """Shutdown the thread pool executor."""
        self.executor.shutdown(wait=True)
