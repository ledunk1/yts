"""
Dual Green Screen Detection Module
Auto-detects multiple green screen areas in templates
"""

import cv2
import numpy as np
from utils.green_screen_detection import create_green_screen_mask

def detect_dual_green_screen_areas(template_image):
    """
    Detect two separate green screen areas in template.
    Returns positions and sizes for video placement.
    """
    print("🔍 Detecting dual green screen areas...")
    
    # Create green screen mask
    mask = create_green_screen_mask(template_image)
    
    # Find contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if len(contours) < 2:
        print(f"⚠️ Only {len(contours)} green screen area(s) detected, expected 2")
        return None
    
    # Sort contours by area (largest first)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)
    
    # Get the two largest areas
    area1_contour = contours[0]
    area2_contour = contours[1]
    
    # Get bounding rectangles
    area1_rect = cv2.boundingRect(area1_contour)
    area2_rect = cv2.boundingRect(area2_contour)
    
    # Calculate areas
    area1_size = cv2.contourArea(area1_contour)
    area2_size = cv2.contourArea(area2_contour)
    
    print(f"✅ Detected dual green screen areas:")
    print(f"   Area 1: {area1_rect} (size: {area1_size:.0f} pixels)")
    print(f"   Area 2: {area2_rect} (size: {area2_size:.0f} pixels)")
    
    # Determine which area is for folder1 and folder2
    # Usually, we assign based on position (top/left = folder1, bottom/right = folder2)
    x1, y1, w1, h1 = area1_rect
    x2, y2, w2, h2 = area2_rect
    
    # Sort by vertical position (top area = folder1, bottom area = folder2)
    if y1 < y2:
        folder1_area = {
            'rect': area1_rect,
            'contour': area1_contour,
            'position': 'top'
        }
        folder2_area = {
            'rect': area2_rect,
            'contour': area2_contour,
            'position': 'bottom'
        }
    else:
        folder1_area = {
            'rect': area2_rect,
            'contour': area2_contour,
            'position': 'top'
        }
        folder2_area = {
            'rect': area1_rect,
            'contour': area1_contour,
            'position': 'bottom'
        }
    
    print(f"📍 Area assignment:")
    print(f"   Folder 1 (top): {folder1_area['rect']}")
    print(f"   Folder 2 (bottom): {folder2_area['rect']}")
    
    return {
        'folder1_area': folder1_area,
        'folder2_area': folder2_area,
        'total_areas': len(contours)
    }

def create_dual_masks(template_image, dual_areas):
    """
    Create separate masks for each green screen area.
    """
    h, w = template_image.shape[:2]
    
    # Create mask for folder1 area
    folder1_mask = np.zeros((h, w), dtype=np.uint8)
    cv2.fillPoly(folder1_mask, [dual_areas['folder1_area']['contour']], 255)
    
    # Create mask for folder2 area
    folder2_mask = np.zeros((h, w), dtype=np.uint8)
    cv2.fillPoly(folder2_mask, [dual_areas['folder2_area']['contour']], 255)
    
    return folder1_mask, folder2_mask

def fit_video_to_dual_mask(video_frame, mask_area, video_source):
    """
    Fit video frame to specific green screen area.
    """
    contour = mask_area['contour']
    rect = mask_area['rect']
    x, y, w, h = rect
    
    # Resize video to fit the area
    resized_video = cv2.resize(video_frame, (w, h))
    
    # Create contour mask for this specific area
    contour_mask = np.zeros((h, w), dtype=np.uint8)
    adjusted_contour = contour - [x, y]
    cv2.fillPoly(contour_mask, [adjusted_contour], 255)
    
    # Apply mask to video
    masked_video = cv2.bitwise_and(resized_video, resized_video, mask=contour_mask)
    
    # Create alpha channel for blending
    alpha = contour_mask.astype(np.float32) / 255.0
    alpha = np.stack([alpha] * 3, axis=-1)
    
    return masked_video, alpha, rect

def process_dual_frame_with_green_screen(template_frame, video1_frame, video2_frame, dual_areas):
    """
    Process frame with dual green screen replacement.
    """
    result = template_frame.copy()
    
    try:
        # Process video from folder1
        if video1_frame is not None:
            masked_video1, alpha1, rect1 = fit_video_to_dual_mask(
                video1_frame, dual_areas['folder1_area'], 'folder1'
            )
            x1, y1, w1, h1 = rect1
            
            # Blend video1 into template
            roi1 = result[y1:y1+h1, x1:x1+w1]
            blended_roi1 = (masked_video1 * alpha1 + roi1 * (1 - alpha1)).astype(np.uint8)
            result[y1:y1+h1, x1:x1+w1] = blended_roi1
        
        # Process video from folder2
        if video2_frame is not None:
            masked_video2, alpha2, rect2 = fit_video_to_dual_mask(
                video2_frame, dual_areas['folder2_area'], 'folder2'
            )
            x2, y2, w2, h2 = rect2
            
            # Blend video2 into template
            roi2 = result[y2:y2+h2, x2:x2+w2]
            blended_roi2 = (masked_video2 * alpha2 + roi2 * (1 - alpha2)).astype(np.uint8)
            result[y2:y2+h2, x2:x2+w2] = blended_roi2
    
    except Exception as e:
        print(f"⚠️ Error in dual frame processing: {e}")
        return template_frame
    
    return result

def validate_dual_green_screen_template(template_path):
    """
    Validate if template has exactly 2 green screen areas.
    """
    try:
        template = cv2.imread(template_path)
        if template is None:
            return False, "Could not load template"
        
        dual_areas = detect_dual_green_screen_areas(template)
        
        if dual_areas is None:
            return False, "Template must have exactly 2 green screen areas"
        
        if dual_areas['total_areas'] < 2:
            return False, f"Only {dual_areas['total_areas']} green screen area(s) found, need 2"
        
        return True, f"✅ Dual green screen template validated: {dual_areas['total_areas']} areas detected"
    
    except Exception as e:
        return False, f"Error validating template: {str(e)}"