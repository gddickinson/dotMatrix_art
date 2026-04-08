"""Data models, enums, and settings for Dot Matrix Art Studio."""

import logging
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Tuple, List

import numpy as np
from PIL import Image

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
        "Deep Sea": [(25, 25, 112), (0, 100, 0), (72, 61, 139), (255, 255, 255)],
    }

    @staticmethod
    def extract_dominant_colors(
        image: Image.Image, num_colors: int = 5
    ) -> List[Tuple[int, int, int]]:
        """Extract dominant colors from an image using simplified clustering."""
        try:
            small_image = image.resize((150, 150))
            pixels = list(small_image.convert("RGB").getdata())

            color_counts: dict = {}
            for pixel in pixels:
                rounded = tuple((c // 32) * 32 for c in pixel)
                color_counts[rounded] = color_counts.get(rounded, 0) + 1

            sorted_colors = sorted(color_counts.items(), key=lambda x: x[1], reverse=True)
            return [color for color, _count in sorted_colors[:num_colors]]

        except Exception as e:
            logger.error(f"Color extraction failed: {e}")
            return [(0, 0, 0), (128, 128, 128), (255, 255, 255)]
