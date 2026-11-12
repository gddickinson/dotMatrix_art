"""SVG text for dot matrix art (no GUI imports).

circles_svg: every dot as a <circle> at full precision (the original export format).
shapes_svg:  every dot drawn with the selected pattern's shapes. The shapes come from the converter's own
             _draw_pattern calls (recorded with ShapeRecorder), numbers are written with 3 decimals, and the text is
             byte-identical to the web app's svgShapes (dot_matrix/web/static/dm_shapes.js) for every pattern except
             stipple, whose scatter is random.
"""
from decimal import ROUND_HALF_UP, Decimal
from typing import Dict, List, Optional, Tuple

THOUSANDTH = Decimal("0.001")


def svg_number(v: float) -> str:
    """Same text as JavaScript String(+v.toFixed(3)): the exact binary value rounded to 3 decimals, ties away from
    zero, trailing zeros dropped, and "0" for anything that rounds to zero."""
    q = Decimal(float(v)).quantize(THOUSANDTH, rounding=ROUND_HALF_UP)
    if q == 0:
        return "0"
    return format(q.normalize(), "f")


def css_color(color) -> str:
    if isinstance(color, str):
        return color
    return f"rgb({int(color[0])},{int(color[1])},{int(color[2])})"


def svg_header(width: int, height: int, background: Optional[Tuple[int, int, int]] = None) -> str:
    bg = f"rgb({int(background[0])},{int(background[1])},{int(background[2])})" if background else "white"
    return (
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">\n'
        f'<rect width="{width}" height="{height}" fill="{bg}"/>\n'
    )


def circles_svg(width: int, height: int, circle_data: List[Dict], background=None) -> str:
    out = [svg_header(width, height, background)]
    for c in circle_data:
        out.append(f'<circle cx="{c["x"]}" cy="{c["y"]}" r="{c["r"]}" fill="{css_color(c["color"])}"/>\n')
    out.append("</svg>")
    return "".join(out)


class ShapeRecorder:
    """Stands in for ImageDraw.Draw and records the primitives a pattern draws."""

    def __init__(self):
        self.calls: List[Dict] = []

    def ellipse(self, box, fill=None, outline=None):
        self.calls.append({"t": "ellipse", "box": [float(v) for v in box]})

    def rectangle(self, box, fill=None):
        self.calls.append({"t": "rect", "box": [float(v) for v in box]})

    def polygon(self, pts, fill=None):
        self.calls.append({"t": "poly", "pts": [[float(x), float(y)] for x, y in pts]})

    def text(self, xy, ch, fill=None, font=None):
        self.calls.append({"t": "text", "x": float(xy[0]), "y": float(xy[1]), "ch": ch})


def shapes_svg(width: int, height: int, circle_data: List[Dict], pattern, background=None) -> str:
    from dot_matrix.patterns import AdvancedDotMatrixConverter  # local import: patterns does not import this module

    conv = AdvancedDotMatrixConverter()
    f = svg_number
    out = [svg_header(width, height, background)]
    for c in circle_data:
        fill = css_color(c["color"])
        rec = ShapeRecorder()
        conv._draw_pattern(rec, pattern, c["x"], c["y"], c["r"], fill)
        for p in rec.calls:
            if p["t"] == "rect":
                b = p["box"]
                out.append(f'<rect x="{f(b[0])}" y="{f(b[1])}" width="{f(b[2] - b[0])}" height="{f(b[3] - b[1])}" fill="{fill}"/>\n')
            elif p["t"] == "ellipse":
                b = p["box"]
                out.append(f'<circle cx="{f((b[0] + b[2]) / 2)}" cy="{f((b[1] + b[3]) / 2)}" r="{f((b[2] - b[0]) / 2)}" fill="{fill}"/>\n')
            elif p["t"] == "poly":
                pts = " ".join(f"{f(x)},{f(y)}" for x, y in p["pts"])
                out.append(f'<polygon points="{pts}" fill="{fill}"/>\n')
            else:
                size = max(8, int(c["r"] * 1.5))  # font size used by _draw_ascii_dot
                out.append(f'<text x="{f(p["x"])}" y="{f(p["y"])}" font-family="Arial, sans-serif" font-size="{size}" '
                           f'dominant-baseline="hanging" fill="{fill}">{p["ch"]}</text>\n')
    out.append("</svg>")
    return "".join(out)
