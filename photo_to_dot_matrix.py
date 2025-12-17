import numpy as np
from PIL import Image, ImageDraw, ImageTk
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import logging
import os
from typing import Optional, Tuple
import math

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dot_matrix_converter.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FaceGenerator:
    """Generate synthetic face images for testing."""
    
    @staticmethod
    def create_test_face(width: int = 200, height: int = 240) -> Image.Image:
        """
        Create a synthetic face image for testing purposes.
        
        Args:
            width: Image width in pixels
            height: Image height in pixels
            
        Returns:
            PIL Image of synthetic face
        """
        logger.info(f"Generating test face image ({width}x{height})")
        
        # Create base image with skin tone
        img = Image.new('RGB', (width, height), (245, 220, 177))
        draw = ImageDraw.Draw(img)
        
        # Face outline (oval)
        face_margin = 20
        draw.ellipse([face_margin, face_margin, width-face_margin, height-face_margin], 
                    fill=(235, 210, 167), outline=(200, 175, 132), width=2)
        
        # Hair
        hair_height = height // 3
        draw.ellipse([face_margin-10, face_margin-10, width-face_margin+10, hair_height], 
                    fill=(101, 67, 33))
        
        # Eyes
        eye_y = height // 3
        eye_width = width // 8
        eye_height = height // 15
        left_eye_x = width // 3 - eye_width
        right_eye_x = 2 * width // 3
        
        # Eye whites
        draw.ellipse([left_eye_x, eye_y, left_eye_x + eye_width*2, eye_y + eye_height], 
                    fill=(255, 255, 255), outline=(150, 150, 150))
        draw.ellipse([right_eye_x, eye_y, right_eye_x + eye_width*2, eye_y + eye_height], 
                    fill=(255, 255, 255), outline=(150, 150, 150))
        
        # Pupils
        pupil_size = eye_width // 2
        draw.ellipse([left_eye_x + eye_width//2, eye_y + eye_height//4, 
                     left_eye_x + eye_width//2 + pupil_size, eye_y + eye_height//4 + pupil_size], 
                    fill=(50, 50, 50))
        draw.ellipse([right_eye_x + eye_width//2, eye_y + eye_height//4, 
                     right_eye_x + eye_width//2 + pupil_size, eye_y + eye_height//4 + pupil_size], 
                    fill=(50, 50, 50))
        
        # Eyebrows
        brow_y = eye_y - eye_height
        draw.ellipse([left_eye_x, brow_y, left_eye_x + eye_width*2, brow_y + eye_height//2], 
                    fill=(80, 50, 20))
        draw.ellipse([right_eye_x, brow_y, right_eye_x + eye_width*2, brow_y + eye_height//2], 
                    fill=(80, 50, 20))
        
        # Nose
        nose_x = width // 2
        nose_y = height // 2
        nose_width = width // 20
        nose_height = height // 8
        draw.ellipse([nose_x - nose_width, nose_y, nose_x + nose_width, nose_y + nose_height], 
                    fill=(225, 200, 157))
        
        # Mouth
        mouth_y = 2 * height // 3
        mouth_width = width // 6
        mouth_height = height // 20
        draw.ellipse([width//2 - mouth_width, mouth_y, width//2 + mouth_width, mouth_y + mouth_height], 
                    fill=(180, 100, 100))
        
        # Add some shading for depth
        # Left side shadow
        for i in range(10):
            alpha = 255 - (i * 20)
            shadow_color = (215 - i*5, 190 - i*5, 147 - i*3)
            draw.line([(face_margin + i, face_margin + 20), 
                      (face_margin + i, height - face_margin - 20)], 
                     fill=shadow_color, width=1)
        
        logger.info("Test face generated successfully")
        return img

class DotMatrixConverter:
    """Core dot matrix conversion functionality."""
    
    def __init__(self):
        self.logger = logger
        
    def convert_image(self, image: Image.Image, matrix_width: int = 45, 
                     matrix_height: int = 19, output_size: Tuple[int, int] = (900, 380),
                     circle_spacing: float = 1.0, use_color: bool = False) -> Optional[Image.Image]:
        """
        Convert an image to dot matrix format.
        
        Args:
            image: PIL Image to convert
            matrix_width: Number of dots horizontally
            matrix_height: Number of dots vertically
            output_size: Output image size (width, height)
            circle_spacing: Space between circles (1.0 = touching)
            use_color: Whether to preserve original colors
            
        Returns:
            Converted dot matrix image or None if failed
        """
        try:
            self.logger.info(f"Converting image to {matrix_width}x{matrix_height} dot matrix")
            
            # Process image
            if use_color:
                img_resized = image.resize((matrix_width, matrix_height), Image.LANCZOS)
                img_gray = img_resized.convert('L')
                pixel_brightness = np.array(img_gray)
                pixel_colors = np.array(img_resized)
            else:
                img_gray = image.convert('L')
                img_resized = img_gray.resize((matrix_width, matrix_height), Image.LANCZOS)
                pixel_brightness = np.array(img_resized)
                pixel_colors = None
            
            # Create output
            output_img = Image.new('RGB', output_size, 'white')
            draw = ImageDraw.Draw(output_img)
            
            # Calculate dimensions
            cell_width = output_size[0] / matrix_width
            cell_height = output_size[1] / matrix_height
            max_radius = min(cell_width, cell_height) / 2 * circle_spacing
            
            circles_drawn = 0
            
            # Draw circles
            for y in range(matrix_height):
                for x in range(matrix_width):
                    brightness = pixel_brightness[y, x]
                    radius = max_radius * (1 - brightness / 255.0)
                    
                    if radius > 0.5:
                        # Determine color
                        if use_color and pixel_colors is not None:
                            if len(pixel_colors.shape) == 3:
                                color = tuple(pixel_colors[y, x])
                            else:
                                gray_val = pixel_colors[y, x]
                                color = (gray_val, gray_val, gray_val)
                        else:
                            color = 'black'
                        
                        # Draw circle
                        center_x = (x + 0.5) * cell_width
                        center_y = (y + 0.5) * cell_height
                        
                        left = center_x - radius
                        top = center_y - radius
                        right = center_x + radius
                        bottom = center_y + radius
                        
                        draw.ellipse([left, top, right, bottom], fill=color)
                        circles_drawn += 1
            
            self.logger.info(f"Conversion complete. Drew {circles_drawn} circles")
            return output_img
            
        except Exception as e:
            self.logger.error(f"Error during conversion: {str(e)}")
            return None

class DotMatrixGUI:
    """Main GUI application."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Dot Matrix Image Converter")
        self.root.geometry("800x700")
        
        # Initialize components
        self.converter = DotMatrixConverter()
        self.face_generator = FaceGenerator()
        self.current_image = None
        self.current_result = None
        
        # Setup GUI
        self.setup_gui()
        self.logger = logger
        
        self.logger.info("GUI initialized")
    
    def setup_gui(self):
        """Create the GUI layout."""
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Dot Matrix Image Converter", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Input section
        input_frame = ttk.LabelFrame(main_frame, text="Input Image", padding="10")
        input_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(input_frame, text="Load Image File", 
                  command=self.load_image).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(input_frame, text="Generate Test Face", 
                  command=self.generate_test_face).grid(row=0, column=1, padx=(0, 10))
        
        self.image_info_label = ttk.Label(input_frame, text="No image loaded")
        self.image_info_label.grid(row=0, column=2, sticky=tk.W)
        
        # Settings section
        settings_frame = ttk.LabelFrame(main_frame, text="Conversion Settings", padding="10")
        settings_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Matrix dimensions
        ttk.Label(settings_frame, text="Matrix Width:").grid(row=0, column=0, sticky=tk.W)
        self.width_var = tk.StringVar(value="45")
        ttk.Entry(settings_frame, textvariable=self.width_var, width=8).grid(row=0, column=1, padx=(5, 15))
        
        ttk.Label(settings_frame, text="Matrix Height:").grid(row=0, column=2, sticky=tk.W)
        self.height_var = tk.StringVar(value="19")
        ttk.Entry(settings_frame, textvariable=self.height_var, width=8).grid(row=0, column=3, padx=(5, 15))
        
        # Output size
        ttk.Label(settings_frame, text="Output Width:").grid(row=1, column=0, sticky=tk.W)
        self.out_width_var = tk.StringVar(value="900")
        ttk.Entry(settings_frame, textvariable=self.out_width_var, width=8).grid(row=1, column=1, padx=(5, 15))
        
        ttk.Label(settings_frame, text="Output Height:").grid(row=1, column=2, sticky=tk.W)
        self.out_height_var = tk.StringVar(value="380")
        ttk.Entry(settings_frame, textvariable=self.out_height_var, width=8).grid(row=1, column=3, padx=(5, 15))
        
        # Options
        self.color_var = tk.BooleanVar()
        ttk.Checkbutton(settings_frame, text="Preserve Colors", 
                       variable=self.color_var).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))
        
        ttk.Label(settings_frame, text="Circle Spacing:").grid(row=2, column=2, sticky=tk.W, pady=(10, 0))
        self.spacing_var = tk.StringVar(value="1.0")
        ttk.Entry(settings_frame, textvariable=self.spacing_var, width=8).grid(row=2, column=3, padx=(5, 0), pady=(10, 0))
        
        # Convert button
        convert_frame = ttk.Frame(main_frame)
        convert_frame.grid(row=3, column=0, columnspan=3, pady=20)
        
        ttk.Button(convert_frame, text="Convert to Dot Matrix", 
                  command=self.convert_image, style='Accent.TButton').pack()
        
        # Preview section
        preview_frame = ttk.LabelFrame(main_frame, text="Preview", padding="10")
        preview_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Canvas for image preview
        self.canvas = tk.Canvas(preview_frame, bg='white', height=300)
        self.canvas.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbars for canvas
        h_scroll = ttk.Scrollbar(preview_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        h_scroll.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E))
        v_scroll = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        v_scroll.grid(row=0, column=3, sticky=(tk.N, tk.S))
        
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.canvas.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)
        
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)
        
        # Save button
        save_frame = ttk.Frame(main_frame)
        save_frame.grid(row=5, column=0, columnspan=3, pady=10)
        
        ttk.Button(save_frame, text="Save Result", 
                  command=self.save_result).pack()
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
    
    def update_status(self, message: str):
        """Update status bar message."""
        self.status_var.set(message)
        self.root.update_idletasks()
        self.logger.info(f"Status: {message}")
    
    def load_image(self):
        """Load an image file."""
        file_path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.gif *.tiff"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            try:
                self.current_image = Image.open(file_path)
                self.image_info_label.config(text=f"Loaded: {os.path.basename(file_path)} "
                                           f"({self.current_image.size[0]}x{self.current_image.size[1]})")
                self.update_status("Image loaded successfully")
                self.show_preview(self.current_image)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load image: {str(e)}")
                self.logger.error(f"Failed to load image {file_path}: {str(e)}")
    
    def generate_test_face(self):
        """Generate a test face image."""
        try:
            self.current_image = self.face_generator.create_test_face()
            self.image_info_label.config(text="Generated test face (200x240)")
            self.update_status("Test face generated")
            self.show_preview(self.current_image)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate test face: {str(e)}")
            self.logger.error(f"Failed to generate test face: {str(e)}")
    
    def convert_image(self):
        """Convert current image to dot matrix."""
        if not self.current_image:
            messagebox.showwarning("Warning", "Please load an image first")
            return
        
        try:
            # Get settings
            matrix_width = int(self.width_var.get())
            matrix_height = int(self.height_var.get())
            output_width = int(self.out_width_var.get())
            output_height = int(self.out_height_var.get())
            circle_spacing = float(self.spacing_var.get())
            use_color = self.color_var.get()
            
            self.update_status("Converting image...")
            
            # Convert
            self.current_result = self.converter.convert_image(
                self.current_image,
                matrix_width=matrix_width,
                matrix_height=matrix_height,
                output_size=(output_width, output_height),
                circle_spacing=circle_spacing,
                use_color=use_color
            )
            
            if self.current_result:
                self.show_preview(self.current_result)
                self.update_status("Conversion completed successfully")
            else:
                messagebox.showerror("Error", "Conversion failed")
                
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid settings: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Conversion failed: {str(e)}")
            self.logger.error(f"Conversion failed: {str(e)}")
    
    def show_preview(self, image: Image.Image):
        """Show image in preview canvas."""
        try:
            # Resize for preview if too large
            preview_image = image.copy()
            max_size = (600, 400)
            
            if preview_image.size[0] > max_size[0] or preview_image.size[1] > max_size[1]:
                preview_image.thumbnail(max_size, Image.LANCZOS)
            
            # Convert to PhotoImage
            self.photo = ImageTk.PhotoImage(preview_image)
            
            # Clear canvas and add image
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            
        except Exception as e:
            self.logger.error(f"Failed to show preview: {str(e)}")
    
    def save_result(self):
        """Save the converted result."""
        if not self.current_result:
            messagebox.showwarning("Warning", "No result to save. Please convert an image first.")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Save Dot Matrix Image",
            defaultextension=".png",
            filetypes=[
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            try:
                self.current_result.save(file_path)
                self.update_status(f"Saved: {os.path.basename(file_path)}")
                messagebox.showinfo("Success", "Image saved successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save image: {str(e)}")
                self.logger.error(f"Failed to save image: {str(e)}")
    
    def run(self):
        """Start the GUI application."""
        self.logger.info("Starting GUI application")
        self.root.mainloop()

def main():
    """Main entry point."""
    try:
        app = DotMatrixGUI()
        app.run()
    except Exception as e:
        logger.error(f"Application failed to start: {str(e)}")
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()