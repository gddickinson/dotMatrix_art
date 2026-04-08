import numpy as np
from PIL import Image, ImageDraw, ImageTk, ImageFont, ImageFilter, ImageEnhance, ImageOps, ImageChops
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
import logging
import os
from typing import Optional, Tuple, List, Dict
import math
import cv2
import threading
import time
import queue
from concurrent.futures import ThreadPoolExecutor
import copy
import random
from enum import Enum

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

class ColorPalette:
    """Predefined color palettes for artistic effects."""

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
        "Fire & Ice": [(255, 0, 0), (255, 165, 0), (0, 191, 255), (255, 255, 255)]
    }

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
        self._load_classifiers()

    def _load_classifiers(self):
        """Load OpenCV face detection classifiers."""
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
        if not self.face_cascade:
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

                            # Draw pattern
                            self._draw_pattern(draw, pattern, center_x, center_y, radius, color)

                return output_img

            except Exception as e:
                self.logger.error(f"Advanced conversion failed: {str(e)}")
                return None

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

class DualDisplayWindow:
    """Enhanced dual display window with effects."""

    def __init__(self, parent, title="Dual Display"):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title(title)
        self.window.geometry("1400x800")

        self.left_canvas_lock = threading.Lock()
        self.right_canvas_lock = threading.Lock()

        self.setup_dual_display()

    def setup_dual_display(self):
        """Create enhanced dual display layout."""
        container = ttk.Frame(self.window, padding="10")
        container.pack(fill=tk.BOTH, expand=True)

        # Left display
        left_frame = ttk.LabelFrame(container, text="Original / Live Feed", padding="10")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        self.left_canvas = tk.Canvas(left_frame, bg='lightgray', width=680, height=650)
        self.left_canvas.pack(fill=tk.BOTH, expand=True)

        # Right display
        right_frame = ttk.LabelFrame(container, text="Artistic Dot Matrix", padding="10")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        self.right_canvas = tk.Canvas(right_frame, bg='black', width=680, height=650)
        self.right_canvas.pack(fill=tk.BOTH, expand=True)

        # Enhanced status
        status_frame = ttk.Frame(container)
        status_frame.pack(fill=tk.X, pady=(10, 0))

        self.left_status = ttk.Label(status_frame, text="Original: No image", relief=tk.SUNKEN)
        self.left_status.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        self.right_status = ttk.Label(status_frame, text="Artistic: No conversion", relief=tk.SUNKEN)
        self.right_status.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))

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
                    canvas_center_x = canvas_width // 2 if canvas_width > 1 else 340
                    canvas_center_y = canvas_height // 2 if canvas_height > 1 else 325
                    self.left_canvas.create_image(canvas_center_x, canvas_center_y, image=self.left_photo)

                    if status_text:
                        self.left_status.config(text=f"Original: {status_text}")

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
                    canvas_center_x = canvas_width // 2 if canvas_width > 1 else 340
                    canvas_center_y = canvas_height // 2 if canvas_height > 1 else 325
                    self.right_canvas.create_image(canvas_center_x, canvas_center_y, image=self.right_photo)

                    if status_text:
                        self.right_status.config(text=f"Artistic: {status_text}")

                except Exception as e:
                    logger.error(f"Failed to update right display: {str(e)}")

        self.window.after(0, _update)

class EnhancedDotMatrixGUI:
    """Enhanced GUI with creative artistic features."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Dot Matrix Art Studio Pro")
        self.root.geometry("700x1000")

        # Initialize components
        self.processor = ThreadSafeImageProcessor()
        self.converter = AdvancedDotMatrixConverter()
        self.face_generator = FaceGenerator()
        self.face_detector = FaceDetector()
        self.camera = CameraCapture()

        # State variables
        self.current_image = None
        self.current_result = None
        self.camera_active = False
        self.auto_convert_active = False
        self.dual_display = None
        self.animation_active = False
        self.animation_frame = 0

        # Threading controls
        self.camera_update_job = None
        self.auto_convert_job = None
        self.animation_job = None

        self.setup_enhanced_gui()
        self.logger = logger

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.logger.info("Enhanced art studio GUI initialized")

    def setup_enhanced_gui(self):
        """Create the enhanced artistic GUI."""
        # Create notebook for tabbed interface
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Main tab
        main_tab = ttk.Frame(notebook)
        notebook.add(main_tab, text="Main Controls")

        # Artistic tab
        artistic_tab = ttk.Frame(notebook)
        notebook.add(artistic_tab, text="Artistic Effects")

        # Animation tab
        animation_tab = ttk.Frame(notebook)
        notebook.add(animation_tab, text="Animation & Live")

        self.setup_main_tab(main_tab)
        self.setup_artistic_tab(artistic_tab)
        self.setup_animation_tab(animation_tab)

    def setup_main_tab(self, parent):
        """Setup main controls tab."""
        # Title
        title_label = ttk.Label(parent, text="Dot Matrix Art Studio Pro",
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(10, 20))

        # Display controls
        display_frame = ttk.LabelFrame(parent, text="Display Controls", padding="10")
        display_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(display_frame, text="🎨 Open Art Studio Display",
                  command=self.open_dual_display).pack(pady=5)

        # Input section
        input_frame = ttk.LabelFrame(parent, text="Input Source", padding="10")
        input_frame.pack(fill=tk.X, pady=(0, 10))

        input_row1 = ttk.Frame(input_frame)
        input_row1.pack(fill=tk.X, pady=(0, 5))

        ttk.Button(input_row1, text="📁 Load Image",
                  command=self.load_image).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(input_row1, text="👤 Generate Test Face",
                  command=self.generate_test_face).pack(side=tk.LEFT, padx=(0, 10))

        input_row2 = ttk.Frame(input_frame)
        input_row2.pack(fill=tk.X, pady=(5, 0))

        self.camera_button = ttk.Button(input_row2, text="📷 Start Camera",
                                       command=self.toggle_camera)
        self.camera_button.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(input_row2, text="📸 Capture Frame",
                  command=self.capture_camera_frame).pack(side=tk.LEFT, padx=(0, 10))

        # Face detection
        face_row = ttk.Frame(input_frame)
        face_row.pack(fill=tk.X, pady=(5, 0))

        ttk.Button(face_row, text="🔍 Detect Faces",
                  command=self.detect_faces).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(face_row, text="✂️ Auto-Crop Face",
                  command=self.auto_crop_face).pack(side=tk.LEFT, padx=(0, 10))

        self.image_info_label = ttk.Label(input_frame, text="No image loaded")
        self.image_info_label.pack(anchor=tk.W, pady=(10, 0))

        # Basic settings
        settings_frame = ttk.LabelFrame(parent, text="Basic Settings", padding="10")
        settings_frame.pack(fill=tk.X, pady=(0, 10))

        settings_row1 = ttk.Frame(settings_frame)
        settings_row1.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(settings_row1, text="Matrix:").pack(side=tk.LEFT)
        self.width_var = tk.StringVar(value="45")
        ttk.Entry(settings_row1, textvariable=self.width_var, width=6).pack(side=tk.LEFT, padx=(5, 5))
        ttk.Label(settings_row1, text="×").pack(side=tk.LEFT)
        self.height_var = tk.StringVar(value="19")
        ttk.Entry(settings_row1, textvariable=self.height_var, width=6).pack(side=tk.LEFT, padx=(5, 15))

        ttk.Label(settings_row1, text="Output:").pack(side=tk.LEFT)
        self.out_width_var = tk.StringVar(value="900")
        ttk.Entry(settings_row1, textvariable=self.out_width_var, width=6).pack(side=tk.LEFT, padx=(5, 5))
        ttk.Label(settings_row1, text="×").pack(side=tk.LEFT)
        self.out_height_var = tk.StringVar(value="380")
        ttk.Entry(settings_row1, textvariable=self.out_height_var, width=6).pack(side=tk.LEFT, padx=(5, 0))

        # Convert button
        convert_frame = ttk.Frame(parent)
        convert_frame.pack(pady=20)

        ttk.Button(convert_frame, text="🎨 Convert to Art",
                  command=self.convert_image, style='Accent.TButton').pack()

        # Status
        self.status_var = tk.StringVar(value="Ready - Open art studio to begin creating!")
        status_bar = ttk.Label(parent, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(fill=tk.X, pady=(20, 0))

    def setup_artistic_tab(self, parent):
        """Setup artistic effects tab."""
        # Pattern selection
        pattern_frame = ttk.LabelFrame(parent, text="Dot Patterns", padding="10")
        pattern_frame.pack(fill=tk.X, pady=(10, 10))

        self.pattern_var = tk.StringVar(value=DotPattern.CIRCLE.value)

        pattern_row1 = ttk.Frame(pattern_frame)
        pattern_row1.pack(fill=tk.X, pady=(0, 5))

        for pattern in [DotPattern.CIRCLE, DotPattern.SQUARE, DotPattern.DIAMOND, DotPattern.HEXAGON]:
            ttk.Radiobutton(pattern_row1, text=pattern.value.title(),
                           variable=self.pattern_var, value=pattern.value).pack(side=tk.LEFT, padx=(0, 10))

        pattern_row2 = ttk.Frame(pattern_frame)
        pattern_row2.pack(fill=tk.X)

        for pattern in [DotPattern.STAR, DotPattern.CROSS, DotPattern.HEART, DotPattern.TRIANGLE]:
            ttk.Radiobutton(pattern_row2, text=pattern.value.title(),
                           variable=self.pattern_var, value=pattern.value).pack(side=tk.LEFT, padx=(0, 10))

        # Color palette
        palette_frame = ttk.LabelFrame(parent, text="Color Palettes", padding="10")
        palette_frame.pack(fill=tk.X, pady=(0, 10))

        self.palette_var = tk.StringVar(value="Classic B&W")
        palette_combo = ttk.Combobox(palette_frame, textvariable=self.palette_var,
                                    values=list(ColorPalette.PALETTES.keys()), state="readonly")
        palette_combo.pack(side=tk.LEFT, padx=(0, 10))

        self.use_palette_var = tk.BooleanVar()
        ttk.Checkbutton(palette_frame, text="Use Color Palette",
                       variable=self.use_palette_var).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(palette_frame, text="🎨 Custom Background",
                  command=self.choose_background_color).pack(side=tk.LEFT)

        self.bg_color = None

        # Artistic effects
        effects_frame = ttk.LabelFrame(parent, text="Artistic Effects", padding="10")
        effects_frame.pack(fill=tk.X, pady=(0, 10))

        self.effect_var = tk.StringVar(value=ArtisticEffect.NONE.value)
        effect_combo = ttk.Combobox(effects_frame, textvariable=self.effect_var,
                                   values=[e.value for e in ArtisticEffect], state="readonly")
        effect_combo.pack(side=tk.LEFT, padx=(0, 10))

        # Enhancement options
        enhance_frame = ttk.LabelFrame(parent, text="Image Enhancement", padding="10")
        enhance_frame.pack(fill=tk.X, pady=(0, 10))

        self.edge_enhance_var = tk.BooleanVar()
        ttk.Checkbutton(enhance_frame, text="Edge Enhancement",
                       variable=self.edge_enhance_var).pack(anchor=tk.W)

        self.noise_reduce_var = tk.BooleanVar()
        ttk.Checkbutton(enhance_frame, text="Noise Reduction",
                       variable=self.noise_reduce_var).pack(anchor=tk.W)

        # Spacing and size
        spacing_frame = ttk.LabelFrame(parent, text="Advanced Settings", padding="10")
        spacing_frame.pack(fill=tk.X, pady=(0, 10))

        spacing_row = ttk.Frame(spacing_frame)
        spacing_row.pack(fill=tk.X)

        ttk.Label(spacing_row, text="Spacing:").pack(side=tk.LEFT)
        self.spacing_var = tk.StringVar(value="1.0")
        spacing_scale = ttk.Scale(spacing_row, from_=0.1, to=2.0, variable=self.spacing_var, orient=tk.HORIZONTAL)
        spacing_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 10))
        ttk.Label(spacing_row, textvariable=self.spacing_var).pack(side=tk.LEFT)

    def setup_animation_tab(self, parent):
        """Setup animation and live effects tab."""
        # Animation controls
        anim_frame = ttk.LabelFrame(parent, text="Animation Effects", padding="10")
        anim_frame.pack(fill=tk.X, pady=(10, 10))

        anim_row1 = ttk.Frame(anim_frame)
        anim_row1.pack(fill=tk.X, pady=(0, 5))

        self.animate_var = tk.BooleanVar()
        ttk.Checkbutton(anim_row1, text="✨ Animated Dots",
                       variable=self.animate_var, command=self.toggle_animation).pack(side=tk.LEFT)

        # Live processing
        live_frame = ttk.LabelFrame(parent, text="Live Processing", padding="10")
        live_frame.pack(fill=tk.X, pady=(0, 10))

        live_row1 = ttk.Frame(live_frame)
        live_row1.pack(fill=tk.X, pady=(0, 5))

        self.auto_convert_var = tk.BooleanVar()
        self.auto_convert_check = ttk.Checkbutton(live_row1, text="🔄 Auto-Convert Camera",
                                                 variable=self.auto_convert_var,
                                                 command=self.toggle_auto_convert)
        self.auto_convert_check.pack(side=tk.LEFT, padx=(0, 10))

        # Face detection settings
        face_settings_frame = ttk.LabelFrame(parent, text="Face Detection Settings", padding="10")
        face_settings_frame.pack(fill=tk.X, pady=(0, 10))

        face_row = ttk.Frame(face_settings_frame)
        face_row.pack(fill=tk.X)

        ttk.Label(face_row, text="Crop Padding:").pack(side=tk.LEFT)
        self.face_padding_var = tk.StringVar(value="0.2")
        ttk.Entry(face_row, textvariable=self.face_padding_var, width=8).pack(side=tk.LEFT, padx=(5, 15))

        self.auto_crop_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(face_row, text="Auto-crop faces",
                       variable=self.auto_crop_var).pack(side=tk.LEFT)

        # Save controls
        save_frame = ttk.LabelFrame(parent, text="Export Art", padding="10")
        save_frame.pack(fill=tk.X, pady=(0, 10))

        save_buttons = ttk.Frame(save_frame)
        save_buttons.pack(fill=tk.X)

        ttk.Button(save_buttons, text="💾 Save Original",
                  command=self.save_original).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(save_buttons, text="🎨 Save Artwork",
                  command=self.save_result).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(save_buttons, text="🎬 Save Animation",
                  command=self.save_animation).pack(side=tk.LEFT)

    def choose_background_color(self):
        """Choose custom background color."""
        color = colorchooser.askcolor(title="Choose Background Color")
        if color[0]:  # RGB tuple
            self.bg_color = tuple(int(c) for c in color[0])
            self.update_status(f"Background color set to {self.bg_color}")

    def toggle_animation(self):
        """Toggle animation effects."""
        if self.animate_var.get():
            self.animation_active = True
            self.start_animation()
            self.update_status("Animation enabled")
        else:
            self.animation_active = False
            if self.animation_job:
                self.root.after_cancel(self.animation_job)
                self.animation_job = None
            self.update_status("Animation disabled")

    def start_animation(self):
        """Start animation loop."""
        if self.animation_active and self.current_image:
            self.animation_frame += 1
            self.convert_image(animate=True)
            self.animation_job = self.root.after(100, self.start_animation)

    def convert_image(self, animate=False):
        """Enhanced convert with artistic options."""
        if not self.current_image:
            if not animate:  # Don't show warning during animation
                messagebox.showwarning("Warning", "Please load an image first")
            return

        def perform_advanced_conversion():
            try:
                # Get all settings
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
                artistic_effect = ArtisticEffect(self.effect_var.get())
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
                self.logger.error(f"Advanced conversion failed: {str(e)}")
                return None

        if not animate:
            self.update_status("Creating artistic masterpiece...")

        # Process in background
        future = self.processor.submit_processing_task(perform_advanced_conversion)

        def handle_result():
            try:
                result = future.result(timeout=0.1)
                if result:
                    self.current_result = result
                    if self.dual_display:
                        pattern_name = self.pattern_var.get().title()
                        effect_name = self.effect_var.get().title()
                        status = f"{pattern_name} pattern, {effect_name} effect"
                        self.dual_display.update_right_display(result, status)

                    if not animate:
                        self.update_status("Artistic conversion completed!")
                else:
                    if not animate:
                        self.update_status("Conversion failed")

            except Exception as e:
                if not animate:
                    self.update_status("Conversion failed")

        self.root.after(200, handle_result)

    def save_animation(self):
        """Save animated sequence."""
        if not self.current_image:
            messagebox.showwarning("Warning", "No image to animate.")
            return

        file_path = filedialog.asksaveasfilename(
            title="Save Animation Frames",
            defaultextension=".gif",
            filetypes=[
                ("GIF Animation", "*.gif"),
                ("PNG Sequence", "*.png"),
                ("All files", "*.*")
            ]
        )

        if file_path:
            # This would create an animated sequence
            messagebox.showinfo("Info", "Animation export feature coming soon!")

    # Include other methods from previous version...
    def update_status(self, message: str):
        """Update status bar message."""
        self.status_var.set(message)
        self.root.update_idletasks()
        self.logger.info(f"Status: {message}")

    def open_dual_display(self):
        """Open the dual display window."""
        if self.dual_display is None or not tk.Toplevel.winfo_exists(self.dual_display.window):
            self.dual_display = DualDisplayWindow(self.root, "Art Studio | Live Original ⟷ Artistic Creation")
            self.update_status("Art studio display opened - Ready to create!")
        else:
            self.dual_display.window.lift()
            self.dual_display.window.focus_set()

    def load_image(self):
        """Load an image file."""
        file_path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.gif *.tiff"),
                ("All files", "*.*")
            ]
        )

        if file_path:
            try:
                self.current_image = Image.open(file_path)
                self.image_info_label.config(text=f"📁 {os.path.basename(file_path)} ({self.current_image.size[0]}×{self.current_image.size[1]})")
                self.update_status("Image loaded - Ready for artistic transformation!")

                if self.dual_display:
                    self.dual_display.update_left_display(self.current_image, f"Loaded: {os.path.basename(file_path)}")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to load image: {str(e)}")
                self.logger.error(f"Failed to load image {file_path}: {str(e)}")

    def generate_test_face(self):
        """Generate a test face image."""
        try:
            self.current_image = self.face_generator.create_test_face()
            self.image_info_label.config(text="👤 Test face generated (200×240)")
            self.update_status("Test face ready for artistic conversion!")

            if self.dual_display:
                self.dual_display.update_left_display(self.current_image, "Test face generated")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate test face: {str(e)}")
            self.logger.error(f"Failed to generate test face: {str(e)}")

    def toggle_camera(self):
        """Start or stop camera capture."""
        if not self.camera_active:
            if self.camera.start_camera():
                self.camera_active = True
                self.camera_button.config(text="📷 Stop Camera")
                self.update_status("Camera active - Live art creation ready!")
                self.start_camera_updates()
            else:
                messagebox.showerror("Error", "Failed to start camera.")
        else:
            self.stop_camera()

    def stop_camera(self):
        """Stop camera capture."""
        self.camera_active = False
        self.camera.stop_camera()
        self.camera_button.config(text="📷 Start Camera")

        if self.camera_update_job:
            self.root.after_cancel(self.camera_update_job)
            self.camera_update_job = None

        self.update_status("Camera stopped")

    def start_camera_updates(self):
        """Start camera display updates."""
        if self.camera_active and self.camera.is_active():
            frame = self.camera.get_latest_frame()
            if frame and self.dual_display:
                self.dual_display.update_left_display(frame, "📹 Live camera feed")
                self.image_info_label.config(text=f"📹 Live feed ({frame.size[0]}×{frame.size[1]})")

            self.camera_update_job = self.root.after(100, self.start_camera_updates)

    def capture_camera_frame(self):
        """Capture current camera frame."""
        if not self.camera_active:
            messagebox.showwarning("Warning", "Camera is not active")
            return

        frame = self.camera.get_latest_frame()
        if frame:
            if self.auto_crop_var.get():
                def process_frame():
                    cropped = self.face_detector.crop_largest_face(
                        frame, padding=float(self.face_padding_var.get())
                    )
                    return cropped if cropped else frame

                future = self.processor.submit_processing_task(process_frame)

                def handle_result():
                    try:
                        processed_frame = future.result(timeout=0.1)
                        self.current_image = processed_frame
                        if processed_frame != frame:
                            status_text = f"📸 Face captured ({processed_frame.size[0]}×{processed_frame.size[1]})"
                            self.update_status("Face captured and ready for art!")
                        else:
                            status_text = f"📸 Frame captured ({processed_frame.size[0]}×{processed_frame.size[1]})"
                            self.update_status("Frame captured")

                        self.image_info_label.config(text=status_text)

                        if self.dual_display:
                            self.dual_display.update_left_display(processed_frame, status_text)

                    except Exception:
                        self.current_image = frame
                        self.image_info_label.config(text=f"📸 Frame captured ({frame.size[0]}×{frame.size[1]})")
                        self.update_status("Frame captured")

                        if self.dual_display:
                            self.dual_display.update_left_display(frame, "Frame captured")

                self.root.after(100, handle_result)

            else:
                self.current_image = frame
                self.image_info_label.config(text=f"📸 Frame captured ({frame.size[0]}×{frame.size[1]})")
                self.update_status("Frame captured and ready!")

                if self.dual_display:
                    self.dual_display.update_left_display(frame, "Frame captured")
        else:
            messagebox.showerror("Error", "Failed to capture frame")

    def detect_faces(self):
        """Detect and highlight faces."""
        if not self.current_image:
            messagebox.showwarning("Warning", "Please load an image first")
            return

        def detect_and_show():
            annotated = self.face_detector.draw_face_boxes(self.current_image)
            faces = self.face_detector.detect_faces(self.current_image)
            return annotated, len(faces)

        future = self.processor.submit_processing_task(detect_and_show)

        def handle_result():
            try:
                annotated, face_count = future.result(timeout=0.1)
                if self.dual_display:
                    self.dual_display.update_left_display(annotated, f"🔍 {face_count} face(s) detected")

                self.update_status(f"Detected {face_count} face(s)" if face_count > 0 else "No faces detected")

            except Exception as e:
                messagebox.showerror("Error", f"Face detection failed: {str(e)}")

        self.root.after(100, handle_result)

    def auto_crop_face(self):
        """Auto-crop the largest face."""
        if not self.current_image:
            messagebox.showwarning("Warning", "Please load an image first")
            return

        def crop_face():
            padding = float(self.face_padding_var.get())
            return self.face_detector.crop_largest_face(self.current_image, padding)

        future = self.processor.submit_processing_task(crop_face)

        def handle_result():
            try:
                cropped = future.result(timeout=0.1)
                if cropped:
                    self.current_image = cropped
                    self.image_info_label.config(text=f"✂️ Face cropped ({cropped.size[0]}×{cropped.size[1]})")
                    self.update_status("Face cropped - Perfect for portrait art!")

                    if self.dual_display:
                        self.dual_display.update_left_display(cropped, "✂️ Auto-cropped face")
                else:
                    messagebox.showinfo("Info", "No faces detected for cropping")

            except ValueError:
                messagebox.showerror("Error", "Invalid padding value")
            except Exception as e:
                messagebox.showerror("Error", f"Face cropping failed: {str(e)}")

        self.root.after(100, handle_result)

    def toggle_auto_convert(self):
        """Toggle automatic conversion."""
        if self.auto_convert_var.get():
            self.auto_convert_active = True
            self.start_auto_convert()
            self.update_status("Live art mode activated!")
        else:
            self.auto_convert_active = False
            if self.auto_convert_job:
                self.root.after_cancel(self.auto_convert_job)
                self.auto_convert_job = None
            self.update_status("Live art mode disabled")

    def start_auto_convert(self):
        """Start automatic conversion."""
        if self.auto_convert_active and self.camera_active:
            frame = self.camera.get_latest_frame()
            if frame:
                def convert_frame():
                    work_frame = frame
                    if self.auto_crop_var.get():
                        cropped = self.face_detector.crop_largest_face(
                            frame, padding=float(self.face_padding_var.get())
                        )
                        if cropped:
                            work_frame = cropped

                    try:
                        pattern = DotPattern(self.pattern_var.get())
                        artistic_effect = ArtisticEffect(self.effect_var.get())

                        return self.converter.convert_image_advanced(
                            work_frame,
                            matrix_width=int(self.width_var.get()),
                            matrix_height=int(self.height_var.get()),
                            output_size=(int(self.out_width_var.get()), int(self.out_height_var.get())),
                            pattern=pattern,
                            circle_spacing=float(self.spacing_var.get()),
                            use_color=self.use_palette_var.get(),
                            color_palette=ColorPalette.PALETTES.get(self.palette_var.get()) if self.use_palette_var.get() else None,
                            artistic_effect=artistic_effect,
                            edge_enhancement=self.edge_enhance_var.get(),
                            noise_reduction=self.noise_reduce_var.get(),
                            custom_background=self.bg_color
                        )
                    except:
                        return None

                future = self.processor.submit_processing_task(convert_frame)

                def handle_conversion():
                    try:
                        result = future.result(timeout=0.1)
                        if result and self.dual_display:
                            self.dual_display.update_right_display(result, "🔄 Live art creation")
                    except:
                        pass

                self.root.after(200, handle_conversion)

            self.auto_convert_job = self.root.after(500, self.start_auto_convert)

    def save_original(self):
        """Save the original image."""
        if not self.current_image:
            messagebox.showwarning("Warning", "No original image to save.")
            return

        file_path = filedialog.asksaveasfilename(
            title="Save Original Image",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("All files", "*.*")]
        )

        if file_path:
            try:
                self.current_image.save(file_path)
                self.update_status(f"💾 Original saved: {os.path.basename(file_path)}")
                messagebox.showinfo("Success", "Original image saved!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save: {str(e)}")

    def save_result(self):
        """Save the artistic result."""
        if not self.current_result:
            messagebox.showwarning("Warning", "No artwork to save. Create art first!")
            return

        file_path = filedialog.asksaveasfilename(
            title="Save Artistic Creation",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("All files", "*.*")]
        )

        if file_path:
            try:
                self.current_result.save(file_path)
                self.update_status(f"🎨 Artwork saved: {os.path.basename(file_path)}")
                messagebox.showinfo("Success", "Your artistic creation has been saved!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save artwork: {str(e)}")

    def on_closing(self):
        """Handle application closing."""
        self.animation_active = False
        self.auto_convert_active = False
        self.stop_camera()
        self.processor.shutdown()
        self.root.destroy()

    def run(self):
        """Start the application."""
        self.logger.info("Starting Enhanced Dot Matrix Art Studio")
        self.root.mainloop()

def main():
    """Main entry point."""
    try:
        try:
            import cv2
            logger.info(f"OpenCV version: {cv2.__version__}")
        except ImportError:
            logger.error("OpenCV not available")
            print("Error: OpenCV required. Install with: pip install opencv-python")
            return

        app = EnhancedDotMatrixGUI()
        app.run()
    except Exception as e:
        logger.error(f"Application failed: {str(e)}")
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
