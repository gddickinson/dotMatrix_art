"""Rotated test JPEG for the EXIF-orientation tests: stored 60 x 30 (landscape) with EXIF Orientation 6, so viewers
show it 30 x 60 (portrait). A red block marks the stored top-left corner; displayed upright it is at the top-right."""
import io

from PIL import Image


def rotated_jpeg() -> bytes:
    img = Image.new("RGB", (60, 30), (240, 240, 240))
    img.paste((220, 0, 0), (0, 0, 15, 15))
    exif = Image.Exif()
    exif[0x0112] = 6  # Orientation: rotate 90 degrees clockwise to display
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95, exif=exif.tobytes())
    return buf.getvalue()


def red_corner_is_top_right(img: Image.Image) -> bool:
    w, h = img.size
    r, g, _ = img.convert("RGB").getpixel((w - 4, 4))
    r2, _, _ = img.convert("RGB").getpixel((3, 3))
    return (w, h) == (30, 60) and r > 180 and g < 60 and r2 > 200 and img.convert("RGB").getpixel((3, 3))[1] > 200
