"""Web interface tests: every exported endpoint answers, the static build is complete, and the JS engine tests pass.

Run: python -m pytest -q tests/test_web.py
"""
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dot_matrix.web.app import STATIC, STATIC_ENDPOINTS, app  # noqa: E402

client = TestClient(app)


def test_index_served():
    r = client.get("/")
    assert r.status_code == 200 and "static/main.js" in r.text


@pytest.mark.parametrize("path", STATIC_ENDPOINTS)
def test_endpoint(path):
    r = client.get("/api" + path)
    assert r.status_code == 200, r.text
    assert r.json() is not None


def test_static_build(tmp_path):
    sys.path.insert(0, str(ROOT / "scripts"))
    import build_static
    build_static.build(tmp_path / "site")
    assert (tmp_path / "site" / "index.html").read_text().count("APP_STATIC") == 1
    for path in STATIC_ENDPOINTS:
        assert (tmp_path / "site" / "api" / (path.strip("/") + ".json")).exists()


def test_static_assets_referenced_exist():
    html = (STATIC / "index.html").read_text()
    for name in ("style.css", "main.js"):
        assert f"static/{name}" in html and (STATIC / name).exists()


@pytest.mark.skipif(not shutil.which("node"), reason="node not installed")
def test_js_engine():
    tests = sorted(STATIC.glob("*.test.mjs"))
    for t in tests:
        r = subprocess.run(["node", str(t)], capture_output=True, text=True)
        assert r.returncode == 0, r.stdout + r.stderr


# --- project-specific ----------------------------------------------------------------------------------------------
import base64  # noqa: E402
import io  # noqa: E402
import json  # noqa: E402

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

FIXTURE = json.loads((ROOT / "tests" / "fixtures" / "dm_fixture.json").read_text())


def _png(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_info_lists_everything_the_python_offers():
    from dot_matrix.models import ArtisticEffect, ColorPalette, DotPattern
    info = client.get("/api/info").json()
    assert [p["value"] for p in info["patterns"]] == [p.value for p in DotPattern]
    assert [e["value"] for e in info["effects"]] == [e.value for e in ArtisticEffect]
    assert set(info["palettes"]) == set(ColorPalette.PALETTES)
    assert info["defaults"]["matrix_width"] == 45 and info["defaults"]["output_width"] == 900


def test_effects_flagged_as_implemented_match_js_engine():
    """The effects the JS port implements (dm_engine.js EFFECTS) are exactly those the Python changes the image for."""
    js = (STATIC / "dm_engine.js").read_text()
    for e in client.get("/api/info").json()["effects"]:
        if e["value"] != "none":
            assert (f"  {e['value']}(" in js or f"  {e['value']}:" in js) == e["implemented"], e


def test_demo_is_the_repo_test_face():
    d = client.get("/api/demo").json()
    img = Image.open(io.BytesIO(base64.b64decode(d["png"].split(",", 1)[1])))
    assert img.size == (200, 240) and (d["width"], d["height"]) == (200, 240)


def test_convert_matches_fixture_dots():
    """POST /api/convert on the fixture image gives the dot list the JS test compares against."""
    raw = np.frombuffer(base64.b64decode(FIXTURE["image"]["rgb"]), np.uint8)
    img = Image.fromarray(raw.reshape(FIXTURE["image"]["h"], FIXTURE["image"]["w"], 3), "RGB")
    case = next(c for c in FIXTURE["matrices"] if c["svg"])
    r = client.post("/api/convert", files={"file": ("t.png", _png(img), "image/png")}, data=case["params"])
    assert r.status_code == 200, r.text
    got = r.json()
    assert len(got["dots"]) == len(case["dots"])
    for d, (x, y, rad, col) in zip(got["dots"], case["dots"]):
        assert abs(d["x"] - x) < 1e-9 and abs(d["y"] - y) < 1e-9 and abs(d["r"] - rad) < 1e-9 and d["color"] == col
    assert got["svg"].startswith('<?xml') and 'fill="rgb(16,24,32)"' in got["svg"].splitlines()[2]


def test_convert_rejects_bad_input():
    png = _png(Image.new("RGB", (30, 20), (90, 90, 90)))
    assert client.post("/api/convert", files={"file": ("t.png", png)}, data={"pattern": "blob"}).status_code == 400
    assert client.post("/api/convert", files={"file": ("t.png", png)}, data={"matrix_width": "0"}).status_code == 400
    assert client.post("/api/convert", files={"file": ("t.txt", b"not an image")}).status_code == 400


def test_convert_rgba_and_palette_upload():
    png = _png(Image.new("RGBA", (40, 30), (200, 10, 10, 128)))
    r = client.post("/api/convert", files={"file": ("t.png", png)},
                    data={"effect": "vintage", "use_palette": "1", "palette": "Ocean Blues", "pattern": "stipple"})
    assert r.status_code == 200, r.text
    r = client.post("/api/palette", files={"file": ("t.png", png)})
    assert r.status_code == 200 and r.json()["colors"]


def test_fixture_is_current(tmp_path, monkeypatch):
    """Re-run scripts/make_dm_fixture.py and compare with the committed fixture (tolerant: libm/FMA differ by platform)."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import make_dm_fixture
    monkeypatch.setattr(make_dm_fixture, "OUT", tmp_path / "f.json")
    make_dm_fixture.main()
    new = json.loads((tmp_path / "f.json").read_text())
    arr = lambda s: np.frombuffer(base64.b64decode(s), np.uint8).astype(int)  # noqa: E731
    assert new["image"] == FIXTURE["image"] and new["palettes"] == FIXTURE["palettes"]
    for a, b in zip(new["effects"] + new["matrices"], FIXTURE["effects"] + FIXTURE["matrices"]):
        key = "rgb" if "rgb" in a else "brightness"
        assert a["params"] == b["params"] and np.abs(arr(a[key]) - arr(b[key])).max() <= 1
    for a, b in zip(new["shapes"], FIXTURE["shapes"]):
        assert [c["t"] for c in a["calls"]] == [c["t"] for c in b["calls"]]
    assert new["dominant"] == FIXTURE["dominant"]


def test_convert_with_custom_palette_colours():
    """An extracted palette (sent as palette_colors) is used instead of a named one."""
    png = _png(Image.new("RGB", (40, 30), (40, 40, 40)))
    r = client.post("/api/convert", files={"file": ("t.png", png)},
                    data={"use_palette": "1", "palette": "Extracted 1", "palette_colors": "[[1, 2, 3]]"})
    assert r.status_code == 200, r.text
    assert {tuple(d["color"]) for d in r.json()["dots"]} == {(1, 2, 3)}
    bad = client.post("/api/convert", files={"file": ("t.png", png)},
                      data={"use_palette": "1", "palette_colors": "[[1, 2, 300]]"})
    assert bad.status_code == 400
