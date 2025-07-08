"""
Video Processor Modes - Specific processing modes (Narasi, Dual, etc.)
"""

import os
from utils.file_operations import get_all_media_files, is_gif_file, is_image_file
from utils.gif_processing import process_gif_greenscreen, process_gif_blur
from utils.narasi_processing import process_narasi_mode
from utils.dual_greenscreen_processing import (
    process_dual_greenscreen_video, 
    process_dual_greenscreen_gif,
    process_dual_greenscreen_image,
    get_template_for_processing,
    process_dual_greenscreen_video_auto
)
from utils.green_screen_detection import create_green_screen_mask
from utils.dual_greenscreen_detection import detect_dual_green_screen_areas
import cv2

class VideoProcessorModes:
    """Handles different processing modes."""
    
    def __init__(self, core_processor, gui_manager=None):
        self.core = core_processor
        self.gui_manager = gui_manager
        self.progress_callback = None  # Will be set by threading manager
    
    def process_narasi_mode(self, settings):
        """Process narasi mode."""
        print("🎙️ Starting Narasi Mode processing...")
        
        folder_path = settings['folder_path']
        template_info = settings['template_info']
        narasi_settings = settings['narasi_settings']
        text_settings = settings['text_settings']
        output_settings = settings['output_settings']
        gpu_settings = settings['gpu_settings']
        
        # Validation
        if not folder_path:
            print("❌ No video folder selected")
            return False
        
        if not template_info['path']:
            print("❌ No template selected")
            return False
        
        if not narasi_settings.get('audio_folder_path'):
            print("❌ No audio folder selected for narasi mode")
            return False
        
        # Determine output folder
        if output_settings['custom_enabled'] and output_settings['custom_folder']:
            output_folder = output_settings['custom_folder']
        else:
            output_folder = folder_path
        
        # Create output subfolder
        from utils.file_operations import create_output_folder
        output_folder = create_output_folder(output_folder, "narasi_output")
        
        # Process narasi mode with bulk processing
        try:
            from utils.narasi_processing import process_narasi_mode_bulk
            
            success = process_narasi_mode_bulk(
                folder_path,
                narasi_settings['audio_folder_path'],
                template_info['path'],
                output_folder,
                text_settings,
                gpu_settings,
                audio_mode=narasi_settings.get('audio_mode', 'narasi_only'),
                narasi_volume=narasi_settings.get('narasi_volume', 100),
                original_volume=narasi_settings.get('original_volume', 30),
                progress_callback=self.progress_callback
            )
            
            if success:
                print(f"✅ Narasi mode bulk processing completed successfully!")
                print(f"📁 Output folder: {output_folder}")
                return True
            else:
                print(f"❌ Narasi mode bulk processing failed")
                return False
                
        except Exception as e:
            print(f"❌ Narasi mode bulk processing error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def process_dual_greenscreen_mode(self, settings):
        """Process dual green screen mode."""
        print("🎬🎬 Starting Dual Green Screen Mode processing...")
        
        folder_paths = settings['folder_paths']
        template_info = settings['template_info']
        text_settings = settings['text_settings']
        audio_settings = settings['audio_settings']
        output_settings = settings['output_settings']
        gpu_settings = settings['gpu_settings']
        
        # Validation
        if not folder_paths['folder1'] or not folder_paths['folder2']:
            print("❌ Both video folders must be selected")
            return False
        
        if not template_info['path']:
            print("❌ No template selected")
            return False
        
        # Get files from both folders
        try:
            # Get template and create mask
            # Check if template has dual green screen areas
            template_path = template_info['path']
            template = get_template_for_processing(template_path)
            template_resized = cv2.resize(template, (1080, 1920))
            
            # Detect dual green screen areas
            dual_areas = detect_dual_green_screen_areas(template_resized)
            
            if dual_areas is not None:
                print("🎬🎬 Auto-detected dual green screen template!")
                return self._process_dual_auto_mode(settings, dual_areas)
            else:
                print("🎬 Single green screen template detected, using legacy mode")
                template_mask = create_green_screen_mask(template_resized)
                return self._process_dual_legacy_mode(settings, template_resized, template_mask)
            
        except Exception as e:
            print(f"❌ Dual Green Screen mode error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _process_dual_auto_mode(self, settings, dual_areas):
        """Process dual green screen with auto-detected areas."""
        print("🎬🎬 Processing with auto-detected dual green screen areas...")
        
        folder_paths = settings['folder_paths']
        template_info = settings['template_info']
        text_settings = settings['text_settings']
        audio_settings = settings['audio_settings']
        output_settings = settings['output_settings']
        gpu_settings = settings['gpu_settings']
        
        # Get files from both folders
        from utils.file_operations import get_all_media_files
        
        folder1_files = get_all_media_files(folder_paths['folder1'])
        folder2_files = get_all_media_files(folder_paths['folder2'])
        
        if not folder1_files or not folder2_files:
            print("❌ Both folders must contain media files")
            return False
        
        print(f"📹 Folder 1: {len(folder1_files)} files")
        print(f"📹 Folder 2: {len(folder2_files)} files")
        
        # Determine output folder
        if output_settings['custom_enabled'] and output_settings['custom_folder']:
            output_folder = output_settings['custom_folder']
        else:
            output_folder = folder_paths['folder1']
        
        from utils.file_operations import create_output_folder
        output_folder = create_output_folder(output_folder, "dual_auto_greenscreen_output")
        
        # Process pairs of videos
        successful_count = 0
        max_files = max(len(folder1_files), len(folder2_files))
        
        for i in range(max_files):
            if self.progress_callback:
                overall_progress = (i / max_files) * 100
                self.progress_callback(
                    overall_progress, 
                    f"Processing pair {i+1}/{max_files}"
                )
            
            # Get files (cycle through if one folder has fewer files)
            file1 = folder1_files[i % len(folder1_files)]
            file2 = folder2_files[i % len(folder2_files)]
            
            file1_path = os.path.join(folder_paths['folder1'], file1)
            file2_path = os.path.join(folder_paths['folder2'], file2)
            
            # Create output filename
            base_name1 = os.path.splitext(file1)[0]
            base_name2 = os.path.splitext(file2)[0]
            output_name = f"dual_auto_{base_name1}_{base_name2}.mp4"
            output_path = os.path.join(output_folder, output_name)
            
            try:
                # Process both videos together
                success = process_dual_greenscreen_video_auto(
                    file1_path, file2_path, template_info['path'],
                    output_path, text_settings, audio_settings, gpu_settings
                )
                
                if success:
                    successful_count += 1
                    print(f"✅ Processed pair: {file1} + {file2}")
                else:
                    print(f"❌ Failed pair: {file1} + {file2}")
            
            except Exception as e:
                print(f"❌ Error processing pair {file1} + {file2}: {e}")
                continue
        
        print(f"🎬🎬 Dual Auto Green Screen processing completed!")
        print(f"✅ Successfully processed: {successful_count}/{max_files} pairs")
        print(f"📁 Output folder: {output_folder}")
        
        return successful_count > 0
    
    def _process_dual_legacy_mode(self, settings, template, template_mask):
        """Process dual green screen with legacy single-area mode."""
        print("🎬 Processing with legacy dual green screen mode...")
        
        folder_paths = settings['folder_paths']
        template_info = settings['template_info']
        text_settings = settings['text_settings']
        audio_settings = settings['audio_settings']
        output_settings = settings['output_settings']
        gpu_settings = settings['gpu_settings']
        
        # Get all files to process (original logic)
        try:
            # Get all files to process
            from gui.dual_video_selection import DualVideoSelection
            dual_selection = DualVideoSelection(None)
            dual_selection.folder1_path = folder_paths['folder1']
            dual_selection.folder2_path = folder_paths['folder2']
            
            files_to_process = dual_selection.get_files_to_process()
            
            if not files_to_process:
                print("❌ No files found to process")
                return False
            
            print(f"📹 Found {len(files_to_process)} files to process")
            
            # Determine output folder
            if output_settings['custom_enabled'] and output_settings['custom_folder']:
                output_folder = output_settings['custom_folder']
            else:
                output_folder = folder_paths['folder1']  # Default to folder1
            
            # Create output subfolder
            from utils.file_operations import create_output_folder
            output_folder = create_output_folder(output_folder, "dual_greenscreen_output")
            
            # Process each file
            successful_count = 0
            total_files = len(files_to_process)
            
            for i, (folder_path, file_name, video_source) in enumerate(files_to_process):
                if self.progress_callback:
                    overall_progress = (i / total_files) * 100
                    self.progress_callback(
                        overall_progress, 
                        f"Processing file {i+1}/{total_files}: {file_name}"
                    )
                
                file_path = os.path.join(folder_path, file_name)
                output_path = os.path.join(output_folder, f"dual_{file_name}")
                
                # Ensure output is MP4
                if not output_path.lower().endswith('.mp4'):
                    output_path = os.path.splitext(output_path)[0] + '.mp4'
                
                try:
                    if is_gif_file(file_path):
                        # Process GIF -> MP4
                        success = process_dual_greenscreen_gif(
                            file_path, video_source, template_info['path'], 
                            template_mask, output_path, text_settings, 
                            audio_settings, gpu_settings
                        )
                    elif is_image_file(file_path):
                        # Process Image -> MP4
                        success = process_dual_greenscreen_image(
                            file_path, video_source, template_info['path'], 
                            template_mask, output_path, text_settings, 
                            audio_settings, gpu_settings
                        )
                    else:
                        # Process Video -> MP4
                        success = process_dual_greenscreen_video(
                            file_path, video_source, template_info['path'], 
                            template_mask, output_path, text_settings, 
                            audio_settings, gpu_settings
                        )
                    
                    if success:
                        successful_count += 1
                        print(f"✅ Processed: {file_name}")
                    else:
                        print(f"❌ Failed: {file_name}")
                
                except Exception as e:
                    print(f"❌ Error processing {file_name}: {e}")
                    continue
            
            print(f"🎬🎬 Dual Green Screen processing completed!")
            print(f"✅ Successfully processed: {successful_count}/{total_files} files")
            print(f"📁 Output folder: {output_folder}")
            
            return successful_count > 0
        
        except Exception as e:
            print(f"❌ Error in dual legacy mode: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def process_greenscreen_mode(self, settings):
        """Process green screen mode."""
        print("🎬 Starting Green Screen Mode processing...")
        
        folder_path = settings['folder_path']
        template_info = settings['template_info']
        text_settings = settings['text_settings']
        audio_settings = settings['audio_settings']
        output_settings = settings['output_settings']
        gpu_settings = settings['gpu_settings']
        
        # Validation
        if not folder_path:
            print("❌ No video folder selected")
            return False
        
        if not template_info['path']:
            print("❌ No template selected")
            return False
        
        # Get template and create mask
        template = cv2.imread(template_info['path'])
        if template is None:
            print("❌ Could not load template")
            return False
        
        template = cv2.resize(template, (1080, 1920))
        template_mask = create_green_screen_mask(template)
        
        # Get media files
        try:
            media_files = get_all_media_files(folder_path)
            
            if not media_files:
                print("❌ No media files found")
                return False
            
            print(f"📹 Found {len(media_files)} media files")
            
            # Determine output folder
            if output_settings['custom_enabled'] and output_settings['custom_folder']:
                output_folder = output_settings['custom_folder']
            else:
                output_folder = folder_path
            
            # Create output subfolder
            from utils.file_operations import create_output_folder
            output_folder = create_output_folder(output_folder, "greenscreen_output")
            
            # Process files
            return self._process_media_files(
                media_files, folder_path, output_folder, template, template_mask,
                text_settings, audio_settings, gpu_settings, "greenscreen"
            )
            
        except Exception as e:
            print(f"❌ Green Screen mode error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def process_blur_mode(self, settings):
        """Process blur mode."""
        print("🌀 Starting Blur Mode processing...")
        
        folder_path = settings['folder_path']
        blur_settings = settings['blur_settings']
        text_settings = settings['text_settings']
        audio_settings = settings['audio_settings']
        output_settings = settings['output_settings']
        gpu_settings = settings['gpu_settings']
        
        # Validation
        if not folder_path:
            print("❌ No video folder selected")
            return False
        
        # Get media files
        try:
            media_files = get_all_media_files(folder_path)
            
            if not media_files:
                print("❌ No media files found")
                return False
            
            print(f"📹 Found {len(media_files)} media files")
            
            # Determine output folder
            if output_settings['custom_enabled'] and output_settings['custom_folder']:
                output_folder = output_settings['custom_folder']
            else:
                output_folder = folder_path
            
            # Create output subfolder
            from utils.file_operations import create_output_folder
            output_folder = create_output_folder(output_folder, "blur_output")
            
            # Process files
            return self._process_media_files(
                media_files, folder_path, output_folder, None, None,
                text_settings, audio_settings, gpu_settings, "blur", blur_settings
            )
            
        except Exception as e:
            print(f"❌ Blur mode error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _process_media_files(self, media_files, folder_path, output_folder, template, template_mask,
                           text_settings, audio_settings, gpu_settings, mode, blur_settings=None):
        """Process media files for greenscreen or blur mode."""
        successful_count = 0
        total_files = len(media_files)
        
        for i, file_name in enumerate(media_files):
            if self.progress_callback:
                overall_progress = (i / total_files) * 100
                self.progress_callback(
                    overall_progress, 
                    f"Processing file {i+1}/{total_files}: {file_name}"
                )
            
            file_path = os.path.join(folder_path, file_name)
            output_path = os.path.join(output_folder, f"{mode}_{file_name}")
            
            # Ensure output is MP4 for videos, keep GIF for GIFs
            if is_gif_file(file_path):
                output_path = os.path.splitext(output_path)[0] + '.gif'
            elif is_image_file(file_path):
                output_path = os.path.splitext(output_path)[0] + '.mp4'  # Convert images to MP4
            else:
                output_path = os.path.splitext(output_path)[0] + '.mp4'
            
            try:
                if is_gif_file(file_path):
                    # Process GIF
                    if mode == "greenscreen":
                        success = process_gif_greenscreen(
                            file_path, template, template_mask, output_path, text_settings
                        )
                    elif mode == "blur":
                        success = process_gif_blur(
                            file_path, output_path, blur_settings, text_settings
                        )
                elif is_image_file(file_path):
                    # Process Image -> MP4
                    if mode == "greenscreen":
                        success = self._process_image_greenscreen(
                            file_path, template, template_mask, output_path, text_settings, audio_settings
                        )
                    elif mode == "blur":
                        success = self._process_image_blur(
                            file_path, output_path, blur_settings, text_settings, audio_settings
                        )
                else:
                    # Process Video
                    if mode == "greenscreen":
                        temp_output = self.core.process_single_video(
                            file_path, template, template_mask, output_path, 
                            text_settings, gpu_settings
                        )
                        if temp_output:
                            # Add audio
                            from utils.file_operations import add_audio_to_video, add_background_music_to_video
                            
                            if audio_settings.get('dual_audio_enabled', False):
                                # Dual audio mixing mode
                                from utils.file_operations import add_dual_audio_to_video
                                import random
                                from utils.file_operations import get_audio_files
                                audio_files = get_audio_files(audio_settings['folder_path'])
                                if audio_files:
                                    background_audio = os.path.join(
                                        audio_settings['folder_path'], 
                                        random.choice(audio_files)
                                    )
                                    success = add_dual_audio_to_video(
                                        temp_output, file_path, background_audio, output_path,
                                        original_volume=audio_settings['original_volume'],
                                        background_volume=audio_settings['background_volume']
                                    )
                                else:
                                    success = add_audio_to_video(temp_output, file_path, output_path)
                            elif audio_settings['enabled'] and audio_settings['folder_path']:
                                # Background music only mode
                                import random
                                from utils.file_operations import get_audio_files
                                audio_files = get_audio_files(audio_settings['folder_path'])
                                if audio_files:
                                    background_audio = os.path.join(
                                        audio_settings['folder_path'], 
                                        random.choice(audio_files)
                                    )
                                    success = add_background_music_to_video(
                                        temp_output, file_path, background_audio, 
                                        output_path, audio_settings.get('volume', audio_settings.get('background_volume', 50))
                                    )
                                else:
                                    success = add_audio_to_video(temp_output, file_path, output_path)
                            else:
                                success = add_audio_to_video(temp_output, file_path, output_path)
                        else:
                            # Original audio only
                            success = False
                    elif mode == "blur":
                        temp_output = self.core.process_single_video_blur(
                            file_path, output_path, blur_settings, text_settings, gpu_settings
                        )
                        if temp_output:
                            # Add audio
                            from utils.file_operations import add_audio_to_video, add_background_music_to_video
                            if audio_settings.get('dual_audio_enabled', False):
                                # Dual audio mixing mode
                                from utils.file_operations import add_dual_audio_to_video
                                import random
                                from utils.file_operations import get_audio_files
                                audio_files = get_audio_files(audio_settings['folder_path'])
                                if audio_files:
                                    background_audio = os.path.join(
                                        audio_settings['folder_path'], 
                                        random.choice(audio_files)
                                    )
                                    success = add_dual_audio_to_video(
                                        temp_output, file_path, background_audio, output_path,
                                        original_volume=audio_settings['original_volume'],
                                        background_volume=audio_settings['background_volume']
                                    )
                                else:
                                    success = add_audio_to_video(temp_output, file_path, output_path)
                            elif audio_settings['enabled'] and audio_settings['folder_path']:
                                # Background music only mode
                                import random
                                from utils.file_operations import get_audio_files
                                audio_files = get_audio_files(audio_settings['folder_path'])
                                if audio_files:
                                    background_audio = os.path.join(
                                        audio_settings['folder_path'], 
                                        random.choice(audio_files)
                                    )
                                    success = add_background_music_to_video(
                                        temp_output, file_path, background_audio, 
                                        output_path, audio_settings.get('volume', audio_settings.get('background_volume', 50))
                                    )
                                else:
                                    success = add_audio_to_video(temp_output, file_path, output_path)
                            else:
                                # Original audio only
                                success = add_audio_to_video(temp_output, file_path, output_path)
                        else:
                            success = False
                
                if success:
                    successful_count += 1
                    print(f"✅ Processed: {file_name}")
                else:
                    print(f"❌ Failed: {file_name}")
            
            except Exception as e:
                print(f"❌ Error processing {file_name}: {e}")
                continue
        
        print(f"🎬 {mode.title()} processing completed!")
        print(f"✅ Successfully processed: {successful_count}/{total_files} files")
        print(f"📁 Output folder: {output_folder}")
        
        return successful_count > 0
    
    def _process_image_greenscreen(self, image_path, template, template_mask, output_path, text_settings, audio_settings):
        """Process image with greenscreen mode -> MP4 output."""
        try:
            import cv2
            from moviepy.editor import VideoFileClip, AudioFileClip
            
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                print(f"❌ Could not load image: {image_path}")
                return False
            
            # Process image with greenscreen
            from utils.video_processing import process_frame_with_green_screen
            processed_frame = process_frame_with_green_screen(template, image, template_mask)
            
            # Add text overlay if enabled
            if text_settings['enabled']:
                processed_frame = self.core.add_text_overlay(processed_frame, os.path.basename(image_path), text_settings)
            
            # Ensure correct size
            if processed_frame.shape[:2] != (1920, 1080):
                processed_frame = cv2.resize(processed_frame, (1080, 1920))
            
            # Create MP4 from single image (5 seconds duration)
            fps = 30
            duration_seconds = 5
            total_frames = fps * duration_seconds
            
            # Setup MP4 writer
            temp_output = output_path.replace('.mp4', '_temp.mp4')
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(temp_output, fourcc, fps, (1080, 1920))
            
            # Write same frame multiple times to create video
            for frame_num in range(total_frames):
                out.write(processed_frame)
            
            out.release()
            
            # Handle audio
            self._add_audio_to_image_video(temp_output, output_path, duration_seconds, audio_settings)
            
            return True
            
        except Exception as e:
            print(f"❌ Image greenscreen processing error: {e}")
            return False
    
    def _process_image_blur(self, image_path, output_path, blur_settings, text_settings, audio_settings):
        """Process image with blur mode -> MP4 output."""
        try:
            import cv2
            
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                print(f"❌ Could not load image: {image_path}")
                return False
            
            # Process image with blur
            from utils.blur_processing import process_blur_frame
            processed_frame = process_blur_frame(
                image,
                blur_settings['crop_top'],
                blur_settings['crop_bottom'],
                blur_settings['video_x_position'],
                blur_settings['video_y_position']
            )
            
            # Add text overlay if enabled
            if text_settings['enabled']:
                processed_frame = self.core.add_text_overlay(processed_frame, os.path.basename(image_path), text_settings)
            
            # Ensure correct size
            if processed_frame.shape[:2] != (1920, 1080):
                processed_frame = cv2.resize(processed_frame, (1080, 1920))
            
            # Create MP4 from single image (5 seconds duration)
            fps = 30
            duration_seconds = 5
            total_frames = fps * duration_seconds
            
            # Setup MP4 writer
            temp_output = output_path.replace('.mp4', '_temp.mp4')
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(temp_output, fourcc, fps, (1080, 1920))
            
            # Write same frame multiple times to create video
            for frame_num in range(total_frames):
                out.write(processed_frame)
            
            out.release()
            
            # Handle audio
            self._add_audio_to_image_video(temp_output, output_path, duration_seconds, audio_settings)
            
            return True
            
        except Exception as e:
            print(f"❌ Image blur processing error: {e}")
            return False
    
    def _add_audio_to_image_video(self, temp_output, output_path, duration_seconds, audio_settings):
        """Add audio to image-converted video."""
        try:
            # For image conversion, we only add background music (no original audio)
            if audio_settings.get('enabled', False) and audio_settings.get('folder_path'):
                import random
                from utils.file_operations import get_audio_files
                from moviepy.editor import VideoFileClip, AudioFileClip
                
                audio_files = get_audio_files(audio_settings['folder_path'])
                if audio_files:
                    background_audio_path = os.path.join(
                        audio_settings['folder_path'], 
                        random.choice(audio_files)
                    )
                    
                    video_clip = VideoFileClip(temp_output)
                    background_audio = AudioFileClip(background_audio_path)
                    
                    # Adjust volume
                    volume = audio_settings.get('background_volume', audio_settings.get('volume', 50)) / 100.0
                    background_audio = background_audio.volumex(volume)
                    
                    # Loop or trim audio to match video duration
                    if background_audio.duration < video_clip.duration:
                        background_audio = background_audio.loop(duration=video_clip.duration)
                    else:
                        background_audio = background_audio.subclip(0, video_clip.duration)
                    
                    final_clip = video_clip.set_audio(background_audio)
                    final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac", logger=None)
                    
                    video_clip.close()
                    background_audio.close()
                    final_clip.close()
                    
                    # Remove temp file
                    if os.path.exists(temp_output):
                        os.remove(temp_output)
                    
                    return
            
            # No audio processing, just rename temp file
            if os.path.exists(temp_output):
                import shutil
                shutil.move(temp_output, output_path)
                
        except Exception as e:
            print(f"❌ Audio processing error for image video: {e}")
            # Fallback: just rename temp file
            if os.path.exists(temp_output):
                import shutil
                shutil.move(temp_output, output_path)