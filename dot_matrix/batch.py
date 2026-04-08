"""Batch processing for Dot Matrix Art Studio."""

import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable

from PIL import Image

from dot_matrix.models import DotPattern, ArtisticEffect, ColorPalette, ProjectSettings

logger = logging.getLogger(__name__)


class BatchProcessor:
    """Batch processing system for multiple images."""

    def __init__(self, converter, progress_callback: Optional[Callable] = None):
        self.converter = converter
        self.progress_callback = progress_callback
        self.is_processing = False

    def process_batch(
        self,
        image_paths: List[str],
        settings: ProjectSettings,
        output_dir: str,
    ) -> Dict[str, Any]:
        """Process multiple images with the same settings."""
        self.is_processing = True
        results: Dict[str, Any] = {
            "processed": 0,
            "failed": 0,
            "errors": [],
            "output_files": [],
        }

        try:
            total_images = len(image_paths)

            for i, image_path in enumerate(image_paths):
                if not self.is_processing:
                    break

                try:
                    image = Image.open(image_path)

                    result = self.converter.convert_image_advanced(
                        image,
                        matrix_width=settings.matrix_width,
                        matrix_height=settings.matrix_height,
                        output_size=(settings.output_width, settings.output_height),
                        pattern=DotPattern(settings.pattern),
                        circle_spacing=settings.spacing,
                        use_color=settings.use_palette,
                        color_palette=(
                            ColorPalette.PALETTES.get(settings.palette)
                            if settings.use_palette
                            else None
                        ),
                        artistic_effect=ArtisticEffect(settings.effect),
                        edge_enhancement=settings.edge_enhance,
                        noise_reduction=settings.noise_reduce,
                        custom_background=settings.background_color,
                    )

                    if result:
                        input_name = Path(image_path).stem
                        output_file = Path(output_dir) / f"{input_name}_dotmatrix.png"
                        result.save(output_file)
                        results["processed"] += 1
                        results["output_files"].append(str(output_file))
                    else:
                        results["failed"] += 1
                        results["errors"].append(f"Conversion failed for {image_path}")

                except Exception as e:
                    results["failed"] += 1
                    results["errors"].append(f"Error processing {image_path}: {e}")

                if self.progress_callback:
                    progress = (i + 1) / total_images * 100
                    self.progress_callback(progress, f"Processing {Path(image_path).name}")

        except Exception as e:
            results["errors"].append(f"Batch processing error: {e}")

        self.is_processing = False
        return results

    def cancel_processing(self):
        """Cancel the current batch processing."""
        self.is_processing = False
