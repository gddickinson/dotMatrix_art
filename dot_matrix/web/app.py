"""FastAPI web app for Dot Matrix Art: serves the front end in static/ and the JSON API under /api.

Run with `python run_web.py` (http://127.0.0.1:8157, local only). `scripts/build_static.py` exports every path in
STATIC_ENDPOINTS to JSON for the GitHub Pages site, so keep that list in step with the GET routes below. The upload
endpoints (POST /api/convert, /api/palette) run the repo's Python converter; the static site has no server, so the
studio page converts in the browser with the JS port (static/dm_*.js) instead.
"""
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from dot_matrix.web import convert_api

STATIC = Path(__file__).resolve().parent / "static"
MAX_UPLOAD_BYTES = 25 * 1024 * 1024

app = FastAPI(title="Dot Matrix Art")
app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/api/info")
def info():
    """Patterns, effects, palettes and defaults, read from the repo's models and GUI settings."""
    return convert_api.info()


@app.get("/api/demo")
def demo():
    """Demo image drawn by the repo's FaceGenerator."""
    return convert_api.demo()


async def _image(file: UploadFile):
    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "Image too large for the web app (25 MB).")
    try:
        return convert_api.decode_image(data)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/convert")
async def convert(request: Request, file: UploadFile = File(...), seed: Optional[int] = None):
    """Convert an uploaded image with AdvancedDotMatrixConverter; form fields as in convert_api.parse_params."""
    img = await _image(file)
    form = await request.form()
    params = {k: v for k, v in form.items() if k != "file"}
    try:
        return convert_api.convert(img, params, seed=seed)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/palette")
async def palette(file: UploadFile = File(...)):
    """Dominant colours of an uploaded image (ColorPalette.extract_dominant_colors)."""
    return convert_api.extract_palette(await _image(file))


# GET paths (without the /api prefix) written to the static site as api/<path>.json.
STATIC_ENDPOINTS = ["/info", "/demo"]
