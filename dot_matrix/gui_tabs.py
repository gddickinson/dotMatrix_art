"""Tab setup methods for MasterDotMatrixStudio (mixin pattern)."""

import tkinter as tk
from tkinter import ttk

from dot_matrix.models import DotPattern, ArtisticEffect, ColorPalette


class TabSetupMixin:
    """Mixin providing GUI tab setup methods for MasterDotMatrixStudio."""

    def setup_project_tab(self):
        """Setup project management tab."""
        project_tab = ttk.Frame(self.notebook)
        self.notebook.add(project_tab, text="Project")

        info_frame = ttk.LabelFrame(project_tab, text="Current Project", padding="10")
        info_frame.pack(fill=tk.X, pady=(10, 10))

        self.project_name_var = tk.StringVar(value="Untitled")
        ttk.Label(info_frame, text="Project Name:").pack(anchor=tk.W)
        ttk.Entry(info_frame, textvariable=self.project_name_var, font=("Arial", 12)).pack(
            fill=tk.X, pady=(5, 10)
        )

        actions_frame = ttk.Frame(info_frame)
        actions_frame.pack(fill=tk.X)

        ttk.Button(actions_frame, text="Save Project", command=self.save_project).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        ttk.Button(actions_frame, text="Load Project", command=self.load_project).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        ttk.Button(actions_frame, text="New Project", command=self.new_project).pack(
            side=tk.LEFT, padx=(0, 5)
        )

        recent_frame = ttk.LabelFrame(project_tab, text="Recent Projects", padding="10")
        recent_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.projects_listbox = tk.Listbox(recent_frame, height=8, font=("Arial", 10))
        self.projects_listbox.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.projects_listbox.bind("<Double-1>", self.load_selected_project)

        ttk.Button(recent_frame, text="Refresh Projects", command=self.refresh_projects_list).pack()

        history_frame = ttk.LabelFrame(project_tab, text="History", padding="10")
        history_frame.pack(fill=tk.X, pady=(0, 10))

        history_buttons = ttk.Frame(history_frame)
        history_buttons.pack(fill=tk.X)

        self.undo_button = ttk.Button(history_buttons, text="Undo (Ctrl+Z)", command=self.undo)
        self.undo_button.pack(side=tk.LEFT, padx=(0, 5))

        self.redo_button = ttk.Button(history_buttons, text="Redo (Ctrl+Y)", command=self.redo)
        self.redo_button.pack(side=tk.LEFT)

        self.refresh_projects_list()

    def setup_input_tab(self):
        """Setup input and capture tab."""
        input_tab = ttk.Frame(self.notebook)
        self.notebook.add(input_tab, text="Input")

        display_frame = ttk.LabelFrame(input_tab, text="Art Studio Display", padding="10")
        display_frame.pack(fill=tk.X, pady=(10, 10))

        ttk.Button(
            display_frame,
            text="Open Dual Display Studio (F11)",
            command=self.open_dual_display,
            style="Accent.TButton",
        ).pack(pady=5)

        source_frame = ttk.LabelFrame(input_tab, text="Input Sources", padding="10")
        source_frame.pack(fill=tk.X, pady=(0, 10))

        source_row1 = ttk.Frame(source_frame)
        source_row1.pack(fill=tk.X, pady=(0, 5))

        ttk.Button(source_row1, text="Load Image", command=self.load_image).pack(
            side=tk.LEFT, padx=(0, 10)
        )
        ttk.Button(source_row1, text="Generate Test Face", command=self.generate_test_face).pack(
            side=tk.LEFT, padx=(0, 10)
        )
        ttk.Button(source_row1, text="Extract Palette", command=self.extract_image_palette).pack(
            side=tk.LEFT
        )

        source_row2 = ttk.Frame(source_frame)
        source_row2.pack(fill=tk.X, pady=(5, 0))

        self.camera_button = ttk.Button(source_row2, text="Start Camera", command=self.toggle_camera)
        self.camera_button.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(source_row2, text="Capture Frame", command=self.capture_camera_frame).pack(
            side=tk.LEFT, padx=(0, 10)
        )

        face_frame = ttk.LabelFrame(input_tab, text="Face Detection", padding="10")
        face_frame.pack(fill=tk.X, pady=(0, 10))

        face_row1 = ttk.Frame(face_frame)
        face_row1.pack(fill=tk.X, pady=(0, 5))

        ttk.Button(face_row1, text="Detect Faces", command=self.detect_faces).pack(
            side=tk.LEFT, padx=(0, 10)
        )
        ttk.Button(face_row1, text="Auto-Crop Face", command=self.auto_crop_face).pack(side=tk.LEFT)

        face_row2 = ttk.Frame(face_frame)
        face_row2.pack(fill=tk.X)

        ttk.Label(face_row2, text="Crop Padding:").pack(side=tk.LEFT)
        self.face_padding_var = tk.StringVar(value="0.2")
        ttk.Entry(face_row2, textvariable=self.face_padding_var, width=8).pack(
            side=tk.LEFT, padx=(5, 15)
        )

        self.auto_crop_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(face_row2, text="Auto-crop from camera", variable=self.auto_crop_var).pack(
            side=tk.LEFT
        )

        self.image_info_label = ttk.Label(
            input_tab, text="No image loaded", font=("Arial", 10, "italic")
        )
        self.image_info_label.pack(pady=10)

    def setup_artistic_tab(self):
        """Setup artistic effects and patterns tab."""
        artistic_tab = ttk.Frame(self.notebook)
        self.notebook.add(artistic_tab, text="Artistic")

        pattern_frame = ttk.LabelFrame(artistic_tab, text="Dot Patterns", padding="10")
        pattern_frame.pack(fill=tk.X, pady=(10, 10))

        self.pattern_var = tk.StringVar(value=DotPattern.CIRCLE.value)

        pattern_row1 = ttk.Frame(pattern_frame)
        pattern_row1.pack(fill=tk.X, pady=(0, 5))
        for pattern in [DotPattern.CIRCLE, DotPattern.SQUARE, DotPattern.DIAMOND, DotPattern.HEXAGON]:
            ttk.Radiobutton(
                pattern_row1, text=pattern.value.title(), variable=self.pattern_var, value=pattern.value
            ).pack(side=tk.LEFT, padx=(0, 10))

        pattern_row2 = ttk.Frame(pattern_frame)
        pattern_row2.pack(fill=tk.X, pady=(0, 5))
        for pattern in [DotPattern.STAR, DotPattern.CROSS, DotPattern.HEART, DotPattern.TRIANGLE]:
            ttk.Radiobutton(
                pattern_row2, text=pattern.value.title(), variable=self.pattern_var, value=pattern.value
            ).pack(side=tk.LEFT, padx=(0, 10))

        pattern_row3 = ttk.Frame(pattern_frame)
        pattern_row3.pack(fill=tk.X)
        for pattern in [DotPattern.HALFTONE, DotPattern.STIPPLE, DotPattern.ASCII_DOT]:
            ttk.Radiobutton(
                pattern_row3,
                text=pattern.value.replace("_", " ").title(),
                variable=self.pattern_var,
                value=pattern.value,
            ).pack(side=tk.LEFT, padx=(0, 10))

        color_frame = ttk.LabelFrame(artistic_tab, text="Color Palettes", padding="10")
        color_frame.pack(fill=tk.X, pady=(0, 10))

        color_row1 = ttk.Frame(color_frame)
        color_row1.pack(fill=tk.X, pady=(0, 5))

        self.palette_var = tk.StringVar(value="Classic B&W")
        self.palette_combo = ttk.Combobox(
            color_row1,
            textvariable=self.palette_var,
            values=list(ColorPalette.PALETTES.keys()),
            state="readonly",
            width=20,
        )
        self.palette_combo.pack(side=tk.LEFT, padx=(0, 10))

        self.use_palette_var = tk.BooleanVar()
        ttk.Checkbutton(color_row1, text="Use Palette", variable=self.use_palette_var).pack(
            side=tk.LEFT, padx=(0, 10)
        )

        ttk.Button(color_row1, text="Custom BG", command=self.choose_background_color).pack(
            side=tk.LEFT
        )

        effects_frame = ttk.LabelFrame(artistic_tab, text="Artistic Effects", padding="10")
        effects_frame.pack(fill=tk.X, pady=(0, 10))

        self.effect_var = tk.StringVar(value=ArtisticEffect.NONE.value)
        effect_combo = ttk.Combobox(
            effects_frame,
            textvariable=self.effect_var,
            values=[e.value.replace("_", " ").title() for e in ArtisticEffect],
            state="readonly",
            width=20,
        )
        effect_combo.pack(side=tk.LEFT, padx=(0, 10))

        enhance_frame = ttk.LabelFrame(artistic_tab, text="Enhancement", padding="10")
        enhance_frame.pack(fill=tk.X, pady=(0, 10))

        enhance_row = ttk.Frame(enhance_frame)
        enhance_row.pack(fill=tk.X)

        self.edge_enhance_var = tk.BooleanVar()
        ttk.Checkbutton(enhance_row, text="Edge Enhancement", variable=self.edge_enhance_var).pack(
            side=tk.LEFT, padx=(0, 15)
        )

        self.noise_reduce_var = tk.BooleanVar()
        ttk.Checkbutton(enhance_row, text="Noise Reduction", variable=self.noise_reduce_var).pack(
            side=tk.LEFT
        )

        convert_frame = ttk.Frame(artistic_tab)
        convert_frame.pack(pady=20)

        ttk.Button(
            convert_frame, text="Create Art (F5)", command=self.convert_image, style="Accent.TButton"
        ).pack()

        self.bg_color = None

    def setup_advanced_tab(self):
        """Setup advanced settings and animation tab."""
        advanced_tab = ttk.Frame(self.notebook)
        self.notebook.add(advanced_tab, text="Advanced")

        matrix_frame = ttk.LabelFrame(advanced_tab, text="Matrix Configuration", padding="10")
        matrix_frame.pack(fill=tk.X, pady=(10, 10))

        matrix_row1 = ttk.Frame(matrix_frame)
        matrix_row1.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(matrix_row1, text="Matrix Size:").pack(side=tk.LEFT)
        self.width_var = tk.StringVar(value="45")
        ttk.Entry(matrix_row1, textvariable=self.width_var, width=8).pack(side=tk.LEFT, padx=(5, 5))
        ttk.Label(matrix_row1, text="x").pack(side=tk.LEFT)
        self.height_var = tk.StringVar(value="19")
        ttk.Entry(matrix_row1, textvariable=self.height_var, width=8).pack(
            side=tk.LEFT, padx=(5, 15)
        )

        ttk.Label(matrix_row1, text="Output Size:").pack(side=tk.LEFT)
        self.out_width_var = tk.StringVar(value="900")
        ttk.Entry(matrix_row1, textvariable=self.out_width_var, width=8).pack(
            side=tk.LEFT, padx=(5, 5)
        )
        ttk.Label(matrix_row1, text="x").pack(side=tk.LEFT)
        self.out_height_var = tk.StringVar(value="380")
        ttk.Entry(matrix_row1, textvariable=self.out_height_var, width=8).pack(
            side=tk.LEFT, padx=(5, 0)
        )

        matrix_row2 = ttk.Frame(matrix_frame)
        matrix_row2.pack(fill=tk.X)

        ttk.Label(matrix_row2, text="Spacing:").pack(side=tk.LEFT)
        self.spacing_var = tk.StringVar(value="1.0")
        spacing_scale = ttk.Scale(
            matrix_row2, from_=0.1, to=2.0, variable=self.spacing_var, orient=tk.HORIZONTAL
        )
        spacing_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 10))
        ttk.Label(matrix_row2, textvariable=self.spacing_var, width=5).pack(side=tk.LEFT)

        anim_frame = ttk.LabelFrame(advanced_tab, text="Animation", padding="10")
        anim_frame.pack(fill=tk.X, pady=(0, 10))

        anim_row = ttk.Frame(anim_frame)
        anim_row.pack(fill=tk.X)

        self.animate_var = tk.BooleanVar()
        ttk.Checkbutton(
            anim_row, text="Animated Effects", variable=self.animate_var, command=self.toggle_animation
        ).pack(side=tk.LEFT, padx=(0, 15))

        live_frame = ttk.LabelFrame(advanced_tab, text="Live Processing", padding="10")
        live_frame.pack(fill=tk.X, pady=(0, 10))

        self.auto_convert_var_adv = tk.BooleanVar()
        ttk.Checkbutton(
            live_frame,
            text="Auto-Convert Camera Feed",
            variable=self.auto_convert_var_adv,
            command=self.toggle_auto_convert,
        ).pack(anchor=tk.W)

        export_frame = ttk.LabelFrame(advanced_tab, text="Export Options", padding="10")
        export_frame.pack(fill=tk.X, pady=(0, 10))

        export_row1 = ttk.Frame(export_frame)
        export_row1.pack(fill=tk.X, pady=(0, 5))

        ttk.Button(export_row1, text="Save Original", command=self.save_original).pack(
            side=tk.LEFT, padx=(0, 10)
        )
        ttk.Button(export_row1, text="Save Artwork", command=self.save_result).pack(
            side=tk.LEFT, padx=(0, 10)
        )
        ttk.Button(export_row1, text="Export SVG", command=self.export_svg).pack(side=tk.LEFT)

        export_row2 = ttk.Frame(export_frame)
        export_row2.pack(fill=tk.X)

        ttk.Button(export_row2, text="High-Res Print", command=self.export_high_res).pack(
            side=tk.LEFT, padx=(0, 10)
        )
        ttk.Button(export_row2, text="Save Animation", command=self.save_animation).pack(
            side=tk.LEFT
        )

    def setup_batch_tab(self):
        """Setup batch processing tab."""
        batch_tab = ttk.Frame(self.notebook)
        self.notebook.add(batch_tab, text="Batch")

        input_frame = ttk.LabelFrame(batch_tab, text="Batch Input", padding="10")
        input_frame.pack(fill=tk.X, pady=(10, 10))

        input_row = ttk.Frame(input_frame)
        input_row.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(input_row, text="Select Images", command=self.select_batch_images).pack(
            side=tk.LEFT, padx=(0, 10)
        )
        ttk.Button(input_row, text="Select Output Folder", command=self.select_output_folder).pack(
            side=tk.LEFT
        )

        self.batch_files_label = ttk.Label(
            input_frame, text="No files selected", font=("Arial", 10, "italic")
        )
        self.batch_files_label.pack(anchor=tk.W)

        self.output_folder_label = ttk.Label(
            input_frame, text="No output folder selected", font=("Arial", 10, "italic")
        )
        self.output_folder_label.pack(anchor=tk.W)

        settings_frame = ttk.LabelFrame(batch_tab, text="Batch Settings", padding="10")
        settings_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(settings_frame, text="Use current artistic settings for all images").pack(
            anchor=tk.W
        )

        process_frame = ttk.LabelFrame(batch_tab, text="Processing", padding="10")
        process_frame.pack(fill=tk.X, pady=(0, 10))

        process_row = ttk.Frame(process_frame)
        process_row.pack(fill=tk.X, pady=(0, 10))

        self.batch_button = ttk.Button(
            process_row, text="Start Batch Processing", command=self.start_batch_processing
        )
        self.batch_button.pack(side=tk.LEFT, padx=(0, 10))

        self.cancel_batch_button = ttk.Button(
            process_row, text="Cancel", command=self.cancel_batch_processing, state=tk.DISABLED
        )
        self.cancel_batch_button.pack(side=tk.LEFT)

        self.batch_progress = ttk.Progressbar(process_frame, mode="determinate")
        self.batch_progress.pack(fill=tk.X, pady=(0, 5))

        self.batch_status_label = ttk.Label(process_frame, text="Ready for batch processing")
        self.batch_status_label.pack(anchor=tk.W)

        results_frame = ttk.LabelFrame(batch_tab, text="Results", padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.batch_results_text = tk.Text(results_frame, height=6, font=("Consolas", 9))
        self.batch_results_text.pack(fill=tk.BOTH, expand=True)

        self.batch_files = []
        self.batch_output_folder = ""

    def setup_gallery_tab(self):
        """Setup gallery and project showcase tab."""
        gallery_tab = ttk.Frame(self.notebook)
        self.notebook.add(gallery_tab, text="Gallery")

        controls_frame = ttk.Frame(gallery_tab)
        controls_frame.pack(fill=tk.X, pady=(10, 10))

        ttk.Button(controls_frame, text="Refresh Gallery", command=self.refresh_gallery).pack(
            side=tk.LEFT, padx=(0, 10)
        )
        ttk.Button(controls_frame, text="Open Gallery Folder", command=self.open_gallery_folder).pack(
            side=tk.LEFT
        )

        gallery_frame = ttk.LabelFrame(gallery_tab, text="Recent Artworks", padding="10")
        gallery_frame.pack(fill=tk.BOTH, expand=True)

        self.gallery_listbox = tk.Listbox(gallery_frame, height=15, font=("Arial", 10))
        self.gallery_listbox.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.gallery_listbox.bind("<Double-1>", self.open_gallery_item)

        ttk.Button(gallery_frame, text="View Selected", command=self.view_gallery_item).pack()

        self.refresh_gallery()
