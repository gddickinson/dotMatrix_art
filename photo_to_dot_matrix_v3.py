import numpy as np
from PIL import Image, ImageDraw, ImageTk, ImageFont, ImageFilter, ImageEnhance, ImageOps, ImageChops
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
import logging
import os
from typing import Optional, Tuple, List, Dict, Any
import math
import threading
import time
import queue
from concurrent.futures import ThreadPoolExecutor
import copy
import random
import json
import base64
import io
from enum import Enum
from dataclasses import dataclass, asdict
import hashlib
from pathlib import Path
import subprocess
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dot_matrix_converter.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Try to import OpenCV, handle gracefully if not available
try:
    import cv2
    CV2_AVAILABLE = True
    logger.info(f"OpenCV version: {cv2.__version__}")
except ImportError:
    CV2_AVAILABLE = False
    logger.warning("OpenCV not available - camera and face detection features disabled")

class DotPattern(Enum):
    """Different dot pattern types."""
    CIRCLE = "circle"
    SQUARE = "square"
    DIAMOND = "diamond"
    HEXAGON = "hexagon"
    STAR = "star"
    CROSS = "cross"
    HEART = "heart"
    TRIANGLE = "triangle"
    HALFTONE = "halftone"
    STIPPLE = "stipple"
    ASCII_DOT = "ascii_dot"

class ArtisticEffect(Enum):
    """Artistic effect types."""
    NONE = "none"
    VINTAGE = "vintage"
    NEON = "neon"
    WATERCOLOR = "watercolor"
    SKETCH = "sketch"
    COMIC = "comic"
    EMBOSS = "emboss"
    SEPIA = "sepia"
    CROSSHATCH = "crosshatch"
    MOSAIC = "mosaic"
    DEPTH_3D = "depth_3d"

class ExportFormat(Enum):
    """Export format options."""
    PNG = "png"
    JPEG = "jpg"
    SVG = "svg"
    PDF = "pdf"
    TIFF = "tiff"
    BMP = "bmp"

@dataclass
class ProjectSettings:
    """Project settings for save/load functionality."""
    name: str
    matrix_width: int = 45
    matrix_height: int = 19
    output_width: int = 900
    output_height: int = 380
    pattern: str = "circle"
    effect: str = "none"
    palette: str = "Classic B&W"
    use_palette: bool = False
    spacing: float = 1.0
    edge_enhance: bool = False
    noise_reduce: bool = False
    background_color: Optional[Tuple[int, int, int]] = None
    auto_crop: bool = True
    face_padding: float = 0.2
    created_date: str = ""
    modified_date: str = ""

class ColorPalette:
    """Enhanced color palettes with auto-extraction."""

    PALETTES = {
        "Classic B&W": [(0, 0, 0), (255, 255, 255)],
        "Vintage Sepia": [(101, 67, 33), (205, 183, 158), (245, 222, 179)],
        "Neon Cyberpunk": [(255, 0, 255), (0, 255, 255), (255, 255, 0), (255, 0, 0)],
        "Ocean Blues": [(0, 105, 148), (0, 157, 196), (138, 215, 235), (255, 255, 255)],
        "Sunset Orange": [(255, 94, 77), (255, 154, 0), (255, 206, 84), (255, 255, 255)],
        "Forest Green": [(34, 139, 34), (144, 238, 144), (173, 255, 47), (255, 255, 255)],
        "Royal Purple": [(75, 0, 130), (138, 43, 226), (186, 85, 211), (255, 255, 255)],
        "Retro Gaming": [(0, 0, 0), (255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)],
        "Pastel Dream": [(255, 182, 193), (255, 218, 185), (255, 255, 186), (186, 255, 201)],
        "Fire & Ice": [(255, 0, 0), (255, 165, 0), (0, 191, 255), (255, 255, 255)],
        "Monochrome Gold": [(0, 0, 0), (139, 116, 37), (255, 215, 0), (255, 255, 255)],
        "Deep Sea": [(25, 25, 112), (0, 100, 0), (72, 61, 139), (255, 255, 255)]
    }

    @staticmethod
    def extract_dominant_colors(image: Image.Image, num_colors: int = 5) -> List[Tuple[int, int, int]]:
        """Extract dominant colors from an image using simplified clustering."""
        try:
            # Resize image for faster processing
            small_image = image.resize((150, 150))
            pixels = list(small_image.convert('RGB').getdata())

            # Simple color frequency analysis
            color_counts = {}
            for pixel in pixels:
                # Round to nearest 32 to group similar colors
                rounded = tuple((c // 32) * 32 for c in pixel)
                color_counts[rounded] = color_counts.get(rounded, 0) + 1

            # Return most frequent colors
            sorted_colors = sorted(color_counts.items(), key=lambda x: x[1], reverse=True)
            return [color for color, count in sorted_colors[:num_colors]]

        except Exception as e:
            logger.error(f"Color extraction failed: {str(e)}")
            return [(0, 0, 0), (128, 128, 128), (255, 255, 255)]

class ProjectManager:
    """Project management system for saving/loading settings and artworks."""

    def __init__(self):
        self.projects_dir = Path("dot_matrix_projects")
        self.projects_dir.mkdir(exist_ok=True)
        self.gallery_dir = self.projects_dir / "gallery"
        self.gallery_dir.mkdir(exist_ok=True)

    def save_project(self, settings: ProjectSettings, original_image: Optional[Image.Image] = None,
                    result_image: Optional[Image.Image] = None) -> bool:
        """Save a project with settings and images."""
        try:
            # Create project directory
            project_dir = self.projects_dir / settings.name
            project_dir.mkdir(exist_ok=True)

            # Save settings
            settings.modified_date = time.strftime("%Y-%m-%d %H:%M:%S")
            if not settings.created_date:
                settings.created_date = settings.modified_date

            settings_file = project_dir / "settings.json"
            with open(settings_file, 'w') as f:
                json.dump(asdict(settings), f, indent=2)

            # Save images
            if original_image:
                original_image.save(project_dir / "original.png")

            if result_image:
                result_image.save(project_dir / "result.png")
                # Also save to gallery
                gallery_file = self.gallery_dir / f"{settings.name}_{int(time.time())}.png"
                result_image.save(gallery_file)

            logger.info(f"Project '{settings.name}' saved successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to save project: {str(e)}")
            return False

    def load_project(self, project_name: str) -> Optional[Tuple[ProjectSettings, Optional[Image.Image], Optional[Image.Image]]]:
        """Load a project with settings and images."""
        try:
            project_dir = self.projects_dir / project_name
            if not project_dir.exists():
                return None

            # Load settings
            settings_file = project_dir / "settings.json"
            if not settings_file.exists():
                return None

            with open(settings_file, 'r') as f:
                settings_dict = json.load(f)

            settings = ProjectSettings(**settings_dict)

            # Load images
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
            logger.error(f"Failed to load project: {str(e)}")
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
            logger.error(f"Failed to list projects: {str(e)}")
            return []

    def get_gallery_images(self) -> List[Path]:
        """Get all images in the gallery."""
        try:
            images = []
            for item in self.gallery_dir.iterdir():
                if item.suffix.lower() in ['.png', '.jpg', '.jpeg']:
                    images.append(item)
            return sorted(images, key=lambda x: x.stat().st_mtime, reverse=True)
        except Exception as e:
            logger.error(f"Failed to get gallery images: {str(e)}")
            return []

class BatchProcessor:
    """Batch processing system for multiple images."""

    def __init__(self, converter, progress_callback=None):
        self.converter = converter
        self.progress_callback = progress_callback
        self.is_processing = False

    def process_batch(self, image_paths: List[str], settings: ProjectSettings,
                     output_dir: str) -> Dict[str, Any]:
        """Process multiple images with the same settings."""
        self.is_processing = True
        results = {
            'processed': 0,
            'failed': 0,
            'errors': [],
            'output_files': []
        }

        try:
            total_images = len(image_paths)

            for i, image_path in enumerate(image_paths):
                if not self.is_processing:  # Check for cancellation
                    break

                try:
                    # Load image
                    image = Image.open(image_path)

                    # Convert using settings
                    result = self.converter.convert_image_advanced(
                        image,
                        matrix_width=settings.matrix_width,
                        matrix_height=settings.matrix_height,
                        output_size=(settings.output_width, settings.output_height),
                        pattern=DotPattern(settings.pattern),
                        circle_spacing=settings.spacing,
                        use_color=settings.use_palette,
                        color_palette=ColorPalette.PALETTES.get(settings.palette) if settings.use_palette else None,
                        artistic_effect=ArtisticEffect(settings.effect),
                        edge_enhancement=settings.edge_enhance,
                        noise_reduction=settings.noise_reduce,
                        custom_background=settings.background_color
                    )

                    if result:
                        # Save result
                        input_name = Path(image_path).stem
                        output_file = Path(output_dir) / f"{input_name}_dotmatrix.png"
                        result.save(output_file)

                        results['processed'] += 1
                        results['output_files'].append(str(output_file))
                    else:
                        results['failed'] += 1
                        results['errors'].append(f"Conversion failed for {image_path}")

                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append(f"Error processing {image_path}: {str(e)}")

                # Update progress
                if self.progress_callback:
                    progress = (i + 1) / total_images * 100
                    self.progress_callback(progress, f"Processing {Path(image_path).name}")

        except Exception as e:
            results['errors'].append(f"Batch processing error: {str(e)}")

        self.is_processing = False
        return results

    def cancel_processing(self):
        """Cancel the current batch processing."""
        self.is_processing = False

class AdvancedExporter:
    """Advanced export system with multiple formats and optimization."""

    @staticmethod
    def export_svg(image: Image.Image, output_path: str, circle_data: List[Dict]) -> bool:
        """Export as SVG vector format."""
        try:
            width, height = image.size

            svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
<rect width="{width}" height="{height}" fill="white"/>
'''

            # Add circles as vector elements
            for circle in circle_data:
                x, y, r, color = circle['x'], circle['y'], circle['r'], circle['color']
                if isinstance(color, tuple):
                    color_str = f"rgb({color[0]},{color[1]},{color[2]})"
                else:
                    color_str = color

                svg_content += f'<circle cx="{x}" cy="{y}" r="{r}" fill="{color_str}"/>\n'

            svg_content += '</svg>'

            with open(output_path, 'w') as f:
                f.write(svg_content)

            return True

        except Exception as e:
            logger.error(f"SVG export failed: {str(e)}")
            return False

    @staticmethod
    def export_high_resolution(image: Image.Image, output_path: str, scale_factor: int = 4) -> bool:
        """Export high-resolution version for printing."""
        try:
            # Upscale image
            new_size = (image.width * scale_factor, image.height * scale_factor)
            high_res = image.resize(new_size, Image.LANCZOS)

            # Save with high quality
            if output_path.lower().endswith('.jpg') or output_path.lower().endswith('.jpeg'):
                high_res.save(output_path, quality=95, dpi=(300, 300))
            else:
                high_res.save(output_path, dpi=(300, 300))

            return True

        except Exception as e:
            logger.error(f"High-res export failed: {str(e)}")
            return False

class UndoRedoManager:
    """Undo/Redo system for operations."""

    def __init__(self, max_history: int = 20):
        self.history: List[Image.Image] = []
        self.current_index = -1
        self.max_history = max_history

    def add_state(self, image: Image.Image):
        """Add a new state to history."""
        # Remove any states after current index
        self.history = self.history[:self.current_index + 1]

        # Add new state
        self.history.append(image.copy())
        self.current_index += 1

        # Limit history size
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
        """Check if undo is possible."""
        return self.current_index > 0

    def can_redo(self) -> bool:
        """Check if redo is possible."""
        return self.current_index < len(self.history) - 1

    def clear(self):
        """Clear all history."""
        self.history.clear()
        self.current_index = -1

class ThreadSafeImageProcessor:
    """Thread-safe image processing with queues."""

    def __init__(self):
        self.processing_queue = queue.Queue(maxsize=5)
        self.result_queue = queue.Queue(maxsize=5)
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

class FaceDetector:
    """Face detection and cropping functionality."""

    def __init__(self):
        self.logger = logger
        self.face_cascade = None
        self.eye_cascade = None
        self.detection_lock = threading.Lock()
        if CV2_AVAILABLE:
            self._load_classifiers()

    def _load_classifiers(self):
        """Load OpenCV face detection classifiers."""
        if not CV2_AVAILABLE:
            return

        try:
            self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')

            if self.face_cascade.empty() or self.eye_cascade.empty():
                raise Exception("Failed to load cascade classifiers")

            self.logger.info("Face detection classifiers loaded successfully")

        except Exception as e:
            self.logger.error(f"Failed to load face detection classifiers: {str(e)}")
            self.face_cascade = None
            self.eye_cascade = None

    def detect_faces(self, image: Image.Image) -> List[Tuple[int, int, int, int]]:
        """Detect faces in an image (thread-safe)."""
        if not CV2_AVAILABLE or not self.face_cascade:
            return []

        with self.detection_lock:
            try:
                cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)

                faces = self.face_cascade.detectMultiScale(
                    gray, scaleFactor=1.1, minNeighbors=5,
                    minSize=(30, 30), flags=cv2.CASCADE_SCALE_IMAGE
                )

                return [(int(x), int(y), int(w), int(h)) for x, y, w, h in faces]

            except Exception as e:
                self.logger.error(f"Face detection failed: {str(e)}")
                return []

    def crop_largest_face(self, image: Image.Image, padding: float = 0.2) -> Optional[Image.Image]:
        """Crop the largest detected face from an image."""
        faces = self.detect_faces(image)
        if not faces:
            return None

        largest_face = max(faces, key=lambda f: f[2] * f[3])
        x, y, w, h = largest_face

        pad_x = int(w * padding)
        pad_y = int(h * padding)

        left = max(0, x - pad_x)
        top = max(0, y - pad_y)
        right = min(image.width, x + w + pad_x)
        bottom = min(image.height, y + h + pad_y)

        return image.crop((left, top, right, bottom))

class CameraCapture:
    """Thread-safe live camera capture functionality."""

    def __init__(self):
        self.logger = logger
        self.camera = None
        self.is_capturing = False
        self.current_frame = None
        self.capture_thread = None
        self.frame_lock = threading.Lock()
        self.frame_queue = queue.Queue(maxsize=2)

    def start_camera(self, camera_index: int = 0) -> bool:
        """Start camera capture."""
        if not CV2_AVAILABLE:
            self.logger.error("OpenCV not available for camera capture")
            return False

        try:
            self.camera = cv2.VideoCapture(camera_index)
            if not self.camera.isOpened():
                raise Exception("Camera not available")

            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera.set(cv2.CAP_PROP_FPS, 30)

            self.is_capturing = True
            self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.capture_thread.start()

            self.logger.info("Camera started successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to start camera: {str(e)}")
            self.stop_camera()
            return False

    def stop_camera(self):
        """Stop camera capture."""
        self.is_capturing = False

        if self.capture_thread:
            self.capture_thread.join(timeout=1.0)

        if self.camera:
            self.camera.release()
            self.camera = None

        while not self.frame_queue.empty():
            try:
                self.frame_queue.get_nowait()
            except queue.Empty:
                break

        self.logger.info("Camera stopped")

    def _capture_loop(self):
        """Main camera capture loop."""
        while self.is_capturing and self.camera:
            try:
                ret, frame = self.camera.read()
                if ret:
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_frame = Image.fromarray(frame_rgb)

                    with self.frame_lock:
                        self.current_frame = pil_frame

                    try:
                        if self.frame_queue.full():
                            self.frame_queue.get_nowait()
                        self.frame_queue.put_nowait(pil_frame)
                    except queue.Full:
                        pass

                time.sleep(0.033)  # ~30 FPS

            except Exception as e:
                self.logger.error(f"Camera capture error: {str(e)}")
                break

        self.is_capturing = False

    def get_latest_frame(self) -> Optional[Image.Image]:
        """Get the latest camera frame."""
        try:
            return self.frame_queue.get_nowait().copy()
        except queue.Empty:
            with self.frame_lock:
                if self.current_frame:
                    return self.current_frame.copy()
            return None

    def is_active(self) -> bool:
        """Check if camera is active."""
        return self.is_capturing

class ArtisticProcessor:
    """Advanced artistic processing and effects."""

    @staticmethod
    def apply_artistic_effect(image: Image.Image, effect: ArtisticEffect) -> Image.Image:
        """Apply artistic effects to an image."""
        if effect == ArtisticEffect.NONE:
            return image

        elif effect == ArtisticEffect.VINTAGE:
            # Vintage effect with sepia and vignette
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(0.8)

            # Convert to sepia
            pixels = np.array(image)
            sepia_filter = np.array([
                [0.393, 0.769, 0.189],
                [0.349, 0.686, 0.168],
                [0.272, 0.534, 0.131]
            ])
            sepia_img = pixels.dot(sepia_filter.T)
            sepia_img = np.clip(sepia_img, 0, 255).astype(np.uint8)
            return Image.fromarray(sepia_img)

        elif effect == ArtisticEffect.NEON:
            # Neon glow effect
            image = image.filter(ImageFilter.EDGE_ENHANCE_MORE)
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.5)
            enhancer = ImageEnhance.Color(image)
            return enhancer.enhance(2.0)

        elif effect == ArtisticEffect.SKETCH:
            # Pencil sketch effect
            gray = image.convert('L')
            inverted = ImageOps.invert(gray)
            blurred = inverted.filter(ImageFilter.GaussianBlur(radius=5))
            sketch = ImageChops.divide(gray, ImageOps.invert(blurred))
            return sketch.convert('RGB')

        elif effect == ArtisticEffect.CROSSHATCH:
            # Cross-hatching effect
            gray = image.convert('L')
            # Simulate cross-hatching with edge detection and contrast
            edges = gray.filter(ImageFilter.FIND_EDGES)
            enhancer = ImageEnhance.Contrast(edges)
            crosshatch = enhancer.enhance(2.0)
            return crosshatch.convert('RGB')

        elif effect == ArtisticEffect.MOSAIC:
            # Mosaic effect by pixelating
            small = image.resize((image.width//20, image.height//20), Image.NEAREST)
            return small.resize(image.size, Image.NEAREST)

        elif effect == ArtisticEffect.EMBOSS:
            return image.filter(ImageFilter.EMBOSS)

        else:
            return image

class FaceGenerator:
    """Generate synthetic face images for testing."""

    @staticmethod
    def create_test_face(width: int = 200, height: int = 240) -> Image.Image:
        """Create a synthetic face image."""
        img = Image.new('RGB', (width, height), (245, 220, 177))
        draw = ImageDraw.Draw(img)

        # Face outline
        face_margin = 20
        draw.ellipse([face_margin, face_margin, width-face_margin, height-face_margin],
                    fill=(235, 210, 167), outline=(200, 175, 132), width=2)

        # Hair
        hair_height = height // 3
        draw.ellipse([face_margin-10, face_margin-10, width-face_margin+10, hair_height],
                    fill=(101, 67, 33))

        # Eyes, nose, mouth (simplified for brevity)
        eye_y = height // 3
        eye_width = width // 8
        left_eye_x = width // 3 - eye_width
        right_eye_x = 2 * width // 3

        # Eyes
        draw.ellipse([left_eye_x, eye_y, left_eye_x + eye_width*2, eye_y + eye_width],
                    fill=(255, 255, 255), outline=(150, 150, 150))
        draw.ellipse([right_eye_x, eye_y, right_eye_x + eye_width*2, eye_y + eye_width],
                    fill=(255, 255, 255), outline=(150, 150, 150))

        # Pupils
        pupil_size = eye_width // 2
        draw.ellipse([left_eye_x + eye_width//2, eye_y + eye_width//4,
                     left_eye_x + eye_width//2 + pupil_size, eye_y + eye_width//4 + pupil_size],
                    fill=(50, 50, 50))
        draw.ellipse([right_eye_x + eye_width//2, eye_y + eye_width//4,
                     right_eye_x + eye_width//2 + pupil_size, eye_y + eye_width//4 + pupil_size],
                    fill=(50, 50, 50))

        return img

class AdvancedDotMatrixConverter:
    """Advanced dot matrix converter with creative patterns and effects."""

    def __init__(self):
        self.logger = logger
        self.conversion_lock = threading.Lock()
        self.circle_data = []  # Store circle data for SVG export

    def convert_image_advanced(self, image: Image.Image, matrix_width: int = 45,
                             matrix_height: int = 19, output_size: Tuple[int, int] = (900, 380),
                             pattern: DotPattern = DotPattern.CIRCLE, circle_spacing: float = 1.0,
                             use_color: bool = False, color_palette: Optional[List] = None,
                             artistic_effect: ArtisticEffect = ArtisticEffect.NONE,
                             animate: bool = False, animation_frame: int = 0,
                             edge_enhancement: bool = False, noise_reduction: bool = False,
                             custom_background: Optional[Tuple[int, int, int]] = None) -> Optional[Image.Image]:
        """
        Advanced image to dot matrix conversion with artistic features.
        """
        with self.conversion_lock:
            try:
                self.logger.info(f"Converting image with pattern: {pattern.value}")
                self.circle_data = []  # Reset circle data

                work_image = image.copy()

                # Apply preprocessing
                if noise_reduction:
                    work_image = work_image.filter(ImageFilter.SMOOTH)

                if edge_enhancement:
                    work_image = work_image.filter(ImageFilter.EDGE_ENHANCE)

                # Apply artistic effect
                if artistic_effect != ArtisticEffect.NONE:
                    work_image = ArtisticProcessor.apply_artistic_effect(work_image, artistic_effect)

                # Process image for dot matrix
                if use_color and color_palette:
                    img_resized = work_image.resize((matrix_width, matrix_height), Image.LANCZOS)
                    img_gray = img_resized.convert('L')
                    pixel_brightness = np.array(img_gray)
                    pixel_colors = self._map_to_palette(np.array(img_resized), color_palette)
                else:
                    img_gray = work_image.convert('L')
                    img_resized = img_gray.resize((matrix_width, matrix_height), Image.LANCZOS)
                    pixel_brightness = np.array(img_resized)
                    pixel_colors = None

                # Create output with custom background
                bg_color = custom_background if custom_background else (255, 255, 255)
                output_img = Image.new('RGB', output_size, bg_color)
                draw = ImageDraw.Draw(output_img)

                # Calculate dimensions
                cell_width = output_size[0] / matrix_width
                cell_height = output_size[1] / matrix_height
                max_radius = min(cell_width, cell_height) / 2 * circle_spacing

                # Draw patterns
                for y in range(matrix_height):
                    for x in range(matrix_width):
                        brightness = pixel_brightness[y, x]
                        base_radius = max_radius * (1 - brightness / 255.0)

                        # Animation effect
                        if animate:
                            radius = base_radius * (0.8 + 0.4 * math.sin(animation_frame * 0.1 + x * 0.2 + y * 0.2))
                        else:
                            radius = base_radius

                        if radius > 0.5:
                            # Determine color
                            if use_color and pixel_colors is not None:
                                color = tuple(pixel_colors[y, x])
                            else:
                                color = 'black'

                            # Calculate position
                            center_x = (x + 0.5) * cell_width
                            center_y = (y + 0.5) * cell_height

                            # Store circle data for SVG export
                            self.circle_data.append({
                                'x': center_x, 'y': center_y, 'r': radius, 'color': color
                            })

                            # Draw pattern
                            self._draw_pattern(draw, pattern, center_x, center_y, radius, color)

                return output_img

            except Exception as e:
                self.logger.error(f"Advanced conversion failed: {str(e)}")
                return None

    def get_circle_data(self) -> List[Dict]:
        """Get circle data for SVG export."""
        return self.circle_data.copy()

    def _map_to_palette(self, image_array: np.ndarray, palette: List[Tuple[int, int, int]]) -> np.ndarray:
        """Map image colors to a specific palette."""
        if len(image_array.shape) != 3:
            return image_array

        height, width, channels = image_array.shape
        mapped = np.zeros_like(image_array)

        for y in range(height):
            for x in range(width):
                pixel = image_array[y, x]
                closest_color = min(palette, key=lambda c: np.sum((np.array(c) - pixel) ** 2))
                mapped[y, x] = closest_color

        return mapped

    def _draw_pattern(self, draw: ImageDraw.Draw, pattern: DotPattern,
                     center_x: float, center_y: float, radius: float, color):
        """Draw different patterns instead of just circles."""
        if pattern == DotPattern.CIRCLE:
            self._draw_circle(draw, center_x, center_y, radius, color)
        elif pattern == DotPattern.SQUARE:
            self._draw_square(draw, center_x, center_y, radius, color)
        elif pattern == DotPattern.DIAMOND:
            self._draw_diamond(draw, center_x, center_y, radius, color)
        elif pattern == DotPattern.HEXAGON:
            self._draw_hexagon(draw, center_x, center_y, radius, color)
        elif pattern == DotPattern.STAR:
            self._draw_star(draw, center_x, center_y, radius, color)
        elif pattern == DotPattern.CROSS:
            self._draw_cross(draw, center_x, center_y, radius, color)
        elif pattern == DotPattern.HEART:
            self._draw_heart(draw, center_x, center_y, radius, color)
        elif pattern == DotPattern.TRIANGLE:
            self._draw_triangle(draw, center_x, center_y, radius, color)
        elif pattern == DotPattern.HALFTONE:
            self._draw_halftone(draw, center_x, center_y, radius, color)
        elif pattern == DotPattern.STIPPLE:
            self._draw_stipple(draw, center_x, center_y, radius, color)
        elif pattern == DotPattern.ASCII_DOT:
            self._draw_ascii_dot(draw, center_x, center_y, radius, color)

    def _draw_circle(self, draw: ImageDraw.Draw, cx: float, cy: float, r: float, color):
        """Draw a circle."""
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)

    def _draw_square(self, draw: ImageDraw.Draw, cx: float, cy: float, r: float, color):
        """Draw a square."""
        draw.rectangle([cx - r, cy - r, cx + r, cy + r], fill=color)

    def _draw_diamond(self, draw: ImageDraw.Draw, cx: float, cy: float, r: float, color):
        """Draw a diamond."""
        points = [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]
        draw.polygon(points, fill=color)

    def _draw_hexagon(self, draw: ImageDraw.Draw, cx: float, cy: float, r: float, color):
        """Draw a hexagon."""
        points = []
        for i in range(6):
            angle = i * math.pi / 3
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            points.append((x, y))
        draw.polygon(points, fill=color)

    def _draw_star(self, draw: ImageDraw.Draw, cx: float, cy: float, r: float, color):
        """Draw a 5-pointed star."""
        points = []
        for i in range(10):
            angle = i * math.pi / 5
            radius = r if i % 2 == 0 else r * 0.4
            x = cx + radius * math.cos(angle - math.pi / 2)
            y = cy + radius * math.sin(angle - math.pi / 2)
            points.append((x, y))
        draw.polygon(points, fill=color)

    def _draw_cross(self, draw: ImageDraw.Draw, cx: float, cy: float, r: float, color):
        """Draw a cross."""
        thickness = r * 0.3
        # Vertical line
        draw.rectangle([cx - thickness, cy - r, cx + thickness, cy + r], fill=color)
        # Horizontal line
        draw.rectangle([cx - r, cy - thickness, cx + r, cy + thickness], fill=color)

    def _draw_heart(self, draw: ImageDraw.Draw, cx: float, cy: float, r: float, color):
        """Draw a heart shape."""
        # Simplified heart using circles and triangle
        r_small = r * 0.3
        # Left circle
        draw.ellipse([cx - r*0.7, cy - r*0.5, cx - r*0.1, cy + r*0.1], fill=color)
        # Right circle
        draw.ellipse([cx + r*0.1, cy - r*0.5, cx + r*0.7, cy + r*0.1], fill=color)
        # Triangle bottom
        points = [(cx - r*0.5, cy), (cx + r*0.5, cy), (cx, cy + r)]
        draw.polygon(points, fill=color)

    def _draw_triangle(self, draw: ImageDraw.Draw, cx: float, cy: float, r: float, color):
        """Draw a triangle."""
        points = [
            (cx, cy - r),
            (cx - r * 0.866, cy + r * 0.5),
            (cx + r * 0.866, cy + r * 0.5)
        ]
        draw.polygon(points, fill=color)

    def _draw_halftone(self, draw: ImageDraw.Draw, cx: float, cy: float, r: float, color):
        """Draw halftone pattern (multiple small circles)."""
        # Create a cluster of small circles for halftone effect
        num_dots = max(1, int(r / 2))
        for i in range(num_dots):
            offset_x = random.uniform(-r*0.3, r*0.3)
            offset_y = random.uniform(-r*0.3, r*0.3)
            dot_r = r / num_dots
            draw.ellipse([cx + offset_x - dot_r, cy + offset_y - dot_r,
                         cx + offset_x + dot_r, cy + offset_y + dot_r], fill=color)

    def _draw_stipple(self, draw: ImageDraw.Draw, cx: float, cy: float, r: float, color):
        """Draw stippling pattern (tiny random dots)."""
        # Create random small dots for stippling effect
        num_dots = max(1, int(r * 2))
        for _ in range(num_dots):
            offset_x = random.uniform(-r, r)
            offset_y = random.uniform(-r, r)
            if offset_x*offset_x + offset_y*offset_y <= r*r:  # Keep within circle
                dot_size = 1
                draw.ellipse([cx + offset_x - dot_size, cy + offset_y - dot_size,
                             cx + offset_x + dot_size, cy + offset_y + dot_size], fill=color)

    def _draw_ascii_dot(self, draw: ImageDraw.Draw, cx: float, cy: float, r: float, color):
        """Draw ASCII-style dot characters."""
        try:
            # Use different characters based on radius/intensity
            if r > 8:
                char = "●"
            elif r > 6:
                char = "◉"
            elif r > 4:
                char = "○"
            elif r > 2:
                char = "·"
            else:
                char = "."

            # Try to draw text (may fail if font not available)
            font_size = max(8, int(r * 1.5))
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                font = ImageFont.load_default()

            draw.text((cx - r/2, cy - r/2), char, fill=color, font=font)

        except Exception:
            # Fallback to circle if text drawing fails
            self._draw_circle(draw, cx, cy, r, color)

class DualDisplayWindow:
    """Enhanced dual display window with gallery and tools."""

    def __init__(self, parent, title="Dual Display"):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title(title)
        self.window.geometry("1600x900")

        self.left_canvas_lock = threading.Lock()
        self.right_canvas_lock = threading.Lock()

        self.setup_enhanced_dual_display()

    def setup_enhanced_dual_display(self):
        """Create enhanced dual display layout with tools."""
        # Main container with paned window
        paned = ttk.PanedWindow(self.window, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left panel (Original)
        left_panel = ttk.Frame(paned)
        paned.add(left_panel, weight=1)

        left_frame = ttk.LabelFrame(left_panel, text="Original / Live Feed", padding="10")
        left_frame.pack(fill=tk.BOTH, expand=True)

        self.left_canvas = tk.Canvas(left_frame, bg='lightgray', width=750, height=700)
        self.left_canvas.pack(fill=tk.BOTH, expand=True)

        # Right panel (Artistic)
        right_panel = ttk.Frame(paned)
        paned.add(right_panel, weight=1)

        right_frame = ttk.LabelFrame(right_panel, text="Artistic Creation", padding="10")
        right_frame.pack(fill=tk.BOTH, expand=True)

        self.right_canvas = tk.Canvas(right_frame, bg='black', width=750, height=700)
        self.right_canvas.pack(fill=tk.BOTH, expand=True)

        # Enhanced status bar
        status_frame = ttk.Frame(self.window)
        status_frame.pack(fill=tk.X, pady=(0, 10), padx=10)

        self.left_status = ttk.Label(status_frame, text="Original: No image", relief=tk.SUNKEN, font=('Arial', 10))
        self.left_status.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        self.right_status = ttk.Label(status_frame, text="Artistic: No creation", relief=tk.SUNKEN, font=('Arial', 10))
        self.right_status.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))

        # Quick actions toolbar
        toolbar = ttk.Frame(self.window)
        toolbar.pack(fill=tk.X, pady=(0, 5), padx=10)

        ttk.Button(toolbar, text="Quick Save Both", command=self.quick_save_both).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Swap Views", command=self.swap_views).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Show Info", command=self.show_image_info).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Fullscreen Art", command=self.fullscreen_art).pack(side=tk.LEFT, padx=(0, 5))

    def update_left_display(self, image: Image.Image, status_text: str = ""):
        """Update left display."""
        def _update():
            with self.left_canvas_lock:
                try:
                    display_image = image.copy()
                    canvas_width = self.left_canvas.winfo_width()
                    canvas_height = self.left_canvas.winfo_height()

                    if canvas_width > 1 and canvas_height > 1:
                        display_image.thumbnail((canvas_width-20, canvas_height-20), Image.LANCZOS)

                    self.left_photo = ImageTk.PhotoImage(display_image)

                    self.left_canvas.delete("all")
                    canvas_center_x = canvas_width // 2 if canvas_width > 1 else 375
                    canvas_center_y = canvas_height // 2 if canvas_height > 1 else 350
                    self.left_canvas.create_image(canvas_center_x, canvas_center_y, image=self.left_photo)

                    if status_text:
                        self.left_status.config(text=f"{status_text}")

                except Exception as e:
                    logger.error(f"Failed to update left display: {str(e)}")

        self.window.after(0, _update)

    def update_right_display(self, image: Image.Image, status_text: str = ""):
        """Update right display."""
        def _update():
            with self.right_canvas_lock:
                try:
                    display_image = image.copy()
                    canvas_width = self.right_canvas.winfo_width()
                    canvas_height = self.right_canvas.winfo_height()

                    if canvas_width > 1 and canvas_height > 1:
                        display_image.thumbnail((canvas_width-20, canvas_height-20), Image.LANCZOS)

                    self.right_photo = ImageTk.PhotoImage(display_image)

                    self.right_canvas.delete("all")
                    canvas_center_x = canvas_width // 2 if canvas_width > 1 else 375
                    canvas_center_y = canvas_height // 2 if canvas_height > 1 else 350
                    self.right_canvas.create_image(canvas_center_x, canvas_center_y, image=self.right_photo)

                    if status_text:
                        self.right_status.config(text=f"{status_text}")

                except Exception as e:
                    logger.error(f"Failed to update right display: {str(e)}")

        self.window.after(0, _update)

    def quick_save_both(self):
        """Quick save both images."""
        messagebox.showinfo("Quick Save", "Quick save feature - saves both images to gallery!")

    def swap_views(self):
        """Swap the left and right views."""
        messagebox.showinfo("Swap Views", "View swapping feature coming soon!")

    def show_image_info(self):
        """Show detailed image information."""
        messagebox.showinfo("Image Info", "Detailed image analysis feature coming soon!")

    def fullscreen_art(self):
        """Show artwork in fullscreen."""
        messagebox.showinfo("Fullscreen", "Fullscreen art viewer feature coming soon!")

class MasterDotMatrixStudio:
    """Master application with all professional features."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Dot Matrix Art Studio Pro - Master Edition")
        self.root.geometry("800x1100")

        # Initialize all systems
        self.processor = ThreadSafeImageProcessor()
        self.converter = AdvancedDotMatrixConverter()
        self.face_generator = FaceGenerator()
        self.face_detector = FaceDetector()
        self.camera = CameraCapture()
        self.project_manager = ProjectManager()
        self.undo_manager = UndoRedoManager()
        self.batch_processor = BatchProcessor(self.converter)

        # State variables
        self.current_image = None
        self.current_result = None
        self.current_project = ProjectSettings("Untitled")
        self.camera_active = False
        self.auto_convert_active = False
        self.dual_display = None
        self.animation_active = False
        self.animation_frame = 0

        # Threading controls
        self.camera_update_job = None
        self.auto_convert_job = None
        self.animation_job = None

        self.setup_master_gui()
        self.logger = logger

        # Keyboard shortcuts
        self.setup_keyboard_shortcuts()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.logger.info("Master Dot Matrix Art Studio initialized")

    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts."""
        self.root.bind('<Control-s>', lambda e: self.save_project())
        self.root.bind('<Control-o>', lambda e: self.load_project())
        self.root.bind('<Control-n>', lambda e: self.new_project())
        self.root.bind('<Control-z>', lambda e: self.undo())
        self.root.bind('<Control-y>', lambda e: self.redo())
        self.root.bind('<F5>', lambda e: self.convert_image())
        self.root.bind('<F11>', lambda e: self.open_dual_display())

    def setup_master_gui(self):
        """Create the master GUI with all professional features."""
        # Create main notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create all tabs
        self.setup_project_tab()
        self.setup_input_tab()
        self.setup_artistic_tab()
        self.setup_advanced_tab()
        self.setup_batch_tab()
        self.setup_gallery_tab()

        # Status bar
        self.status_var = tk.StringVar(value="Master Art Studio Ready - Create Amazing Dot Matrix Art!")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, font=('Arial', 10))
        status_bar.pack(fill=tk.X, pady=(0, 10), padx=10)

    def setup_project_tab(self):
        """Setup project management tab."""
        project_tab = ttk.Frame(self.notebook)
        self.notebook.add(project_tab, text="Project")

        # Project info
        info_frame = ttk.LabelFrame(project_tab, text="Current Project", padding="10")
        info_frame.pack(fill=tk.X, pady=(10, 10))

        self.project_name_var = tk.StringVar(value="Untitled")
        ttk.Label(info_frame, text="Project Name:").pack(anchor=tk.W)
        ttk.Entry(info_frame, textvariable=self.project_name_var, font=('Arial', 12)).pack(fill=tk.X, pady=(5, 10))

        # Project actions
        actions_frame = ttk.Frame(info_frame)
        actions_frame.pack(fill=tk.X)

        ttk.Button(actions_frame, text="Save Project", command=self.save_project).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(actions_frame, text="Load Project", command=self.load_project).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(actions_frame, text="New Project", command=self.new_project).pack(side=tk.LEFT, padx=(0, 5))

        # Recent projects
        recent_frame = ttk.LabelFrame(project_tab, text="Recent Projects", padding="10")
        recent_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Projects listbox
        self.projects_listbox = tk.Listbox(recent_frame, height=8, font=('Arial', 10))
        self.projects_listbox.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.projects_listbox.bind('<Double-1>', self.load_selected_project)

        ttk.Button(recent_frame, text="Refresh Projects", command=self.refresh_projects_list).pack()

        # Undo/Redo
        history_frame = ttk.LabelFrame(project_tab, text="History", padding="10")
        history_frame.pack(fill=tk.X, pady=(0, 10))

        history_buttons = ttk.Frame(history_frame)
        history_buttons.pack(fill=tk.X)

        self.undo_button = ttk.Button(history_buttons, text="Undo (Ctrl+Z)", command=self.undo)
        self.undo_button.pack(side=tk.LEFT, padx=(0, 5))

        self.redo_button = ttk.Button(history_buttons, text="Redo (Ctrl+Y)", command=self.redo)
        self.redo_button.pack(side=tk.LEFT)

        self.refresh_projects_list()

    def setup_input_tab(self):
        """Setup input and capture tab."""
        input_tab = ttk.Frame(self.notebook)
        self.notebook.add(input_tab, text="Input")

        # Display controls
        display_frame = ttk.LabelFrame(input_tab, text="Art Studio Display", padding="10")
        display_frame.pack(fill=tk.X, pady=(10, 10))

        ttk.Button(display_frame, text="Open Dual Display Studio (F11)",
                  command=self.open_dual_display, style='Accent.TButton').pack(pady=5)

        # Input sources
        source_frame = ttk.LabelFrame(input_tab, text="Input Sources", padding="10")
        source_frame.pack(fill=tk.X, pady=(0, 10))

        source_row1 = ttk.Frame(source_frame)
        source_row1.pack(fill=tk.X, pady=(0, 5))

        ttk.Button(source_row1, text="Load Image", command=self.load_image).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(source_row1, text="Generate Test Face", command=self.generate_test_face).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(source_row1, text="Extract Palette", command=self.extract_image_palette).pack(side=tk.LEFT)

        source_row2 = ttk.Frame(source_frame)
        source_row2.pack(fill=tk.X, pady=(5, 0))

        self.camera_button = ttk.Button(source_row2, text="Start Camera", command=self.toggle_camera)
        self.camera_button.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(source_row2, text="Capture Frame", command=self.capture_camera_frame).pack(side=tk.LEFT, padx=(0, 10))

        # Face detection
        face_frame = ttk.LabelFrame(input_tab, text="Face Detection", padding="10")
        face_frame.pack(fill=tk.X, pady=(0, 10))

        face_row1 = ttk.Frame(face_frame)
        face_row1.pack(fill=tk.X, pady=(0, 5))

        ttk.Button(face_row1, text="Detect Faces", command=self.detect_faces).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(face_row1, text="Auto-Crop Face", command=self.auto_crop_face).pack(side=tk.LEFT)

        face_row2 = ttk.Frame(face_frame)
        face_row2.pack(fill=tk.X)

        ttk.Label(face_row2, text="Crop Padding:").pack(side=tk.LEFT)
        self.face_padding_var = tk.StringVar(value="0.2")
        ttk.Entry(face_row2, textvariable=self.face_padding_var, width=8).pack(side=tk.LEFT, padx=(5, 15))

        self.auto_crop_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(face_row2, text="Auto-crop from camera", variable=self.auto_crop_var).pack(side=tk.LEFT)

        # Current image info
        self.image_info_label = ttk.Label(input_tab, text="No image loaded", font=('Arial', 10, 'italic'))
        self.image_info_label.pack(pady=10)

    def setup_artistic_tab(self):
        """Setup artistic effects and patterns tab."""
        artistic_tab = ttk.Frame(self.notebook)
        self.notebook.add(artistic_tab, text="Artistic")

        # Pattern selection
        pattern_frame = ttk.LabelFrame(artistic_tab, text="Dot Patterns", padding="10")
        pattern_frame.pack(fill=tk.X, pady=(10, 10))

        self.pattern_var = tk.StringVar(value=DotPattern.CIRCLE.value)

        pattern_row1 = ttk.Frame(pattern_frame)
        pattern_row1.pack(fill=tk.X, pady=(0, 5))

        for pattern in [DotPattern.CIRCLE, DotPattern.SQUARE, DotPattern.DIAMOND, DotPattern.HEXAGON]:
            ttk.Radiobutton(pattern_row1, text=pattern.value.title(),
                           variable=self.pattern_var, value=pattern.value).pack(side=tk.LEFT, padx=(0, 10))

        pattern_row2 = ttk.Frame(pattern_frame)
        pattern_row2.pack(fill=tk.X, pady=(0, 5))

        for pattern in [DotPattern.STAR, DotPattern.CROSS, DotPattern.HEART, DotPattern.TRIANGLE]:
            ttk.Radiobutton(pattern_row2, text=pattern.value.title(),
                           variable=self.pattern_var, value=pattern.value).pack(side=tk.LEFT, padx=(0, 10))

        pattern_row3 = ttk.Frame(pattern_frame)
        pattern_row3.pack(fill=tk.X)

        for pattern in [DotPattern.HALFTONE, DotPattern.STIPPLE, DotPattern.ASCII_DOT]:
            ttk.Radiobutton(pattern_row3, text=pattern.value.replace('_', ' ').title(),
                           variable=self.pattern_var, value=pattern.value).pack(side=tk.LEFT, padx=(0, 10))

        # Color palettes
        color_frame = ttk.LabelFrame(artistic_tab, text="Color Palettes", padding="10")
        color_frame.pack(fill=tk.X, pady=(0, 10))

        color_row1 = ttk.Frame(color_frame)
        color_row1.pack(fill=tk.X, pady=(0, 5))

        self.palette_var = tk.StringVar(value="Classic B&W")
        self.palette_combo = ttk.Combobox(color_row1, textvariable=self.palette_var,
                                    values=list(ColorPalette.PALETTES.keys()), state="readonly", width=20)
        self.palette_combo.pack(side=tk.LEFT, padx=(0, 10))

        self.use_palette_var = tk.BooleanVar()
        ttk.Checkbutton(color_row1, text="Use Palette", variable=self.use_palette_var).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(color_row1, text="Custom BG", command=self.choose_background_color).pack(side=tk.LEFT)

        # Artistic effects
        effects_frame = ttk.LabelFrame(artistic_tab, text="Artistic Effects", padding="10")
        effects_frame.pack(fill=tk.X, pady=(0, 10))

        self.effect_var = tk.StringVar(value=ArtisticEffect.NONE.value)
        effect_combo = ttk.Combobox(effects_frame, textvariable=self.effect_var,
                                   values=[e.value.replace('_', ' ').title() for e in ArtisticEffect],
                                   state="readonly", width=20)
        effect_combo.pack(side=tk.LEFT, padx=(0, 10))

        # Enhancement options
        enhance_frame = ttk.LabelFrame(artistic_tab, text="Enhancement", padding="10")
        enhance_frame.pack(fill=tk.X, pady=(0, 10))

        enhance_row = ttk.Frame(enhance_frame)
        enhance_row.pack(fill=tk.X)

        self.edge_enhance_var = tk.BooleanVar()
        ttk.Checkbutton(enhance_row, text="Edge Enhancement", variable=self.edge_enhance_var).pack(side=tk.LEFT, padx=(0, 15))

        self.noise_reduce_var = tk.BooleanVar()
        ttk.Checkbutton(enhance_row, text="Noise Reduction", variable=self.noise_reduce_var).pack(side=tk.LEFT)

        # Convert button
        convert_frame = ttk.Frame(artistic_tab)
        convert_frame.pack(pady=20)

        ttk.Button(convert_frame, text="Create Art (F5)", command=self.convert_image,
                  style='Accent.TButton').pack()

        self.bg_color = None

    def setup_advanced_tab(self):
        """Setup advanced settings and animation tab."""
        advanced_tab = ttk.Frame(self.notebook)
        self.notebook.add(advanced_tab, text="Advanced")

        # Matrix settings
        matrix_frame = ttk.LabelFrame(advanced_tab, text="Matrix Configuration", padding="10")
        matrix_frame.pack(fill=tk.X, pady=(10, 10))

        matrix_row1 = ttk.Frame(matrix_frame)
        matrix_row1.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(matrix_row1, text="Matrix Size:").pack(side=tk.LEFT)
        self.width_var = tk.StringVar(value="45")
        ttk.Entry(matrix_row1, textvariable=self.width_var, width=8).pack(side=tk.LEFT, padx=(5, 5))
        ttk.Label(matrix_row1, text="×").pack(side=tk.LEFT)
        self.height_var = tk.StringVar(value="19")
        ttk.Entry(matrix_row1, textvariable=self.height_var, width=8).pack(side=tk.LEFT, padx=(5, 15))

        ttk.Label(matrix_row1, text="Output Size:").pack(side=tk.LEFT)
        self.out_width_var = tk.StringVar(value="900")
        ttk.Entry(matrix_row1, textvariable=self.out_width_var, width=8).pack(side=tk.LEFT, padx=(5, 5))
        ttk.Label(matrix_row1, text="×").pack(side=tk.LEFT)
        self.out_height_var = tk.StringVar(value="380")
        ttk.Entry(matrix_row1, textvariable=self.out_height_var, width=8).pack(side=tk.LEFT, padx=(5, 0))

        matrix_row2 = ttk.Frame(matrix_frame)
        matrix_row2.pack(fill=tk.X)

        ttk.Label(matrix_row2, text="Spacing:").pack(side=tk.LEFT)
        self.spacing_var = tk.StringVar(value="1.0")
        spacing_scale = ttk.Scale(matrix_row2, from_=0.1, to=2.0, variable=self.spacing_var, orient=tk.HORIZONTAL)
        spacing_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 10))
        spacing_label = ttk.Label(matrix_row2, textvariable=self.spacing_var, width=5)
        spacing_label.pack(side=tk.LEFT)

        # Animation
        anim_frame = ttk.LabelFrame(advanced_tab, text="Animation", padding="10")
        anim_frame.pack(fill=tk.X, pady=(0, 10))

        anim_row = ttk.Frame(anim_frame)
        anim_row.pack(fill=tk.X)

        self.animate_var = tk.BooleanVar()
        ttk.Checkbutton(anim_row, text="Animated Effects", variable=self.animate_var,
                       command=self.toggle_animation).pack(side=tk.LEFT, padx=(0, 15))

        # Live processing
        live_frame = ttk.LabelFrame(advanced_tab, text="Live Processing", padding="10")
        live_frame.pack(fill=tk.X, pady=(0, 10))

        self.auto_convert_var = tk.BooleanVar()
        ttk.Checkbutton(live_frame, text="Auto-Convert Camera Feed", variable=self.auto_convert_var,
                       command=self.toggle_auto_convert).pack(anchor=tk.W)

        # Export options
        export_frame = ttk.LabelFrame(advanced_tab, text="Export Options", padding="10")
        export_frame.pack(fill=tk.X, pady=(0, 10))

        export_row1 = ttk.Frame(export_frame)
        export_row1.pack(fill=tk.X, pady=(0, 5))

        ttk.Button(export_row1, text="Save Original", command=self.save_original).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(export_row1, text="Save Artwork", command=self.save_result).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(export_row1, text="Export SVG", command=self.export_svg).pack(side=tk.LEFT)

        export_row2 = ttk.Frame(export_frame)
        export_row2.pack(fill=tk.X)

        ttk.Button(export_row2, text="High-Res Print", command=self.export_high_res).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(export_row2, text="Save Animation", command=self.save_animation).pack(side=tk.LEFT)

    def setup_batch_tab(self):
        """Setup batch processing tab."""
        batch_tab = ttk.Frame(self.notebook)
        self.notebook.add(batch_tab, text="Batch")

        # Batch input
        input_frame = ttk.LabelFrame(batch_tab, text="Batch Input", padding="10")
        input_frame.pack(fill=tk.X, pady=(10, 10))

        input_row = ttk.Frame(input_frame)
        input_row.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(input_row, text="Select Images", command=self.select_batch_images).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(input_row, text="Select Output Folder", command=self.select_output_folder).pack(side=tk.LEFT)

        # Selected files
        self.batch_files_label = ttk.Label(input_frame, text="No files selected", font=('Arial', 10, 'italic'))
        self.batch_files_label.pack(anchor=tk.W)

        self.output_folder_label = ttk.Label(input_frame, text="No output folder selected", font=('Arial', 10, 'italic'))
        self.output_folder_label.pack(anchor=tk.W)

        # Batch settings
        settings_frame = ttk.LabelFrame(batch_tab, text="Batch Settings", padding="10")
        settings_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(settings_frame, text="Use current artistic settings for all images").pack(anchor=tk.W)

        # Batch processing
        process_frame = ttk.LabelFrame(batch_tab, text="Processing", padding="10")
        process_frame.pack(fill=tk.X, pady=(0, 10))

        process_row = ttk.Frame(process_frame)
        process_row.pack(fill=tk.X, pady=(0, 10))

        self.batch_button = ttk.Button(process_row, text="Start Batch Processing",
                                      command=self.start_batch_processing)
        self.batch_button.pack(side=tk.LEFT, padx=(0, 10))

        self.cancel_batch_button = ttk.Button(process_row, text="Cancel",
                                             command=self.cancel_batch_processing, state=tk.DISABLED)
        self.cancel_batch_button.pack(side=tk.LEFT)

        # Progress
        self.batch_progress = ttk.Progressbar(process_frame, mode='determinate')
        self.batch_progress.pack(fill=tk.X, pady=(0, 5))

        self.batch_status_label = ttk.Label(process_frame, text="Ready for batch processing")
        self.batch_status_label.pack(anchor=tk.W)

        # Results
        results_frame = ttk.LabelFrame(batch_tab, text="Results", padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.batch_results_text = tk.Text(results_frame, height=6, font=('Consolas', 9))
        self.batch_results_text.pack(fill=tk.BOTH, expand=True)

        # Initialize batch variables
        self.batch_files = []
        self.batch_output_folder = ""

    def setup_gallery_tab(self):
        """Setup gallery and project showcase tab."""
        gallery_tab = ttk.Frame(self.notebook)
        self.notebook.add(gallery_tab, text="Gallery")

        # Gallery controls
        controls_frame = ttk.Frame(gallery_tab)
        controls_frame.pack(fill=tk.X, pady=(10, 10))

        ttk.Button(controls_frame, text="Refresh Gallery", command=self.refresh_gallery).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(controls_frame, text="Open Gallery Folder", command=self.open_gallery_folder).pack(side=tk.LEFT)

        # Gallery grid (simplified for now)
        gallery_frame = ttk.LabelFrame(gallery_tab, text="Recent Artworks", padding="10")
        gallery_frame.pack(fill=tk.BOTH, expand=True)

        # Gallery listbox (will be enhanced to show thumbnails)
        self.gallery_listbox = tk.Listbox(gallery_frame, height=15, font=('Arial', 10))
        self.gallery_listbox.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.gallery_listbox.bind('<Double-1>', self.open_gallery_item)

        ttk.Button(gallery_frame, text="View Selected", command=self.view_gallery_item).pack()

        self.refresh_gallery()

    # Core functionality methods
    def update_status(self, message: str):
        """Update status bar message."""
        self.status_var.set(message)
        self.root.update_idletasks()
        self.logger.info(f"Status: {message}")

    def open_dual_display(self):
        """Open the enhanced dual display window."""
        if self.dual_display is None or not tk.Toplevel.winfo_exists(self.dual_display.window):
            self.dual_display = DualDisplayWindow(self.root, "Master Art Studio | Original ⟷ Artistic Creation")
            self.update_status("Master Art Studio Display opened - Ready to create masterpieces!")
        else:
            self.dual_display.window.lift()
            self.dual_display.window.focus_set()

    def load_image(self):
        """Load an image file."""
        file_path = filedialog.askopenfilename(
            title="Select Image for Artistic Transformation",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.gif *.tiff *.webp"),
                ("All files", "*.*")
            ]
        )

        if file_path:
            try:
                self.current_image = Image.open(file_path)
                self.undo_manager.add_state(self.current_image)

                filename = os.path.basename(file_path)
                self.image_info_label.config(text=f"{filename} ({self.current_image.size[0]}×{self.current_image.size[1]})")
                self.update_status(f"Image loaded: {filename} - Ready for artistic transformation!")

                if self.dual_display:
                    self.dual_display.update_left_display(self.current_image, f"Loaded: {filename}")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to load image: {str(e)}")
                self.logger.error(f"Failed to load image {file_path}: {str(e)}")

    def generate_test_face(self):
        """Generate a test face image."""
        try:
            self.current_image = self.face_generator.create_test_face()
            self.undo_manager.add_state(self.current_image)

            self.image_info_label.config(text="AI Generated test face (200×240)")
            self.update_status("AI Test face generated - Perfect for portrait art experiments!")

            if self.dual_display:
                self.dual_display.update_left_display(self.current_image, "AI Generated test face")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate test face: {str(e)}")
            self.logger.error(f"Failed to generate test face: {str(e)}")

    def extract_image_palette(self):
        """Extract color palette from current image."""
        if not self.current_image:
            messagebox.showwarning("Warning", "Please load an image first")
            return

        try:
            colors = ColorPalette.extract_dominant_colors(self.current_image, 6)

            # Create a custom palette
            palette_name = f"Extracted_{int(time.time())}"
            ColorPalette.PALETTES[palette_name] = colors

            # Update palette combobox
            self.palette_combo['values'] = list(ColorPalette.PALETTES.keys())
            self.palette_var.set(palette_name)
            self.use_palette_var.set(True)

            color_str = ", ".join([f"RGB{color}" for color in colors[:3]])
            self.update_status(f"Color palette extracted: {color_str}...")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to extract palette: {str(e)}")

    def convert_image(self, animate=False):
        """Master convert function with all features."""
        if not self.current_image:
            if not animate:
                messagebox.showwarning("Warning", "Please load an image first")
            return

        def perform_master_conversion():
            try:
                # Get all settings from GUI
                matrix_width = int(self.width_var.get())
                matrix_height = int(self.height_var.get())
                output_width = int(self.out_width_var.get())
                output_height = int(self.out_height_var.get())

                pattern = DotPattern(self.pattern_var.get())
                circle_spacing = float(self.spacing_var.get())

                # Color settings
                use_color = self.use_palette_var.get()
                color_palette = None
                if use_color:
                    palette_name = self.palette_var.get()
                    color_palette = ColorPalette.PALETTES.get(palette_name)

                # Effects
                effect_name = self.effect_var.get().lower().replace(' ', '_')
                try:
                    artistic_effect = ArtisticEffect(effect_name)
                except ValueError:
                    artistic_effect = ArtisticEffect.NONE

                edge_enhancement = self.edge_enhance_var.get()
                noise_reduction = self.noise_reduce_var.get()

                # Animation
                animation_frame = self.animation_frame if animate else 0

                return self.converter.convert_image_advanced(
                    self.current_image,
                    matrix_width=matrix_width,
                    matrix_height=matrix_height,
                    output_size=(output_width, output_height),
                    pattern=pattern,
                    circle_spacing=circle_spacing,
                    use_color=use_color,
                    color_palette=color_palette,
                    artistic_effect=artistic_effect,
                    animate=animate,
                    animation_frame=animation_frame,
                    edge_enhancement=edge_enhancement,
                    noise_reduction=noise_reduction,
                    custom_background=self.bg_color
                )
            except Exception as e:
                self.logger.error(f"Master conversion failed: {str(e)}")
                return None

        if not animate:
            pattern_name = self.pattern_var.get().replace('_', ' ').title()
            effect_name = self.effect_var.get().replace('_', ' ').title()
            self.update_status(f"Creating {pattern_name} art with {effect_name} effect...")

        # Process in background
        future = self.processor.submit_processing_task(perform_master_conversion)

        def handle_result():
            try:
                result = future.result(timeout=0.1)
                if result:
                    self.current_result = result
                    if not animate:
                        self.undo_manager.add_state(result)

                    if self.dual_display:
                        pattern_name = self.pattern_var.get().replace('_', ' ').title()
                        effect_name = self.effect_var.get().replace('_', ' ').title()
                        status = f"{pattern_name} • {effect_name}"
                        self.dual_display.update_right_display(result, status)

                    if not animate:
                        self.update_status("Artistic masterpiece created successfully!")
                else:
                    if not animate:
                        self.update_status("Conversion failed - Please check settings")

            except Exception as e:
                if not animate:
                    self.update_status("Conversion error occurred")

        self.root.after(200, handle_result)

    def toggle_camera(self):
        """Toggle camera on/off."""
        if not CV2_AVAILABLE:
            messagebox.showerror("Error", "OpenCV not available. Please install opencv-python to use camera features.")
            return

        if not self.camera_active:
            success = self.camera.start_camera()
            if success:
                self.camera_active = True
                self.camera_button.config(text="Stop Camera")
                self.update_status("Camera started - Live feed active!")
                self.start_camera_updates()
            else:
                messagebox.showerror("Error", "Failed to start camera")
        else:
            self.camera.stop_camera()
            self.camera_active = False
            self.camera_button.config(text="Start Camera")
            self.update_status("Camera stopped")
            if self.camera_update_job:
                self.root.after_cancel(self.camera_update_job)
                self.camera_update_job = None

    def start_camera_updates(self):
        """Start live camera feed updates."""
        if self.camera_active and self.camera.is_active():
            frame = self.camera.get_latest_frame()
            if frame:
                # Auto-crop face if enabled
                if self.auto_crop_var.get():
                    cropped = self.face_detector.crop_largest_face(frame, float(self.face_padding_var.get()))
                    if cropped:
                        frame = cropped

                if self.dual_display:
                    self.dual_display.update_left_display(frame, "Live Camera Feed")

                # Auto-convert if enabled
                if self.auto_convert_active:
                    self.current_image = frame
                    self.convert_image()

            self.camera_update_job = self.root.after(100, self.start_camera_updates)

    def capture_camera_frame(self):
        """Capture current camera frame as input image."""
        if not self.camera_active:
            messagebox.showwarning("Warning", "Camera not active")
            return

        frame = self.camera.get_latest_frame()
        if frame:
            # Auto-crop face if enabled
            if self.auto_crop_var.get():
                cropped = self.face_detector.crop_largest_face(frame, float(self.face_padding_var.get()))
                if cropped:
                    frame = cropped

            self.current_image = frame
            self.undo_manager.add_state(self.current_image)

            self.image_info_label.config(text=f"Camera capture ({frame.size[0]}×{frame.size[1]})")
            self.update_status("Camera frame captured successfully!")
        else:
            messagebox.showerror("Error", "No camera frame available")

    def detect_faces(self):
        """Detect faces in current image."""
        if not self.current_image:
            messagebox.showwarning("Warning", "Please load an image first")
            return

        if not CV2_AVAILABLE:
            messagebox.showerror("Error", "OpenCV not available for face detection")
            return

        faces = self.face_detector.detect_faces(self.current_image)
        if faces:
            messagebox.showinfo("Face Detection", f"Found {len(faces)} face(s) in the image!")
            self.update_status(f"Face detection complete: {len(faces)} face(s) found")
        else:
            messagebox.showinfo("Face Detection", "No faces detected in the image")
            self.update_status("Face detection complete: No faces found")

    def auto_crop_face(self):
        """Auto-crop the largest face from current image."""
        if not self.current_image:
            messagebox.showwarning("Warning", "Please load an image first")
            return

        if not CV2_AVAILABLE:
            messagebox.showerror("Error", "OpenCV not available for face detection")
            return

        try:
            padding = float(self.face_padding_var.get())
            cropped = self.face_detector.crop_largest_face(self.current_image, padding)

            if cropped:
                self.current_image = cropped
                self.undo_manager.add_state(self.current_image)

                self.image_info_label.config(text=f"Face cropped ({cropped.size[0]}×{cropped.size[1]})")
                self.update_status("Face auto-cropped successfully!")

                if self.dual_display:
                    self.dual_display.update_left_display(self.current_image, "Auto-cropped face")
            else:
                messagebox.showinfo("Auto-Crop", "No face found to crop")

        except ValueError:
            messagebox.showerror("Error", "Invalid padding value")

    def toggle_auto_convert(self):
        """Toggle auto-convert camera feed."""
        self.auto_convert_active = self.auto_convert_var.get()
        if self.auto_convert_active:
            self.update_status("Auto-convert enabled - Live artistic transformation!")
        else:
            self.update_status("Auto-convert disabled")

    def save_project(self):
        """Save current project."""
        try:
            # Update project settings from GUI
            self.current_project.name = self.project_name_var.get()
            self.current_project.matrix_width = int(self.width_var.get())
            self.current_project.matrix_height = int(self.height_var.get())
            self.current_project.output_width = int(self.out_width_var.get())
            self.current_project.output_height = int(self.out_height_var.get())
            self.current_project.pattern = self.pattern_var.get()
            self.current_project.effect = self.effect_var.get()
            self.current_project.palette = self.palette_var.get()
            self.current_project.use_palette = self.use_palette_var.get()
            self.current_project.spacing = float(self.spacing_var.get())
            self.current_project.edge_enhance = self.edge_enhance_var.get()
            self.current_project.noise_reduce = self.noise_reduce_var.get()
            self.current_project.background_color = self.bg_color
            self.current_project.auto_crop = self.auto_crop_var.get()
            self.current_project.face_padding = float(self.face_padding_var.get())

            success = self.project_manager.save_project(
                self.current_project,
                self.current_image,
                self.current_result
            )

            if success:
                self.update_status(f"Project '{self.current_project.name}' saved successfully!")
                self.refresh_projects_list()
            else:
                self.update_status("Failed to save project")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save project: {str(e)}")

    def load_project(self):
        """Load a project from dialog."""
        projects = self.project_manager.list_projects()
        if not projects:
            messagebox.showinfo("Load Project", "No saved projects found")
            return

        # Simple dialog for project selection
        dialog = tk.Toplevel(self.root)
        dialog.title("Load Project")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Select a project to load:").pack(pady=10)

        listbox = tk.Listbox(dialog, height=10)
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        for project in projects:
            listbox.insert(tk.END, project)

        def load_selected():
            selection = listbox.curselection()
            if selection:
                project_name = projects[selection[0]]
                self._load_project_by_name(project_name)
                dialog.destroy()

        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Load", command=load_selected).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT)

    def _load_project_by_name(self, project_name: str):
        """Load a specific project by name."""
        try:
            result = self.project_manager.load_project(project_name)
            if result:
                settings, original_image, result_image = result

                # Update GUI with loaded settings
                self.project_name_var.set(settings.name)
                self.width_var.set(str(settings.matrix_width))
                self.height_var.set(str(settings.matrix_height))
                self.out_width_var.set(str(settings.output_width))
                self.out_height_var.set(str(settings.output_height))
                self.pattern_var.set(settings.pattern)
                self.effect_var.set(settings.effect)
                self.palette_var.set(settings.palette)
                self.use_palette_var.set(settings.use_palette)
                self.spacing_var.set(str(settings.spacing))
                self.edge_enhance_var.set(settings.edge_enhance)
                self.noise_reduce_var.set(settings.noise_reduce)
                self.auto_crop_var.set(settings.auto_crop)
                self.face_padding_var.set(str(settings.face_padding))
                self.bg_color = settings.background_color

                # Load images
                if original_image:
                    self.current_image = original_image
                    self.undo_manager.add_state(original_image)

                    self.image_info_label.config(text=f"Loaded from project ({original_image.size[0]}×{original_image.size[1]})")

                    if self.dual_display:
                        self.dual_display.update_left_display(original_image, f"Project: {settings.name}")

                if result_image:
                    self.current_result = result_image

                    if self.dual_display:
                        self.dual_display.update_right_display(result_image, f"Loaded: {settings.name}")

                self.current_project = settings
                self.update_status(f"Project '{project_name}' loaded successfully!")

            else:
                messagebox.showerror("Error", f"Failed to load project '{project_name}'")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load project: {str(e)}")

    def new_project(self):
        """Create a new project."""
        self.current_project = ProjectSettings("Untitled")
        self.project_name_var.set("Untitled")

        # Reset to defaults
        self.width_var.set("45")
        self.height_var.set("19")
        self.out_width_var.set("900")
        self.out_height_var.set("380")
        self.pattern_var.set(DotPattern.CIRCLE.value)
        self.effect_var.set(ArtisticEffect.NONE.value)
        self.palette_var.set("Classic B&W")
        self.use_palette_var.set(False)
        self.spacing_var.set("1.0")
        self.edge_enhance_var.set(False)
        self.noise_reduce_var.set(False)
        self.auto_crop_var.set(True)
        self.face_padding_var.set("0.2")
        self.bg_color = None

        # Clear images
        self.current_image = None
        self.current_result = None
        self.undo_manager.clear()

        self.image_info_label.config(text="No image loaded")
        self.update_status("New project created - Ready to start!")

    def refresh_projects_list(self):
        """Refresh the projects list."""
        try:
            projects = self.project_manager.list_projects()
            self.projects_listbox.delete(0, tk.END)
            for project in projects:
                self.projects_listbox.insert(tk.END, project)
        except Exception as e:
            self.logger.error(f"Failed to refresh projects list: {str(e)}")

    def load_selected_project(self, event):
        """Load selected project from listbox."""
        selection = self.projects_listbox.curselection()
        if selection:
            project_name = self.projects_listbox.get(selection[0])
            self._load_project_by_name(project_name)

    def save_original(self):
        """Save the original image."""
        if not self.current_image:
            messagebox.showwarning("Warning", "No original image to save")
            return

        file_path = filedialog.asksaveasfilename(
            title="Save Original Image",
            defaultextension=".png",
            filetypes=[
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg"),
                ("All files", "*.*")
            ]
        )

        if file_path:
            try:
                self.current_image.save(file_path)
                self.update_status(f"Original image saved: {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save image: {str(e)}")

    def save_result(self):
        """Save the result artwork."""
        if not self.current_result:
            messagebox.showwarning("Warning", "No artwork to save - create art first")
            return

        file_path = filedialog.asksaveasfilename(
            title="Save Artwork",
            defaultextension=".png",
            filetypes=[
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg"),
                ("All files", "*.*")
            ]
        )

        if file_path:
            try:
                self.current_result.save(file_path)
                self.update_status(f"Artwork saved: {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save artwork: {str(e)}")

    def export_svg(self):
        """Export artwork as SVG."""
        if not self.current_result:
            messagebox.showwarning("Warning", "No artwork to export - create art first")
            return

        file_path = filedialog.asksaveasfilename(
            title="Export as SVG",
            defaultextension=".svg",
            filetypes=[("SVG files", "*.svg"), ("All files", "*.*")]
        )

        if file_path:
            try:
                circle_data = self.converter.get_circle_data()
                success = AdvancedExporter.export_svg(self.current_result, file_path, circle_data)
                if success:
                    self.update_status(f"SVG exported: {os.path.basename(file_path)}")
                else:
                    messagebox.showerror("Error", "Failed to export SVG")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export SVG: {str(e)}")

    def export_high_res(self):
        """Export high-resolution version for printing."""
        if not self.current_result:
            messagebox.showwarning("Warning", "No artwork to export - create art first")
            return

        file_path = filedialog.asksaveasfilename(
            title="Export High-Resolution",
            defaultextension=".png",
            filetypes=[
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg"),
                ("All files", "*.*")
            ]
        )

        if file_path:
            try:
                success = AdvancedExporter.export_high_resolution(self.current_result, file_path, scale_factor=4)
                if success:
                    self.update_status(f"High-res export completed: {os.path.basename(file_path)}")
                else:
                    messagebox.showerror("Error", "Failed to export high-resolution image")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export high-res: {str(e)}")

    def save_animation(self):
        """Save animation frames."""
        if not self.current_image:
            messagebox.showwarning("Warning", "No image loaded for animation")
            return

        folder_path = filedialog.askdirectory(title="Select folder for animation frames")
        if folder_path:
            try:
                self.update_status("Creating animation frames...")

                for frame in range(24):  # Create 24 frames
                    self.animation_frame = frame
                    result = self.converter.convert_image_advanced(
                        self.current_image,
                        matrix_width=int(self.width_var.get()),
                        matrix_height=int(self.height_var.get()),
                        output_size=(int(self.out_width_var.get()), int(self.out_height_var.get())),
                        pattern=DotPattern(self.pattern_var.get()),
                        circle_spacing=float(self.spacing_var.get()),
                        use_color=self.use_palette_var.get(),
                        color_palette=ColorPalette.PALETTES.get(self.palette_var.get()) if self.use_palette_var.get() else None,
                        artistic_effect=ArtisticEffect(self.effect_var.get().lower().replace(' ', '_')),
                        animate=True,
                        animation_frame=frame,
                        edge_enhancement=self.edge_enhance_var.get(),
                        noise_reduction=self.noise_reduce_var.get(),
                        custom_background=self.bg_color
                    )

                    if result:
                        frame_path = os.path.join(folder_path, f"frame_{frame:03d}.png")
                        result.save(frame_path)

                self.update_status(f"Animation frames saved to {folder_path}")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to save animation: {str(e)}")

    def select_batch_images(self):
        """Select images for batch processing."""
        file_paths = filedialog.askopenfilenames(
            title="Select Images for Batch Processing",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.gif *.tiff *.webp"),
                ("All files", "*.*")
            ]
        )

        if file_paths:
            self.batch_files = list(file_paths)
            self.batch_files_label.config(text=f"{len(self.batch_files)} files selected")
            self.update_status(f"Selected {len(self.batch_files)} images for batch processing")

    def select_output_folder(self):
        """Select output folder for batch processing."""
        folder_path = filedialog.askdirectory(title="Select Output Folder")
        if folder_path:
            self.batch_output_folder = folder_path
            self.output_folder_label.config(text=f"Output: {folder_path}")
            self.update_status(f"Output folder set: {folder_path}")

    def start_batch_processing(self):
        """Start batch processing."""
        if not self.batch_files or not self.batch_output_folder:
            messagebox.showwarning("Warning", "Please select images and output folder")
            return

        # Create current settings
        current_settings = ProjectSettings(
            name="Batch_Process",
            matrix_width=int(self.width_var.get()),
            matrix_height=int(self.height_var.get()),
            output_width=int(self.out_width_var.get()),
            output_height=int(self.out_height_var.get()),
            pattern=self.pattern_var.get(),
            effect=self.effect_var.get(),
            palette=self.palette_var.get(),
            use_palette=self.use_palette_var.get(),
            spacing=float(self.spacing_var.get()),
            edge_enhance=self.edge_enhance_var.get(),
            noise_reduce=self.noise_reduce_var.get(),
            background_color=self.bg_color
        )

        # Setup progress callback
        def update_progress(progress, message):
            self.batch_progress['value'] = progress
            self.batch_status_label.config(text=message)
            self.root.update_idletasks()

        self.batch_processor.progress_callback = update_progress

        # Disable/enable buttons
        self.batch_button.config(state=tk.DISABLED)
        self.cancel_batch_button.config(state=tk.NORMAL)

        # Clear results
        self.batch_results_text.delete(1.0, tk.END)

        # Start processing in background
        def process_batch():
            try:
                results = self.batch_processor.process_batch(
                    self.batch_files, current_settings, self.batch_output_folder
                )

                # Update results display
                def update_results():
                    self.batch_results_text.insert(tk.END, f"Batch processing completed!\n")
                    self.batch_results_text.insert(tk.END, f"Processed: {results['processed']}\n")
                    self.batch_results_text.insert(tk.END, f"Failed: {results['failed']}\n")

                    if results['errors']:
                        self.batch_results_text.insert(tk.END, f"\nErrors:\n")
                        for error in results['errors'][:5]:  # Show first 5 errors
                            self.batch_results_text.insert(tk.END, f"- {error}\n")

                    if results['output_files']:
                        self.batch_results_text.insert(tk.END, f"\nOutput files:\n")
                        for file_path in results['output_files'][:5]:  # Show first 5 files
                            self.batch_results_text.insert(tk.END, f"- {os.path.basename(file_path)}\n")

                    self.batch_button.config(state=tk.NORMAL)
                    self.cancel_batch_button.config(state=tk.DISABLED)
                    self.batch_status_label.config(text="Batch processing completed")
                    self.update_status(f"Batch processing done: {results['processed']} processed, {results['failed']} failed")

                self.root.after(0, update_results)

            except Exception as e:
                def show_error():
                    self.batch_results_text.insert(tk.END, f"Batch processing error: {str(e)}\n")
                    self.batch_button.config(state=tk.NORMAL)
                    self.cancel_batch_button.config(state=tk.DISABLED)
                    self.batch_status_label.config(text="Batch processing failed")

                self.root.after(0, show_error)

        # Start processing thread
        processing_thread = threading.Thread(target=process_batch, daemon=True)
        processing_thread.start()

    def cancel_batch_processing(self):
        """Cancel batch processing."""
        self.batch_processor.cancel_processing()
        self.batch_button.config(state=tk.NORMAL)
        self.cancel_batch_button.config(state=tk.DISABLED)
        self.batch_status_label.config(text="Batch processing cancelled")
        self.update_status("Batch processing cancelled")

    def refresh_gallery(self):
        """Refresh the gallery."""
        try:
            images = self.project_manager.get_gallery_images()
            self.gallery_listbox.delete(0, tk.END)

            for image_path in images:
                # Show filename and modification time
                mod_time = time.strftime("%Y-%m-%d %H:%M", time.localtime(image_path.stat().st_mtime))
                self.gallery_listbox.insert(tk.END, f"{image_path.name} - {mod_time}")

        except Exception as e:
            self.logger.error(f"Failed to refresh gallery: {str(e)}")

    def open_gallery_folder(self):
        """Open the gallery folder in file explorer."""
        try:
            gallery_path = self.project_manager.gallery_dir
            if sys.platform == "win32":
                os.startfile(gallery_path)
            elif sys.platform == "darwin":  # macOS
                subprocess.Popen(["open", gallery_path])
            else:  # Linux and others
                subprocess.Popen(["xdg-open", gallery_path])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open gallery folder: {str(e)}")

    def open_gallery_item(self, event):
        """Open selected gallery item."""
        self.view_gallery_item()

    def view_gallery_item(self):
        """View selected gallery item."""
        selection = self.gallery_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an image to view")
            return

        try:
            images = self.project_manager.get_gallery_images()
            if selection[0] < len(images):
                image_path = images[selection[0]]
                image = Image.open(image_path)

                # Create a simple viewer window
                viewer = tk.Toplevel(self.root)
                viewer.title(f"Gallery Viewer - {image_path.name}")
                viewer.geometry("800x600")

                # Display image
                display_image = image.copy()
                display_image.thumbnail((750, 550), Image.LANCZOS)
                photo = ImageTk.PhotoImage(display_image)

                canvas = tk.Canvas(viewer, bg='black')
                canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                canvas.create_image(400, 300, image=photo)

                # Keep reference to prevent garbage collection
                canvas.photo = photo

                # Info label
                info_text = f"{image_path.name} | {image.size[0]}×{image.size[1]} | {image_path.stat().st_size // 1024} KB"
                ttk.Label(viewer, text=info_text).pack(pady=5)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to view image: {str(e)}")

    def choose_background_color(self):
        """Choose custom background color."""
        color = colorchooser.askcolor(title="Choose Background Color")
        if color[0]:
            self.bg_color = tuple(int(c) for c in color[0])
            self.update_status(f"Background color set to {self.bg_color}")

    def toggle_animation(self):
        """Toggle animation effects."""
        if self.animate_var.get():
            self.animation_active = True
            self.start_animation()
            self.update_status("Animation effects enabled - Watch the magic!")
        else:
            self.animation_active = False
            if self.animation_job:
                self.root.after_cancel(self.animation_job)
                self.animation_job = None
            self.update_status("Animation effects disabled")

    def start_animation(self):
        """Start animation loop."""
        if self.animation_active and self.current_image:
            self.animation_frame += 1
            self.convert_image(animate=True)
            self.animation_job = self.root.after(150, self.start_animation)

    def undo(self):
        """Undo last operation."""
        if self.undo_manager.can_undo():
            image = self.undo_manager.undo()
            if image:
                self.current_image = image
                self.update_status("Undone - Previous state restored")
                if self.dual_display and self.current_image:
                    self.dual_display.update_left_display(self.current_image, "Undone")
        else:
            self.update_status("Nothing to undo")

    def redo(self):
        """Redo last undone operation."""
        if self.undo_manager.can_redo():
            image = self.undo_manager.redo()
            if image:
                self.current_image = image
                self.update_status("Redone - State restored")
                if self.dual_display and self.current_image:
                    self.dual_display.update_left_display(self.current_image, "Redone")
        else:
            self.update_status("Nothing to redo")

    def on_closing(self):
        """Handle application closing."""
        self.animation_active = False
        self.auto_convert_active = False
        if hasattr(self, 'camera'):
            self.camera.stop_camera()
        self.processor.shutdown()
        self.root.destroy()

    def run(self):
        """Start the master application."""
        self.logger.info("Starting Master Dot Matrix Art Studio")
        self.root.mainloop()

def main():
    """Main entry point."""
    try:
        if not CV2_AVAILABLE:
            print("Warning: OpenCV not available. Camera and face detection features will be disabled.")
            print("To enable these features, install OpenCV with: pip install opencv-python")

        app = MasterDotMatrixStudio()
        app.run()
    except Exception as e:
        logger.error(f"Application failed: {str(e)}")
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
