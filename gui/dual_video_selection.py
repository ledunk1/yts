import tkinter as tk
from tkinter import filedialog
import os
from utils.file_operations import get_all_media_files

class DualVideoSelection:
    """Dual video selection section for dual green screen mode."""
    
    def __init__(self, parent_frame):
        self.parent_frame = parent_frame
        self.folder1_path = ""
        self.folder2_path = ""
        self.text_source = "folder1"  # Default to folder 1
        self.audio_source = "folder1"  # Default to folder 1
        self.create_dual_video_selection()
    
    def create_dual_video_selection(self):
        """Create dual video selection section."""
        self.dual_video_frame = tk.LabelFrame(
            self.parent_frame, 
            text="📁📁 Dual Media Selection (Video/GIF/Image)", 
            font=("Arial", 11, "bold"), 
            bg="#f0f0f0", 
            fg="#2c3e50", 
            padx=10, 
            pady=8
        )
        self.dual_video_frame.pack(pady=10, padx=20, fill=tk.X)
        
        # Info
        info_label = tk.Label(
            self.dual_video_frame, 
            text="Select two folders containing videos/GIFs/images for dual green screen processing",
            font=("Arial", 9), 
            fg="#7f8c8d", 
            bg="#f0f0f0", 
            wraplength=600
        )
        info_label.pack(pady=5)
        
        # Folder 1 Selection
        folder1_section = tk.Frame(self.dual_video_frame, bg="#f0f0f0")
        folder1_section.pack(pady=8, fill=tk.X)
        
        folder1_title = tk.Label(
            folder1_section, 
            text="📁 Media Folder 1", 
            font=("Arial", 10, "bold"), 
            bg="#f0f0f0", 
            fg="#2c3e50"
        )
        folder1_title.pack(pady=(0, 5))
        
        self.folder1_label = tk.Label(
            folder1_section, 
            text="No folder selected", 
            font=("Arial", 10), 
            bg="#f0f0f0", 
            fg="#7f8c8d"
        )
        self.folder1_label.pack(pady=3)
        
        select_folder1_btn = tk.Button(
            folder1_section, 
            text="📂 Select Media Folder 1", 
            command=self.select_folder1, 
            font=("Arial", 10, "bold"), 
            bg="#3498db", 
            fg="white", 
            activebackground="#2980b9"
        )
        select_folder1_btn.pack(pady=5)
        
        self.folder1_info_label = tk.Label(
            folder1_section, 
            text="", 
            font=("Arial", 9), 
            fg="#7f8c8d", 
            bg="#f0f0f0"
        )
        self.folder1_info_label.pack(pady=2)
        
        # Folder 2 Selection
        folder2_section = tk.Frame(self.dual_video_frame, bg="#f0f0f0")
        folder2_section.pack(pady=8, fill=tk.X)
        
        folder2_title = tk.Label(
            folder2_section, 
            text="📁 Media Folder 2", 
            font=("Arial", 10, "bold"), 
            bg="#f0f0f0", 
            fg="#2c3e50"
        )
        folder2_title.pack(pady=(0, 5))
        
        self.folder2_label = tk.Label(
            folder2_section, 
            text="No folder selected", 
            font=("Arial", 10), 
            bg="#f0f0f0", 
            fg="#7f8c8d"
        )
        self.folder2_label.pack(pady=3)
        
        select_folder2_btn = tk.Button(
            folder2_section, 
            text="📂 Select Media Folder 2", 
            command=self.select_folder2, 
            font=("Arial", 10, "bold"), 
            bg="#9b59b6", 
            fg="white", 
            activebackground="#8e44ad"
        )
        select_folder2_btn.pack(pady=5)
        
        self.folder2_info_label = tk.Label(
            folder2_section, 
            text="", 
            font=("Arial", 9), 
            fg="#7f8c8d", 
            bg="#f0f0f0"
        )
        self.folder2_info_label.pack(pady=2)
        
        # Text Source Selection
        text_source_section = tk.Frame(self.dual_video_frame, bg="#f0f0f0")
        text_source_section.pack(pady=8, fill=tk.X)
        
        text_source_title = tk.Label(
            text_source_section, 
            text="📝 Text Source Selection", 
            font=("Arial", 10, "bold"), 
            bg="#f0f0f0", 
            fg="#2c3e50"
        )
        text_source_title.pack(pady=(0, 5))
        
        # Text source radio buttons
        self.text_source_var = tk.StringVar(value="folder1")
        
        text_radio_frame = tk.Frame(text_source_section, bg="#f0f0f0")
        text_radio_frame.pack(pady=5)
        
        text_folder1_radio = tk.Radiobutton(
            text_radio_frame, 
            text="📁 Use text from Folder 1", 
            variable=self.text_source_var, 
            value="folder1",
            font=("Arial", 9), 
            bg="#f0f0f0",
            activebackground="#f0f0f0",
            command=self.on_text_source_change
        )
        text_folder1_radio.pack(side=tk.LEFT, padx=10)
        
        text_folder2_radio = tk.Radiobutton(
            text_radio_frame, 
            text="📁 Use text from Folder 2", 
            variable=self.text_source_var, 
            value="folder2",
            font=("Arial", 9), 
            bg="#f0f0f0",
            activebackground="#f0f0f0",
            command=self.on_text_source_change
        )
        text_folder2_radio.pack(side=tk.LEFT, padx=10)
    
    def select_folder1(self):
        """Select folder 1 for videos/GIFs/images."""
        folder_path = filedialog.askdirectory(title="Select Media Folder 1 (Video/GIF/Image)")
        if folder_path:
            self.folder1_path = folder_path
            folder_name = os.path.basename(folder_path)
            self.folder1_label.config(text=f"Folder 1: {folder_name}")
            
            # Count files
            try:
                media_files = get_all_media_files(folder_path)
                video_count = sum(1 for f in media_files if not f.lower().endswith('.gif'))
                gif_count = sum(1 for f in media_files if f.lower().endswith('.gif'))
                image_count = sum(1 for f in media_files if self.is_image_file(f))
                
                self.folder1_info_label.config(
                    text=f"Found: {video_count} videos, {gif_count} GIFs, {image_count} images"
                )
            except Exception as e:
                self.folder1_info_label.config(text=f"Error scanning folder: {str(e)}")
    
    def select_folder2(self):
        """Select folder 2 for videos/GIFs/images."""
        folder_path = filedialog.askdirectory(title="Select Media Folder 2 (Video/GIF/Image)")
        if folder_path:
            self.folder2_path = folder_path
            folder_name = os.path.basename(folder_path)
            self.folder2_label.config(text=f"Folder 2: {folder_name}")
            
            # Count files
            try:
                media_files = get_all_media_files(folder_path)
                video_count = sum(1 for f in media_files if not f.lower().endswith('.gif'))
                gif_count = sum(1 for f in media_files if f.lower().endswith('.gif'))
                image_count = sum(1 for f in media_files if self.is_image_file(f))
                
                self.folder2_info_label.config(
                    text=f"Found: {video_count} videos, {gif_count} GIFs, {image_count} images"
                )
            except Exception as e:
                self.folder2_info_label.config(text=f"Error scanning folder: {str(e)}")
    
    def is_image_file(self, file_name):
        """Check if file is an image."""
        image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp')
        return file_name.lower().endswith(image_extensions)
    
    def on_text_source_change(self):
        """Handle text source selection change."""
        self.text_source = self.text_source_var.get()
        print(f"📝 Text source changed to: {self.text_source}")
    
    def get_folder_paths(self):
        """Get both folder paths."""
        return {
            'folder1': self.folder1_path,
            'folder2': self.folder2_path
        }
    
    def get_text_source(self):
        """Get selected text source."""
        return self.text_source
    
    def get_files_to_process(self):
        """Get all media files from both folders for processing."""
        files_to_process = []
        
        # Add files from folder 1
        if self.folder1_path:
            try:
                media_files = get_all_media_files(self.folder1_path)
                for file_name in media_files:
                    files_to_process.append((self.folder1_path, file_name, "folder1"))
            except Exception as e:
                print(f"Error getting files from folder 1: {e}")
        
        # Add files from folder 2
        if self.folder2_path:
            try:
                media_files = get_all_media_files(self.folder2_path)
                for file_name in media_files:
                    files_to_process.append((self.folder2_path, file_name, "folder2"))
            except Exception as e:
                print(f"Error getting files from folder 2: {e}")
        
        return files_to_process
    
    def pack_forget(self):
        """Hide dual video selection section."""
        if hasattr(self, 'dual_video_frame'):
            self.dual_video_frame.pack_forget()
    
    def pack(self, **kwargs):
        """Show dual video selection section."""
        if hasattr(self, 'dual_video_frame'):
            self.dual_video_frame.pack(**kwargs)