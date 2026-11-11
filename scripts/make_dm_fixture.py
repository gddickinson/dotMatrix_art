"""Write tests/fixtures/dm_fixture.json: a small generated test image plus what the repo's Python makes of it.

The node test dot_matrix/web/static/dm_engine.test.mjs runs the JS port on the same pixels and compares:
  * effects   - AdvancedDotMatrixConverter.preprocess_image output (every effect, smoothing, edge enhancement)
  * matrices  - sample_matrix brightness / palette colours and the convert_image_advanced dot list ("circle data",
                stored for matrices of up to 600 cells to keep the file small)
  * svg       - AdvancedExporter.export_svg text for one case
  * shapes    - the ImageDraw calls each pattern makes (_draw_pattern, recorded with a fake ImageDraw)
  * palette   - ColorPalette.extract_dominant_colors
The test image is a seeded gradient + noise with the repo's FaceGenerator face pasted in (80 x 60 px).

Run: python scripts/make_dm_fixture.py
"""
import base64
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dot_matrix.effects import FaceGenerator  # noqa: E402
from dot_matrix.models import ArtisticEffect, ColorPalette, DotPattern  # noqa: E402
from dot_matrix.patterns import AdvancedDotMatrixConverter  # noqa: E402
from dot_matrix.web.convert_api import parse_params, svg_text  # noqa: E402

OUT = ROOT / "tests" / "fixtures" / "dm_fixture.json"
b64 = lambda a: base64.b64encode(np.ascontiguousarray(a, dtype=np.uint8).tobytes()).decode()  # noqa: E731


def test_image() -> Image.Image:
    rng = np.random.default_rng(7)
    h, w = 60, 80
    yy, xx = np.mgrid[0:h, 0:w]
    arr = np.stack([xx * 4, yy * 5, 255 - xx * 2 - yy * 2], axis=-1).astype(float)
    arr += rng.normal(0, 18, arr.shape)
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")
    img.paste(FaceGenerator.create_test_face(48, 56), (16, 2))
    return img


EFFECT_CASES = [{"effect": e.value} for e in ArtisticEffect] + [
    {"effect": "none", "noise_reduce": "1"}, {"effect": "none", "edge_enhance": "1"},
    {"effect": "neon", "noise_reduce": "1", "edge_enhance": "1"},
]

MATRIX_CASES = [
    {},
    {"matrix_width": 20, "matrix_height": 12, "output_width": 400, "output_height": 240, "spacing": 1.5},
    {"matrix_width": 76, "matrix_height": 5, "output_width": 600, "output_height": 100},      # vertical pass first
    {"matrix_width": 80, "matrix_height": 90, "output_width": 640, "output_height": 720},     # upsampling
    {"matrix_width": 13, "matrix_height": 9, "output_width": 333, "output_height": 211, "spacing": 0.37},
    {"matrix_width": 30, "matrix_height": 20, "use_palette": "1", "palette": "Neon Cyberpunk"},
    {"matrix_width": 24, "matrix_height": 18, "use_palette": "1", "palette": "Ocean Blues", "background": "#101820"},
    {"matrix_width": 24, "matrix_height": 18, "use_palette": "1", "palette": "Retro Gaming", "effect": "vintage"},
    {"matrix_width": 32, "matrix_height": 24, "effect": "sketch"},
    {"matrix_width": 24, "matrix_height": 18, "effect": "mosaic", "animate": "1", "frame": 17},
    {"matrix_width": 32, "matrix_height": 24, "effect": "emboss", "noise_reduce": "1"},
    {"matrix_width": 32, "matrix_height": 24, "effect": "crosshatch", "use_palette": "1", "palette": "Fire & Ice"},
    {"matrix_width": 30, "matrix_height": 19, "effect": "neon", "edge_enhance": "1", "animate": "1", "frame": 3},
]


class RecordingDraw:
    """Stands in for ImageDraw.Draw and records the calls _draw_pattern makes."""

    def __init__(self):
        self.calls = []

    def ellipse(self, box, fill=None, outline=None):
        self.calls.append({"t": "ellipse", "box": [float(v) for v in box]})

    def rectangle(self, box, fill=None):
        self.calls.append({"t": "rect", "box": [float(v) for v in box]})

    def polygon(self, pts, fill=None):
        self.calls.append({"t": "poly", "pts": [[float(x), float(y)] for x, y in pts]})

    def text(self, xy, ch, fill=None, font=None):
        self.calls.append({"t": "text", "x": float(xy[0]), "y": float(xy[1]), "ch": ch})


def shapes():
    conv = AdvancedDotMatrixConverter()
    out = []
    for pattern in DotPattern:
        if pattern is DotPattern.STIPPLE:
            continue  # random positions
        for cx, cy, r in [(10.0, 10.0, 0.75), (33.5, 21.25, 2.6), (100.0, 57.0, 4.2), (250.5, 99.0, 9.87)]:
            d = RecordingDraw()
            conv._draw_pattern(d, pattern, cx, cy, r, "black")
            out.append({"pattern": pattern.value, "cx": cx, "cy": cy, "r": r, "calls": d.calls})
    return out


def main():
    img = test_image()
    conv = AdvancedDotMatrixConverter()
    effects = []
    for case in EFFECT_CASES:
        kw = parse_params(case)
        work = conv.preprocess_image(img, kw["artistic_effect"], kw["edge_enhancement"], kw["noise_reduction"])
        effects.append({"params": case, "rgb": b64(np.array(work))})
    matrices = []
    for case in MATRIX_CASES:
        kw = parse_params(case)
        work = conv.preprocess_image(img, kw["artistic_effect"], kw["edge_enhancement"], kw["noise_reduction"])
        bright, colors = conv.sample_matrix(work, kw["matrix_width"], kw["matrix_height"], kw["use_color"],
                                            kw["color_palette"])
        result = conv.convert_image_advanced(img, **kw)
        dots = conv.get_circle_data()
        matrices.append({
            "params": case, "brightness": b64(bright), "colors": None if colors is None else b64(colors),
            "dots": None if len(bright.flat) > 600 else [[d["x"], d["y"], float(d["r"]), d["color"] if isinstance(d["color"], str) else [int(c) for c in d["color"]]]
                     for d in dots],
            "svg": svg_text(result, dots, kw["custom_background"]) if case.get("background") else None,
        })
    fixture = {
        "note": "Generated by scripts/make_dm_fixture.py from the repo's Python (Pillow "
                f"{Image.__version__}); compared with the JS port by dm_engine.test.mjs.",
        "image": {"w": img.width, "h": img.height, "rgb": b64(np.array(img))},
        "palettes": {k: [list(c) for c in v] for k, v in ColorPalette.PALETTES.items()},
        "effects": effects, "matrices": matrices, "shapes": shapes(),
        "dominant": [list(c) for c in ColorPalette.extract_dominant_colors(img, 6)],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(fixture, separators=(",", ":")))
    print(f"wrote {OUT} ({OUT.stat().st_size / 1e3:.0f} kB): {len(effects)} effect, {len(matrices)} matrix, "
          f"{len(fixture['shapes'])} shape cases")


if __name__ == "__main__":
    main()
