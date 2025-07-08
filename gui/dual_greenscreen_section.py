import tkinter as tk
from tkinter import filedialog
import os
import cv2
import numpy as np
from PIL import Image, ImageTk, ImageDraw, ImageFont
from utils.green_screen_detection import create_green_screen_mask
from utils.text_rendering import smart_text_wrap, render_text_with_emoji_multiline

class DualGreenScreenSection:
    """Dual Green Screen mode section of the GUI."""
    
    def __init__(self, parent_frame, update_preview_callback):
        self.parent_frame = parent_frame
        self.update_preview_callback = update_preview_callback
        self.background_image_path = ""
        self.preview_label = None
        self.is_gif_template = False
        self.is_video_template = False
        self.gif_frames = []
        self.gif_durations = []
        self.current_frame_index = 0
        self.animation_job = None
        self.create_dual_greenscreen_section()
    
    def create_dual_greenscreen_section(self):
        """Create dual green screen mode section."""
        self.dual_greenscreen_frame = tk.LabelFrame(
            self.parent_frame, 
            text="🎬🎬 Dual Green Screen Template", 
            font=("Arial", 11, "bold"), 
            bg="#f0f0f0", 
            fg="#2c3e50", 
            padx=10, 
            pady=8
        )
        self.dual_greenscreen_frame.pack(pady=10, padx=20, fill=tk.X)
        
        # Info section
        info_label = tk.Label(
            self.dual_greenscreen_frame, 
            text="Dual Green Screen Mode: Combines videos from two folders with green screen template processing",
            font=("Arial", 9), 
            fg="#7f8c8d", 
            bg="#f0f0f0", 
            wraplength=600
        )
        info_label.pack(pady=5)
        
        # Template selection
        self.background_label = tk.Label(
            self.dual_greenscreen_frame, 
            text="No template selected", 
            font=("Arial", 10), 
            bg="#f0f0f0", 
            fg="#7f8c8d"
        )
        self.background_label.pack(pady=5)
        
        select_btn = tk.Button(
            self.dual_greenscreen_frame, 
            text="📁 Select Template (Image/GIF/Video)", 
            command=self.select_background_template, 
            font=("Arial", 10, "bold"), 
            bg="#27ae60", 
            fg="white", 
            activebackground="#229954"
        )
        select_btn.pack(pady=5)
        
        self.preview_text = tk.Label(
            self.dual_greenscreen_frame, 
            text="", 
            font=("Arial", 9), 
            fg="#7f8c8d", 
            bg="#f0f0f0"
        )
        self.preview_text.pack(pady=2)
        
        # Preview
        self.create_preview()
    
    def create_preview(self):
        """Create preview area."""
        preview_frame = tk.Frame(self.dual_greenscreen_frame, bg="#e0e0e0", relief=tk.SUNKEN, bd=1)
        preview_frame.pack(pady=8)
        
        preview_title = tk.Label(
            preview_frame, 
            text="📱 Dual Template Preview (9:16)", 
            font=("Arial", 10, "bold"), 
            bg="#e0e0e0"
        )
        preview_title.pack(pady=5)
        
        self.preview_label = tk.Label(
            preview_frame, 
            text="Upload template to see preview\nSupports: JPG, PNG, BMP, GIF, MP4, AVI, MOV", 
            bg="#ffffff", 
            fg="#95a5a6", 
            width=22, 
            height=14,
            relief=tk.SUNKEN, 
            bd=1
        )
        self.preview_label.pack(pady=8, padx=8)
    
    def select_background_template(self):
        """Select background template (image, GIF, or video)."""
        path = filedialog.askopenfilename(
            title="Select Template with Green Screen (Image, GIF, or Video)",
            filetypes=[
                ("All Supported", "*.jpg *.jpeg *.png *.bmp *.gif *.mp4 *.avi *.mov"),
                ("Image Files", "*.jpg *.jpeg *.png *.bmp"),
                ("Animated GIF", "*.gif"),
                ("Video Files", "*.mp4 *.avi *.mov"),
                ("All Files", "*.*")
            ]
        )
        if path:
            self.background_image_path = path
            filename = os.path.basename(self.background_image_path)
            self.background_label.config(text=f"Template: {filename}")
            
            # Stop any existing animation
            self.stop_animation()
            
            # Check template type
            self.is_gif_template = path.lower().endswith('.gif')
            self.is_video_template = path.lower().endswith(('.mp4', '.avi', '.mov'))
            
            try:
                if self.is_gif_template:
                    self.load_gif_template(path)
                elif self.is_video_template:
                    self.load_video_template(path)
                else:
                    self.load_image_template(path)
                
                self.update_preview_callback()
            except Exception as e:
                self.preview_text.config(text=f"Error loading template: {str(e)}")
                print(f"Error loading template: {e}")
    
    def load_gif_template(self, gif_path):
        """Load GIF template and extract frames."""
        try:
            from utils.gif_processing import extract_gif_frames
            
            print(f"🎬 Loading GIF template: {os.path.basename(gif_path)}")
            
            frames, durations = extract_gif_frames(gif_path)
            if frames and durations:
                self.gif_frames = frames
                self.gif_durations = durations
                self.current_frame_index = 0
                
                print(f"✅ GIF template loaded: {len(frames)} frames")
                
                # Test green screen detection on first frame
                first_frame = frames[0]
                resized_frame = cv2.resize(first_frame, (200, 150))
                mask = create_green_screen_mask(resized_frame)
                green_pixels = np.sum(mask > 0)
                
                self.preview_text.config(
                    text=f"🎬 Animated GIF Template: {len(frames)} frames, Green screen area: {green_pixels} pixels"
                )
                
                # Start animated preview
                self.start_animated_preview()
                
            else:
                self.preview_text.config(text="❌ Error: Could not extract frames from GIF")
                self.is_gif_template = False
                
        except Exception as e:
            self.preview_text.config(text=f"❌ Error loading GIF: {str(e)}")
            self.is_gif_template = False
            print(f"Error loading GIF template: {e}")
    
    def load_video_template(self, video_path):
        """Load video template and extract first frame."""
        try:
            print(f"🎬 Loading Video template: {os.path.basename(video_path)}")
            
            cap = cv2.VideoCapture(video_path)
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                # Store first frame for preview
                self.gif_frames = [frame]  # Use same structure as GIF
                self.gif_durations = [100]
                self.current_frame_index = 0
                
                # Test green screen detection
                resized_frame = cv2.resize(frame, (200, 150))
                mask = create_green_screen_mask(resized_frame)
                green_pixels = np.sum(mask > 0)
                
                self.preview_text.config(
                    text=f"🎥 Video Template: Green screen area detected: {green_pixels} pixels"
                )
                
                # Update preview with first frame
                self.update_preview_frame({'enabled': False})
                
            else:
                self.preview_text.config(text="❌ Error: Could not load video")
                self.is_video_template = False
                
        except Exception as e:
            self.preview_text.config(text=f"❌ Error loading video: {str(e)}")
            self.is_video_template = False
            print(f"Error loading video template: {e}")
    
    def load_image_template(self, image_path):
        """Load static image template."""
        try:
            img = cv2.imread(image_path)
            if img is not None:
                img_resized = cv2.resize(img, (200, 150))
                mask = create_green_screen_mask(img_resized)
                green_pixels = np.sum(mask > 0)
                self.preview_text.config(text=f"🖼️ Static Template: Green screen area detected: {green_pixels} pixels")
                
                # Store for preview
                self.gif_frames = [img]
                self.gif_durations = [100]
                self.current_frame_index = 0
                
                # Update preview
                self.update_preview_frame({'enabled': False})
            else:
                self.preview_text.config(text="❌ Error: Could not load image")
        except Exception as e:
            self.preview_text.config(text=f"❌ Error loading image: {str(e)}")
            print(f"Error loading image template: {e}")
    
    def get_current_template_frame(self):
        """Get current template frame."""
        if self.gif_frames:
            return self.gif_frames[self.current_frame_index]
        elif not self.is_gif_template and not self.is_video_template and self.background_image_path:
            img = cv2.imread(self.background_image_path)
            return img
        return None
    
    def advance_gif_frame(self):
        """Advance to next frame (for animated preview)."""
        if self.gif_frames and len(self.gif_frames) > 1:
            self.current_frame_index = (self.current_frame_index + 1) % len(self.gif_frames)
    
    def start_animated_preview(self):
        """Start animated preview for GIF templates."""
        if self.is_gif_template and len(self.gif_frames) > 1:
            self.animate_preview()
    
    def stop_animation(self):
        """Stop animated preview."""
        if self.animation_job:
            self.dual_greenscreen_frame.after_cancel(self.animation_job)
            self.animation_job = None
    
    def animate_preview(self):
        """Animate the preview for GIF templates."""
        if not self.is_gif_template or not self.gif_frames:
            return
        
        try:
            # Update preview with current frame
            text_settings = {'enabled': False}  # Simple preview without text
            self.update_preview_frame(text_settings)
            
            # Advance to next frame
            self.advance_gif_frame()
            
            # Schedule next frame
            current_duration = self.gif_durations[self.current_frame_index] if self.gif_durations else 100
            frame_delay = max(100, current_duration)  # Minimum 100ms for preview
            
            self.animation_job = self.dual_greenscreen_frame.after(frame_delay, self.animate_preview)
            
        except Exception as e:
            print(f"Animation error: {e}")
            self.stop_animation()
    
    def update_preview(self, text_settings):
        """Update preview with current settings."""
        if not self.background_image_path:
            return
        
        # For GIF templates, this will be called from outside
        # For static templates, update immediately
        if not self.is_gif_template:
            self.update_preview_frame(text_settings)
    
    def update_preview_frame(self, text_settings):
        """Update preview frame (used by both static and animated previews)."""
        try:
            # Get current template frame
            img = self.get_current_template_frame()
            if img is None:
                self.preview_label.config(text="❌ Error loading template")
                return
            
            preview_width = 160
            preview_height = 285
            
            h, w = img.shape[:2]
            target_ratio = preview_width / preview_height
            current_ratio = w / h
            
            # Crop to fit aspect ratio
            if current_ratio > target_ratio:
                new_width = int(h * target_ratio)
                start_x = (w - new_width) // 2
                img = img[:, start_x:start_x + new_width]
            else:
                new_height = int(w / target_ratio)
                start_y = (h - new_height) // 2
                img = img[start_y:start_y + new_height, :]
            
            img = cv2.resize(img, (preview_width, preview_height))
            pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
            draw = ImageDraw.Draw(pil_img)
            
            # Draw video area (green screen detection)
            mask = create_green_screen_mask(img)
            if np.sum(mask) > 0:
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                if contours:
                    largest_contour = max(contours, key=cv2.contourArea)
                    x, y, w, h = cv2.boundingRect(largest_contour)
                    
                    if w > 5 and h > 5:
                        draw.rectangle([x, y, x+w, y+h], outline="red", width=2)
                        try:
                            small_font = ImageFont.truetype("arial.ttf", 10)
                        except:
                            small_font = ImageFont.load_default()
                        
                        text_bbox = draw.textbbox((0, 0), "DUAL VIDEO", font=small_font)
                        text_width = text_bbox[2] - text_bbox[0]
                        text_height = text_bbox[3] - text_bbox[1]
                        text_x = x + (w - text_width) // 2
                        text_y = y + (h - text_height) // 2
                        draw.text((text_x, text_y), "DUAL VIDEO", fill="red", font=small_font)
            
            # Add text overlay preview
            if text_settings and text_settings['enabled']:
                try:
                    preview_font_size = max(8, int(text_settings['size'] * 0.15))
                    
                    try:
                        font = ImageFont.truetype("arial.ttf", preview_font_size)
                    except:
                        font = ImageFont.load_default()
                except:
                    font = ImageFont.load_default()
                
                sample_text = f"Sample Text ({text_settings['font']})"
                max_width = pil_img.width - 10
                lines = smart_text_wrap(sample_text, draw, font, max_width, emoji_size=15)
                
                line_height = preview_font_size + 3
                total_height = len(lines) * line_height
                base_y = int((text_settings['y_position'] / 100) * (pil_img.height - total_height - 10))
                base_y = max(5, min(base_y, pil_img.height - total_height - 5))
                
                rendered_lines = render_text_with_emoji_multiline(
                    draw, lines, font, pil_img.width, pil_img.height, 
                    base_y, emoji_size=15, line_spacing=3
                )
                
                # Get text color from settings (default to black if not specified)
                text_color = text_settings.get('color', '#000000')
                
                for line_data in rendered_lines:
                    for item_type, item, x_offset in line_data['items']:
                        if item_type == 'emoji':
                            emoji_y = line_data['y'] + (preview_font_size - line_data['emoji_size']) // 2
                            pil_img.paste(item, (line_data['x_start'] + x_offset, emoji_y), item)
                        elif item_type == 'text':
                            draw.text((line_data['x_start'] + x_offset, line_data['y']), 
                                     item, fill=text_color, font=font)
            
            # Add template type indicator
            try:
                indicator_font = ImageFont.truetype("arial.ttf", 8)
            except:
                indicator_font = ImageFont.load_default()
            
            if self.is_gif_template:
                frame_text = f"🎬 GIF Frame {self.current_frame_index + 1}/{len(self.gif_frames)}"
                draw.text((5, preview_height - 15), frame_text, fill="blue", font=indicator_font)
            elif self.is_video_template:
                draw.text((5, preview_height - 15), "🎥 Video Template", fill="purple", font=indicator_font)
            else:
                draw.text((5, preview_height - 15), "🖼️ Static Image", fill="green", font=indicator_font)
            
            photo = ImageTk.PhotoImage(pil_img)
            self.preview_label.config(image=photo, text="", width=preview_width, height=preview_height)
            self.preview_label.image = photo
            
        except Exception as e:
            print(f"Preview error: {e}")
            self.preview_label.config(text=f"❌ Error: {str(e)}")
    
    def get_template_info(self):
        """Get template information for processing."""
        return {
            'path': self.background_image_path,
            'is_gif': self.is_gif_template,
            'is_video': self.is_video_template,
            'frames': self.gif_frames if (self.is_gif_template or self.is_video_template) else None,
            'durations': self.gif_durations if (self.is_gif_template or self.is_video_template) else None,
            'frame_count': len(self.gif_frames) if (self.is_gif_template or self.is_video_template) else 1
        }
    
    def pack_forget(self):
        """Hide dual greenscreen section."""
        self.stop_animation()
        if hasattr(self, 'dual_greenscreen_frame'):
            self.dual_greenscreen_frame.pack_forget()
    
    def pack(self, **kwargs):
        """Show dual greenscreen section."""
        if hasattr(self, 'dual_greenscreen_frame'):
            self.dual_greenscreen_frame.pack(**kwargs)
            # Restart animation if it's a GIF
            if self.is_gif_template and len(self.gif_frames) > 1:
                self.start_animated_preview()