"""Open images the right way up (no GUI imports).

Cameras and phones store photos sideways and record the rotation in the EXIF Orientation tag; viewers and browsers
apply it. open_image does the same, so the desktop app, batch mode and the web app all see the photo as displayed.
"""
from typing import BinaryIO, Union

from PIL import Image, ImageOps


def open_image(source: Union[str, BinaryIO]) -> Image.Image:
    """Image.open + load, with the EXIF orientation applied (images without the tag are returned as they are)."""
    img = Image.open(source)
    img.load()
    return ImageOps.exif_transpose(img)
