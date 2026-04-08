"""Dual display window for Dot Matrix Art Studio."""

import logging
import threading
import tkinter as tk
from tkinter import ttk, messagebox

from PIL import Image, ImageTk

logger = logging.getLogger(__name__)


class DualDisplayWindow:
    """Enhanced dual display window with gallery and tools."""

    def __init__(self, parent, title="Dual Display"):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title(title)
        self.window.geometry("1600x900")

        self.left_canvas_lock = threading.Lock()
        self.right_canvas_lock = threading.Lock()

        self.setup_enhanced_dual_display()

    def setup_enhanced_dual_display(self):
        """Create enhanced dual display layout with tools."""
        paned = ttk.PanedWindow(self.window, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left panel (Original)
        left_panel = ttk.Frame(paned)
        paned.add(left_panel, weight=1)

        left_frame = ttk.LabelFrame(left_panel, text="Original / Live Feed", padding="10")
        left_frame.pack(fill=tk.BOTH, expand=True)

        self.left_canvas = tk.Canvas(left_frame, bg="lightgray", width=750, height=700)
        self.left_canvas.pack(fill=tk.BOTH, expand=True)

        # Right panel (Artistic)
        right_panel = ttk.Frame(paned)
        paned.add(right_panel, weight=1)

        right_frame = ttk.LabelFrame(right_panel, text="Artistic Creation", padding="10")
        right_frame.pack(fill=tk.BOTH, expand=True)

        self.right_canvas = tk.Canvas(right_frame, bg="black", width=750, height=700)
        self.right_canvas.pack(fill=tk.BOTH, expand=True)

        # Status bar
        status_frame = ttk.Frame(self.window)
        status_frame.pack(fill=tk.X, pady=(0, 10), padx=10)

        self.left_status = ttk.Label(
            status_frame, text="Original: No image", relief=tk.SUNKEN, font=("Arial", 10)
        )
        self.left_status.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        self.right_status = ttk.Label(
            status_frame, text="Artistic: No creation", relief=tk.SUNKEN, font=("Arial", 10)
        )
        self.right_status.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))

        # Quick actions toolbar
        toolbar = ttk.Frame(self.window)
        toolbar.pack(fill=tk.X, pady=(0, 5), padx=10)

        ttk.Button(toolbar, text="Quick Save Both", command=self.quick_save_both).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        ttk.Button(toolbar, text="Swap Views", command=self.swap_views).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        ttk.Button(toolbar, text="Show Info", command=self.show_image_info).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        ttk.Button(toolbar, text="Fullscreen Art", command=self.fullscreen_art).pack(
            side=tk.LEFT, padx=(0, 5)
        )

    def update_left_display(self, image: Image.Image, status_text: str = ""):
        """Update left display."""
        def _update():
            with self.left_canvas_lock:
                try:
                    display_image = image.copy()
                    canvas_width = self.left_canvas.winfo_width()
                    canvas_height = self.left_canvas.winfo_height()

                    if canvas_width > 1 and canvas_height > 1:
                        display_image.thumbnail(
                            (canvas_width - 20, canvas_height - 20), Image.LANCZOS
                        )

                    self.left_photo = ImageTk.PhotoImage(display_image)

                    self.left_canvas.delete("all")
                    cx = canvas_width // 2 if canvas_width > 1 else 375
                    cy = canvas_height // 2 if canvas_height > 1 else 350
                    self.left_canvas.create_image(cx, cy, image=self.left_photo)

                    if status_text:
                        self.left_status.config(text=status_text)

                except Exception as e:
                    logger.error(f"Failed to update left display: {e}")

        self.window.after(0, _update)

    def update_right_display(self, image: Image.Image, status_text: str = ""):
        """Update right display."""
        def _update():
            with self.right_canvas_lock:
                try:
                    display_image = image.copy()
                    canvas_width = self.right_canvas.winfo_width()
                    canvas_height = self.right_canvas.winfo_height()

                    if canvas_width > 1 and canvas_height > 1:
                        display_image.thumbnail(
                            (canvas_width - 20, canvas_height - 20), Image.LANCZOS
                        )

                    self.right_photo = ImageTk.PhotoImage(display_image)

                    self.right_canvas.delete("all")
                    cx = canvas_width // 2 if canvas_width > 1 else 375
                    cy = canvas_height // 2 if canvas_height > 1 else 350
                    self.right_canvas.create_image(cx, cy, image=self.right_photo)

                    if status_text:
                        self.right_status.config(text=status_text)

                except Exception as e:
                    logger.error(f"Failed to update right display: {e}")

        self.window.after(0, _update)

    def quick_save_both(self):
        messagebox.showinfo("Quick Save", "Quick save feature - saves both images to gallery!")

    def swap_views(self):
        messagebox.showinfo("Swap Views", "View swapping feature coming soon!")

    def show_image_info(self):
        messagebox.showinfo("Image Info", "Detailed image analysis feature coming soon!")

    def fullscreen_art(self):
        messagebox.showinfo("Fullscreen", "Fullscreen art viewer feature coming soon!")
