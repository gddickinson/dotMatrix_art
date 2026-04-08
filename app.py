"""Main entry point for Dot Matrix Art Studio."""

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("dot_matrix_converter.log"),
        logging.StreamHandler(),
    ],
)

from dot_matrix.camera import CV2_AVAILABLE
from dot_matrix.gui_main import MasterDotMatrixStudio


def main():
    """Main entry point."""
    try:
        if not CV2_AVAILABLE:
            print(
                "Warning: OpenCV not available. Camera and face detection features will be disabled."
            )
            print("To enable these features, install OpenCV with: pip install opencv-python")

        app = MasterDotMatrixStudio()
        app.run()
    except Exception as e:
        logging.getLogger(__name__).error(f"Application failed: {e}")
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
