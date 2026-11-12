"""Glue between the web API and the repo's real converter (no GUI imports).

Everything here calls the desktop app's own code: AdvancedDotMatrixConverter (patterns.py), ArtisticProcessor
(effects.py), ColorPalette / ProjectSettings (models.py), AdvancedExporter.export_svg and FaceGenerator. The web layer
only parses parameters, decodes uploads and encodes results as JSON.
"""
import base64
import io
import json
import os
import random
import re
import tempfile
from dataclasses import fields
from typing import Optional

from PIL import Image

from dot_matrix.effects import ArtisticProcessor, FaceGenerator
from dot_matrix.image_loader import open_image
from dot_matrix.models import ArtisticEffect, ColorPalette, DotPattern, ProjectSettings
from dot_matrix.patterns import AdvancedDotMatrixConverter
from dot_matrix.project_io import AdvancedExporter

# Spacing slider range of the desktop app (gui_tabs.py, "Matrix Configuration").
SPACING_RANGE = (0.1, 2.0)
# Limits for the web app only (the desktop entry fields accept anything).
LIMITS = {"matrix": (1, 400), "output": (16, 4000), "spacing": (0.05, 3.0), "frame": (0, 100000)}
MAX_PIXELS = 40_000_000


def _label(value: str) -> str:
    return value.replace("_", " ").title()


def _implemented(effect: ArtisticEffect) -> bool:
    """True if ArtisticProcessor changes the image for this effect (some enum values fall through unchanged)."""
    probe = Image.new("RGB", (4, 4), (90, 120, 150))
    return ArtisticProcessor.apply_artistic_effect(probe, effect) is not probe


def defaults() -> dict:
    d = {f.name: f.default for f in fields(ProjectSettings) if f.name != "name"}
    return {k: d[k] for k in ("matrix_width", "matrix_height", "output_width", "output_height", "pattern",
                              "effect", "palette", "use_palette", "spacing", "edge_enhance", "noise_reduce")}


def info() -> dict:
    return {
        "title": "Dot Matrix Art",
        "description": "Photo to dot matrix converter: turn any image into dot matrix art with 11 dot patterns, "
                       "artistic effects and colour palettes.",
        "repo": "dotMatrix_art",
        "patterns": [{"value": p.value, "label": _label(p.value)} for p in DotPattern],
        "effects": [{"value": e.value, "label": _label(e.value), "implemented": e is ArtisticEffect.NONE or _implemented(e)}
                    for e in ArtisticEffect],
        "palettes": {k: [list(c) for c in v] for k, v in ColorPalette.PALETTES.items()},
        "defaults": defaults(),
        "spacing_range": list(SPACING_RANGE),
        "limits": LIMITS,
    }


def png_data_url(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def demo() -> dict:
    """The desktop app's "test face" (FaceGenerator.create_test_face) as the demo image."""
    img = FaceGenerator.create_test_face()
    return {"name": "test_face.png", "width": img.width, "height": img.height, "png": png_data_url(img),
            "source": "dot_matrix/effects.py FaceGenerator.create_test_face() (synthetic, drawn by the repo's code)"}


def decode_image(data: bytes) -> Image.Image:
    """Open an uploaded image upright (image_loader.open_image: EXIF orientation applied, as browsers display it)."""
    try:
        with Image.open(io.BytesIO(data)) as probe:
            size = probe.size
    except Exception as e:
        raise ValueError(f"Could not read the image: {e}")
    if size[0] * size[1] > MAX_PIXELS:
        raise ValueError(f"Image too large ({size[0]}x{size[1]}); the web app accepts up to 40 megapixels.")
    try:
        return open_image(io.BytesIO(data))
    except Exception as e:
        raise ValueError(f"Could not read the image: {e}")


def _num(params: dict, key: str, default, lo, hi, cast=float):
    raw = params.get(key, default)
    try:
        v = cast(float(raw)) if cast is int else cast(raw)
    except (TypeError, ValueError):
        raise ValueError(f"{key} must be a number")
    if not lo <= v <= hi:
        raise ValueError(f"{key} must be between {lo} and {hi}")
    return v


def _flag(params: dict, key: str) -> bool:
    return str(params.get(key, "")).lower() in ("1", "true", "on", "yes")


def _background(raw: Optional[str]):
    if not raw:
        return None
    m = re.fullmatch(r"#?([0-9a-fA-F]{6})", raw.strip())
    if not m:
        raise ValueError("background must be a colour like #102030")
    h = m.group(1)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _palette_colors(raw: Optional[str]):
    """Optional custom palette (e.g. one extracted from the image, as the desktop "Extract Palette" button adds)."""
    if not raw:
        return None
    try:
        colors = [tuple(int(v) for v in c) for c in json.loads(raw)]
    except (TypeError, ValueError):
        raise ValueError("palette_colors must be a JSON list of [r, g, b] colours")
    if not 1 <= len(colors) <= 32 or any(len(c) != 3 or not all(0 <= v <= 255 for v in c) for c in colors):
        raise ValueError("palette_colors must hold 1 to 32 [r, g, b] colours with values 0-255")
    return colors


def parse_params(params: dict) -> dict:
    """Validate web form fields into keyword arguments for convert_image_advanced."""
    d = defaults()
    try:
        pattern = DotPattern(params.get("pattern", d["pattern"]))
        effect = ArtisticEffect(params.get("effect", d["effect"]))
    except ValueError as e:
        raise ValueError(str(e))
    use_palette = _flag(params, "use_palette")
    palette_name = params.get("palette", d["palette"])
    colors = _palette_colors(params.get("palette_colors")) if use_palette else None
    if use_palette and colors is None and palette_name not in ColorPalette.PALETTES:
        raise ValueError(f"unknown palette {palette_name!r}")
    animate = _flag(params, "animate")
    m, o = LIMITS["matrix"], LIMITS["output"]
    return dict(
        matrix_width=_num(params, "matrix_width", d["matrix_width"], *m, cast=int),
        matrix_height=_num(params, "matrix_height", d["matrix_height"], *m, cast=int),
        output_size=(_num(params, "output_width", d["output_width"], *o, cast=int),
                     _num(params, "output_height", d["output_height"], *o, cast=int)),
        pattern=pattern,
        circle_spacing=_num(params, "spacing", d["spacing"], *LIMITS["spacing"]),
        use_color=use_palette,
        color_palette=(colors or ColorPalette.PALETTES[palette_name]) if use_palette else None,
        artistic_effect=effect,
        animate=animate,
        animation_frame=_num(params, "frame", 0, *LIMITS["frame"], cast=int) if animate else 0,
        edge_enhancement=_flag(params, "edge_enhance"),
        noise_reduction=_flag(params, "noise_reduce"),
        custom_background=_background(params.get("background")),
    )


def svg_text(result: Image.Image, circle_data: list, background, pattern=None) -> str:
    """The desktop app's SVG export (AdvancedExporter.export_svg) as a string: pattern shapes, or circles if None."""
    fd, path = tempfile.mkstemp(suffix=".svg")
    os.close(fd)
    try:
        if not AdvancedExporter.export_svg(result, path, circle_data, background_color=background, pattern=pattern):
            raise ValueError("SVG export failed")
        with open(path) as f:
            return f.read()
    finally:
        os.unlink(path)


def _color_json(c):
    return c if isinstance(c, str) else [int(v) for v in c]


def convert(image: Image.Image, params: dict, seed: Optional[int] = None) -> dict:
    """Run AdvancedDotMatrixConverter.convert_image_advanced and return PNG, SVG and the dot list."""
    kw = parse_params(params)
    if seed is not None:  # stipple dots are random; a seed makes the server result repeatable
        random.seed(seed)
    conv = AdvancedDotMatrixConverter()
    result = conv.convert_image_advanced(image, **kw)
    if result is None:
        raise ValueError("The converter returned no image (see the server log)")
    dots = conv.get_circle_data()
    return {
        "width": result.width, "height": result.height, "png": png_data_url(result),
        "svg": svg_text(result, dots, kw["custom_background"], kw["pattern"]),
        "dots": [{"x": d["x"], "y": d["y"], "r": float(d["r"]), "color": _color_json(d["color"])} for d in dots],
    }


def extract_palette(image: Image.Image, num_colors: int = 6) -> dict:
    """ColorPalette.extract_dominant_colors, as the desktop "Extract Palette" button (6 colours)."""
    return {"colors": [[int(v) for v in c] for c in ColorPalette.extract_dominant_colors(image, num_colors)]}
