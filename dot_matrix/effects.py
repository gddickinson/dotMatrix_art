"""Artistic effects and test face generation for Dot Matrix Art Studio."""

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageOps, ImageChops

from dot_matrix.models import ArtisticEffect


class ArtisticProcessor:
    """Advanced artistic processing and effects."""

    @staticmethod
    def apply_artistic_effect(image: Image.Image, effect: ArtisticEffect) -> Image.Image:
        """Apply artistic effects to an image."""
        if effect == ArtisticEffect.NONE:
            return image

        elif effect == ArtisticEffect.VINTAGE:
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(0.8)
            pixels = np.array(image)
            sepia_filter = np.array([
                [0.393, 0.769, 0.189],
                [0.349, 0.686, 0.168],
                [0.272, 0.534, 0.131],
            ])
            sepia_img = pixels.dot(sepia_filter.T)
            sepia_img = np.clip(sepia_img, 0, 255).astype(np.uint8)
            return Image.fromarray(sepia_img)

        elif effect == ArtisticEffect.NEON:
            image = image.filter(ImageFilter.EDGE_ENHANCE_MORE)
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.5)
            enhancer = ImageEnhance.Color(image)
            return enhancer.enhance(2.0)

        elif effect == ArtisticEffect.SKETCH:
            gray = image.convert("L")
            inverted = ImageOps.invert(gray)
            blurred = inverted.filter(ImageFilter.GaussianBlur(radius=5))
            # Use lighter (screen blend) as a fallback for divide
            inv_blurred = ImageOps.invert(blurred)
            sketch = ImageChops.lighter(gray, inv_blurred)
            return sketch.convert("RGB")

        elif effect == ArtisticEffect.CROSSHATCH:
            gray = image.convert("L")
            edges = gray.filter(ImageFilter.FIND_EDGES)
            enhancer = ImageEnhance.Contrast(edges)
            crosshatch = enhancer.enhance(2.0)
            return crosshatch.convert("RGB")

        elif effect == ArtisticEffect.MOSAIC:
            small = image.resize(
                (image.width // 20, image.height // 20), Image.NEAREST
            )
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
        img = Image.new("RGB", (width, height), (245, 220, 177))
        draw = ImageDraw.Draw(img)

        # Face outline
        face_margin = 20
        draw.ellipse(
            [face_margin, face_margin, width - face_margin, height - face_margin],
            fill=(235, 210, 167),
            outline=(200, 175, 132),
            width=2,
        )

        # Hair
        hair_height = height // 3
        draw.ellipse(
            [face_margin - 10, face_margin - 10, width - face_margin + 10, hair_height],
            fill=(101, 67, 33),
        )

        # Eyes
        eye_y = height // 3
        eye_width = width // 8
        left_eye_x = width // 3 - eye_width
        right_eye_x = 2 * width // 3

        draw.ellipse(
            [left_eye_x, eye_y, left_eye_x + eye_width * 2, eye_y + eye_width],
            fill=(255, 255, 255),
            outline=(150, 150, 150),
        )
        draw.ellipse(
            [right_eye_x, eye_y, right_eye_x + eye_width * 2, eye_y + eye_width],
            fill=(255, 255, 255),
            outline=(150, 150, 150),
        )

        # Pupils
        pupil_size = eye_width // 2
        draw.ellipse(
            [
                left_eye_x + eye_width // 2,
                eye_y + eye_width // 4,
                left_eye_x + eye_width // 2 + pupil_size,
                eye_y + eye_width // 4 + pupil_size,
            ],
            fill=(50, 50, 50),
        )
        draw.ellipse(
            [
                right_eye_x + eye_width // 2,
                eye_y + eye_width // 4,
                right_eye_x + eye_width // 2 + pupil_size,
                eye_y + eye_width // 4 + pupil_size,
            ],
            fill=(50, 50, 50),
        )

        return img
