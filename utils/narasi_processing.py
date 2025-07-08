import cv2
import os
import numpy as np
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips
from .video_processing import process_frame_with_green_screen
from .green_screen_detection import create_green_screen_mask
from .gif_processing import extract_gif_frames
import tempfile

def concatenate_videos_opencv(video_paths, temp_output_path, target_fps=30):
    """
    Concatenate multiple videos using OpenCV.
    Returns the total duration in seconds and frame count.
    """
    print(f"🔗 Concatenating {len(video_paths)} videos with OpenCV...")
    
    # Get properties from first video
    first_cap = cv2.VideoCapture(video_paths[0])
    width = int(first_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(first_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    first_cap.release()
    
    # Setup video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_output_path, fourcc, target_fps, (width, height))
    
    total_frames = 0
    
    try:
        for i, video_path in enumerate(video_paths):
            print(f"📹 Processing video {i+1}/{len(video_paths)}: {os.path.basename(video_path)}")
            
            cap = cv2.VideoCapture(video_path)
            frame_count = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Resize frame to match target dimensions
                if frame.shape[:2] != (height, width):
                    frame = cv2.resize(frame, (width, height))
                
                out.write(frame)
                frame_count += 1
                total_frames += 1
                
                if frame_count % 100 == 0:
                    print(f"   📊 Processed {frame_count} frames from {os.path.basename(video_path)}")
            
            cap.release()
            print(f"   ✅ Completed {os.path.basename(video_path)}: {frame_count} frames")
    
    finally:
        out.release()
    
    total_duration = total_frames / target_fps
    print(f"✅ Video concatenation completed: {total_frames} frames, {total_duration:.2f} seconds")
    
    return total_duration, total_frames

def concatenate_videos_moviepy(video_paths, temp_output_path):
    """
    Concatenate multiple videos using MoviePy (more reliable for different formats).
    Returns the total duration in seconds.
    """
    print(f"🔗 Concatenating {len(video_paths)} videos with MoviePy...")
    
    clips = []
    total_duration = 0
    
    try:
        for i, video_path in enumerate(video_paths):
            print(f"📹 Loading video {i+1}/{len(video_paths)}: {os.path.basename(video_path)}")
            
            clip = VideoFileClip(video_path)
            clips.append(clip)
            total_duration += clip.duration
            
            print(f"   ✅ Loaded: {clip.duration:.2f}s, {clip.fps}fps, {clip.size}")
        
        print(f"🔗 Concatenating {len(clips)} clips...")
        final_clip = concatenate_videoclips(clips, method="compose")
        
        print(f"💾 Writing concatenated video...")
        # FIXED: Remove unsupported temp_audiofile_path parameter
        final_clip.write_videofile(
            temp_output_path, 
            codec="libx264", 
            audio_codec="aac",
            logger=None
        )
        
        total_duration = final_clip.duration
        print(f"✅ Video concatenation completed: {total_duration:.2f} seconds")
        
    finally:
        # Cleanup clips
        for clip in clips:
            clip.close()
        if 'final_clip' in locals():
            final_clip.close()
    
    return total_duration

def process_concatenated_video_with_template(concatenated_video_path, template_path, template_mask, 
                                           output_path, text_settings, target_duration, gpu_settings):
    """
    Process concatenated video with green screen template and adjust duration.
    """
    print(f"🎬 Processing concatenated video with template...")
    print(f"   Target duration: {target_duration:.2f} seconds")
    
    # Check if template is GIF
    if template_path.lower().endswith('.gif'):
        return process_concatenated_video_with_gif_template(
            concatenated_video_path, template_path, output_path, 
            text_settings, target_duration, gpu_settings
        )
    
    # Static template processing
    template = cv2.imread(template_path)
    if template is None:
        raise Exception("Could not load template")
    
    template = cv2.resize(template, (1080, 1920))
    
    # Open concatenated video
    cap = cv2.VideoCapture(concatenated_video_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    video_duration = total_frames / fps
    
    print(f"📹 Concatenated video: {total_frames} frames, {video_duration:.2f}s at {fps}fps")
    
    # Calculate target frames
    target_frames = int(target_duration * fps)
    
    # Setup output writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (1080, 1920))
    
    frames_written = 0
    
    try:
        while frames_written < target_frames:
            ret, frame = cap.read()
            
            if not ret:
                # Video ended, restart from beginning (loop)
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = cap.read()
                if not ret:
                    break
                print(f"🔄 Looping video to match audio duration...")
            
            # Process frame with green screen
            processed_frame = process_frame_with_green_screen(template, frame, template_mask)
            
            # Add text overlay
            if text_settings and text_settings['enabled']:
                from .video_processor import VideoProcessor
                processor = VideoProcessor(None)
                video_name = "Narasi Video"  # Generic name for concatenated video
                processed_frame = processor.add_text_overlay(processed_frame, video_name, text_settings)
            
            # Ensure correct size
            if processed_frame.shape[:2] != (1920, 1080):
                processed_frame = cv2.resize(processed_frame, (1080, 1920))
            
            out.write(processed_frame)
            frames_written += 1
            
            if frames_written % 100 == 0:
                progress = (frames_written / target_frames) * 100
                print(f"📊 Processing: {frames_written}/{target_frames} frames ({progress:.1f}%)")
    
    finally:
        cap.release()
        out.release()
    
    print(f"✅ Template processing completed: {frames_written} frames")
    return True

def process_concatenated_video_with_gif_template(concatenated_video_path, gif_template_path, 
                                               output_path, text_settings, target_duration, gpu_settings):
    """
    Process concatenated video with animated GIF template.
    """
    print(f"🎬 Processing with animated GIF template...")
    
    # Extract GIF frames
    gif_frames, gif_durations = extract_gif_frames(gif_template_path)
    if not gif_frames:
        raise Exception("Could not extract GIF frames")
    
    print(f"🎬 GIF template: {len(gif_frames)} frames")
    
    # Open concatenated video
    cap = cv2.VideoCapture(concatenated_video_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    video_duration = total_frames / fps
    
    # Calculate target frames
    target_frames = int(target_duration * fps)
    gif_frame_count = len(gif_frames)
    
    # Setup output writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (1080, 1920))
    
    frames_written = 0
    
    try:
        while frames_written < target_frames:
            ret, frame = cap.read()
            
            if not ret:
                # Video ended, restart from beginning (loop)
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = cap.read()
                if not ret:
                    break
            
            # Get current GIF frame (cycle through GIF frames)
            gif_frame_index = frames_written % gif_frame_count
            current_gif_frame = gif_frames[gif_frame_index]
            current_gif_frame = cv2.resize(current_gif_frame, (1080, 1920))
            
            # Create mask from current GIF frame
            template_mask = create_green_screen_mask(current_gif_frame)
            
            # Process frame with green screen
            processed_frame = process_frame_with_green_screen(current_gif_frame, frame, template_mask)
            
            # Add text overlay
            if text_settings and text_settings['enabled']:
                from .video_processor import VideoProcessor
                processor = VideoProcessor(None)
                video_name = "Narasi Video"
                processed_frame = processor.add_text_overlay(processed_frame, video_name, text_settings)
            
            # Ensure correct size
            if processed_frame.shape[:2] != (1920, 1080):
                processed_frame = cv2.resize(processed_frame, (1080, 1920))
            
            out.write(processed_frame)
            frames_written += 1
            
            if frames_written % 100 == 0:
                progress = (frames_written / target_frames) * 100
                print(f"📊 Processing: {frames_written}/{target_frames} frames (GIF frame: {gif_frame_index + 1}/{gif_frame_count}) ({progress:.1f}%)")
    
    finally:
        cap.release()
        out.release()
    
    print(f"✅ GIF template processing completed: {frames_written} frames")
    return True

def add_audio_to_narasi_video(temp_video_path, audio_path, output_path, target_duration, 
                             audio_mode="narasi_only", narasi_volume=100, original_volume=30):
    """
    Add audio to narasi video with duration matching and audio mode support.
    """
    print(f"🎵 Adding audio to narasi video (Mode: {audio_mode})...")
    print(f"   Target duration: {target_duration:.2f} seconds")
    print(f"   Narasi volume: {narasi_volume}%")
    if audio_mode == "mixed_audio":
        print(f"   Original volume: {original_volume}%")
    
    video_clip = None
    audio_clip = None
    original_audio_clip = None
    final_clip = None
    
    try:
        video_clip = VideoFileClip(temp_video_path)
        audio_clip = AudioFileClip(audio_path)
        
        print(f"📹 Video duration: {video_clip.duration:.2f}s")
        print(f"🎵 Audio duration: {audio_clip.duration:.2f}s")
        
        # Adjust audio to match target duration
        if audio_clip.duration > target_duration:
            # Cut audio to target duration
            audio_clip = audio_clip.subclip(0, target_duration)
            print(f"✂️ Audio cut to {target_duration:.2f} seconds")
        elif audio_clip.duration < target_duration:
            # Loop audio to match target duration
            loops_needed = int(target_duration / audio_clip.duration) + 1
            audio_clip = audio_clip.loop(duration=target_duration)
            print(f"🔄 Audio looped to {target_duration:.2f} seconds")
        
        # Apply narasi volume
        if narasi_volume != 100:
            narasi_volume_factor = narasi_volume / 100.0
            audio_clip = audio_clip.volumex(narasi_volume_factor)
            print(f"🔊 Narasi audio volume adjusted to {narasi_volume}%")
        
        # Handle audio mode
        if audio_mode == "narasi_only":
            # Use only narasi audio
            final_audio = audio_clip
            print(f"🎙️ Using narasi audio only")
        
        elif audio_mode == "mixed_audio":
            # Mix narasi audio with original video audio
            print(f"🎭 Mixing narasi audio with original video audio...")
            
            # Get original video audio
            if video_clip.audio is not None:
                original_audio_clip = video_clip.audio
                
                # Apply original volume
                if original_volume != 100:
                    original_volume_factor = original_volume / 100.0
                    original_audio_clip = original_audio_clip.volumex(original_volume_factor)
                    print(f"🔊 Original audio volume adjusted to {original_volume}%")
                
                # Adjust original audio duration to match target
                if original_audio_clip.duration > target_duration:
                    original_audio_clip = original_audio_clip.subclip(0, target_duration)
                elif original_audio_clip.duration < target_duration:
                    original_audio_clip = original_audio_clip.loop(duration=target_duration)
                
                # Mix both audio tracks
                from moviepy.editor import CompositeAudioClip
                final_audio = CompositeAudioClip([audio_clip, original_audio_clip])
                print(f"✅ Audio tracks mixed successfully")
            else:
                # No original audio, use narasi only
                final_audio = audio_clip
                print(f"⚠️ No original audio found, using narasi audio only")
        
        else:
            # Default to narasi only
            final_audio = audio_clip
        
        # Set final audio to video
        final_clip = video_clip.set_audio(final_audio)
        
        # Write final video - FIXED: Remove unsupported parameter
        final_clip.write_videofile(
            output_path, 
            codec="libx264", 
            audio_codec="aac", 
            logger=None
        )
        
        print(f"✅ Audio processing completed (Mode: {audio_mode})")
        return True
        
    except Exception as e:
        print(f"❌ Audio processing error: {e}")
        # Fallback: copy video without audio
        try:
            import shutil
            shutil.copy2(temp_video_path, output_path)
            print(f"🔄 Copied video without audio")
        except Exception as copy_error:
            print(f"❌ Failed to copy video: {copy_error}")
        return False
        
    finally:
        # Cleanup
        if video_clip:
            video_clip.close()
        if audio_clip:
            audio_clip.close()
        if original_audio_clip:
            original_audio_clip.close()
        if final_clip:
            final_clip.close()
        
        # Remove temp file
        try:
            if os.path.exists(temp_video_path):
                os.remove(temp_video_path)
        except:
            pass

def process_narasi_mode_bulk(video_folder_path, audio_folder_path, template_path, 
                            output_folder, text_settings, gpu_settings, 
                            audio_mode="narasi_only", narasi_volume=100, original_volume=30,
                            progress_callback=None):
    """
    Main function to process narasi mode with bulk processing:
    1. Match video and audio files by filename
    2. For each match: concatenate videos, process with template, add audio
    3. Create multiple output files
    """
    print(f"🎬 Starting Narasi Mode bulk processing...")
    print(f"   Video folder: {video_folder_path}")
    print(f"   Audio folder: {audio_folder_path}")
    print(f"   Template: {os.path.basename(template_path)}")
    print(f"   Audio mode: {audio_mode}")
    
    from utils.file_operations import get_all_media_files, get_audio_files
    
    # Get video and audio files
    try:
        video_files = get_all_media_files(video_folder_path)
        audio_files = get_audio_files(audio_folder_path)
        
        if not video_files:
            print("❌ No video files found")
            return False
        
        if not audio_files:
            print("❌ No audio files found")
            return False
        
        print(f"📹 Found {len(video_files)} video files")
        print(f"🎵 Found {len(audio_files)} audio files")
        
        # Create file matches
        matches = create_narasi_file_matches(video_files, audio_files)
        
        if not matches:
            print("❌ No matching files found")
            return False
        
        print(f"🔗 Created {len(matches)} matching pairs")
        
        # Process each match
        successful_count = 0
        total_matches = len(matches)
        
        for i, (audio_file, matched_videos) in enumerate(matches.items()):
            if progress_callback:
                overall_progress = (i / total_matches) * 100
                progress_callback(
                    overall_progress, 
                    f"Processing {i+1}/{total_matches}: {audio_file}"
                )
            
            try:
                # Prepare paths
                audio_path = os.path.join(audio_folder_path, audio_file)
                video_paths = [os.path.join(video_folder_path, vf) for vf in matched_videos]
                
                # Create output filename
                audio_base_name = os.path.splitext(audio_file)[0]
                output_path = os.path.join(output_folder, f"narasi_{audio_base_name}.mp4")
                
                print(f"\n🎬 Processing match {i+1}/{total_matches}:")
                print(f"   Audio: {audio_file}")
                print(f"   Videos: {len(matched_videos)} files")
                print(f"   Output: {os.path.basename(output_path)}")
                
                # Process this match
                success = process_single_narasi_match(
                    video_paths, template_path, audio_path, output_path,
                    text_settings, gpu_settings, audio_mode, narasi_volume, original_volume
                )
                
                if success:
                    successful_count += 1
                    print(f"✅ Completed: {audio_file}")
                else:
                    print(f"❌ Failed: {audio_file}")
            
            except Exception as e:
                print(f"❌ Error processing {audio_file}: {e}")
                continue
        
        print(f"\n🎬 Narasi Mode bulk processing completed!")
        print(f"✅ Successfully processed: {successful_count}/{total_matches} matches")
        print(f"📁 Output folder: {output_folder}")
        
        return successful_count > 0
        
    except Exception as e:
        print(f"❌ Narasi Mode bulk processing error: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_narasi_file_matches(video_files, audio_files):
    """Create matches between video and audio files based on filename."""
    matches = {}
    
    # Get base names (without extensions) for audio files
    audio_base_names = {}
    for audio_file in audio_files:
        base_name = os.path.splitext(audio_file)[0].lower()
        audio_base_names[base_name] = audio_file
    
    # For each audio file, find matching videos
    for base_name, audio_file in audio_base_names.items():
        matched_videos = []
        
        # Find videos that match this audio file name
        for video_file in video_files:
            video_base_name = os.path.splitext(video_file)[0].lower()
            
            # Exact match or partial match
            if (base_name == video_base_name or 
                base_name in video_base_name or 
                video_base_name in base_name):
                matched_videos.append(video_file)
        
        # If no exact matches found, use all videos (fallback)
        if not matched_videos:
            print(f"⚠️ No specific matches for '{audio_file}', using all videos")
            matched_videos = video_files.copy()
        
        matches[audio_file] = matched_videos
    
    return matches

def process_single_narasi_match(video_paths, template_path, audio_path, output_path, 
                               text_settings, gpu_settings, audio_mode="narasi_only", 
                               narasi_volume=100, original_volume=30):
    """
    Process a single narasi match:
    1. Concatenate videos for this match
    2. Process with green screen template
    3. Adjust duration to match audio
    4. Add audio
    """
    print(f"🎬 Processing single narasi match...")
    print(f"   Videos: {len(video_paths)} files")
    print(f"   Audio: {os.path.basename(audio_path)}")
    print(f"   Audio mode: {audio_mode}")
    
    # Get audio duration first
    try:
        audio_clip = AudioFileClip(audio_path)
        target_duration = audio_clip.duration
        audio_clip.close()
    except Exception as e:
        print(f"❌ Could not read audio duration: {e}")
        return False
    
    print(f"🎵 Target duration (from audio): {target_duration:.2f} seconds")
    
    # Create temporary files
    temp_dir = tempfile.mkdtemp()
    concatenated_video_path = os.path.join(temp_dir, "concatenated_video.mp4")
    processed_video_path = os.path.join(temp_dir, "processed_video.mp4")
    
    try:
        # Step 1: Concatenate videos
        print(f"\n📝 Step 1: Concatenating videos...")
        video_duration = concatenate_videos_moviepy(video_paths, concatenated_video_path)
        
        # Step 2: Process with template
        print(f"\n📝 Step 2: Processing with template...")
        
        # Get template for mask creation
        if template_path.lower().endswith('.gif'):
            # For GIF templates, extract first frame for mask
            gif_frames, _ = extract_gif_frames(template_path)
            if gif_frames:
                template_for_mask = gif_frames[0]
            else:
                raise Exception("Could not extract GIF frames")
        else:
            template_for_mask = cv2.imread(template_path)
            if template_for_mask is None:
                raise Exception("Could not load template")
        
        template_for_mask = cv2.resize(template_for_mask, (1080, 1920))
        template_mask = create_green_screen_mask(template_for_mask)
        
        if np.sum(template_mask) == 0:
            raise Exception("No green screen detected in template")
        
        success = process_concatenated_video_with_template(
            concatenated_video_path, template_path, template_mask,
            processed_video_path, text_settings, target_duration, gpu_settings
        )
        
        if not success:
            raise Exception("Template processing failed")
        
        # Step 3: Add audio
        print(f"\n📝 Step 3: Adding audio...")
        success = add_audio_to_narasi_video(
            processed_video_path, audio_path, output_path, target_duration,
            audio_mode, narasi_volume, original_volume
        )
        
        if success:
            print(f"✅ Narasi Mode processing completed successfully!")
            print(f"📁 Output: {output_path}")
            return True
        else:
            print(f"❌ Audio processing failed")
            return False
            
    except Exception as e:
        print(f"❌ Narasi Mode processing error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup temporary files
        try:
            import shutil
            shutil.rmtree(temp_dir)
            print(f"🧹 Cleaned up temporary files")
        except Exception as cleanup_error:
            print(f"⚠️ Cleanup error: {cleanup_error}")

# Keep the original function for backward compatibility
def process_narasi_mode(video_paths, template_path, audio_path, output_path, 
                       text_settings, gpu_settings, audio_mode="narasi_only", 
                       narasi_volume=100, original_volume=30):
    """
    Original narasi mode function (for backward compatibility).
    """
    return process_single_narasi_match(video_paths, template_path, audio_path, output_path, 
                                     text_settings, gpu_settings, audio_mode, 
                                     narasi_volume, original_volume)