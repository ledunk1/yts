import tkinter as tk
from tkinter import filedialog
import os
from utils.file_operations import get_audio_files

class DualAudioSection:
    """Enhanced audio section for dual green screen mode."""
    
    def __init__(self, parent_frame):
        self.parent_frame = parent_frame
        self.audio_folder1_path = ""
        self.audio_folder2_path = ""
        self.create_dual_audio_section()
    
    def create_dual_audio_section(self):
        """Create dual audio section."""
        self.dual_audio_frame = tk.LabelFrame(
            self.parent_frame, 
            text="🎵🎵 Enhanced Audio Settings", 
            font=("Arial", 11, "bold"), 
            bg="#f0f0f0", 
            fg="#2c3e50", 
            padx=10, 
            pady=8
        )
        self.dual_audio_frame.pack(pady=10, padx=20, fill=tk.X)
        
        # Audio enable checkbox
        self.audio_enabled = tk.BooleanVar()
        audio_checkbox = tk.Checkbutton(
            self.dual_audio_frame, 
            text="🎵 Enable Background Music", 
            variable=self.audio_enabled, 
            font=("Arial", 10), 
            bg="#f0f0f0",
            command=self.on_audio_enable_change
        )
        audio_checkbox.pack(pady=5)
        
        # Dual audio enable checkbox
        self.dual_audio_enabled = tk.BooleanVar()
        dual_audio_checkbox = tk.Checkbutton(
            self.dual_audio_frame, 
            text="🎭 Enable Dual Audio Mixing (Original + Background)", 
            variable=self.dual_audio_enabled, 
            font=("Arial", 10), 
            bg="#f0f0f0",
            command=self.on_dual_audio_enable_change
        )
        dual_audio_checkbox.pack(pady=5)
        
        # Audio source selection
        audio_source_frame = tk.Frame(self.dual_audio_frame, bg="#f0f0f0")
        audio_source_frame.pack(pady=8, fill=tk.X)
        
        audio_source_title = tk.Label(
            audio_source_frame, 
            text="🎵 Background Music Source Selection", 
            font=("Arial", 10, "bold"), 
            bg="#f0f0f0", 
            fg="#2c3e50"
        )
        audio_source_title.pack(pady=(0, 5))
        
        audio_source_info = tk.Label(
            audio_source_frame, 
            text="Choose which folder's audio files to use for background music", 
            font=("Arial", 9), 
            fg="#7f8c8d", 
            bg="#f0f0f0"
        )
        audio_source_info.pack(pady=(0, 5))
        
        # Audio source radio buttons
        self.audio_source_var = tk.StringVar(value="folder1")
        
        audio_radio_frame = tk.Frame(audio_source_frame, bg="#f0f0f0")
        audio_radio_frame.pack(pady=5)
        
        audio_folder1_radio = tk.Radiobutton(
            audio_radio_frame, 
            text="📁 Use background music from Video Folder 1", 
            variable=self.audio_source_var, 
            value="folder1",
            font=("Arial", 9), 
            bg="#f0f0f0",
            activebackground="#f0f0f0",
            command=self.on_audio_source_change
        )
        audio_folder1_radio.pack(side=tk.LEFT, padx=10)
        
        audio_folder2_radio = tk.Radiobutton(
            audio_radio_frame, 
            text="📁 Use background music from Video Folder 2", 
            variable=self.audio_source_var, 
            value="folder2",
            font=("Arial", 9), 
            bg="#f0f0f0",
            activebackground="#f0f0f0",
            command=self.on_audio_source_change
        )
        audio_folder2_radio.pack(side=tk.LEFT, padx=10)
        
        # Audio Folder 1 Selection
        self.audio_folder1_section = tk.Frame(self.dual_audio_frame, bg="#f0f0f0")
        self.audio_folder1_section.pack(pady=8, fill=tk.X)
        
        audio_folder1_title = tk.Label(
            self.audio_folder1_section, 
            text="🎵 Audio Folder 1", 
            font=("Arial", 10, "bold"), 
            bg="#f0f0f0", 
            fg="#2c3e50"
        )
        audio_folder1_title.pack(pady=(0, 5))
        
        self.audio_folder1_label = tk.Label(
            self.audio_folder1_section, 
            text="No audio folder selected", 
            font=("Arial", 10), 
            bg="#f0f0f0", 
            fg="#7f8c8d"
        )
        self.audio_folder1_label.pack(pady=3)
        
        select_audio_folder1_btn = tk.Button(
            self.audio_folder1_section, 
            text="🎵 Select Audio Folder 1", 
            command=self.select_audio_folder1, 
            font=("Arial", 10, "bold"), 
            bg="#e67e22", 
            fg="white", 
            activebackground="#d35400"
        )
        select_audio_folder1_btn.pack(pady=5)
        
        self.audio_folder1_info_label = tk.Label(
            self.audio_folder1_section, 
            text="", 
            font=("Arial", 9), 
            fg="#7f8c8d", 
            bg="#f0f0f0"
        )
        self.audio_folder1_info_label.pack(pady=2)
        
        # Audio Folder 2 Selection
        self.audio_folder2_section = tk.Frame(self.dual_audio_frame, bg="#f0f0f0")
        self.audio_folder2_section.pack(pady=8, fill=tk.X)
        
        audio_folder2_title = tk.Label(
            self.audio_folder2_section, 
            text="🎵 Audio Folder 2", 
            font=("Arial", 10, "bold"), 
            bg="#f0f0f0", 
            fg="#2c3e50"
        )
        audio_folder2_title.pack(pady=(0, 5))
        
        self.audio_folder2_label = tk.Label(
            self.audio_folder2_section, 
            text="No audio folder selected", 
            font=("Arial", 10), 
            bg="#f0f0f0", 
            fg="#7f8c8d"
        )
        self.audio_folder2_label.pack(pady=3)
        
        select_audio_folder2_btn = tk.Button(
            self.audio_folder2_section, 
            text="🎵 Select Audio Folder 2", 
            command=self.select_audio_folder2, 
            font=("Arial", 10, "bold"), 
            bg="#e67e22", 
            fg="white", 
            activebackground="#d35400"
        )
        select_audio_folder2_btn.pack(pady=5)
        
        self.audio_folder2_info_label = tk.Label(
            self.audio_folder2_section, 
            text="", 
            font=("Arial", 9), 
            fg="#7f8c8d", 
            bg="#f0f0f0"
        )
        self.audio_folder2_info_label.pack(pady=2)
        
        # Volume controls
        self.create_volume_controls()
        
        # Initially disable audio sections
        self.update_audio_sections_state()
    
    def create_volume_controls(self):
        """Create volume control sliders."""
        volume_frame = tk.Frame(self.dual_audio_frame, bg="#f0f0f0")
        volume_frame.pack(pady=8, fill=tk.X)
        
        # Original audio volume (for dual audio mode)
        self.original_volume_frame = tk.Frame(volume_frame, bg="#f0f0f0")
        self.original_volume_frame.pack(pady=5, fill=tk.X)
        
        original_volume_label = tk.Label(
            self.original_volume_frame, 
            text="🎤 Original Audio Volume:", 
            font=("Arial", 10), 
            bg="#f0f0f0"
        )
        original_volume_label.pack(side=tk.LEFT)
        
        self.original_volume = tk.IntVar(value=100)
        original_volume_scale = tk.Scale(
            self.original_volume_frame, 
            from_=0, 
            to=100, 
            orient=tk.HORIZONTAL, 
            variable=self.original_volume, 
            bg="#f0f0f0",
            length=200
        )
        original_volume_scale.pack(side=tk.LEFT, padx=10)
        
        original_volume_percent = tk.Label(
            self.original_volume_frame, 
            textvariable=self.original_volume, 
            font=("Arial", 10), 
            bg="#f0f0f0"
        )
        original_volume_percent.pack(side=tk.LEFT)
        
        original_percent_label = tk.Label(
            self.original_volume_frame, 
            text="%", 
            font=("Arial", 10), 
            bg="#f0f0f0"
        )
        original_percent_label.pack(side=tk.LEFT)
        
        # Background audio volume
        background_volume_frame = tk.Frame(volume_frame, bg="#f0f0f0")
        background_volume_frame.pack(pady=5, fill=tk.X)
        
        background_volume_label = tk.Label(
            background_volume_frame, 
            text="🎵 Background Music Volume:", 
            font=("Arial", 10), 
            bg="#f0f0f0"
        )
        background_volume_label.pack(side=tk.LEFT)
        
        self.background_volume = tk.IntVar(value=50)
        background_volume_scale = tk.Scale(
            background_volume_frame, 
            from_=0, 
            to=100, 
            orient=tk.HORIZONTAL, 
            variable=self.background_volume, 
            bg="#f0f0f0",
            length=200
        )
        background_volume_scale.pack(side=tk.LEFT, padx=10)
        
        background_volume_percent = tk.Label(
            background_volume_frame, 
            textvariable=self.background_volume, 
            font=("Arial", 10), 
            bg="#f0f0f0"
        )
        background_volume_percent.pack(side=tk.LEFT)
        
        background_percent_label = tk.Label(
            background_volume_frame, 
            text="%", 
            font=("Arial", 10), 
            bg="#f0f0f0"
        )
        background_percent_label.pack(side=tk.LEFT)
    
    def select_audio_folder1(self):
        """Select audio folder 1."""
        folder_path = filedialog.askdirectory(title="Select Audio Folder 1")
        if folder_path:
            self.audio_folder1_path = folder_path
            folder_name = os.path.basename(folder_path)
            self.audio_folder1_label.config(text=f"Audio Folder 1: {folder_name}")
            
            # Count audio files
            try:
                audio_files = get_audio_files(folder_path)
                self.audio_folder1_info_label.config(
                    text=f"Found: {len(audio_files)} audio files"
                )
            except Exception as e:
                self.audio_folder1_info_label.config(text=f"Error scanning folder: {str(e)}")
    
    def select_audio_folder2(self):
        """Select audio folder 2."""
        folder_path = filedialog.askdirectory(title="Select Audio Folder 2")
        if folder_path:
            self.audio_folder2_path = folder_path
            folder_name = os.path.basename(folder_path)
            self.audio_folder2_label.config(text=f"Audio Folder 2: {folder_name}")
            
            # Count audio files
            try:
                audio_files = get_audio_files(folder_path)
                self.audio_folder2_info_label.config(
                    text=f"Found: {len(audio_files)} audio files"
                )
            except Exception as e:
                self.audio_folder2_info_label.config(text=f"Error scanning folder: {str(e)}")
    
    def on_audio_enable_change(self):
        """Handle audio enable change."""
        self.update_audio_sections_state()
    
    def on_dual_audio_enable_change(self):
        """Handle dual audio enable change."""
        self.update_audio_sections_state()
    
    def on_audio_source_change(self):
        """Handle audio source change."""
        audio_source = self.audio_source_var.get()
        print(f"🎵 Audio source changed to: {audio_source}")
    
    def update_audio_sections_state(self):
        """Update the state of audio sections based on checkboxes."""
        audio_enabled = self.audio_enabled.get()
        dual_audio_enabled = self.dual_audio_enabled.get()
        
        # Show/hide original volume control based on dual audio mode
        if dual_audio_enabled:
            self.original_volume_frame.pack(pady=5, fill=tk.X)
        else:
            self.original_volume_frame.pack_forget()
        
        # Enable/disable audio folder sections
        if audio_enabled or dual_audio_enabled:
            # Enable audio folder sections
            for widget in self.audio_folder1_section.winfo_children():
                if isinstance(widget, (tk.Button, tk.Label)):
                    widget.config(state=tk.NORMAL)
            
            for widget in self.audio_folder2_section.winfo_children():
                if isinstance(widget, (tk.Button, tk.Label)):
                    widget.config(state=tk.NORMAL)
        else:
            # Disable audio folder sections
            for widget in self.audio_folder1_section.winfo_children():
                if isinstance(widget, tk.Button):
                    widget.config(state=tk.DISABLED)
            
            for widget in self.audio_folder2_section.winfo_children():
                if isinstance(widget, tk.Button):
                    widget.config(state=tk.DISABLED)
    
    def get_audio_settings(self):
        """Get audio settings for dual mode."""
        audio_source = self.audio_source_var.get()
        
        # Determine which folder to use based on source selection
        if audio_source == "folder1":
            folder_path = self.audio_folder1_path
        else:
            folder_path = self.audio_folder2_path
        
        return {
            'enabled': self.audio_enabled.get(),
            'dual_audio_enabled': self.dual_audio_enabled.get(),
            'folder_path': folder_path,
            'audio_source': audio_source,
            'folder1_path': self.audio_folder1_path,
            'folder2_path': self.audio_folder2_path,
            'original_volume': self.original_volume.get(),
            'background_volume': self.background_volume.get()
        }
    
    def pack_forget(self):
        """Hide dual audio section."""
        if hasattr(self, 'dual_audio_frame'):
            self.dual_audio_frame.pack_forget()
    
    def pack(self, **kwargs):
        """Show dual audio section."""
        if hasattr(self, 'dual_audio_frame'):
            self.dual_audio_frame.pack(**kwargs)