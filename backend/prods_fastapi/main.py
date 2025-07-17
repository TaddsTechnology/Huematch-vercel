from fastapi import FastAPI, Query, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import json
import math
import os
from typing import List, Optional, Dict
from color_utils import get_color_mapping, get_seasonal_palettes, get_monk_hex_codes
from pathlib import Path
import re
import numpy as np
import cv2
from webcolors import hex_to_rgb, rgb_to_hex
import io
from PIL import Image
import logging
import random

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Path to the processed data directory
PROCESSED_DATA_DIR = Path("../processed_data")

# Get color mapping from the color_utils module
color_mapping = get_color_mapping()
seasonal_palettes = get_seasonal_palettes()
monk_hex_codes = get_monk_hex_codes()

# Add default Monk skin tone hex codes if they're not loaded from files
if not monk_hex_codes:
    monk_hex_codes = {
        "Monk01": ["#f6ede4"],
        "Monk02": ["#f3e7db"],
        "Monk03": ["#f7ead0"],
        "Monk04": ["#eadaba"],
        "Monk05": ["#d7bd96"],
        "Monk06": ["#a07e56"],
        "Monk07": ["#825c43"],
        "Monk08": ["#604134"],
        "Monk09": ["#3a312a"],
        "Monk10": ["#292420"]
    }

# Map Monk skin tones to seasonal types for better color recommendations
monk_to_seasonal = {
    "Monk01": "Light Spring",
    "Monk02": "Light Spring",
    "Monk03": "Clear Spring",
    "Monk04": "Warm Spring",
    "Monk05": "Soft Autumn",
    "Monk06": "Warm Autumn",
    "Monk07": "Deep Autumn",
    "Monk08": "Deep Winter",
    "Monk09": "Cool Winter",
    "Monk10": "Clear Winter"
}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Monk skin tone scale for analysis
MONK_SKIN_TONES = {
    'Monk 1': '#f6ede4',
    'Monk 2': '#f3e7db', 
    'Monk 3': '#f7ead0',
    'Monk 4': '#eadaba',
    'Monk 5': '#d7bd96',
    'Monk 6': '#a07e56',
    'Monk 7': '#825c43',
    'Monk 8': '#604134',
    'Monk 9': '#3a312a',
    'Monk 10': '#292420'
}

def apply_lighting_correction(image_array: np.ndarray) -> np.ndarray:
    """
    Apply advanced lighting correction using CLAHE and LAB color space
    """
    try:
        # Convert to LAB color space for better lighting correction
        lab_image = cv2.cvtColor(image_array, cv2.COLOR_RGB2LAB)
        
        # Split LAB channels
        l_channel, a_channel, b_channel = cv2.split(lab_image)
        
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization) to L channel
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l_channel_corrected = clahe.apply(l_channel)
        
        # Merge channels back
        corrected_lab = cv2.merge([l_channel_corrected, a_channel, b_channel])
        
        # Convert back to RGB
        corrected_rgb = cv2.cvtColor(corrected_lab, cv2.COLOR_LAB2RGB)
        
        # Additional gamma correction for better exposure
        gamma = 1.2  # Slightly brighten the image
        corrected_rgb = np.power(corrected_rgb / 255.0, gamma) * 255.0
        corrected_rgb = np.clip(corrected_rgb, 0, 255).astype(np.uint8)
        
        return corrected_rgb
        
    except Exception as e:
        logger.warning(f"Lighting correction failed: {e}, using original image")
        return image_array

def apply_white_balance(image_array: np.ndarray) -> np.ndarray:
    """
    Apply simple white balance correction
    """
    try:
        # Convert to float for calculations
        image_float = image_array.astype(np.float64)
        
        # Calculate mean values for each channel
        mean_r = np.mean(image_float[:, :, 0])
        mean_g = np.mean(image_float[:, :, 1])
        mean_b = np.mean(image_float[:, :, 2])
        
        # Calculate scaling factors
        gray_world_mean = (mean_r + mean_g + mean_b) / 3
        
        # Apply white balance correction
        if mean_r > 0:
            image_float[:, :, 0] = image_float[:, :, 0] * (gray_world_mean / mean_r)
        if mean_g > 0:
            image_float[:, :, 1] = image_float[:, :, 1] * (gray_world_mean / mean_g)
        if mean_b > 0:
            image_float[:, :, 2] = image_float[:, :, 2] * (gray_world_mean / mean_b)
        
        # Clip values and convert back to uint8
        balanced_image = np.clip(image_float, 0, 255).astype(np.uint8)
        
        return balanced_image
        
    except Exception as e:
        logger.warning(f"White balance correction failed: {e}, using original image")
        return image_array

def apply_gentle_lighting_correction(image_array: np.ndarray) -> np.ndarray:
    """
    Apply gentle lighting correction optimized for lighter skin tones
    """
    try:
        # Convert to LAB color space for better lighting correction
        lab_image = cv2.cvtColor(image_array, cv2.COLOR_RGB2LAB)
        
        # Split LAB channels
        l_channel, a_channel, b_channel = cv2.split(lab_image)
        
        # Apply gentler CLAHE for lighter skin tones
        clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))  # Reduced clip limit
        l_channel_corrected = clahe.apply(l_channel)
        
        # Merge channels back
        corrected_lab = cv2.merge([l_channel_corrected, a_channel, b_channel])
        
        # Convert back to RGB
        corrected_rgb = cv2.cvtColor(corrected_lab, cv2.COLOR_LAB2RGB)
        
        # Gentler gamma correction for lighter skin tones
        gamma = 1.1  # Less aggressive gamma correction
        corrected_rgb = np.power(corrected_rgb / 255.0, gamma) * 255.0
        corrected_rgb = np.clip(corrected_rgb, 0, 255).astype(np.uint8)
        
        return corrected_rgb
        
    except Exception as e:
        logger.warning(f"Gentle lighting correction failed: {e}, using original image")
        return image_array

def apply_improved_white_balance(image_array: np.ndarray) -> np.ndarray:
    """
    Apply improved white balance correction with better handling of light skin tones
    """
    try:
        # Convert to float for calculations
        image_float = image_array.astype(np.float64)
        
        # Calculate mean values for each channel, excluding very dark and very bright pixels
        # This helps with light skin tone detection
        mask = (image_float[:, :, 0] > 30) & (image_float[:, :, 0] < 250) & \
               (image_float[:, :, 1] > 30) & (image_float[:, :, 1] < 250) & \
               (image_float[:, :, 2] > 30) & (image_float[:, :, 2] < 250)
        
        if np.sum(mask) > 0:
            mean_r = np.mean(image_float[:, :, 0][mask])
            mean_g = np.mean(image_float[:, :, 1][mask])
            mean_b = np.mean(image_float[:, :, 2][mask])
        else:
            # Fallback to full image if mask is empty
            mean_r = np.mean(image_float[:, :, 0])
            mean_g = np.mean(image_float[:, :, 1])
            mean_b = np.mean(image_float[:, :, 2])
        
        # Calculate scaling factors with gentle correction
        gray_world_mean = (mean_r + mean_g + mean_b) / 3
        
        # Apply gentler white balance correction
        correction_strength = 0.7  # Reduce correction strength for lighter skin tones
        
        if mean_r > 0:
            factor_r = (gray_world_mean / mean_r - 1) * correction_strength + 1
            image_float[:, :, 0] = image_float[:, :, 0] * factor_r
        if mean_g > 0:
            factor_g = (gray_world_mean / mean_g - 1) * correction_strength + 1
            image_float[:, :, 1] = image_float[:, :, 1] * factor_g
        if mean_b > 0:
            factor_b = (gray_world_mean / mean_b - 1) * correction_strength + 1
            image_float[:, :, 2] = image_float[:, :, 2] * factor_b
        
        # Clip values and convert back to uint8
        balanced_image = np.clip(image_float, 0, 255).astype(np.uint8)
        
        return balanced_image
        
    except Exception as e:
        logger.warning(f"Improved white balance correction failed: {e}, using original image")
        return image_array

def analyze_skin_tone_simple(image_array: np.ndarray) -> Dict:
    """
    Highly refined skin tone analysis with special optimization for very light skin tones
    """
    try:
        # Step 1: Minimal processing for light skin tones to preserve true colors
        processed_image = apply_minimal_processing(image_array)
        
        # Step 2: Advanced multi-method skin color extraction
        skin_colors = extract_skin_colors_advanced(processed_image)
        
        # Step 3: Intelligent color analysis with light skin bias
        final_color = analyze_colors_with_light_bias(skin_colors, processed_image)
        
        # Step 4: Enhanced Monk tone matching with light skin priority
        closest_monk = find_closest_monk_tone_enhanced(final_color)
        
        # Step 5: Advanced confidence scoring
        confidence = calculate_advanced_confidence(skin_colors, final_color)
        
        return {
            'monk_skin_tone': closest_monk['monk_id'],
            'monk_tone_display': closest_monk['monk_name'],
            'monk_hex': closest_monk['monk_hex'],
            'derived_hex_code': closest_monk['derived_hex'],
            'dominant_rgb': final_color.astype(int).tolist(),
            'confidence': confidence,
            'success': True
        }
    
    except Exception as e:
        logger.error(f"Error in skin tone analysis: {e}")
        return get_fallback_result()

def apply_minimal_processing(image_array: np.ndarray) -> np.ndarray:
    """
    Apply minimal processing to preserve light skin tones
    """
    try:
        # Very gentle processing only
        processed = image_array.copy()
        
        # Only apply slight gamma correction if image is too dark
        mean_brightness = np.mean(cv2.cvtColor(processed, cv2.COLOR_RGB2GRAY))
        
        if mean_brightness < 120:  # Only if image is quite dark
            gamma = 1.05  # Very gentle gamma correction
            processed = np.power(processed / 255.0, gamma) * 255.0
            processed = np.clip(processed, 0, 255).astype(np.uint8)
        
        return processed
        
    except Exception as e:
        logger.warning(f"Minimal processing failed: {e}, using original image")
        return image_array

def extract_skin_colors_advanced(image_array: np.ndarray) -> List[np.ndarray]:
    """
    Advanced skin color extraction with multiple sophisticated methods
    """
    skin_colors = []
    h, w = image_array.shape[:2]
    
    # Method 1: Advanced HSV-based detection optimized for light skin
    hsv = cv2.cvtColor(image_array, cv2.COLOR_RGB2HSV)
    
    # Highly optimized ranges for light skin detection
    light_skin_ranges = [
        # Very light skin (almost white)
        ([0, 0, 220], [30, 30, 255]),
        # Light skin with slight warmth
        ([0, 5, 200], [25, 50, 255]),
        # Light skin with more color
        ([0, 10, 180], [30, 80, 240]),
        # Light-medium skin
        ([0, 15, 150], [25, 100, 220])
    ]
    
    combined_mask = None
    for lower, upper in light_skin_ranges:
        mask = cv2.inRange(hsv, np.array(lower, dtype=np.uint8), np.array(upper, dtype=np.uint8))
        if combined_mask is None:
            combined_mask = mask
        else:
            combined_mask = cv2.bitwise_or(combined_mask, mask)
    
    # Clean up mask
    kernel = np.ones((2, 2), np.uint8)
    combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel)
    combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel)
    
    skin_pixels = image_array[combined_mask > 0]
    if len(skin_pixels) > 50:
        skin_colors.append(np.mean(skin_pixels, axis=0))
    
    # Method 2: Strategic face region sampling
    face_regions = [
        # Forehead (most reliable for light skin)
        image_array[h//8:h//3, w//3:2*w//3],
        # Upper cheeks
        image_array[h//3:h//2, w//4:3*w//4],
        # Nose bridge
        image_array[h//3:2*h//3, 2*w//5:3*w//5],
        # Lower cheeks
        image_array[h//2:2*h//3, w//4:3*w//4],
        # Chin area
        image_array[2*h//3:5*h//6, 2*w//5:3*w//5]
    ]
    
    for region in face_regions:
        if region.size > 0:
            # Use only pixels in the light skin tone range
            region_gray = cv2.cvtColor(region, cv2.COLOR_RGB2GRAY)
            light_mask = (region_gray > 150) & (region_gray < 250)  # Focus on light pixels
            
            if np.sum(light_mask) > 20:
                light_pixels = region[light_mask]
                region_color = np.mean(light_pixels, axis=0)
                
                # Only add if it's in the light skin range
                if np.mean(region_color) > 180:  # Light skin threshold
                    skin_colors.append(region_color)
    
    # Method 3: Percentile-based analysis for light skin
    center_region = image_array[h//4:3*h//4, w//4:3*w//4]
    if center_region.size > 0:
        center_flat = center_region.reshape(-1, 3)
        
        # Use 75th percentile (lighter pixels) instead of mean
        percentile_75 = np.percentile(center_flat, 75, axis=0)
        if np.mean(percentile_75) > 160:  # Light skin threshold
            skin_colors.append(percentile_75)
    
    # Method 4: Weighted sampling based on brightness
    if len(skin_colors) == 0:  # Fallback method
        # Sample the brightest regions of the face
        face_area = image_array[h//4:3*h//4, w//4:3*w//4]
        if face_area.size > 0:
            face_gray = cv2.cvtColor(face_area, cv2.COLOR_RGB2GRAY)
            bright_threshold = np.percentile(face_gray, 80)  # Top 20% brightest pixels
            bright_mask = face_gray > bright_threshold
            
            if np.sum(bright_mask) > 100:
                bright_pixels = face_area[bright_mask]
                skin_colors.append(np.mean(bright_pixels, axis=0))
    
    return skin_colors

def analyze_colors_with_light_bias(skin_colors: List[np.ndarray], image_array: np.ndarray) -> np.ndarray:
    """
    Analyze extracted colors with strong bias towards light skin tones
    """
    if not skin_colors:
        # Ultimate fallback - use brightest regions
        h, w = image_array.shape[:2]
        center = image_array[h//3:2*h//3, w//3:2*w//3]
        gray = cv2.cvtColor(center, cv2.COLOR_RGB2GRAY)
        brightest_mask = gray > np.percentile(gray, 85)
        if np.sum(brightest_mask) > 0:
            return np.mean(center[brightest_mask], axis=0)
        else:
            return np.mean(center.reshape(-1, 3), axis=0)
    
    skin_colors_array = np.array(skin_colors)
    
    # Strongly bias towards lighter colors
    brightness_scores = np.mean(skin_colors_array, axis=1)
    
    # Weight colors by brightness - lighter colors get much higher weight
    weights = np.power(brightness_scores / 255.0, 0.3)  # Strong light bias
    weights = weights / np.sum(weights)  # Normalize
    
    # Weighted average favoring lighter tones
    final_color = np.average(skin_colors_array, axis=0, weights=weights)
    
    # Ensure result is not too dark for light skin
    if np.mean(final_color) < 200:
        # Boost lighter colors in the mix
        light_colors = skin_colors_array[brightness_scores > 200]
        if len(light_colors) > 0:
            final_color = np.mean(light_colors, axis=0)
    
    return final_color

def find_closest_monk_tone_enhanced(rgb_color: np.ndarray) -> Dict:
    """
    Enhanced Monk tone matching with special handling for light skin tones
    """
    # Log the detected color
    logger.info(f"Detected skin color: RGB({rgb_color[0]:.1f}, {rgb_color[1]:.1f}, {rgb_color[2]:.1f})")
    
    # Check if this is clearly a light skin tone
    avg_brightness = np.mean(rgb_color)
    is_light_skin = avg_brightness > 200
    
    if is_light_skin:
        logger.info("Light skin tone detected - prioritizing Monk 1-4")
        
        # For very light skin, only consider Monk 1-4
        light_monk_tones = {
            'Monk 1': '#f6ede4',
            'Monk 2': '#f3e7db',
            'Monk 3': '#f7ead0',
            'Monk 4': '#eadaba'
        }
        
        min_distance = float('inf')
        closest_monk = None
        
        for monk_name, monk_hex in light_monk_tones.items():
            monk_rgb = np.array(hex_to_rgb(monk_hex))
            
            # Enhanced distance calculation for light skin
            distance = calculate_light_skin_distance(rgb_color, monk_rgb)
            
            logger.info(f"Light skin - {monk_name}: distance={distance:.2f}")
            
            if distance < min_distance:
                min_distance = distance
                closest_monk = monk_name
    else:
        # Standard processing for non-light skin
        min_distance = float('inf')
        closest_monk = None
        
        for monk_name, monk_hex in MONK_SKIN_TONES.items():
            monk_rgb = np.array(hex_to_rgb(monk_hex))
            
            # Standard distance calculation
            distance_rgb = np.sqrt(np.sum((rgb_color - monk_rgb) ** 2))
            
            if distance_rgb < min_distance:
                min_distance = distance_rgb
                closest_monk = monk_name
    
    # Format result
    monk_number = closest_monk.split()[1]
    monk_id = f"Monk{monk_number.zfill(2)}"
    derived_hex = rgb_to_hex((int(rgb_color[0]), int(rgb_color[1]), int(rgb_color[2])))
    
    logger.info(f"Final selection: {monk_id} ({closest_monk}) with distance {min_distance:.2f}")
    
    return {
        'monk_name': closest_monk,
        'monk_id': monk_id,
        'monk_hex': MONK_SKIN_TONES[closest_monk],
        'derived_hex': derived_hex
    }

def calculate_light_skin_distance(color1: np.ndarray, color2: np.ndarray) -> float:
    """
    Special distance calculation optimized for light skin tones
    """
    # Standard euclidean distance
    euclidean = np.sqrt(np.sum((color1 - color2) ** 2))
    
    # Brightness difference penalty
    brightness_diff = abs(np.mean(color1) - np.mean(color2))
    
    # Color variance penalty (light skin should have low variance)
    color_var_penalty = np.var(color1) * 0.1
    
    # Combined distance favoring similar brightness
    combined_distance = euclidean + brightness_diff * 0.5 + color_var_penalty
    
    return combined_distance

def calculate_advanced_confidence(skin_colors: List[np.ndarray], final_color: np.ndarray) -> float:
    """
    Advanced confidence calculation
    """
    base_confidence = 0.7
    
    # More skin color samples = higher confidence
    sample_bonus = min(len(skin_colors) * 0.05, 0.2)
    
    # Light skin gets confidence boost (easier to detect)
    if np.mean(final_color) > 200:
        light_bonus = 0.1
    else:
        light_bonus = 0.0
    
    # Consistency bonus
    if len(skin_colors) > 1:
        colors_array = np.array(skin_colors)
        consistency = 1.0 / (1.0 + np.var(colors_array))
        consistency_bonus = consistency * 0.1
    else:
        consistency_bonus = 0.0
    
    total_confidence = base_confidence + sample_bonus + light_bonus + consistency_bonus
    
    return max(0.0, min(1.0, total_confidence))
        
        
    return {
        'monk_name': closest_monk,
        'monk_id': monk_id,
        'monk_hex': MONK_SKIN_TONES[closest_monk],
        'derived_hex': derived_hex
    }

def find_closest_monk_tone_improved(rgb_color: np.ndarray) -> Dict:
    """
    Improved function to find the closest Monk skin tone using multiple color spaces
    """
    min_distance = float('inf')
    closest_monk = None
    
    # Log the detected average color for debugging
    logger.info(f"Detected average skin color: RGB({rgb_color[0]:.1f}, {rgb_color[1]:.1f}, {rgb_color[2]:.1f})")
    
    # Calculate distances using multiple methods
    for monk_name, monk_hex in MONK_SKIN_TONES.items():
        monk_rgb = np.array(hex_to_rgb(monk_hex))
        
        # Method 1: Euclidean distance in RGB space
        distance_rgb = np.sqrt(np.sum((rgb_color - monk_rgb) ** 2))
        
        # Method 2: Weighted RGB distance (human perception)
        # Red contributes less to perceived brightness, green more, blue least
        weight_r, weight_g, weight_b = 0.3, 0.59, 0.11
        distance_weighted = np.sqrt(
            weight_r * (rgb_color[0] - monk_rgb[0]) ** 2 +
            weight_g * (rgb_color[1] - monk_rgb[1]) ** 2 +
            weight_b * (rgb_color[2] - monk_rgb[2]) ** 2
        )
        
        # Method 3: HSV distance (focusing on hue and saturation)
        def rgb_to_hsv(rgb):
            rgb_normalized = rgb / 255.0
            r, g, b = rgb_normalized
            
            max_val = max(r, g, b)
            min_val = min(r, g, b)
            diff = max_val - min_val
            
            # Hue calculation
            if diff == 0:
                h = 0
            elif max_val == r:
                h = (60 * ((g - b) / diff) + 360) % 360
            elif max_val == g:
                h = (60 * ((b - r) / diff) + 120) % 360
            else:
                h = (60 * ((r - g) / diff) + 240) % 360
            
            # Saturation calculation
            s = 0 if max_val == 0 else diff / max_val
            
            # Value calculation
            v = max_val
            
            return np.array([h, s, v])
        
        input_hsv = rgb_to_hsv(rgb_color)
        monk_hsv = rgb_to_hsv(monk_rgb)
        
        # Calculate HSV distance with proper hue wrapping
        hue_diff = min(abs(input_hsv[0] - monk_hsv[0]), 360 - abs(input_hsv[0] - monk_hsv[0]))
        distance_hsv = np.sqrt(
            (hue_diff / 360) ** 2 +
            (input_hsv[1] - monk_hsv[1]) ** 2 +
            (input_hsv[2] - monk_hsv[2]) ** 2
        )
        
        # Combine distances with weights
        # RGB distance has most weight, but HSV helps with color perception
        combined_distance = 0.5 * distance_rgb + 0.3 * distance_weighted + 0.2 * distance_hsv * 100
        
        # Debug logging
        logger.info(f"Monk {monk_name}: RGB_dist={distance_rgb:.2f}, Weighted_dist={distance_weighted:.2f}, HSV_dist={distance_hsv:.2f}, Combined={combined_distance:.2f}")
        
        if combined_distance < min_distance:
            min_distance = combined_distance
            closest_monk = monk_name
    
    # Format monk ID (e.g., "Monk 5" -> "Monk05")
    monk_number = closest_monk.split()[1]
    monk_id = f"Monk{monk_number.zfill(2)}"
    
    # Convert RGB to hex
    derived_hex = rgb_to_hex((int(rgb_color[0]), int(rgb_color[1]), int(rgb_color[2])))
    
    logger.info(f"Selected Monk tone: {monk_id} ({closest_monk}) with distance {min_distance:.2f}")
    
    return {
        'monk_name': closest_monk,
        'monk_id': monk_id,
        'monk_hex': MONK_SKIN_TONES[closest_monk],
        'derived_hex': derived_hex
    }

def get_fallback_result() -> Dict:
    """
    Return a fallback result when analysis fails
    """
    # Randomly select from common skin tones instead of always Monk05
    fallback_tones = ['Monk 3', 'Monk 4', 'Monk 5', 'Monk 6']
    selected_tone = random.choice(fallback_tones)
    
    monk_number = selected_tone.split()[1]
    monk_id = f"Monk{monk_number.zfill(2)}"
    monk_hex = MONK_SKIN_TONES[selected_tone]
    
    logger.warning(f"Using fallback skin tone: {selected_tone}")
    
    return {
        'monk_skin_tone': monk_id,
        'monk_tone_display': selected_tone,
        'monk_hex': monk_hex,
        'derived_hex_code': monk_hex,
        'dominant_rgb': list(hex_to_rgb(monk_hex)),
        'confidence': 0.3,  # Lower confidence for fallback
        'success': False,  # Indicate this is a fallback
        'message': 'Using fallback skin tone due to analysis failure'
    }

def color_distance(color1, color2):
    """Calculate Euclidean distance between two RGB colors."""
    # Convert hex strings to RGB tuples
    def hex_to_rgb(hex_color):
        # Remove # if present
        hex_color = hex_color.replace('#', '')
        # Convert to RGB
        try:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return (r, g, b)
        except (ValueError, IndexError):
            # Return black as fallback for invalid hex colors
            return (0, 0, 0)
    
    # Convert hex colors to RGB
    rgb1 = hex_to_rgb(color1)
    rgb2 = hex_to_rgb(color2)
    
    # Calculate Euclidean distance
    return math.sqrt(sum((c1 - c2) ** 2 for c1, c2 in zip(rgb1, rgb2)))

def advanced_color_distance(color1, color2, method='euclidean'):
    """Calculate color distance using various methods for better color matching."""
    def hex_to_rgb(hex_color):
        hex_color = hex_color.replace('#', '')
        try:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return (r, g, b)
        except (ValueError, IndexError):
            return (0, 0, 0)
    
    def rgb_to_lab(rgb):
        """Convert RGB to LAB color space for better perceptual distance."""
        r, g, b = [x / 255.0 for x in rgb]
        
        # Convert to XYZ first
        def gamma_correction(c):
            return pow((c + 0.055) / 1.055, 2.4) if c > 0.04045 else c / 12.92
        
        r, g, b = map(gamma_correction, [r, g, b])
        
        # Observer = 2°, Illuminant = D65
        x = r * 0.4124 + g * 0.3576 + b * 0.1805
        y = r * 0.2126 + g * 0.7152 + b * 0.0722
        z = r * 0.0193 + g * 0.1192 + b * 0.9505
        
        # Convert XYZ to LAB
        def f(t):
            return pow(t, 1/3) if t > 0.008856 else (7.787 * t + 16/116)
        
        x, y, z = x / 0.95047, y / 1.00000, z / 1.08883
        fx, fy, fz = map(f, [x, y, z])
        
        L = 116 * fy - 16
        a = 500 * (fx - fy)
        b = 200 * (fy - fz)
        
        return (L, a, b)
    
    rgb1 = hex_to_rgb(color1)
    rgb2 = hex_to_rgb(color2)
    
    if method == 'euclidean':
        return math.sqrt(sum((c1 - c2) ** 2 for c1, c2 in zip(rgb1, rgb2)))
    elif method == 'lab':
        lab1 = rgb_to_lab(rgb1)
        lab2 = rgb_to_lab(rgb2)
        return math.sqrt(sum((c1 - c2) ** 2 for c1, c2 in zip(lab1, lab2)))
    elif method == 'weighted':
        # Weighted RGB distance considering human perception
        r1, g1, b1 = rgb1
        r2, g2, b2 = rgb2
        return math.sqrt(2 * (r1 - r2) ** 2 + 4 * (g1 - g2) ** 2 + 3 * (b1 - b2) ** 2)
    else:
        return color_distance(color1, color2)

def calculate_product_score(product, user_preferences, skin_tone=None, color_method='lab'):
    """Calculate a comprehensive score for product recommendations."""
    score = 0.0
    max_score = 0.0
    
    # Brand preference scoring (weight: 25%)
    brand_weight = 0.25
    if 'preferred_brands' in user_preferences and user_preferences['preferred_brands']:
        max_score += brand_weight
        product_brand = str(product.get('brand', '')).lower()
        preferred_brands = [b.lower() for b in user_preferences['preferred_brands']]
        if any(brand in product_brand for brand in preferred_brands):
            score += brand_weight
    
    # Price range scoring (weight: 20%)
    price_weight = 0.20
    if 'price_range' in user_preferences and user_preferences['price_range']:
        max_score += price_weight
        product_price = str(product.get('price', ''))
        # Extract numeric price
        price_match = re.search(r'\d+(?:\.\d+)?', product_price)
        if price_match:
            product_price_val = float(price_match.group())
            min_price = user_preferences['price_range'].get('min', 0)
            max_price = user_preferences['price_range'].get('max', 1000)
            
            if min_price <= product_price_val <= max_price:
                score += price_weight
            else:
                # Partial score based on how close it is to the range
                if product_price_val < min_price:
                    proximity = 1 - min((min_price - product_price_val) / min_price, 1)
                else:
                    proximity = 1 - min((product_price_val - max_price) / max_price, 1)
                score += price_weight * proximity
    
    # Color matching scoring (weight: 30%)
    color_weight = 0.30
    if skin_tone and 'baseColour' in product:
        max_score += color_weight
        product_color = str(product.get('baseColour', ''))
        
        # Get seasonal type from skin tone
        seasonal_type = None
        if skin_tone in monk_to_seasonal:
            seasonal_type = monk_to_seasonal[skin_tone]
        
        # Check if color is in recommended palette
        if seasonal_type and seasonal_type in seasonal_palettes:
            recommended_colors = seasonal_palettes[seasonal_type]
            if isinstance(recommended_colors, list):
                if any(color.lower() in product_color.lower() for color in recommended_colors):
                    score += color_weight
            elif isinstance(recommended_colors, dict) and 'recommended' in recommended_colors:
                if any(color.lower() in product_color.lower() for color in recommended_colors['recommended']):
                    score += color_weight
    
    # Product type preference scoring (weight: 15%)
    type_weight = 0.15
    if 'preferred_types' in user_preferences and user_preferences['preferred_types']:
        max_score += type_weight
        product_type = str(product.get('Product Type', '') or product.get('product_type', '')).lower()
        preferred_types = [t.lower() for t in user_preferences['preferred_types']]
        if any(ptype in product_type for ptype in preferred_types):
            score += type_weight
    
    # Diversity bonus (weight: 10%)
    diversity_weight = 0.10
    max_score += diversity_weight
    # This would be calculated based on how different this product is from previously recommended items
    # For now, we'll give a base diversity score
    score += diversity_weight * 0.5
    
    # Normalize score to 0-1 range
    return score / max_score if max_score > 0 else 0.0

def get_diverse_recommendations(products, user_preferences, skin_tone=None, limit=20):
    """Get diverse product recommendations using advanced scoring."""
    # Calculate scores for all products
    scored_products = []
    for product in products:
        score = calculate_product_score(product, user_preferences, skin_tone)
        scored_products.append((product, score))
    
    # Sort by score descending
    scored_products.sort(key=lambda x: x[1], reverse=True)
    
    # Apply diversity filter to avoid too similar products
    diverse_products = []
    seen_categories = set()
    seen_brands = set()
    
    for product, score in scored_products:
        if len(diverse_products) >= limit:
            break
            
        category = str(product.get('Product Type', '') or product.get('product_type', '')).lower()
        brand = str(product.get('brand', '')).lower()
        
        # Limit products per category and brand for diversity
        category_count = sum(1 for p in diverse_products if 
                           str(p.get('Product Type', '') or p.get('product_type', '')).lower() == category)
        brand_count = sum(1 for p in diverse_products if 
                         str(p.get('brand', '')).lower() == brand)
        
        if category_count < 3 and brand_count < 2:  # Max 3 per category, 2 per brand
            diverse_products.append(product)
    
    return diverse_products

# Load data files with fallback options
def load_data_file(primary_path, fallback_path, default_df=None):
    """Load a data file with fallback options."""
    if os.path.exists(primary_path):
        return pd.read_csv(primary_path).fillna("")
    elif os.path.exists(fallback_path):
        return pd.read_csv(fallback_path).fillna("")
    else:
        print(f"Warning: Neither {primary_path} nor {fallback_path} found.")
        return default_df if default_df is not None else pd.DataFrame()

# Load CSV data for H&M products
df_hm = load_data_file(
    "../processed_data/hm_products_hm_products.csv",
    "hm_products2.csv",
    pd.DataFrame(columns=["Product Name", "Price", "Image URL", "Product Type", "brand", "gender", "baseColour", "masterCategory", "subCategory"])
)

# Load CSV data for Ulta & Sephora products
df_sephora = load_data_file(
    "processed_data/all_makeup_products.csv",
    "ulta_with_mst_index.csv",
    pd.DataFrame(columns=["product", "brand", "price", "imgSrc", "mst", "hex", "desc", "product_type"])
)

# Load outfit data from the specified CSV files
df_outfit1 = load_data_file(
    "../processed_data/outfit_products_outfit1.csv",
    "outfit_products_outfit1.csv",
    pd.DataFrame(columns=["products", "brand", "Product Type", "gender", "baseColour", "masterCategory", "subCategory"])
)

df_outfit2 = load_data_file(
    "../processed_data/outfit_products_outfit2.csv",
    "outfit_products_outfit2.csv",
    pd.DataFrame(columns=["products", "brand", "Product Type", "gender", "baseColour", "masterCategory", "subCategory"])
)

# Load apparel data
df_apparel = load_data_file(
    "processed_data/outfit_products.csv",
    "apparel.csv",
    pd.DataFrame(columns=["Product Name", "Price", "Image URL", "gender", "baseColour", "masterCategory", "subCategory"])
)

# Load color suggestions
df_color_suggestions = load_data_file(
    "processed_data/color_suggestions.csv",
    "color_suggestions.csv",
    pd.DataFrame(columns=["skin_tone", "suitable_colors"])
)

# Load combined outfits products
df_combined_outfits = load_data_file(
    "processed_data/all_combined_outfits.csv",
    "../processed_data/all_combined_outfits.csv",
    pd.DataFrame(columns=["brand", "product_name", "price", "gender", "image_url", "base_colour", "product_type", "sub_category", "master_category", "source"])
)

@app.get("/")
def home():
    return {"message": "Welcome to the API!"}

@app.get("/color-suggestions")
def get_color_suggestions(skin_tone: str = Query(None)):
    """Get color suggestions for a specific skin tone."""
    if skin_tone:
        filtered_df = df_color_suggestions[df_color_suggestions["skin_tone"].str.contains(skin_tone, case=False)]
    else:
        filtered_df = df_color_suggestions
    
    return {
        "data": filtered_df.to_dict(orient="records"),
        "total_items": len(filtered_df)
    }

@app.get("/apparel")
def get_apparel(
    gender: str = Query(None, description="Filter by gender (e.g., 'Men', 'Women')"),
    color: List[str] = Query(None, description="Filter by one or more baseColour values (e.g., 'Blue', 'Black')"),
    page: int = Query(1, description="Page number (default: 1)", ge=1),
    limit: int = Query(24, description="Items per page (default: 24)", le=100)
):
    """
    Get random outfit products with pagination.
    
    - gender: Filter by gender
    - color: Filter by one or more colors
    - page: Page number (starts at 1)
    - limit: Number of items per page (max 100)
    """
    # Prepare to use the outfit data
    outfit_products = []
    
    # Try to extract products from outfit1 CSV
    if not df_outfit1.empty and 'products' in df_outfit1.columns:
        try:
            # The products column contains a JSON string with product data
            products_str = df_outfit1.iloc[0]['products']
            if isinstance(products_str, str):
                import ast
                outfit_products.extend(ast.literal_eval(products_str))
        except (ValueError, SyntaxError, IndexError) as e:
            print(f"Error parsing outfit1 products: {e}")
    
    # Try to extract products from outfit2 CSV
    if not df_outfit2.empty and 'products' in df_outfit2.columns:
        try:
            # The products column contains a JSON string with product data
            products_str = df_outfit2.iloc[0]['products']
            if isinstance(products_str, str):
                import ast
                outfit_products.extend(ast.literal_eval(products_str))
        except (ValueError, SyntaxError, IndexError) as e:
            print(f"Error parsing outfit2 products: {e}")
    
    # If we don't have enough outfit products, add H&M products
    if len(outfit_products) < 24 and not df_hm.empty:
        for _, row in df_hm.iterrows():
            outfit_products.append({
                'brand': row.get('brand', 'H&M'),
                'price': row.get('Price', ''),
                'images': row.get('Image URL', ''),
                'product_name': row.get('Product Name', '')
            })
    
    # Add combined outfits products - Always include ALL products from combined CSV
    if not df_combined_outfits.empty:
        for _, row in df_combined_outfits.iterrows():
            outfit_products.append({
                'brand': row.get('brand', 'Fashion Brand'),
                'price': row.get('price', ''),
                'images': row.get('image_url', ''),
                'product_name': row.get('product_name', ''),
                'baseColour': row.get('base_colour', ''),
                'gender': row.get('gender', ''),
                'masterCategory': row.get('master_category', ''),
                'Product Type': row.get('product_type', ''),
                'source': row.get('source', 'combined')
            })
    
    # If we still don't have enough products, use the apparel dataframe as fallback
    if len(outfit_products) < 24:
        filtered_df = df_apparel.copy()
        for _, row in filtered_df.iterrows():
            outfit_products.append({
                'brand': row.get('brand', 'Fashion Brand'),
                'price': row.get('Price', ''),
                'images': row.get('Image URL', ''),
                'product_name': row.get('Product Name', '')
            })
    
    # Apply color filtering if provided
    if color and len(color) > 0:
        # Map color names if provided
        color = [color_mapping.get(c, c) for c in color]  # Use the original value if key is not found
        color = list(set(color))  # Remove duplicates
        color = [c for c in color if pd.notna(c)]

        # Filter products by color if possible
        # Note: This is a simple implementation since we don't have color data for all products
        filtered_products = []
        for product in outfit_products:
            # If the product has a baseColour field and it matches one of our colors, include it
            if 'baseColour' in product and product['baseColour'] in color:
                filtered_products.append(product)
            # Otherwise, include a random subset of products to ensure we have enough results
            elif np.random.random() < 0.3:  # 30% chance to include
                filtered_products.append(product)
        
        # If we have enough filtered products, use them
        if len(filtered_products) >= 10:
            outfit_products = filtered_products
    
    # Shuffle the products for randomness
    import random
    random.seed()  # Use a different seed each time
    random.shuffle(outfit_products)
    
    # Calculate pagination
    total_items = len(outfit_products)
    total_pages = math.ceil(total_items / limit)
    start = (page - 1) * limit
    end = min(start + limit, total_items)
    
    # Get paginated data
    paginated_products = outfit_products[start:end]
    
    # Prepare the result with consistent field names
    result = []
    for product in paginated_products:
        # Generate a random price if missing
        price = product.get("price", "")
        if not price or pd.isna(price) or price == "":
            # Generate random price between $19.99 and $99.99
            price = f"${np.random.randint(1999, 9999) / 100:.2f}"
        
        # Create a standardized product object
        product_obj = {
            "Product Name": product.get("product_name", "Stylish Outfit"),
            "Price": price,
            "Image URL": product.get("images", ""),
            "Product Type": product.get("Product Type", "Apparel")
        }
        
        # Add additional fields if they exist
        if 'gender' in product and product['gender']:
            product_obj["gender"] = product["gender"]
        
        if 'baseColour' in product and product['baseColour']:
            product_obj["baseColour"] = product["baseColour"]
        
        if 'masterCategory' in product and product['masterCategory']:
            product_obj["masterCategory"] = product["masterCategory"]
        
        result.append(product_obj)

    return {
        "data": result,
        "page": page,
        "limit": limit,
        "total_items": total_items,
        "total_pages": total_pages
    }

@app.get("/api/random-outfits")
async def get_random_outfits(limit: int = Query(default=8)):
    """Get random outfits from H&M dataset."""
    try:
        # Randomly sample products from the H&M dataset
        random_products = df_hm.sample(n=min(limit, len(df_hm))).to_dict(orient="records")
        
        # Clean up the data
        cleaned_products = []
        for product in random_products:
            cleaned_products.append({
                "Product Name": product.get("Product Name", ""),
                "Price": product.get("Price", "$29.99"),
                "Image URL": product.get("Image URL", ""),
                "Product Type": product.get("Product Type", "")
            })
        
        return {
            "data": cleaned_products,
            "total_items": len(cleaned_products)
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {"error": str(e)}

# Endpoint to fetch products from combined outfits dataset
@app.get("/api/combined-outfits")
async def get_combined_outfits():
    """Get all combined outfit products."""
    try:
        products = df_combined_outfits.to_dict(orient="records")
        return {
            "data": products,
            "total_items": len(products)
        }
    except Exception as e:
        print(f"Error fetching combined outfits: {str(e)}")
        return {"error": str(e)}

# **H&M Products API**
@app.get("/products")
def get_products(product_type: str = Query(None), random: bool = Query(False)):
    """Fetch H&M products filtered by product type."""
    filtered_df = df_hm.copy()
    
    if product_type:
        # Split product types by comma and create regex pattern
        types = product_type.split(',')
        pattern = '|'.join(types)
        filtered_df = filtered_df[
            filtered_df["Product Type"].str.contains(pattern, case=False, na=False)
        ]
    
    # Always return random products for outfits
    if random or len(filtered_df) > 15:
        filtered_df = filtered_df.sample(n=min(15, len(filtered_df)))
    
    # Convert DataFrame to records
    products = filtered_df.to_dict(orient="records")
    
    # Ensure all necessary fields are present
    for product in products:
        product["Product_Name"] = product.get("Product Name", "")
        product["Brand"] = product.get("Brand", "H&M")
        product["Price"] = product.get("Price", "$ 29.99")
        product["Image_URL"] = product.get("Image URL", "")
    
    return products

@app.post("/api/recommendations")
async def get_recommendations(request: dict):
    """Fetch recommended H&M products based on type (makeup or outfit)."""
    filtered_df1 = df_hm.copy()
    
    recommendation_type = request.get("type", "makeup")

    if recommendation_type == "makeup":
        # filtered_df = filtered_df[
        #     filtered_df["Product Type"].str.contains("makeup|cosmetic|lipstick|foundation", case=False, na=False)
        # ]
        pass
    else:  # outfit recommendations
        filtered_df1 = filtered_df1[
            filtered_df1["Product Type"].str.contains("dress|top|shirt|pants", case=False, na=False)
        ]

    # Take random 15 products
    filtered_df = filtered_df.sample(n=min(15, len(filtered_df)))

    return {"products": json.loads(filtered_df.to_json(orient="records"))}

# **Ulta & Sephora Products API**
@app.get("/data/")
def get_data(
    mst: Optional[str] = None,
    ogcolor: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(24, ge=1, le=100),
    product_type: Optional[str] = None
):
    """
    Get makeup products with pagination and filtering.
    
    - mst: Monk Skin Tone
    - ogcolor: Original color in hex (without #)
    - page: Page number (starts at 1)
    - limit: Number of items per page (max 100)
    - product_type: Filter by product type (comma-separated for multiple types)
    """
    # Try to load from processed_data directory first, then fallback to other locations
    makeup_file_paths = [
        os.path.join(PROCESSED_DATA_DIR, "sample_makeup_products.csv"),
        os.path.join(PROCESSED_DATA_DIR, "all_makeup_products.csv"),
        "processed_data/all_makeup_products.csv",
        "ulta_with_mst_index.csv"
    ]
    
    df = None
    for file_path in makeup_file_paths:
        if os.path.exists(file_path):
            try:
                df = pd.read_csv(file_path).fillna("")
                print(f"Successfully loaded makeup data from {file_path}")
                break
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
    
    if df is None or df.empty:
        df = pd.DataFrame(columns=["product", "brand", "price", "imgSrc", "mst", "hex", "desc", "product_type"])
        print("Using empty DataFrame as fallback")
    
    if df.empty:
        return {"data": [], "total_items": 0, "total_pages": 0, "page": page, "limit": limit}
    
    # Filter by MST if provided
    if mst:
        # Handle different formats of Monk skin tone (e.g., "Monk03", "Monk 3")
        monk_id = mst
        if " " in mst:
            # Extract just the ID part (e.g., "Monk" from "Monk 3")
            parts = mst.split()
            if len(parts) >= 2 and parts[0].lower().startswith("monk"):
                try:
                    # Try to convert the number part to an integer and format it
                    monk_num = int(parts[1])
                    monk_id = f"Monk{monk_num:02d}"
                except ValueError:
                    # If conversion fails, use the original value
                    monk_id = mst
        
        # Try exact match first
        filtered_df = df[df['mst'].str.lower() == monk_id.lower()]
        
        # If no exact matches, try partial match
        if len(filtered_df) < 5:
            filtered_df = df[df['mst'].str.lower().str.contains(monk_id.lower(), na=False)]
        
        # If still not enough results, try matching by skin tone category
        if len(filtered_df) < 5 and monk_id in monk_to_seasonal:
            seasonal_type = monk_to_seasonal[monk_id]
            seasonal_df = df[df['mst'].str.lower().str.contains(seasonal_type.lower(), na=False)]
            filtered_df = pd.concat([filtered_df, seasonal_df]).drop_duplicates()
        
        # If we have results from filtering, use them
        if len(filtered_df) > 0:
            df = filtered_df
    
    # Filter by product type if provided
    if product_type:
        # Split comma-separated product types
        product_types = [pt.strip() for pt in product_type.split(',')]
        
        # Create regex pattern for matching any of the product types
        pattern = '|'.join([f'(?i){re.escape(pt)}' for pt in product_types])
        
        # Filter DataFrame
        if 'product_type' in df.columns:
            filtered_df = df[df['product_type'].str.contains(pattern, regex=True, na=False)]
            # Only use filtered results if we found some
            if len(filtered_df) > 0:
                df = filtered_df
    
    # Sort by color similarity if ogcolor is provided
    if ogcolor and len(ogcolor) == 6:
        # Calculate color distance for each product
        if 'hex' in df.columns:
            # Remove # if present in hex
            df['hex'] = df['hex'].str.replace('#', '')
            
            # Calculate distance only for valid hex colors
            valid_hex_mask = df['hex'].str.match(r'^[0-9A-Fa-f]{6}$', na=False)
            
            if valid_hex_mask.any():
                valid_df = df[valid_hex_mask].copy()
                valid_df['distance'] = valid_df['hex'].apply(lambda x: color_distance(x, ogcolor))
                
                # Sort by distance (closest color match first)
                valid_df = valid_df.sort_values(['distance'])
                
                # Combine with invalid hex colors (which will be at the end)
                df = pd.concat([valid_df, df[~valid_hex_mask]])
    
    # If we have very few results, add some random products
    if len(df) < 10:
        # Try to load the Sephora dataset if it's not already loaded
        if df_sephora is not None and not df_sephora.empty:
            # Get some random products to supplement
            random_products = df_sephora.sample(min(30, len(df_sephora)))
            df = pd.concat([df, random_products])
        else:
            # Try to load from the sample file
            sample_file = os.path.join(PROCESSED_DATA_DIR, "sample_makeup_products.csv")
            if os.path.exists(sample_file):
                try:
                    sample_df = pd.read_csv(sample_file).fillna("")
                    df = pd.concat([df, sample_df])
                except Exception as e:
                    print(f"Error loading sample makeup products: {e}")
    
    # Remove duplicate products based on product name and brand
    if 'product' in df.columns and 'brand' in df.columns:
        df = df.drop_duplicates(subset=['product', 'brand'])
    
    # Generate additional makeup products if we still don't have enough
    if len(df) < 50:
        # Create synthetic makeup products with realistic names and brands
        makeup_brands = ["Fenty Beauty", "MAC Cosmetics", "NARS", "Maybelline", "L'Oreal", 
                         "Dior", "Chanel", "Estée Lauder", "Clinique", "Revlon", "NYX", 
                         "Bobbi Brown", "Urban Decay", "Too Faced", "Benefit"]
        
        product_types = ["Foundation", "Concealer", "Powder", "Blush", "Bronzer", 
                         "Highlighter", "Eyeshadow", "Eyeliner", "Mascara", 
                         "Lipstick", "Lip Gloss", "Lip Liner", "Primer", "Setting Spray"]
        
        product_adjectives = ["Matte", "Dewy", "Radiant", "Luminous", "Velvet", 
                              "Creamy", "Shimmering", "Satin", "Glossy", "Ultra", 
                              "Hydrating", "Long-lasting", "Waterproof", "Intense"]
        
        product_colors = ["Rose Gold", "Nude", "Coral", "Mauve", "Berry", "Plum", 
                          "Peach", "Taupe", "Bronze", "Copper", "Gold", "Silver", 
                          "Ruby", "Emerald", "Sapphire", "Amber", "Sienna"]
        
        # Generate random hex colors that match the Monk skin tone if provided
        def generate_matching_hex():
            if mst:
                # Extract Monk ID
                monk_id = mst
                if " " in mst:
                    parts = mst.split()
                    if len(parts) >= 2 and parts[0].lower().startswith("monk"):
                        try:
                            monk_num = int(parts[1])
                            monk_id = f"Monk{monk_num:02d}"
                        except ValueError:
                            monk_id = mst
                
                # Get base colors for this Monk skin tone
                if monk_id in monk_hex_codes:
                    base_hex = monk_hex_codes[monk_id][0].replace('#', '')
                    # Generate a color with slight variation
                    try:
                        r = int(base_hex[0:2], 16)
                        g = int(base_hex[2:4], 16)
                        b = int(base_hex[4:6], 16)
                        
                        # Add some variation
                        r = max(0, min(255, r + np.random.randint(-30, 30)))
                        g = max(0, min(255, g + np.random.randint(-30, 30)))
                        b = max(0, min(255, b + np.random.randint(-30, 30)))
                        
                        return f"{r:02x}{g:02x}{b:02x}"
                    except (ValueError, IndexError):
                        pass
            
            # Default: generate random hex
            return f"{np.random.randint(0, 256):02x}{np.random.randint(0, 256):02x}{np.random.randint(0, 256):02x}"
        
        # Generate synthetic products
        synthetic_products = []
        for _ in range(50 - len(df)):
            brand = np.random.choice(makeup_brands)
            prod_type = np.random.choice(product_types)
            adjective = np.random.choice(product_adjectives)
            color = np.random.choice(product_colors)
            
            product_name = f"{adjective} {prod_type} - {color}"
            price = f"${np.random.randint(1599, 4999) / 100:.2f}"
            hex_color = generate_matching_hex()
            
            synthetic_products.append({
                "product": product_name,
                "brand": brand,
                "price": price,
                "imgSrc": f"https://via.placeholder.com/150/{hex_color}/FFFFFF?text={brand.replace(' ', '+')}",
                "mst": mst if mst else "",
                "hex": hex_color,
                "desc": f"Beautiful {adjective.lower()} finish {prod_type.lower()} in {color.lower()} shade",
                "product_type": prod_type
            })
        
        # Add synthetic products to the dataframe
        synthetic_df = pd.DataFrame(synthetic_products)
        df = pd.concat([df, synthetic_df])
    
    # Calculate total items and pages
    total_items = len(df)
    total_pages = math.ceil(total_items / limit)
    
    # Apply pagination
    start_idx = (page - 1) * limit
    end_idx = min(start_idx + limit, len(df))
    
    # Get paginated data
    paginated_df = df.iloc[start_idx:end_idx]
    
    # Convert to list of dictionaries
    result = []
    for _, row in paginated_df.iterrows():
        # Generate a random price if missing
        price = row.get("price", "")
        if not price or pd.isna(price) or price == "":
            # Generate random price between $15.99 and $49.99
            price = f"${np.random.randint(1599, 4999) / 100:.2f}"
        
        # Handle NaN values to prevent JSON serialization errors
        item = {
            "product_name": str(row.get("product", "")) if not pd.isna(row.get("product", "")) else "",
            "brand": str(row.get("brand", "")) if not pd.isna(row.get("brand", "")) else "",
            "price": price,
            "image_url": str(row.get("imgSrc", "")) if not pd.isna(row.get("imgSrc", "")) else "",
            "mst": str(row.get("mst", "")) if not pd.isna(row.get("mst", "")) else "",
            "desc": str(row.get("desc", "")) if not pd.isna(row.get("desc", "")) else "",
        }
        
        # Add product_type if available
        if 'product_type' in row and not pd.isna(row['product_type']):
            item["product_type"] = str(row['product_type'])
            
        result.append(item)

    return {
        "data": result,
        "total_items": total_items,
        "total_pages": total_pages,
        "page": page,
        "limit": limit
    }

@app.get("/makeup-types", response_model=dict)
def get_makeup_types():
    """Get all available makeup product types."""
    df = load_data_file(
        "processed_data/all_makeup_products.csv",
        "ulta_with_mst_index.csv",
        pd.DataFrame(columns=["product", "brand", "price", "imgSrc", "mst", "hex", "desc"])
    )
    
    if 'product_type' in df.columns:
        # Get unique product types, excluding NaN values
        types = df['product_type'].dropna().unique().tolist()
        # Sort alphabetically
        types.sort()
        return {"types": types}
    else:
        # Return default types if product_type column doesn't exist
        default_types = [
            "Foundation", "Concealer", "Powder", "Blush", "Bronzer", 
            "Highlighter", "Eyeshadow", "Eyeliner", "Mascara", 
            "Lipstick", "Lip Gloss", "Lip Liner", "Primer", "Setting Spray"
        ]
        return {"types": default_types}

@app.get("/api/color-recommendations")
async def get_color_recommendations(
    skin_tone: str = Query(None, description="Skin tone category (e.g., 'Winter', 'Summer')"),
    hex_color: str = Query(None, description="Hex color code of the skin tone (e.g., '#f6ede4')")
):
    """
    Get color recommendations based on skin tone.
    
    Returns only colors that suit the user's skin tone.
    """
    # Process Monk skin tone format if provided
    monk_id = None
    if skin_tone and skin_tone.startswith("Monk"):
        # Handle different formats (e.g., "Monk03", "Monk 3")
        monk_id = skin_tone
        if " " in skin_tone:
            parts = skin_tone.split()
            if len(parts) >= 2 and parts[0].lower() == "monk":
                try:
                    # Try to convert the number part to an integer and format it
                    monk_num = int(parts[1])
                    monk_id = f"Monk{monk_num:02d}"
                except ValueError:
                    # If conversion fails, use the original value
                    monk_id = skin_tone
    
    # If we have a Monk skin tone, convert it to seasonal type
    seasonal_type = None
    if monk_id and monk_id in monk_to_seasonal:
        seasonal_type = monk_to_seasonal[monk_id]
    
    # Try to load seasonal palettes from the processed_data directory
    seasonal_palettes_file = os.path.join(PROCESSED_DATA_DIR, "seasonal_palettes.json")
    local_seasonal_palettes = {}
    
    if os.path.exists(seasonal_palettes_file):
        try:
            with open(seasonal_palettes_file, 'r') as f:
                local_seasonal_palettes = json.load(f)
        except Exception as e:
            print(f"Error loading seasonal_palettes.json: {e}")
    
    # Enhanced color palettes for each seasonal type
    enhanced_palettes = {
        "Clear Spring": [
            {"name": "Light Yellow", "hex": "#FFF9D7"},
            {"name": "Pale Yellow", "hex": "#F1EB9C"},
            {"name": "Cream Yellow", "hex": "#F5E1A4"},
            {"name": "Peach", "hex": "#F8CFA9"},
            {"name": "Bright Yellow", "hex": "#FCE300"},
            {"name": "Golden Yellow", "hex": "#FDD26E"},
            {"name": "Sunflower Yellow", "hex": "#FFCD00"},
            {"name": "Amber", "hex": "#FFB81C"},
            {"name": "Coral", "hex": "#FF7F50"},
            {"name": "Warm Coral", "hex": "#FF6B53"},
            {"name": "Bright Coral", "hex": "#FF4040"},
            {"name": "Salmon Pink", "hex": "#FF91A4"},
            {"name": "Warm Pink", "hex": "#FF9999"},
            {"name": "Bright Pink", "hex": "#FF69B4"},
            {"name": "Watermelon", "hex": "#FD5B78"},
            {"name": "Bright Red", "hex": "#FF0000"},
            {"name": "Tomato Red", "hex": "#FF6347"},
            {"name": "Warm Red", "hex": "#E32636"},
            {"name": "Bright Orange", "hex": "#FF4500"},
            {"name": "Tangerine", "hex": "#F28500"},
            {"name": "Golden Orange", "hex": "#FFA000"},
            {"name": "Apricot", "hex": "#FBCEB1"},
            {"name": "Peach Orange", "hex": "#FFCC99"},
            {"name": "Spring Green", "hex": "#00FF7F"},
            {"name": "Bright Green", "hex": "#66FF00"},
            {"name": "Apple Green", "hex": "#8DB600"},
            {"name": "Grass Green", "hex": "#7CFC00"},
            {"name": "Lime Green", "hex": "#32CD32"},
            {"name": "Mint Green", "hex": "#98FB98"},
            {"name": "Aquamarine", "hex": "#7FFFD4"},
            {"name": "Turquoise", "hex": "#40E0D0"},
            {"name": "Sky Blue", "hex": "#87CEEB"},
            {"name": "Bright Blue", "hex": "#007FFF"},
            {"name": "Periwinkle", "hex": "#CCCCFF"},
            {"name": "Clear Blue", "hex": "#1F75FE"},
            {"name": "Bright Purple", "hex": "#9370DB"},
            {"name": "Lavender", "hex": "#E6E6FA"},
            {"name": "Lilac", "hex": "#C8A2C8"},
            {"name": "Orchid", "hex": "#DA70D6"},
            {"name": "Fuchsia", "hex": "#FF00FF"}
        ],
        "Light Spring": [
            {"name": "Light Yellow", "hex": "#FFF9D7"},
            {"name": "Pale Yellow", "hex": "#F1EB9C"},
            {"name": "Cream Yellow", "hex": "#F5E1A4"},
            {"name": "Peach", "hex": "#F8CFA9"},
            {"name": "Soft Coral", "hex": "#F88379"},
            {"name": "Light Coral", "hex": "#F08080"},
            {"name": "Pastel Pink", "hex": "#FFD1DC"},
            {"name": "Blush Pink", "hex": "#FFB6C1"},
            {"name": "Light Apricot", "hex": "#FDD5B1"},
            {"name": "Pale Orange", "hex": "#FFDAB9"},
            {"name": "Soft Peach", "hex": "#FFDAB9"},
            {"name": "Light Mint", "hex": "#98FB98"},
            {"name": "Pastel Green", "hex": "#77DD77"},
            {"name": "Soft Aqua", "hex": "#7FFFD4"},
            {"name": "Light Turquoise", "hex": "#AFEEEE"},
            {"name": "Pale Blue", "hex": "#B0E0E6"},
            {"name": "Baby Blue", "hex": "#89CFF0"},
            {"name": "Soft Periwinkle", "hex": "#CCCCFF"},
            {"name": "Pastel Lavender", "hex": "#D8BFD8"},
            {"name": "Light Lilac", "hex": "#C8A2C8"}
        ],
        "Warm Spring": [
            {"name": "Bright Yellow", "hex": "#FCE300"},
            {"name": "Golden Yellow", "hex": "#FDD26E"},
            {"name": "Sunflower Yellow", "hex": "#FFCD00"},
            {"name": "Amber", "hex": "#FFB81C"},
            {"name": "Warm Coral", "hex": "#FF6B53"},
            {"name": "Terracotta", "hex": "#E2725B"},
            {"name": "Rust", "hex": "#B7410E"},
            {"name": "Pumpkin", "hex": "#FF7518"},
            {"name": "Warm Orange", "hex": "#FF8C00"},
            {"name": "Golden Orange", "hex": "#FFA000"},
            {"name": "Honey", "hex": "#E6C200"},
            {"name": "Mustard", "hex": "#FFDB58"},
            {"name": "Olive Green", "hex": "#808000"},
            {"name": "Moss Green", "hex": "#8A9A5B"},
            {"name": "Avocado", "hex": "#568203"},
            {"name": "Warm Teal", "hex": "#008080"},
            {"name": "Peacock Blue", "hex": "#005F69"},
            {"name": "Warm Turquoise", "hex": "#30D5C8"},
            {"name": "Warm Periwinkle", "hex": "#8F99FB"},
            {"name": "Golden Brown", "hex": "#996515"}
        ]
    }
    
    # Add more seasonal palettes as needed
    enhanced_palettes["Soft Autumn"] = [
        {"name": "Camel", "hex": "#C19A6B"},
        {"name": "Soft Gold", "hex": "#D4AF37"},
        {"name": "Muted Olive", "hex": "#6B8E23"},
        {"name": "Sage Green", "hex": "#9CAF88"},
        {"name": "Dusty Teal", "hex": "#4F7369"},
        {"name": "Soft Burgundy", "hex": "#8D4E85"},
        {"name": "Muted Coral", "hex": "#F08080"},
        {"name": "Dusty Rose", "hex": "#C08081"},
        {"name": "Soft Rust", "hex": "#CD5C5C"},
        {"name": "Terracotta", "hex": "#E2725B"},
        {"name": "Warm Taupe", "hex": "#AF8F6F"},
        {"name": "Soft Brown", "hex": "#A67B5B"},
        {"name": "Muted Orange", "hex": "#E67F33"},
        {"name": "Soft Mustard", "hex": "#DEBA13"},
        {"name": "Muted Gold", "hex": "#D4AF37"},
        {"name": "Soft Khaki", "hex": "#BDB76B"},
        {"name": "Muted Turquoise", "hex": "#66CDAA"},
        {"name": "Dusty Blue", "hex": "#6699CC"},
        {"name": "Soft Navy", "hex": "#39537B"},
        {"name": "Muted Purple", "hex": "#8B7B8B"}
    ]
    
    enhanced_palettes["Warm Autumn"] = [
        {"name": "Rust", "hex": "#B7410E"},
        {"name": "Burnt Orange", "hex": "#CC5500"},
        {"name": "Pumpkin", "hex": "#FF7518"},
        {"name": "Copper", "hex": "#B87333"},
        {"name": "Bronze", "hex": "#CD7F32"},
        {"name": "Olive Green", "hex": "#808000"},
        {"name": "Moss Green", "hex": "#8A9A5B"},
        {"name": "Forest Green", "hex": "#228B22"},
        {"name": "Warm Brown", "hex": "#8B4513"},
        {"name": "Chocolate", "hex": "#7B3F00"},
        {"name": "Caramel", "hex": "#C68E17"},
        {"name": "Mustard", "hex": "#FFDB58"},
        {"name": "Golden Yellow", "hex": "#FFDF00"},
        {"name": "Amber", "hex": "#FFBF00"},
        {"name": "Warm Teal", "hex": "#008080"},
        {"name": "Deep Turquoise", "hex": "#00CED1"},
        {"name": "Warm Burgundy", "hex": "#8C001A"},
        {"name": "Tomato Red", "hex": "#FF6347"},
        {"name": "Brick Red", "hex": "#CB4154"},
        {"name": "Terracotta", "hex": "#E2725B"}
    ]
    
    enhanced_palettes["Deep Autumn"] = [
        {"name": "Burgundy", "hex": "#800020"},
        {"name": "Deep Red", "hex": "#8B0000"},
        {"name": "Ruby", "hex": "#9B111E"},
        {"name": "Brick Red", "hex": "#CB4154"},
        {"name": "Rust", "hex": "#B7410E"},
        {"name": "Burnt Orange", "hex": "#CC5500"},
        {"name": "Copper", "hex": "#B87333"},
        {"name": "Chocolate", "hex": "#7B3F00"},
        {"name": "Coffee", "hex": "#6F4E37"},
        {"name": "Deep Olive", "hex": "#556B2F"},
        {"name": "Forest Green", "hex": "#228B22"},
        {"name": "Deep Teal", "hex": "#004D40"},
        {"name": "Dark Turquoise", "hex": "#00868B"},
        {"name": "Deep Purple", "hex": "#301934"},
        {"name": "Plum", "hex": "#8E4585"},
        {"name": "Aubergine", "hex": "#614051"},
        {"name": "Deep Gold", "hex": "#B8860B"},
        {"name": "Amber", "hex": "#FFBF00"},
        {"name": "Mustard", "hex": "#FFDB58"},
        {"name": "Deep Moss", "hex": "#4A5D23"}
    ]
    
    enhanced_palettes["Deep Winter"] = [
        {"name": "Black", "hex": "#000000"},
        {"name": "Charcoal", "hex": "#36454F"},
        {"name": "Navy", "hex": "#000080"},
        {"name": "Royal Blue", "hex": "#4169E1"},
        {"name": "Deep Purple", "hex": "#301934"},
        {"name": "Plum", "hex": "#8E4585"},
        {"name": "Burgundy", "hex": "#800020"},
        {"name": "Deep Red", "hex": "#8B0000"},
        {"name": "Ruby", "hex": "#9B111E"},
        {"name": "Emerald", "hex": "#046307"},
        {"name": "Forest Green", "hex": "#228B22"},
        {"name": "Deep Teal", "hex": "#004D40"},
        {"name": "Dark Turquoise", "hex": "#00868B"},
        {"name": "Sapphire", "hex": "#0F52BA"},
        {"name": "Deep Magenta", "hex": "#8B008B"},
        {"name": "Aubergine", "hex": "#614051"},
        {"name": "Deep Fuchsia", "hex": "#C154C1"},
        {"name": "Deep Raspberry", "hex": "#872657"},
        {"name": "Deep Violet", "hex": "#9400D3"},
        {"name": "Deep Indigo", "hex": "#4B0082"}
    ]
    
    enhanced_palettes["Cool Winter"] = [
        {"name": "Black", "hex": "#000000"},
        {"name": "Charcoal", "hex": "#36454F"},
        {"name": "Navy", "hex": "#000080"},
        {"name": "Royal Blue", "hex": "#4169E1"},
        {"name": "Ice Blue", "hex": "#99FFFF"},
        {"name": "Cool Pink", "hex": "#FF69B4"},
        {"name": "Magenta", "hex": "#FF00FF"},
        {"name": "Fuchsia", "hex": "#FF00FF"},
        {"name": "Blue Red", "hex": "#FF0038"},
        {"name": "Cherry Red", "hex": "#D2042D"},
        {"name": "Cool Purple", "hex": "#800080"},
        {"name": "Violet", "hex": "#8F00FF"},
        {"name": "Lavender", "hex": "#E6E6FA"},
        {"name": "Cool Emerald", "hex": "#50C878"},
        {"name": "Pine Green", "hex": "#01796F"},
        {"name": "Cool Teal", "hex": "#008080"},
        {"name": "Silver", "hex": "#C0C0C0"},
        {"name": "Cool Gray", "hex": "#808080"},
        {"name": "Raspberry", "hex": "#E30B5C"},
        {"name": "Cool Burgundy", "hex": "#8C001A"}
    ]
    
    enhanced_palettes["Clear Winter"] = [
        {"name": "Black", "hex": "#000000"},
        {"name": "White", "hex": "#FFFFFF"},
        {"name": "Bright Red", "hex": "#FF0000"},
        {"name": "Cherry Red", "hex": "#D2042D"},
        {"name": "Fuchsia", "hex": "#FF00FF"},
        {"name": "Magenta", "hex": "#FF00FF"},
        {"name": "Royal Blue", "hex": "#4169E1"},
        {"name": "Electric Blue", "hex": "#0000FF"},
        {"name": "Ice Blue", "hex": "#99FFFF"},
        {"name": "Bright Purple", "hex": "#9370DB"},
        {"name": "Violet", "hex": "#8F00FF"},
        {"name": "Emerald", "hex": "#50C878"},
        {"name": "Bright Green", "hex": "#66FF00"},
        {"name": "Bright Turquoise", "hex": "#00FFEF"},
        {"name": "Hot Pink", "hex": "#FF69B4"},
        {"name": "Bright Yellow", "hex": "#FFFF00"},
        {"name": "Silver", "hex": "#C0C0C0"},
        {"name": "Bright Teal", "hex": "#008080"},
        {"name": "Bright Raspberry", "hex": "#E30B5C"},
        {"name": "Bright Navy", "hex": "#000080"}
    ]
    
    # If we have a seasonal type and it exists in our palettes
    if seasonal_type:
        # First check enhanced palettes
        if seasonal_type in enhanced_palettes:
            return {
                "colors_that_suit": enhanced_palettes[seasonal_type],
                "seasonal_type": seasonal_type,
                "monk_skin_tone": monk_id,
                "message": "We've matched your skin tone to colors that will complement your natural complexion."
            }
        # Then check local file
        elif seasonal_type in local_seasonal_palettes:
            palette = local_seasonal_palettes[seasonal_type]
            
            # Handle dictionary format
            if isinstance(palette, dict) and "recommended" in palette:
                return {
                    "colors_that_suit": palette["recommended"],
                    "seasonal_type": seasonal_type,
                    "monk_skin_tone": monk_id,
                    "message": "We've matched your skin tone to colors that will complement your natural complexion."
                }
            # Handle list format
            elif isinstance(palette, list):
                # If it's a list, use the first 70% as recommended colors
                split_point = int(len(palette) * 0.7)
                return {
                    "colors_that_suit": palette[:split_point],
                    "seasonal_type": seasonal_type,
                    "monk_skin_tone": monk_id,
                    "message": "We've matched your skin tone to colors that will complement your natural complexion."
                }
        # Finally check loaded palettes
        elif seasonal_type in seasonal_palettes:
            palette = seasonal_palettes[seasonal_type]
            
            # Handle both dictionary and list formats
            colors_that_suit = []
            if isinstance(palette, dict) and "recommended" in palette:
                colors_that_suit = palette["recommended"]
            elif isinstance(palette, list):
                # If it's a list, use the first 70% as recommended colors
                split_point = int(len(palette) * 0.7)
                colors_that_suit = palette[:split_point]
            
            return {
                "colors_that_suit": colors_that_suit,
                "seasonal_type": seasonal_type,
                "monk_skin_tone": monk_id,
                "message": "We've matched your skin tone to colors that will complement your natural complexion."
            }
    
    # If we have a hex color but no seasonal type yet
    elif hex_color:
        # Remove # if present
        hex_color = hex_color.replace('#', '')
        
        # First try to find the closest Monk skin tone
        closest_monk = None
        min_distance = float('inf')
        
        for m_id, hex_codes in monk_hex_codes.items():
            for hex_code in hex_codes:
                hex_code = hex_code.replace('#', '')
                distance = color_distance(hex_color, hex_code)
                if distance < min_distance:
                    min_distance = distance
                    closest_monk = m_id
        
        # If we found a close Monk skin tone, use its seasonal mapping
        if closest_monk and closest_monk in monk_to_seasonal:
            seasonal_type = monk_to_seasonal[closest_monk]
            
            # First check enhanced palettes
            if seasonal_type in enhanced_palettes:
                return {
                    "colors_that_suit": enhanced_palettes[seasonal_type],
                    "seasonal_type": seasonal_type,
                    "monk_skin_tone": closest_monk,
                    "message": "We've matched your skin tone to colors that will complement your natural complexion."
                }
            # Then check local file
            elif seasonal_type in local_seasonal_palettes:
                palette = local_seasonal_palettes[seasonal_type]
                
                # Handle dictionary format
                if isinstance(palette, dict) and "recommended" in palette:
                    return {
                        "colors_that_suit": palette["recommended"],
                        "seasonal_type": seasonal_type,
                        "monk_skin_tone": closest_monk,
                        "message": "We've matched your skin tone to colors that will complement your natural complexion."
                    }
                # Handle list format
                elif isinstance(palette, list):
                    # If it's a list, use the first 70% as recommended colors
                    split_point = int(len(palette) * 0.7)
                    return {
                        "colors_that_suit": palette[:split_point],
                        "seasonal_type": seasonal_type,
                        "monk_skin_tone": closest_monk,
                        "message": "We've matched your skin tone to colors that will complement your natural complexion."
                    }
            # Finally check loaded palettes
            elif seasonal_type in seasonal_palettes:
                palette = seasonal_palettes[seasonal_type]
                
                # Handle both dictionary and list formats
                colors_that_suit = []
                if isinstance(palette, dict) and "recommended" in palette:
                    colors_that_suit = palette["recommended"]
                elif isinstance(palette, list):
                    # If it's a list, use the first 70% as recommended colors
                    split_point = int(len(palette) * 0.7)
                    colors_that_suit = palette[:split_point]
                
                return {
                    "colors_that_suit": colors_that_suit,
                    "seasonal_type": seasonal_type,
                    "monk_skin_tone": closest_monk,
                    "message": "We've matched your skin tone to colors that will complement your natural complexion."
                }
    
    # Default response with generic color recommendations
    return {
        "colors_that_suit": [
            {"name": "Navy Blue", "hex": "#000080"},
            {"name": "Forest Green", "hex": "#228B22"},
            {"name": "Burgundy", "hex": "#800020"},
            {"name": "Charcoal Gray", "hex": "#36454F"},
            {"name": "Deep Purple", "hex": "#301934"},
            {"name": "Olive Green", "hex": "#556B2F"},
            {"name": "Teal", "hex": "#008080"},
            {"name": "Maroon", "hex": "#800000"},
            {"name": "Royal Blue", "hex": "#4169E1"},
            {"name": "Emerald Green", "hex": "#50C878"},
            {"name": "Ruby Red", "hex": "#E0115F"},
            {"name": "Sapphire Blue", "hex": "#0F52BA"}
        ],
        "message": "We're working on expanding our color recommendations. Stay tuned for more colors!"
    }

@app.post("/analyze-skin-tone")
async def analyze_skin_tone(file: UploadFile = File(...)):
    """
    Analyze skin tone from uploaded image
    """
    try:
        # Validate file type
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read image data
        image_data = await file.read()
        
        # Convert to PIL Image
        image = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Convert to numpy array
        image_array = np.array(image)
        
        # Analyze skin tone
        result = analyze_skin_tone_simple(image_array)
        
        logger.info(f"Skin tone analysis result: {result}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in analyze_skin_tone endpoint: {e}")
        return get_fallback_result()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Skin tone analysis API is running",
        "available_tones": list(MONK_SKIN_TONES.keys())
    }
