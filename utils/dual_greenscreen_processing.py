"""
Dual Green Screen Processing Module
Handles dual green screen mode processing with two video folders
"""

import cv2
import os
import numpy as np
import random
from .video_processing import process_frame_with_green_screen
from .green_screen_detection import create_green_screen_mask
from .dual_greenscreen_detection import (
    detect_dual_green_screen_areas, 
    process_dual_frame_with_green_screen,
    validate_dual_green_screen_template
)
from .gif_processing import extract_gif_frames, process_video_with_gif_template
from .file_operations import (add_audio_to_video, add_background_music_to_video, 
                           add_dual_audio_to_video, get_video_properties, 
                           get_audio_files, is_gif_file, is_image_file)
import tempfile

def process_dual_greenscreen_image(image_path, video_source, template_path, template_mask, 
                                 output_path, text_settings, audio_settings, gpu_settings):
    """Process image with dual green screen mode -> MP4 output."""
    print(f"🖼️ Processing dual greenscreen image: {os.path.basename(image_path)} (Source: {video_source})")
    
    try:
        # Load image
        import cv2
        image = cv2.imread(image_path)
        if image is None:
            print(f"❌ Could not load image: {image_path}")
            return False
        
        # Get template
        template = get_template_for_processing(template_path)
        template = cv2.resize(template, (1080, 1920))
        
        # Process image with greenscreen (single frame)
        processed_frame = process_frame_with_green_screen(template, image, template_mask)
        
        # Add text overlay if enabled
        if text_settings['enabled']:
            image_name = os.path.basename(image_path)
            processed_frame = add_dual_text_overlay(processed_frame, image_name, text_settings)
        
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
        
        if not out.isOpened():
            print(f"❌ Could not create output file: {temp_output}")
            return False
        
        print(f"🎬 Converting image to MP4: {total_frames} frames at {fps} FPS")
        
        # Write same frame multiple times to create video
        for frame_num in range(total_frames):
            out.write(processed_frame)
            
            if (frame_num + 1) % 30 == 0:
                print(f"📊 Generated {frame_num + 1}/{total_frames} frames")
        
        out.release()
        
        # Handle audio (use silence or background music for image conversion)
        handle_dual_image_audio_processing(temp_output, output_path, video_source, duration_seconds, audio_settings)
        
        return True
        
    except Exception as e:
        print(f"❌ Image to MP4 conversion error: {e}")
        import traceback
        traceback.print_exc()
        return False

def handle_dual_image_audio_processing(temp_output, output_path, video_source, duration_seconds, audio_settings):
    """Handle audio for image to MP4 conversion in dual mode."""
    try:
        # Determine which audio folder to use based on source
        if audio_settings.get('audio_source', 'folder1') == "folder1":
            audio_folder = audio_settings['folder1_path']
        else:
            audio_folder = audio_settings['folder2_path']
        
        # For image conversion, we only add background music (no original audio)
        if (audio_settings['enabled'] or audio_settings.get('dual_audio_enabled', False)) and audio_folder:
            # Add background music
            background_audio_path = get_random_audio_file(audio_folder)
            
            if background_audio_path:
                print(f"🎵 Adding background music to converted MP4 from {audio_settings.get('audio_source', 'folder1')}")
                from moviepy.editor import VideoFileClip, AudioFileClip
                
                video_clip = VideoFileClip(temp_output)
                background_audio = AudioFileClip(background_audio_path)
                
                # Adjust volume based on mode
                if audio_settings.get('dual_audio_enabled', False):
                    # Use background volume from dual audio settings
                    background_volume = audio_settings['background_volume'] / 100.0
                else:
                    # Use regular background volume
                    background_volume = audio_settings['background_volume'] / 100.0
                
                background_audio = background_audio.volumex(background_volume)
                
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
        
        # No audio processing needed, just rename temp file
        if os.path.exists(temp_output):
            import shutil
            shutil.move(temp_output, output_path)
            
    except Exception as e:
        print(f"❌ Audio processing error for image conversion: {e}")
        # Fallback: just rename temp file
        if os.path.exists(temp_output):
            import shutil
            shutil.move(temp_output, output_path)
def process_dual_greenscreen_video_auto(video1_path, video2_path, template_path, 
                                       output_path, text_settings, audio_settings, gpu_settings):
    """
    Process two videos with auto-detected dual green screen areas.
    """
    print(f"🎬🎬 Processing dual videos with auto-detection:")
    print(f"   Video 1: {os.path.basename(video1_path)}")
    print(f"   Video 2: {os.path.basename(video2_path)}")
    
    # Load and validate template
    template = get_template_for_processing(template_path)
    template = cv2.resize(template, (1080, 1920))
    
    # Detect dual green screen areas
    dual_areas = detect_dual_green_screen_areas(template)
    if dual_areas is None:
        print("❌ Could not detect dual green screen areas")
        return False
    
    # Open both videos
    cap1 = cv2.VideoCapture(video1_path)
    cap2 = cv2.VideoCapture(video2_path)
    
    if not cap1.isOpened() or not cap2.isOpened():
        print("❌ Could not open one or both videos")
        cap1.release()
        cap2.release()
        return False
    
    # Get video properties (use video1 as reference)
    fps1, _, _ = get_video_properties(video1_path)
    fps2, _, _ = get_video_properties(video2_path)
    
    # Use the higher FPS for output
    output_fps = max(fps1, fps2)
    
    total_frames1 = int(cap1.get(cv2.CAP_PROP_FRAME_COUNT))
    total_frames2 = int(cap2.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Use the longer video as reference for total frames
    max_frames = max(total_frames1, total_frames2)
    
    print(f"📹 Video 1: {total_frames1} frames at {fps1} FPS")
    print(f"📹 Video 2: {total_frames2} frames at {fps2} FPS")
    print(f"📹 Output: {max_frames} frames at {output_fps} FPS")
    
    # Setup output
    temp_output = output_path.replace('.mp4', '_temp.mp4')
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_output, fourcc, output_fps, (1080, 1920))
    
    if not out.isOpened():
        print("❌ Could not create output file")
        cap1.release()
        cap2.release()
        return False
    
    frame_count = 0
    
    try:
        while frame_count < max_frames:
            # Read frames from both videos
            ret1, frame1 = cap1.read()
            ret2, frame2 = cap2.read()
            
            # Handle video looping if one video is shorter
            if not ret1 and total_frames1 > 0:
                cap1.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret1, frame1 = cap1.read()
            
            if not ret2 and total_frames2 > 0:
                cap2.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret2, frame2 = cap2.read()
            
            # If both videos ended, break
            if not ret1 and not ret2:
                break
            
            # Use black frame if one video is not available
            if not ret1:
                frame1 = np.zeros((480, 640, 3), dtype=np.uint8)
            if not ret2:
                frame2 = np.zeros((480, 640, 3), dtype=np.uint8)
            
            # Process frame with dual green screen
            processed_frame = process_dual_frame_with_green_screen(
                template, frame1, frame2, dual_areas
            )
            
            # Add text overlay if enabled
            if text_settings['enabled']:
                video_name = f"{os.path.basename(video1_path)} + {os.path.basename(video2_path)}"
                processed_frame = add_dual_text_overlay(processed_frame, video_name, text_settings)
            
            # Ensure correct size
            if processed_frame.shape[:2] != (1920, 1080):
                processed_frame = cv2.resize(processed_frame, (1080, 1920))
            
            out.write(processed_frame)
            frame_count += 1
            
            # Progress update
            if frame_count % 30 == 0:
                progress = (frame_count / max_frames) * 100
                print(f"📊 Processed {frame_count}/{max_frames} frames ({progress:.1f}%)")
    
    except Exception as e:
        print(f"❌ Error during dual processing: {e}")
        return False
    
    finally:
        cap1.release()
        cap2.release()
        out.release()
    
    print(f"✅ Dual video processing completed: {frame_count} frames")
    
    # Handle audio (use video1 as primary audio source)
    handle_dual_audio_processing(temp_output, video1_path, "folder1", output_path, audio_settings)
    
    return True

def get_template_for_processing(template_path):
    """Get template for processing - handles static images, GIFs, and videos."""
    if template_path.lower().endswith('.gif'):
        # For GIF templates, extract first frame as the base template
        frames, _ = extract_gif_frames(template_path)
        if frames:
            return frames[0]  # Use first frame as template
        else:
            raise Exception("Could not extract frames from GIF template")
    elif template_path.lower().endswith(('.mp4', '.avi', '.mov')):
        # For video templates, extract first frame
        cap = cv2.VideoCapture(template_path)
        ret, frame = cap.read()
        cap.release()
        if ret:
            return frame
        else:
            raise Exception("Could not extract frame from video template")
    else:
        # Static image template
        template = cv2.imread(template_path)
        if template is None:
            raise Exception("Could not load image template")
        return template

def get_random_audio_file(audio_folder):
    """Get random audio file from folder."""
    if not audio_folder or not os.path.exists(audio_folder):
        return None
    
    audio_files = get_audio_files(audio_folder)
    if not audio_files:
        return None
    
    return os.path.join(audio_folder, random.choice(audio_files))

def process_dual_greenscreen_video(video_path, video_source, template_path, template_mask, 
                                 output_path, text_settings, audio_settings, gpu_settings):
    """Process single video with dual green screen mode."""
    print(f"🎬🎬 Processing dual greenscreen video: {os.path.basename(video_path)} (Source: {video_source})")
    
    # Check if template is a GIF or video - IMPORTANT: Output is still MP4!
    if template_path.lower().endswith('.gif'):
        print(f"🎬 Processing with animated GIF template -> MP4 output")
        temp_output = output_path.replace('.mp4', '_temp.mp4')
        success = process_video_with_gif_template(template_path, video_path, temp_output, text_settings)
        
        if success:
            # Handle audio processing for dual mode
            handle_dual_audio_processing(temp_output, video_path, video_source, output_path, audio_settings)
            return True
        else:
            return False
    elif template_path.lower().endswith(('.mp4', '.avi', '.mov')):
        print(f"🎥 Processing with video template -> MP4 output")
        return process_video_with_video_template(video_path, video_source, template_path, 
                                               output_path, text_settings, audio_settings, gpu_settings)
    
    # Regular static template processing
    template = get_template_for_processing(template_path)
    template = cv2.resize(template, (1080, 1920))
    
    cap = cv2.VideoCapture(video_path)
    fps, _, _ = get_video_properties(video_path)
    
    temp_output = output_path.replace('.mp4', '_temp.mp4')
    
    # Setup video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_output, fourcc, fps, (1080, 1920))
    
    video_name = os.path.basename(video_path)
    frame_count = 0
    
    print(f"🎬 Processing {video_name} with GPU: {'Enabled' if gpu_settings['enabled'] else 'Disabled'}")
    
    try:
        while True:
            ret, video_frame = cap.read()
            if not ret:
                break
            
            processed_frame = process_frame_with_green_screen(template, video_frame, template_mask)
            
            # Add text overlay (use video name based on text source)
            if text_settings['enabled']:
                # Use video name for text overlay
                processed_frame = add_dual_text_overlay(processed_frame, video_name, text_settings)
            
            # Ensure frame is the correct size
            if processed_frame.shape[:2] != (1920, 1080):
                processed_frame = cv2.resize(processed_frame, (1080, 1920))
            
            out.write(processed_frame)
            frame_count += 1
            
            # Progress update every 30 frames
            if frame_count % 30 == 0:
                print(f"📊 Processed {frame_count} frames")
    
    except Exception as e:
        print(f"❌ Error during video processing: {e}")
        return False
    
    finally:
        cap.release()
        out.release()
        print(f"✅ Video processing completed: {frame_count} frames")
    
    # Handle audio processing for dual mode
    handle_dual_audio_processing(temp_output, video_path, video_source, output_path, audio_settings)
    return True

def process_video_with_video_template(video_path, video_source, template_path, 
                                    output_path, text_settings, audio_settings, gpu_settings):
    """Process video with video template."""
    print(f"🎥 Processing video with video template")
    
    # Open template video
    template_cap = cv2.VideoCapture(template_path)
    template_fps = int(template_cap.get(cv2.CAP_PROP_FPS))
    template_frame_count = int(template_cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Open input video
    input_cap = cv2.VideoCapture(video_path)
    input_fps, _, _ = get_video_properties(video_path)
    input_frame_count = int(input_cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Use input video FPS for output
    temp_output = output_path.replace('.mp4', '_temp.mp4')
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_output, fourcc, input_fps, (1080, 1920))
    
    video_name = os.path.basename(video_path)
    frame_count = 0
    template_frame_index = 0
    
    print(f"🎥 Template: {template_frame_count} frames at {template_fps} FPS")
    print(f"🎬 Input: {input_frame_count} frames at {input_fps} FPS")
    
    try:
        while True:
            # Read input video frame
            ret_input, input_frame = input_cap.read()
            if not ret_input:
                break
            
            # Read template frame (cycle through template frames)
            template_cap.set(cv2.CAP_PROP_POS_FRAMES, template_frame_index)
            ret_template, template_frame = template_cap.read()
            
            if not ret_template:
                # Reset template to beginning if we've reached the end
                template_frame_index = 0
                template_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret_template, template_frame = template_cap.read()
            
            if ret_template:
                # Resize template frame
                template_frame = cv2.resize(template_frame, (1080, 1920))
                
                # Create mask from current template frame
                template_mask = create_green_screen_mask(template_frame)
                
                # Process frame with green screen
                processed_frame = process_frame_with_green_screen(template_frame, input_frame, template_mask)
                
                # Add text overlay
                if text_settings['enabled']:
                    processed_frame = add_dual_text_overlay(processed_frame, video_name, text_settings)
                
                # Ensure correct size
                if processed_frame.shape[:2] != (1920, 1080):
                    processed_frame = cv2.resize(processed_frame, (1080, 1920))
                
                out.write(processed_frame)
                
                # Advance template frame index
                template_frame_index = (template_frame_index + 1) % template_frame_count
            
            frame_count += 1
            
            if frame_count % 30 == 0:
                print(f"📊 Processed {frame_count} frames (Template frame: {template_frame_index + 1}/{template_frame_count})")
    
    except Exception as e:
        print(f"❌ Error during video template processing: {e}")
        return False
    
    finally:
        template_cap.release()
        input_cap.release()
        out.release()
        print(f"✅ Video template processing completed: {frame_count} frames")
    
    # Handle audio processing
    handle_dual_audio_processing(temp_output, video_path, video_source, output_path, audio_settings)
    return True

def process_dual_greenscreen_gif(gif_path, video_source, template_path, template_mask, 
                               output_path, text_settings, audio_settings, gpu_settings):
    """Process GIF with dual green screen mode -> MP4 output."""
    print(f"🎬🎬 Processing dual greenscreen GIF: {os.path.basename(gif_path)} (Source: {video_source})")
    
    try:
        # Extract GIF frames
        frames, durations = extract_gif_frames(gif_path)
        if not frames:
            return False
        
        # Get template
        template = get_template_for_processing(template_path)
        template = cv2.resize(template, (1080, 1920))
        
        # Setup MP4 writer
        fps = 10  # Default FPS for GIF conversion
        temp_output = output_path.replace('.mp4', '_temp.mp4')
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(temp_output, fourcc, fps, (1080, 1920))
        
        gif_name = os.path.basename(gif_path)
        
        print(f"🎬 Converting GIF to MP4: {len(frames)} frames")
        
        for i, frame in enumerate(frames):
            # Process with greenscreen
            processed_frame = process_frame_with_green_screen(template, frame, template_mask)
            
            # Add text overlay
            if text_settings['enabled']:
                processed_frame = add_dual_text_overlay(processed_frame, gif_name, text_settings)
            
            # Ensure correct size
            if processed_frame.shape[:2] != (1920, 1080):
                processed_frame = cv2.resize(processed_frame, (1080, 1920))
            
            out.write(processed_frame)
            
            if (i + 1) % 10 == 0:
                print(f"📊 Converted {i + 1}/{len(frames)} frames")
        
        out.release()
        
        # Handle audio (use silence for GIF conversion)
        handle_dual_gif_audio_processing(temp_output, output_path, video_source, len(frames), fps, audio_settings)
        
        return True
        
    except Exception as e:
        print(f"❌ GIF to MP4 conversion error: {e}")
        return False

def add_dual_text_overlay(frame, video_name, text_settings):
    """Add text overlay for dual mode (simplified version)."""
    try:
        from PIL import Image, ImageDraw, ImageFont
        from utils.text_rendering import smart_text_wrap, render_text_with_emoji_multiline
        
        pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil_image)
        
        try:
            font_file = get_font_file(text_settings['font'])
            font = ImageFont.truetype(font_file, text_settings['size'])
        except:
            font = ImageFont.load_default()
        
        video_name_text = os.path.splitext(video_name)[0].replace("_", " ")
        
        # Calculate available text area
        max_text_width = 1080 - 80  # 40px margin left-right
        
        # Auto-wrap text based on frame width
        lines = smart_text_wrap(video_name_text, draw, font, max_text_width, emoji_size=80)
        
        # Calculate position based on settings
        x_percent = text_settings['x_position'] / 100
        y_percent = text_settings['y_position'] / 100
        
        # Calculate total text height
        line_height = text_settings['size'] + 10
        total_text_height = len(lines) * line_height
        
        # Y position based on percentage, with auto-adjustment
        base_y = int(y_percent * (1920 - total_text_height - 40))
        base_y = max(20, min(base_y, 1920 - total_text_height - 20))
        
        # Render multiline text with emoji
        rendered_lines = render_text_with_emoji_multiline(
            draw, lines, font, 1080, 1920, 
            base_y, emoji_size=80, line_spacing=10
        )
        
        # Get text color from settings (default to black if not specified)
        text_color = text_settings.get('color', '#000000')
        
        # Draw text and emoji
        for line_data in rendered_lines:
            for item_type, item, x_offset in line_data['items']:
                if item_type == 'emoji':
                    # Position emoji adjusted to font height
                    emoji_y = line_data['y'] + (text_settings['size'] - line_data['emoji_size']) // 2
                    pil_image.paste(item, (line_data['x_start'] + x_offset, emoji_y), item)
                elif item_type == 'text':
                    # Draw text with selected color
                    draw.text((line_data['x_start'] + x_offset, line_data['y']), 
                             item, font=font, fill=text_color)
        
        return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    
    except Exception as e:
        print(f"⚠️ Text overlay error: {e}")
        return frame  # Return original frame if text overlay fails

def get_font_file(font_name):
    """Get font file based on font name."""
    font_mapping = {
        "Arial": "arial.ttf",
        "Times New Roman": "times.ttf",
        "Helvetica": "arial.ttf",  # fallback
        "Courier New": "cour.ttf",
        "Verdana": "verdana.ttf",
        "Georgia": "georgia.ttf",
        "Comic Sans MS": "comic.ttf",
        "Impact": "impact.ttf",
        "Trebuchet MS": "trebuc.ttf",
        "Tahoma": "tahoma.ttf"
    }
    return font_mapping.get(font_name, "arial.ttf")

def handle_dual_audio_processing(temp_output, video_path, video_source, output_path, audio_settings):
    """Handle audio processing for dual green screen mode."""
    try:
        # Determine which audio folder to use based on source
        if audio_settings.get('audio_source', 'folder1') == "folder1":
            audio_folder = audio_settings['folder1_path']
        else:
            audio_folder = audio_settings['folder2_path']
        
        # Check if dual audio mixing is enabled
        if audio_settings.get('dual_audio_enabled', False):
            # Dual audio mixing mode
            if audio_folder:
                background_audio_path = get_random_audio_file(audio_folder)
                
                if background_audio_path:
                    print(f"🎭 Dual audio mixing: Original + Background (Source: {audio_settings.get('audio_source', 'folder1')})")
                    print(f"   Background music: {os.path.basename(background_audio_path)}")
                    
                    success = add_dual_audio_to_video(
                        temp_output, video_path, background_audio_path, output_path,
                        original_volume=audio_settings['original_volume'],
                        background_volume=audio_settings['background_volume']
                    )
                    
                    if success:
                        print(f"✅ Dual audio mixing completed")
                        return
                    else:
                        print(f"❌ Dual audio mixing failed, falling back to original audio")
                else:
                    print(f"⚠️ No background music found for dual audio, using original audio")
            else:
                print(f"⚠️ No background music folder selected for dual audio, using original audio")
            
            # Fallback to original audio if dual audio fails
            add_audio_to_video(temp_output, video_path, output_path)
            
        elif audio_settings['enabled'] and audio_folder:
            # Background music only mode
            background_audio_path = get_random_audio_file(audio_folder)
            
            if background_audio_path:
                print(f"🎵 Adding background music from {audio_settings.get('audio_source', 'folder1')}: {os.path.basename(background_audio_path)}")
                # Add background music with specified volume
                success = add_background_music_to_video(
                    temp_output, video_path, background_audio_path, output_path,
                    volume=audio_settings['background_volume']
                )
                if not success:
                    print("🔄 Background music failed, using original audio")
                    add_audio_to_video(temp_output, video_path, output_path)
            else:
                # Fallback to original audio if no background music found
                print("🔄 No background music found, using original audio")
                add_audio_to_video(temp_output, video_path, output_path)
        else:
            # Use original audio only
            print("🎵 Using original audio")
            add_audio_to_video(temp_output, video_path, output_path)
    
    except Exception as e:
        print(f"❌ Audio processing error: {e}")
        # Try to at least copy the temp file
        try:
            if os.path.exists(temp_output):
                import shutil
                shutil.copy2(temp_output, output_path)
                print("🔄 Copied video without audio processing")
        except Exception as copy_error:
            print(f"❌ Failed to copy video: {copy_error}")

def handle_dual_gif_audio_processing(temp_output, output_path, video_source, frame_count, fps, audio_settings):
    """Handle audio for GIF to MP4 conversion in dual mode."""
    try:
        # Determine which audio folder to use based on source
        if audio_settings.get('audio_source', 'folder1') == "folder1":
            audio_folder = audio_settings['folder1_path']
        else:
            audio_folder = audio_settings['folder2_path']
        
        # For GIF conversion, we only add background music (no original audio)
        if (audio_settings['enabled'] or audio_settings.get('dual_audio_enabled', False)) and audio_folder:
            # Add background music
            background_audio_path = get_random_audio_file(audio_folder)
            
            if background_audio_path:
                print(f"🎵 Adding background music to converted MP4 from {audio_settings.get('audio_source', 'folder1')}")
                from moviepy.editor import VideoFileClip, AudioFileClip
                
                video_clip = VideoFileClip(temp_output)
                background_audio = AudioFileClip(background_audio_path)
                
                # Adjust volume based on mode
                if audio_settings.get('dual_audio_enabled', False):
                    # Use background volume from dual audio settings
                    background_volume = audio_settings['background_volume'] / 100.0
                else:
                    # Use regular background volume
                    background_volume = audio_settings['background_volume'] / 100.0
                
                background_audio = background_audio.volumex(background_volume)
                
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
        
        # No audio processing needed, just rename temp file
        if os.path.exists(temp_output):
            import shutil
            shutil.move(temp_output, output_path)
            
    except Exception as e:
        print(f"❌ Audio processing error for GIF conversion: {e}")
        # Fallback: just rename temp file
        if os.path.exists(temp_output):
            import shutil
            shutil.move(temp_output, output_path)