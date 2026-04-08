"""Dot pattern rendering engine for Dot Matrix Art Studio."""

import math
import random
import logging
import threading
from typing import Optional, Tuple, List, Dict

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from dot_matrix.models import DotPattern, ArtisticEffect, ColorPalette
from dot_matrix.effects import ArtisticProcessor

logger = logging.getLogger(__name__)


class AdvancedDotMatrixConverter:
    """Advanced dot matrix converter with creative patterns and effects."""

    def __init__(self):
        self.logger = logger
        self.conversion_lock = threading.Lock()
        self.circle_data: List[Dict] = []

    def convert_image_advanced(
        self,
        image: Image.Image,
        matrix_width: int = 45,
        matrix_height: int = 19,
        output_size: Tuple[int, int] = (900, 380),
        pattern: DotPattern = DotPattern.CIRCLE,
        circle_spacing: float = 1.0,
        use_color: bool = False,
        color_palette: Optional[List] = None,
        artistic_effect: ArtisticEffect = ArtisticEffect.NONE,
        animate: bool = False,
        animation_frame: int = 0,
        edge_enhancement: bool = False,
        noise_reduction: bool = False,
        custom_background: Optional[Tuple[int, int, int]] = None,
    ) -> Optional[Image.Image]:
        """Advanced image to dot matrix conversion with artistic features."""
        with self.conversion_lock:
            try:
                self.logger.info(f"Converting image with pattern: {pattern.value}")
                self.circle_data = []

                work_image = image.copy()

                if noise_reduction:
                    work_image = work_image.filter(ImageFilter.SMOOTH)
                if edge_enhancement:
                    work_image = work_image.filter(ImageFilter.EDGE_ENHANCE)
                if artistic_effect != ArtisticEffect.NONE:
                    work_image = ArtisticProcessor.apply_artistic_effect(
                        work_image, artistic_effect
                    )

                if use_color and color_palette:
                    img_resized = work_image.resize(
                        (matrix_width, matrix_height), Image.LANCZOS
                    )
                    img_gray = img_resized.convert("L")
                    pixel_brightness = np.array(img_gray)
                    pixel_colors = self._map_to_palette(
                        np.array(img_resized), color_palette
                    )
                else:
                    img_gray = work_image.convert("L")
                    img_resized = img_gray.resize(
                        (matrix_width, matrix_height), Image.LANCZOS
                    )
                    pixel_brightness = np.array(img_resized)
                    pixel_colors = None

                bg_color = custom_background if custom_background else (255, 255, 255)
                output_img = Image.new("RGB", output_size, bg_color)
                draw = ImageDraw.Draw(output_img)

                cell_width = output_size[0] / matrix_width
                cell_height = output_size[1] / matrix_height
                max_radius = min(cell_width, cell_height) / 2 * circle_spacing

                for y in range(matrix_height):
                    for x in range(matrix_width):
                        brightness = pixel_brightness[y, x]
                        base_radius = max_radius * (1 - brightness / 255.0)

                        if animate:
                            radius = base_radius * (
                                0.8
                                + 0.4
                                * math.sin(
                                    animation_frame * 0.1 + x * 0.2 + y * 0.2
                                )
                            )
                        else:
                            radius = base_radius

                        if radius > 0.5:
                            if use_color and pixel_colors is not None:
                                color = tuple(pixel_colors[y, x])
                            else:
                                color = "black"

                            center_x = (x + 0.5) * cell_width
                            center_y = (y + 0.5) * cell_height

                            self.circle_data.append(
                                {"x": center_x, "y": center_y, "r": radius, "color": color}
                            )
                            self._draw_pattern(draw, pattern, center_x, center_y, radius, color)

                return output_img

            except Exception as e:
                self.logger.error(f"Advanced conversion failed: {e}")
                return None

    def get_circle_data(self) -> List[Dict]:
        """Get circle data for SVG export."""
        return self.circle_data.copy()

    def _map_to_palette(
        self, image_array: np.ndarray, palette: List[Tuple[int, int, int]]
    ) -> np.ndarray:
        """Map image colors to a specific palette."""
        if len(image_array.shape) != 3:
            return image_array

        height, width, _channels = image_array.shape
        mapped = np.zeros_like(image_array)

        for y in range(height):
            for x in range(width):
                pixel = image_array[y, x]
                closest_color = min(
                    palette, key=lambda c: np.sum((np.array(c) - pixel) ** 2)
                )
                mapped[y, x] = closest_color

        return mapped

    def _draw_pattern(
        self,
        draw: ImageDraw.Draw,
        pattern: DotPattern,
        center_x: float,
        center_y: float,
        radius: float,
        color,
    ):
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
        else:
            self._draw_circle(draw, center_x, center_y, radius, color)

    def _draw_circle(self, draw, cx, cy, r, color):
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)

    def _draw_square(self, draw, cx, cy, r, color):
        draw.rectangle([cx - r, cy - r, cx + r, cy + r], fill=color)

    def _draw_diamond(self, draw, cx, cy, r, color):
        points = [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]
        draw.polygon(points, fill=color)

    def _draw_hexagon(self, draw, cx, cy, r, color):
        points = []
        for i in range(6):
            angle = math.radians(60 * i - 30)
            points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
        draw.polygon(points, fill=color)

    def _draw_star(self, draw, cx, cy, r, color):
        points = []
        for i in range(10):
            angle = math.radians(36 * i - 90)
            radius = r if i % 2 == 0 else r * 0.4
            points.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
        draw.polygon(points, fill=color)

    def _draw_cross(self, draw, cx, cy, r, color):
        w = r * 0.3
        draw.rectangle([cx - w, cy - r, cx + w, cy + r], fill=color)
        draw.rectangle([cx - r, cy - w, cx + r, cy + w], fill=color)

    def _draw_heart(self, draw, cx, cy, r, color):
        points = []
        for i in range(50):
            t = math.radians(i * 360 / 50)
            x = r * 0.5 * (16 * math.sin(t) ** 3) / 16
            y = (
                -r
                * 0.5
                * (13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
                / 16
            )
            points.append((cx + x, cy + y))
        if len(points) >= 3:
            draw.polygon(points, fill=color)

    def _draw_triangle(self, draw, cx, cy, r, color):
        points = [
            (cx, cy - r),
            (cx - r * 0.866, cy + r * 0.5),
            (cx + r * 0.866, cy + r * 0.5),
        ]
        draw.polygon(points, fill=color)

    def _draw_halftone(self, draw, cx, cy, r, color):
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
        if r > 3:
            inner_r = r * 0.6
            draw.ellipse(
                [cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r],
                fill=color,
                outline=color,
            )

    def _draw_stipple(self, draw, cx, cy, r, color):
        num_dots = max(1, int(r * 2))
        dot_r = max(0.5, r / 4)
        for _ in range(num_dots):
            dx = random.uniform(-r, r)
            dy = random.uniform(-r, r)
            if dx * dx + dy * dy <= r * r:
                draw.ellipse(
                    [cx + dx - dot_r, cy + dy - dot_r, cx + dx + dot_r, cy + dy + dot_r],
                    fill=color,
                )

    def _draw_ascii_dot(self, draw, cx, cy, r, color):
        try:
            if r > 5:
                char = "@"
            elif r > 3:
                char = "#"
            elif r > 2:
                char = "*"
            elif r > 1:
                char = "+"
            else:
                char = "."

            font_size = max(8, int(r * 1.5))
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except OSError:
                font = ImageFont.load_default()

            draw.text((cx - r / 2, cy - r / 2), char, fill=color, font=font)

        except Exception:
            self._draw_circle(draw, cx, cy, r, color)
