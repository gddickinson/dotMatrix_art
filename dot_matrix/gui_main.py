"""Main GUI application for Dot Matrix Art Studio."""

import os
import sys
import time
import logging
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser

from PIL import Image, ImageTk

from dot_matrix.models import (
    DotPattern, ArtisticEffect, ColorPalette, ProjectSettings,
)
from dot_matrix.patterns import AdvancedDotMatrixConverter
from dot_matrix.effects import FaceGenerator
from dot_matrix.camera import FaceDetector, CameraCapture, CV2_AVAILABLE
from dot_matrix.batch import BatchProcessor
from dot_matrix.project_io import (
    ProjectManager, AdvancedExporter, UndoRedoManager, ThreadSafeImageProcessor,
)
from dot_matrix.gui_display import DualDisplayWindow
from dot_matrix.gui_tabs import TabSetupMixin

logger = logging.getLogger(__name__)


class MasterDotMatrixStudio(TabSetupMixin):
    """Master application with all professional features."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Dot Matrix Art Studio Pro - Master Edition")
        self.root.geometry("800x1100")

        # Initialize all systems
        self.processor = ThreadSafeImageProcessor()
        self.converter = AdvancedDotMatrixConverter()
        self.face_generator = FaceGenerator()
        self.face_detector = FaceDetector()
        self.camera = CameraCapture()
        self.project_manager = ProjectManager()
        self.undo_manager = UndoRedoManager()
        self.batch_processor = BatchProcessor(self.converter)

        # State variables
        self.current_image = None
        self.current_result = None
        self.current_project = ProjectSettings("Untitled")
        self.camera_active = False
        self.auto_convert_active = False
        self.dual_display = None
        self.animation_active = False
        self.animation_frame = 0

        # Threading controls
        self.camera_update_job = None
        self.auto_convert_job = None
        self.animation_job = None

        self.setup_master_gui()
        self.logger = logger

        self.setup_keyboard_shortcuts()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.logger.info("Master Dot Matrix Art Studio initialized")

    def setup_keyboard_shortcuts(self):
        self.root.bind("<Control-s>", lambda e: self.save_project())
        self.root.bind("<Control-o>", lambda e: self.load_project())
        self.root.bind("<Control-n>", lambda e: self.new_project())
        self.root.bind("<Control-z>", lambda e: self.undo())
        self.root.bind("<Control-y>", lambda e: self.redo())
        self.root.bind("<F5>", lambda e: self.convert_image())
        self.root.bind("<F11>", lambda e: self.open_dual_display())

    def setup_master_gui(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.setup_project_tab()
        self.setup_input_tab()
        self.setup_artistic_tab()
        self.setup_advanced_tab()
        self.setup_batch_tab()
        self.setup_gallery_tab()

        self.status_var = tk.StringVar(
            value="Master Art Studio Ready - Create Amazing Dot Matrix Art!"
        )
        status_bar = ttk.Label(
            self.root, textvariable=self.status_var, relief=tk.SUNKEN, font=("Arial", 10)
        )
        status_bar.pack(fill=tk.X, pady=(0, 10), padx=10)

    # -- Core functionality -------------------------------------------------

    def update_status(self, message: str):
        self.status_var.set(message)
        self.root.update_idletasks()
        self.logger.info(f"Status: {message}")

    def open_dual_display(self):
        if self.dual_display is None or not tk.Toplevel.winfo_exists(self.dual_display.window):
            self.dual_display = DualDisplayWindow(
                self.root, "Master Art Studio | Original <-> Artistic Creation"
            )
            self.update_status("Master Art Studio Display opened - Ready to create masterpieces!")
        else:
            self.dual_display.window.lift()
            self.dual_display.window.focus_set()

    def load_image(self):
        file_path = filedialog.askopenfilename(
            title="Select Image for Artistic Transformation",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.gif *.tiff *.webp"),
                ("All files", "*.*"),
            ],
        )
        if file_path:
            try:
                self.current_image = Image.open(file_path)
                self.undo_manager.add_state(self.current_image)
                filename = os.path.basename(file_path)
                self.image_info_label.config(
                    text=f"{filename} ({self.current_image.size[0]}x{self.current_image.size[1]})"
                )
                self.update_status(f"Image loaded: {filename} - Ready for artistic transformation!")
                if self.dual_display:
                    self.dual_display.update_left_display(self.current_image, f"Loaded: {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load image: {e}")
                self.logger.error(f"Failed to load image {file_path}: {e}")

    def generate_test_face(self):
        try:
            self.current_image = self.face_generator.create_test_face()
            self.undo_manager.add_state(self.current_image)
            self.image_info_label.config(text="AI Generated test face (200x240)")
            self.update_status("AI Test face generated - Perfect for portrait art experiments!")
            if self.dual_display:
                self.dual_display.update_left_display(self.current_image, "AI Generated test face")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate test face: {e}")
            self.logger.error(f"Failed to generate test face: {e}")

    def extract_image_palette(self):
        if not self.current_image:
            messagebox.showwarning("Warning", "Please load an image first")
            return
        try:
            colors = ColorPalette.extract_dominant_colors(self.current_image, 6)
            palette_name = f"Extracted_{int(time.time())}"
            ColorPalette.PALETTES[palette_name] = colors
            self.palette_combo["values"] = list(ColorPalette.PALETTES.keys())
            self.palette_var.set(palette_name)
            self.use_palette_var.set(True)
            color_str = ", ".join([f"RGB{color}" for color in colors[:3]])
            self.update_status(f"Color palette extracted: {color_str}...")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to extract palette: {e}")

    def convert_image(self, animate=False):
        if not self.current_image:
            if not animate:
                messagebox.showwarning("Warning", "Please load an image first")
            return

        def perform_master_conversion():
            try:
                matrix_width = int(self.width_var.get())
                matrix_height = int(self.height_var.get())
                output_width = int(self.out_width_var.get())
                output_height = int(self.out_height_var.get())

                pattern = DotPattern(self.pattern_var.get())
                circle_spacing = float(self.spacing_var.get())

                use_color = self.use_palette_var.get()
                color_palette = None
                if use_color:
                    palette_name = self.palette_var.get()
                    color_palette = ColorPalette.PALETTES.get(palette_name)

                effect_name = self.effect_var.get().lower().replace(" ", "_")
                try:
                    artistic_effect = ArtisticEffect(effect_name)
                except ValueError:
                    artistic_effect = ArtisticEffect.NONE

                edge_enhancement = self.edge_enhance_var.get()
                noise_reduction = self.noise_reduce_var.get()
                animation_frame = self.animation_frame if animate else 0

                return self.converter.convert_image_advanced(
                    self.current_image,
                    matrix_width=matrix_width,
                    matrix_height=matrix_height,
                    output_size=(output_width, output_height),
                    pattern=pattern,
                    circle_spacing=circle_spacing,
                    use_color=use_color,
                    color_palette=color_palette,
                    artistic_effect=artistic_effect,
                    animate=animate,
                    animation_frame=animation_frame,
                    edge_enhancement=edge_enhancement,
                    noise_reduction=noise_reduction,
                    custom_background=self.bg_color,
                )
            except Exception as e:
                self.logger.error(f"Master conversion failed: {e}")
                return None

        if not animate:
            pattern_name = self.pattern_var.get().replace("_", " ").title()
            effect_name = self.effect_var.get().replace("_", " ").title()
            self.update_status(f"Creating {pattern_name} art with {effect_name} effect...")

        future = self.processor.submit_processing_task(perform_master_conversion)

        def handle_result():
            try:
                result = future.result(timeout=0.1)
                if result:
                    self.current_result = result
                    if not animate:
                        self.undo_manager.add_state(result)
                    if self.dual_display:
                        pn = self.pattern_var.get().replace("_", " ").title()
                        en = self.effect_var.get().replace("_", " ").title()
                        self.dual_display.update_right_display(result, f"{pn} - {en}")
                    if not animate:
                        self.update_status("Artistic masterpiece created successfully!")
                else:
                    if not animate:
                        self.update_status("Conversion failed - Please check settings")
            except Exception:
                if not animate:
                    self.update_status("Conversion error occurred")

        self.root.after(200, handle_result)

    # -- Camera methods -----------------------------------------------------

    def toggle_camera(self):
        if not CV2_AVAILABLE:
            messagebox.showerror(
                "Error",
                "OpenCV not available. Please install opencv-python to use camera features.",
            )
            return
        if not self.camera_active:
            success = self.camera.start_camera()
            if success:
                self.camera_active = True
                self.camera_button.config(text="Stop Camera")
                self.update_status("Camera started - Live feed active!")
                self.start_camera_updates()
            else:
                messagebox.showerror("Error", "Failed to start camera")
        else:
            self.camera.stop_camera()
            self.camera_active = False
            self.camera_button.config(text="Start Camera")
            self.update_status("Camera stopped")
            if self.camera_update_job:
                self.root.after_cancel(self.camera_update_job)
                self.camera_update_job = None

    def start_camera_updates(self):
        if self.camera_active and self.camera.is_active():
            frame = self.camera.get_latest_frame()
            if frame:
                if self.auto_crop_var.get():
                    cropped = self.face_detector.crop_largest_face(
                        frame, float(self.face_padding_var.get())
                    )
                    if cropped:
                        frame = cropped
                if self.dual_display:
                    self.dual_display.update_left_display(frame, "Live Camera Feed")
                if self.auto_convert_active:
                    self.current_image = frame
                    self.convert_image()
            self.camera_update_job = self.root.after(100, self.start_camera_updates)

    def capture_camera_frame(self):
        if not self.camera_active:
            messagebox.showwarning("Warning", "Camera not active")
            return
        frame = self.camera.get_latest_frame()
        if frame:
            if self.auto_crop_var.get():
                cropped = self.face_detector.crop_largest_face(
                    frame, float(self.face_padding_var.get())
                )
                if cropped:
                    frame = cropped
            self.current_image = frame
            self.undo_manager.add_state(self.current_image)
            self.image_info_label.config(
                text=f"Camera capture ({frame.size[0]}x{frame.size[1]})"
            )
            self.update_status("Camera frame captured successfully!")
        else:
            messagebox.showerror("Error", "No camera frame available")

    def detect_faces(self):
        if not self.current_image:
            messagebox.showwarning("Warning", "Please load an image first")
            return
        if not CV2_AVAILABLE:
            messagebox.showerror("Error", "OpenCV not available for face detection")
            return
        faces = self.face_detector.detect_faces(self.current_image)
        if faces:
            messagebox.showinfo("Face Detection", f"Found {len(faces)} face(s) in the image!")
            self.update_status(f"Face detection complete: {len(faces)} face(s) found")
        else:
            messagebox.showinfo("Face Detection", "No faces detected in the image")
            self.update_status("Face detection complete: No faces found")

    def auto_crop_face(self):
        if not self.current_image:
            messagebox.showwarning("Warning", "Please load an image first")
            return
        if not CV2_AVAILABLE:
            messagebox.showerror("Error", "OpenCV not available for face detection")
            return
        try:
            padding = float(self.face_padding_var.get())
            cropped = self.face_detector.crop_largest_face(self.current_image, padding)
            if cropped:
                self.current_image = cropped
                self.undo_manager.add_state(self.current_image)
                self.image_info_label.config(
                    text=f"Face cropped ({cropped.size[0]}x{cropped.size[1]})"
                )
                self.update_status("Face auto-cropped successfully!")
                if self.dual_display:
                    self.dual_display.update_left_display(self.current_image, "Auto-cropped face")
            else:
                messagebox.showinfo("Auto-Crop", "No face found to crop")
        except ValueError:
            messagebox.showerror("Error", "Invalid padding value")

    def toggle_auto_convert(self):
        self.auto_convert_active = self.auto_convert_var_adv.get()
        if self.auto_convert_active:
            self.update_status("Auto-convert enabled - Live artistic transformation!")
        else:
            self.update_status("Auto-convert disabled")

    # -- Project methods ----------------------------------------------------

    def save_project(self):
        try:
            self.current_project.name = self.project_name_var.get()
            self.current_project.matrix_width = int(self.width_var.get())
            self.current_project.matrix_height = int(self.height_var.get())
            self.current_project.output_width = int(self.out_width_var.get())
            self.current_project.output_height = int(self.out_height_var.get())
            self.current_project.pattern = self.pattern_var.get()
            self.current_project.effect = self.effect_var.get()
            self.current_project.palette = self.palette_var.get()
            self.current_project.use_palette = self.use_palette_var.get()
            self.current_project.spacing = float(self.spacing_var.get())
            self.current_project.edge_enhance = self.edge_enhance_var.get()
            self.current_project.noise_reduce = self.noise_reduce_var.get()
            self.current_project.background_color = self.bg_color
            self.current_project.auto_crop = self.auto_crop_var.get()
            self.current_project.face_padding = float(self.face_padding_var.get())

            success = self.project_manager.save_project(
                self.current_project, self.current_image, self.current_result
            )
            if success:
                self.update_status(f"Project '{self.current_project.name}' saved successfully!")
                self.refresh_projects_list()
            else:
                self.update_status("Failed to save project")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save project: {e}")

    def load_project(self):
        projects = self.project_manager.list_projects()
        if not projects:
            messagebox.showinfo("Load Project", "No saved projects found")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Load Project")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Select a project to load:").pack(pady=10)
        listbox = tk.Listbox(dialog, height=10)
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        for project in projects:
            listbox.insert(tk.END, project)

        def load_selected():
            selection = listbox.curselection()
            if selection:
                project_name = projects[selection[0]]
                self._load_project_by_name(project_name)
                dialog.destroy()

        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Load", command=load_selected).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT)

    def _load_project_by_name(self, project_name: str):
        try:
            result = self.project_manager.load_project(project_name)
            if result:
                settings, original_image, result_image = result
                self.project_name_var.set(settings.name)
                self.width_var.set(str(settings.matrix_width))
                self.height_var.set(str(settings.matrix_height))
                self.out_width_var.set(str(settings.output_width))
                self.out_height_var.set(str(settings.output_height))
                self.pattern_var.set(settings.pattern)
                self.effect_var.set(settings.effect)
                self.palette_var.set(settings.palette)
                self.use_palette_var.set(settings.use_palette)
                self.spacing_var.set(str(settings.spacing))
                self.edge_enhance_var.set(settings.edge_enhance)
                self.noise_reduce_var.set(settings.noise_reduce)
                self.auto_crop_var.set(settings.auto_crop)
                self.face_padding_var.set(str(settings.face_padding))
                self.bg_color = settings.background_color

                if original_image:
                    self.current_image = original_image
                    self.undo_manager.add_state(original_image)
                    self.image_info_label.config(
                        text=f"Loaded from project ({original_image.size[0]}x{original_image.size[1]})"
                    )
                    if self.dual_display:
                        self.dual_display.update_left_display(
                            original_image, f"Project: {settings.name}"
                        )
                if result_image:
                    self.current_result = result_image
                    if self.dual_display:
                        self.dual_display.update_right_display(
                            result_image, f"Loaded: {settings.name}"
                        )
                self.current_project = settings
                self.update_status(f"Project '{project_name}' loaded successfully!")
            else:
                messagebox.showerror("Error", f"Failed to load project '{project_name}'")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load project: {e}")

    def new_project(self):
        self.current_project = ProjectSettings("Untitled")
        self.project_name_var.set("Untitled")
        self.width_var.set("45")
        self.height_var.set("19")
        self.out_width_var.set("900")
        self.out_height_var.set("380")
        self.pattern_var.set(DotPattern.CIRCLE.value)
        self.effect_var.set(ArtisticEffect.NONE.value)
        self.palette_var.set("Classic B&W")
        self.use_palette_var.set(False)
        self.spacing_var.set("1.0")
        self.edge_enhance_var.set(False)
        self.noise_reduce_var.set(False)
        self.auto_crop_var.set(True)
        self.face_padding_var.set("0.2")
        self.bg_color = None
        self.current_image = None
        self.current_result = None
        self.undo_manager.clear()
        self.image_info_label.config(text="No image loaded")
        self.update_status("New project created - Ready to start!")

    def refresh_projects_list(self):
        try:
            projects = self.project_manager.list_projects()
            self.projects_listbox.delete(0, tk.END)
            for project in projects:
                self.projects_listbox.insert(tk.END, project)
        except Exception as e:
            self.logger.error(f"Failed to refresh projects list: {e}")

    def load_selected_project(self, event):
        selection = self.projects_listbox.curselection()
        if selection:
            project_name = self.projects_listbox.get(selection[0])
            self._load_project_by_name(project_name)

    # -- Export methods -----------------------------------------------------

    def save_original(self):
        if not self.current_image:
            messagebox.showwarning("Warning", "No original image to save")
            return
        file_path = filedialog.asksaveasfilename(
            title="Save Original Image",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("All files", "*.*")],
        )
        if file_path:
            try:
                self.current_image.save(file_path)
                self.update_status(f"Original image saved: {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save image: {e}")

    def save_result(self):
        if not self.current_result:
            messagebox.showwarning("Warning", "No artwork to save - create art first")
            return
        file_path = filedialog.asksaveasfilename(
            title="Save Artwork",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("All files", "*.*")],
        )
        if file_path:
            try:
                self.current_result.save(file_path)
                self.update_status(f"Artwork saved: {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save artwork: {e}")

    def export_svg(self):
        if not self.current_result:
            messagebox.showwarning("Warning", "No artwork to export - create art first")
            return
        file_path = filedialog.asksaveasfilename(
            title="Export as SVG",
            defaultextension=".svg",
            filetypes=[("SVG files", "*.svg"), ("All files", "*.*")],
        )
        if file_path:
            try:
                circle_data = self.converter.get_circle_data()
                success = AdvancedExporter.export_svg(self.current_result, file_path, circle_data)
                if success:
                    self.update_status(f"SVG exported: {os.path.basename(file_path)}")
                else:
                    messagebox.showerror("Error", "Failed to export SVG")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export SVG: {e}")

    def export_high_res(self):
        if not self.current_result:
            messagebox.showwarning("Warning", "No artwork to export - create art first")
            return
        file_path = filedialog.asksaveasfilename(
            title="Export High-Resolution",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("All files", "*.*")],
        )
        if file_path:
            try:
                success = AdvancedExporter.export_high_resolution(
                    self.current_result, file_path, scale_factor=4
                )
                if success:
                    self.update_status(f"High-res export completed: {os.path.basename(file_path)}")
                else:
                    messagebox.showerror("Error", "Failed to export high-resolution image")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export high-res: {e}")

    def save_animation(self):
        if not self.current_image:
            messagebox.showwarning("Warning", "No image loaded for animation")
            return
        folder_path = filedialog.askdirectory(title="Select folder for animation frames")
        if folder_path:
            try:
                self.update_status("Creating animation frames...")
                for frame in range(24):
                    self.animation_frame = frame
                    result = self.converter.convert_image_advanced(
                        self.current_image,
                        matrix_width=int(self.width_var.get()),
                        matrix_height=int(self.height_var.get()),
                        output_size=(int(self.out_width_var.get()), int(self.out_height_var.get())),
                        pattern=DotPattern(self.pattern_var.get()),
                        circle_spacing=float(self.spacing_var.get()),
                        use_color=self.use_palette_var.get(),
                        color_palette=(
                            ColorPalette.PALETTES.get(self.palette_var.get())
                            if self.use_palette_var.get()
                            else None
                        ),
                        artistic_effect=ArtisticEffect(
                            self.effect_var.get().lower().replace(" ", "_")
                        ),
                        animate=True,
                        animation_frame=frame,
                        edge_enhancement=self.edge_enhance_var.get(),
                        noise_reduction=self.noise_reduce_var.get(),
                        custom_background=self.bg_color,
                    )
                    if result:
                        frame_path = os.path.join(folder_path, f"frame_{frame:03d}.png")
                        result.save(frame_path)
                self.update_status(f"Animation frames saved to {folder_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save animation: {e}")

    # -- Batch methods ------------------------------------------------------

    def select_batch_images(self):
        file_paths = filedialog.askopenfilenames(
            title="Select Images for Batch Processing",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.gif *.tiff *.webp"),
                ("All files", "*.*"),
            ],
        )
        if file_paths:
            self.batch_files = list(file_paths)
            self.batch_files_label.config(text=f"{len(self.batch_files)} files selected")
            self.update_status(f"Selected {len(self.batch_files)} images for batch processing")

    def select_output_folder(self):
        folder_path = filedialog.askdirectory(title="Select Output Folder")
        if folder_path:
            self.batch_output_folder = folder_path
            self.output_folder_label.config(text=f"Output: {folder_path}")
            self.update_status(f"Output folder set: {folder_path}")

    def start_batch_processing(self):
        if not self.batch_files or not self.batch_output_folder:
            messagebox.showwarning("Warning", "Please select images and output folder")
            return

        current_settings = ProjectSettings(
            name="Batch_Process",
            matrix_width=int(self.width_var.get()),
            matrix_height=int(self.height_var.get()),
            output_width=int(self.out_width_var.get()),
            output_height=int(self.out_height_var.get()),
            pattern=self.pattern_var.get(),
            effect=self.effect_var.get(),
            palette=self.palette_var.get(),
            use_palette=self.use_palette_var.get(),
            spacing=float(self.spacing_var.get()),
            edge_enhance=self.edge_enhance_var.get(),
            noise_reduce=self.noise_reduce_var.get(),
            background_color=self.bg_color,
        )

        def update_progress(progress, message):
            self.batch_progress["value"] = progress
            self.batch_status_label.config(text=message)
            self.root.update_idletasks()

        self.batch_processor.progress_callback = update_progress
        self.batch_button.config(state=tk.DISABLED)
        self.cancel_batch_button.config(state=tk.NORMAL)
        self.batch_results_text.delete(1.0, tk.END)

        def process_batch():
            try:
                results = self.batch_processor.process_batch(
                    self.batch_files, current_settings, self.batch_output_folder
                )

                def update_results():
                    self.batch_results_text.insert(tk.END, "Batch processing completed!\n")
                    self.batch_results_text.insert(tk.END, f"Processed: {results['processed']}\n")
                    self.batch_results_text.insert(tk.END, f"Failed: {results['failed']}\n")
                    if results["errors"]:
                        self.batch_results_text.insert(tk.END, "\nErrors:\n")
                        for error in results["errors"][:5]:
                            self.batch_results_text.insert(tk.END, f"- {error}\n")
                    if results["output_files"]:
                        self.batch_results_text.insert(tk.END, "\nOutput files:\n")
                        for fp in results["output_files"][:5]:
                            self.batch_results_text.insert(tk.END, f"- {os.path.basename(fp)}\n")
                    self.batch_button.config(state=tk.NORMAL)
                    self.cancel_batch_button.config(state=tk.DISABLED)
                    self.batch_status_label.config(text="Batch processing completed")
                    self.update_status(
                        f"Batch done: {results['processed']} processed, {results['failed']} failed"
                    )

                self.root.after(0, update_results)
            except Exception as e:
                def show_error():
                    self.batch_results_text.insert(tk.END, f"Batch processing error: {e}\n")
                    self.batch_button.config(state=tk.NORMAL)
                    self.cancel_batch_button.config(state=tk.DISABLED)
                    self.batch_status_label.config(text="Batch processing failed")
                self.root.after(0, show_error)

        processing_thread = threading.Thread(target=process_batch, daemon=True)
        processing_thread.start()

    def cancel_batch_processing(self):
        self.batch_processor.cancel_processing()
        self.batch_button.config(state=tk.NORMAL)
        self.cancel_batch_button.config(state=tk.DISABLED)
        self.batch_status_label.config(text="Batch processing cancelled")
        self.update_status("Batch processing cancelled")

    # -- Gallery methods ----------------------------------------------------

    def refresh_gallery(self):
        try:
            images = self.project_manager.get_gallery_images()
            self.gallery_listbox.delete(0, tk.END)
            for image_path in images:
                mod_time = time.strftime(
                    "%Y-%m-%d %H:%M", time.localtime(image_path.stat().st_mtime)
                )
                self.gallery_listbox.insert(tk.END, f"{image_path.name} - {mod_time}")
        except Exception as e:
            self.logger.error(f"Failed to refresh gallery: {e}")

    def open_gallery_folder(self):
        try:
            gallery_path = self.project_manager.gallery_dir
            if sys.platform == "win32":
                os.startfile(gallery_path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", gallery_path])
            else:
                subprocess.Popen(["xdg-open", gallery_path])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open gallery folder: {e}")

    def open_gallery_item(self, event):
        self.view_gallery_item()

    def view_gallery_item(self):
        selection = self.gallery_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an image to view")
            return
        try:
            images = self.project_manager.get_gallery_images()
            if selection[0] < len(images):
                image_path = images[selection[0]]
                image = Image.open(image_path)

                viewer = tk.Toplevel(self.root)
                viewer.title(f"Gallery Viewer - {image_path.name}")
                viewer.geometry("800x600")

                display_image = image.copy()
                display_image.thumbnail((750, 550), Image.LANCZOS)
                photo = ImageTk.PhotoImage(display_image)

                canvas = tk.Canvas(viewer, bg="black")
                canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                canvas.create_image(400, 300, image=photo)
                canvas.photo = photo

                info_text = (
                    f"{image_path.name} | {image.size[0]}x{image.size[1]} | "
                    f"{image_path.stat().st_size // 1024} KB"
                )
                ttk.Label(viewer, text=info_text).pack(pady=5)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to view image: {e}")

    def choose_background_color(self):
        color = colorchooser.askcolor(title="Choose Background Color")
        if color[0]:
            self.bg_color = tuple(int(c) for c in color[0])
            self.update_status(f"Background color set to {self.bg_color}")

    # -- Animation and undo -------------------------------------------------

    def toggle_animation(self):
        if self.animate_var.get():
            self.animation_active = True
            self.start_animation()
            self.update_status("Animation effects enabled - Watch the magic!")
        else:
            self.animation_active = False
            if self.animation_job:
                self.root.after_cancel(self.animation_job)
                self.animation_job = None
            self.update_status("Animation effects disabled")

    def start_animation(self):
        if self.animation_active and self.current_image:
            self.animation_frame += 1
            self.convert_image(animate=True)
            self.animation_job = self.root.after(150, self.start_animation)

    def undo(self):
        if self.undo_manager.can_undo():
            image = self.undo_manager.undo()
            if image:
                self.current_image = image
                self.update_status("Undone - Previous state restored")
                if self.dual_display and self.current_image:
                    self.dual_display.update_left_display(self.current_image, "Undone")
        else:
            self.update_status("Nothing to undo")

    def redo(self):
        if self.undo_manager.can_redo():
            image = self.undo_manager.redo()
            if image:
                self.current_image = image
                self.update_status("Redone - State restored")
                if self.dual_display and self.current_image:
                    self.dual_display.update_left_display(self.current_image, "Redone")
        else:
            self.update_status("Nothing to redo")

    def on_closing(self):
        self.animation_active = False
        self.auto_convert_active = False
        if hasattr(self, "camera"):
            self.camera.stop_camera()
        self.processor.shutdown()
        self.root.destroy()

    def run(self):
        self.logger.info("Starting Master Dot Matrix Art Studio")
        self.root.mainloop()
