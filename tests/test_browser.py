"""Browser checks (Playwright + Chrome/Chromium; skipped where they are not installed, e.g. in CI).

The static site decodes the user's photo with image_io.fileToRGB (createImageBitmap, imageOrientation 'from-image');
a JPEG stored sideways with EXIF Orientation 6 must come out upright, like the Python upload path.

Run: python -m pytest -q tests/test_browser.py
"""
import functools
import http.server
import sys
import threading
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

sync_api = pytest.importorskip("playwright.sync_api")

from tests.exif_sample import rotated_jpeg  # noqa: E402


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    import build_static
    out = tmp_path_factory.mktemp("site") / "site"
    build_static.build(out)
    (out / "rotated.jpg").write_bytes(rotated_jpeg())
    handler = functools.partial(type("Q", (http.server.SimpleHTTPRequestHandler,), {"log_message": lambda *a: None}),
                                directory=str(out))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}/"
    srv.shutdown()


@pytest.fixture(scope="module")
def page(site):
    with sync_api.sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="chrome")
        except Exception:
            try:
                browser = p.chromium.launch()
            except Exception as e:
                pytest.skip(f"no browser: {e}")
        pg = browser.new_page()
        pg.goto(site + "#/about")
        pg.wait_for_selector("#app h1")
        yield pg
        browser.close()


def test_browser_decodes_exif_rotated_jpeg_upright(page):
    res = page.evaluate("""async () => {
      const { fileToRGB } = await import('./static/image_io.js');
      const im = await fileToRGB(await (await fetch('rotated.jpg')).blob());
      const px = (x, y) => Array.from(im.data.slice((y * im.w + x) * 3, (y * im.w + x) * 3 + 3));
      return { w: im.w, h: im.h, topRight: px(im.w - 4, 4), topLeft: px(3, 3) };
    }""")
    assert (res["w"], res["h"]) == (30, 60)
    r, g, _ = res["topRight"]
    assert r > 180 and g < 60, res
    assert min(res["topLeft"]) > 200, res
