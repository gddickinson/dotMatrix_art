"""Smoke tests for dot matrix pattern generation."""

import sys
import os

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(__file__))

from PIL import Image
from dot_matrix.models import DotPattern, ArtisticEffect, ColorPalette, ProjectSettings
from dot_matrix.patterns import AdvancedDotMatrixConverter
from dot_matrix.effects import ArtisticProcessor, FaceGenerator
from dot_matrix.project_io import UndoRedoManager, AdvancedExporter
from dot_matrix.batch import BatchProcessor


def test_all_patterns():
    """Test that each dot pattern renders without error."""
    converter = AdvancedDotMatrixConverter()
    # Create a simple gradient test image
    test_image = Image.new("RGB", (100, 100), (128, 128, 128))

    for pattern in DotPattern:
        result = converter.convert_image_advanced(
            test_image,
            matrix_width=10,
            matrix_height=10,
            output_size=(200, 200),
            pattern=pattern,
        )
        assert result is not None, f"Pattern {pattern.value} returned None"
        assert result.size == (200, 200), f"Pattern {pattern.value} wrong size: {result.size}"
    print("PASSED: test_all_patterns")


def test_artistic_effects():
    """Test that each artistic effect applies without error."""
    test_image = Image.new("RGB", (100, 100), (100, 150, 200))

    for effect in ArtisticEffect:
        result = ArtisticProcessor.apply_artistic_effect(test_image, effect)
        assert result is not None, f"Effect {effect.value} returned None"
    print("PASSED: test_artistic_effects")


def test_face_generator():
    """Test synthetic face generation."""
    face = FaceGenerator.create_test_face()
    assert face is not None
    assert face.size == (200, 240)
    assert face.mode == "RGB"
    print("PASSED: test_face_generator")


def test_color_palette_extraction():
    """Test dominant color extraction."""
    test_image = Image.new("RGB", (50, 50), (255, 0, 0))
    colors = ColorPalette.extract_dominant_colors(test_image, 3)
    assert len(colors) > 0
    # The dominant color should be close to red
    print("PASSED: test_color_palette_extraction")


def test_color_conversion():
    """Test color palette-mapped conversion."""
    converter = AdvancedDotMatrixConverter()
    test_image = Image.new("RGB", (100, 100), (128, 64, 200))

    palette = ColorPalette.PALETTES["Neon Cyberpunk"]
    result = converter.convert_image_advanced(
        test_image,
        matrix_width=10,
        matrix_height=10,
        output_size=(200, 200),
        use_color=True,
        color_palette=palette,
    )
    assert result is not None
    assert result.size == (200, 200)
    print("PASSED: test_color_conversion")


def test_undo_redo_manager():
    """Test undo/redo functionality."""
    mgr = UndoRedoManager(max_history=5)
    img1 = Image.new("RGB", (10, 10), (255, 0, 0))
    img2 = Image.new("RGB", (10, 10), (0, 255, 0))

    assert not mgr.can_undo()
    assert not mgr.can_redo()

    mgr.add_state(img1)
    mgr.add_state(img2)

    assert mgr.can_undo()
    undone = mgr.undo()
    assert undone is not None

    assert mgr.can_redo()
    redone = mgr.redo()
    assert redone is not None
    print("PASSED: test_undo_redo_manager")


def test_project_settings_defaults():
    """Test ProjectSettings has sensible defaults."""
    settings = ProjectSettings(name="test")
    assert settings.matrix_width == 45
    assert settings.matrix_height == 19
    assert settings.pattern == "circle"
    assert settings.effect == "none"
    print("PASSED: test_project_settings_defaults")


def test_svg_export(tmp_path=None):
    """Test SVG export produces valid output."""
    import tempfile

    converter = AdvancedDotMatrixConverter()
    test_image = Image.new("RGB", (100, 100), (128, 128, 128))

    result = converter.convert_image_advanced(
        test_image, matrix_width=5, matrix_height=5, output_size=(100, 100)
    )
    assert result is not None

    circle_data = converter.get_circle_data()

    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as f:
        svg_path = f.name

    try:
        success = AdvancedExporter.export_svg(result, svg_path, circle_data)
        assert success, "SVG export failed"
        with open(svg_path, "r") as f:
            content = f.read()
        assert "<svg" in content
        assert "</svg>" in content
    finally:
        os.unlink(svg_path)

    print("PASSED: test_svg_export")


def test_non_rgb_images_convert():
    """Regression: RGBA/L/P/LA images (PNG with alpha, grayscale, GIF) must convert
    with every effect and with a colour palette (they used to return None)."""
    converter = AdvancedDotMatrixConverter()
    palette = ColorPalette.PALETTES["Ocean Blues"]
    for mode in ["RGBA", "L", "P", "LA"]:
        img = Image.new(mode, (60, 40))
        for effect in ArtisticEffect:
            out = converter.convert_image_advanced(
                img, 10, 5, (100, 50), artistic_effect=effect,
                edge_enhancement=True, noise_reduction=True,
            )
            assert out is not None, f"{mode} + {effect.value} failed"
        out = converter.convert_image_advanced(
            img, 10, 5, (100, 50), use_color=True, color_palette=palette
        )
        assert out is not None, f"{mode} + palette failed"


def test_mosaic_small_image():
    """Regression: the mosaic effect crashed on images narrower than 20 px."""
    out = ArtisticProcessor.apply_artistic_effect(
        Image.new("RGB", (15, 15), (10, 20, 30)), ArtisticEffect.MOSAIC
    )
    assert out.size == (15, 15)


def test_svg_export_uses_background_color():
    """Regression: SVG export always painted a white background, ignoring Custom BG."""
    import tempfile

    converter = AdvancedDotMatrixConverter()
    img = Image.new("RGB", (40, 40), (128, 128, 128))
    result = converter.convert_image_advanced(
        img, 4, 4, (40, 40), custom_background=(10, 20, 30)
    )
    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as f:
        svg_path = f.name
    try:
        assert AdvancedExporter.export_svg(
            result, svg_path, converter.get_circle_data(), background_color=(10, 20, 30)
        )
        content = open(svg_path).read()
        assert 'fill="rgb(10,20,30)"' in content.splitlines()[2]
        assert AdvancedExporter.export_svg(result, svg_path, converter.get_circle_data())
        assert 'fill="white"' in open(svg_path).read().splitlines()[2]
    finally:
        os.unlink(svg_path)


def test_every_menu_effect_changes_the_image():
    """Regression: Watercolor, Comic, Sepia and Depth 3D were listed in the menu but returned the image unchanged."""
    import numpy as np
    rng = np.random.default_rng(0)
    img = Image.fromarray(rng.integers(0, 256, (40, 60, 3), dtype=np.uint8), "RGB")
    for effect in ArtisticEffect:
        if effect is ArtisticEffect.NONE:
            continue
        out = ArtisticProcessor.apply_artistic_effect(img, effect)
        assert out.size == img.size and out.mode == "RGB", effect
        assert not np.array_equal(np.array(out), np.array(img)), f"{effect.value} left the image unchanged"


def test_open_image_applies_exif_orientation(tmp_path=None):
    """Regression: phone photos (EXIF Orientation) were loaded sideways by the desktop app and batch mode."""
    import tempfile
    from tests.exif_sample import rotated_jpeg, red_corner_is_top_right
    from dot_matrix.image_loader import open_image

    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        f.write(rotated_jpeg())
        path = f.name
    try:
        assert red_corner_is_top_right(open_image(path))
    finally:
        os.unlink(path)
    for module in ("gui_main.py", "batch.py"):
        src = open(os.path.join(os.path.dirname(__file__), "dot_matrix", module)).read()
        assert "Image.open(" not in src, f"{module} should load images with open_image"


if __name__ == "__main__":
    test_all_patterns()
    test_artistic_effects()
    test_face_generator()
    test_color_palette_extraction()
    test_color_conversion()
    test_undo_redo_manager()
    test_project_settings_defaults()
    test_svg_export()
    test_non_rgb_images_convert()
    test_mosaic_small_image()
    test_svg_export_uses_background_color()
    test_every_menu_effect_changes_the_image()
    test_open_image_applies_exif_orientation()
    print("\nAll tests passed!")
