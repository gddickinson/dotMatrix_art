"""Camera capture and face detection for Dot Matrix Art Studio."""

import logging
import threading
import queue
import time
from typing import Optional, List, Tuple

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

# Try to import OpenCV, handle gracefully if not available
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logger.warning("OpenCV not available - camera and face detection features disabled")


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
            self.face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            )
            self.eye_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + "haarcascade_eye.xml"
            )

            if self.face_cascade.empty() or self.eye_cascade.empty():
                raise RuntimeError("Failed to load cascade classifiers")

            self.logger.info("Face detection classifiers loaded successfully")

        except Exception as e:
            self.logger.error(f"Failed to load face detection classifiers: {e}")
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
                    gray,
                    scaleFactor=1.1,
                    minNeighbors=5,
                    minSize=(30, 30),
                    flags=cv2.CASCADE_SCALE_IMAGE,
                )

                return [(int(x), int(y), int(w), int(h)) for x, y, w, h in faces]

            except Exception as e:
                self.logger.error(f"Face detection failed: {e}")
                return []

    def crop_largest_face(
        self, image: Image.Image, padding: float = 0.2
    ) -> Optional[Image.Image]:
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
        self.frame_queue: queue.Queue = queue.Queue(maxsize=2)

    def start_camera(self, camera_index: int = 0) -> bool:
        """Start camera capture."""
        if not CV2_AVAILABLE:
            self.logger.error("OpenCV not available for camera capture")
            return False

        try:
            self.camera = cv2.VideoCapture(camera_index)
            if not self.camera.isOpened():
                raise RuntimeError("Camera not available")

            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera.set(cv2.CAP_PROP_FPS, 30)

            self.is_capturing = True
            self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.capture_thread.start()

            self.logger.info("Camera started successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to start camera: {e}")
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
                self.logger.error(f"Camera capture error: {e}")
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
