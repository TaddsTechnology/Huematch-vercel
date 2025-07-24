from fastapi import FastAPI, Query, HTTPException, File, UploadFile, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import asyncio
import base64
import uuid
from contextlib import asynccontextmanager

# Import our performance optimization modules
from config import settings, FEATURE_FLAGS, get_environment_config
from cache_manager import cache_manager, cached, skin_tone_cache, warm_cache_skin_tones, warm_cache_color_palettes
from async_database import async_db_service, get_async_db, async_create_tables, async_init_color_palette_data, warm_async_caches
from background_tasks import (
    process_image_analysis_task, 
    generate_color_recommendations_task,
    generate_product_recommendations_task,
    warm_cache_task,
    cleanup_expired_cache_task,
    get_task_result,
    is_task_complete
)
from monitoring import (
    performance_monitor, 
    health_check_manager,
    RequestMonitoringMiddleware,
    get_health_endpoint,
    get_metrics_endpoint,
    get_system_stats_endpoint,
    periodic_health_check,
    cleanup_old_metrics
)
import pandas as pd
import json
import math
import os
from typing import List, Optional, Dict
try:
    from color_utils import get_color_mapping, get_seasonal_palettes, get_monk_hex_codes
except ImportError:
    from prods_fastapi.color_utils import get_color_mapping, get_seasonal_palettes, get_monk_hex_codes
from pathlib import Path
import re
import numpy as np
import cv2
from webcolors import hex_to_rgb, rgb_to_hex
import io
from PIL import Image
import logging
import random
import sys
sys.path.append('..')
from advanced_recommendation_engine import get_recommendation_engine
from performance_optimizer import performance_optimizer, cached, skin_tone_cache
from ab_testing_system import ab_testing_system, create_ab_test, get_ab_test_recommendations, track_ab_test_event, RecommendationAlgorithm
# Get environment configuration
env_config = get_environment_config()

try:
    from database import get_database, ColorPalette, create_tables, init_color_palette_data
except ImportError:
    from prods_fastapi.database import get_database, ColorPalette, create_tables, init_color_palette_data
    
# Import the new color service - commented out as color_service.py doesn't exist
# try:
#     from color_service import color_palette_service, get_comprehensive_recommendations
# except ImportError:
#     from prods_fastapi.color_service import color_palette_service, get_comprehensive_recommendations


# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import color routes
try:
    from color_routes import color_router
    COLOR_ROUTER_AVAILABLE = True
except ImportError:
    try:
        from prods_fastapi.color_routes import color_router
        COLOR_ROUTER_AVAILABLE = True
    except ImportError:
        logger.warning("color_routes module not found - color endpoints will not be available")
        color_router = None
        COLOR_ROUTER_AVAILABLE = False

# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    try:
        logger.info("Starting AI Fashion Backend with performance optimizations...")
        
        # Initialize database
        if FEATURE_FLAGS["enable_async_db"]:
            await async_create_tables()
            await async_init_color_palette_data()
            logger.info("Async database initialized")
        
        # Warm caches
        if FEATURE_FLAGS["enable_caching"]:
            warm_cache_skin_tones()
            warm_cache_color_palettes()
            await warm_async_caches()
            logger.info("Caches warmed")
        
        # Start background tasks
        if FEATURE_FLAGS["enable_background_processing"]:
            # Warm cache task
            warm_cache_task.send()
            logger.info("Background tasks started")
        
        # Start monitoring tasks
        if FEATURE_FLAGS["enable_health_checks"]:
            asyncio.create_task(periodic_health_check())
            asyncio.create_task(cleanup_old_metrics())
            logger.info("Monitoring tasks started")
        
        logger.info(f"Application started successfully with {settings.max_workers} workers")
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
    
    yield
    
    # Shutdown
    try:
        logger.info("Shutting down AI Fashion Backend...")
        
        # Close database connections
        if FEATURE_FLAGS["enable_async_db"]:
            await async_db_service.close()
            logger.info("Database connections closed")
        
        logger.info("Application shut down successfully")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

# Create FastAPI app with optimized configuration
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=env_config["debug"],
    lifespan=lifespan
)

# Add performance middleware
if FEATURE_FLAGS["enable_compression"]:
    app.add_middleware(GZipMiddleware, minimum_size=1000)

if FEATURE_FLAGS["enable_metrics"]:
    # Add request monitoring middleware
    monitoring_middleware = RequestMonitoringMiddleware()
    app.middleware("http")(monitoring_middleware)

# Include color router only if available
if COLOR_ROUTER_AVAILABLE and color_router:
    app.include_router(color_router)

# Note: Startup/shutdown events now handled by lifespan context manager

# Configure CORS with settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
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
    Apply comprehensive lighting correction pipeline with CLAHE, white balance, 
    gamma correction, and shadow/highlight balancing.
    """
    try:
        logger.info("Starting comprehensive lighting correction pipeline")
        
        # Step 1: Analyze image brightness and determine correction strategy
        gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
        mean_brightness = np.mean(gray)
        std_brightness = np.std(gray)
        
        logger.info(f"Image analysis: mean_brightness={mean_brightness:.1f}, std_brightness={std_brightness:.1f}")
        
        # Step 2: Apply white balance correction first
        white_balanced = apply_advanced_white_balance(image_array, mean_brightness)
        
        # Step 3: Convert to LAB color space for perceptual corrections
        lab_image = cv2.cvtColor(white_balanced, cv2.COLOR_RGB2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab_image)
        
        # Step 4: Apply adaptive CLAHE based on image characteristics
        l_channel_corrected = apply_adaptive_clahe(l_channel, mean_brightness, std_brightness)
        
        # Step 5: Apply shadow/highlight balancing
        l_channel_balanced = apply_shadow_highlight_balancing(l_channel_corrected, mean_brightness)
        
        # Step 6: Merge LAB channels back
        corrected_lab = cv2.merge([l_channel_balanced, a_channel, b_channel])
        
        # Step 7: Convert back to RGB
        corrected_rgb = cv2.cvtColor(corrected_lab, cv2.COLOR_LAB2RGB)
        
        # Step 8: Apply adaptive gamma correction
        gamma_corrected = apply_adaptive_gamma_correction(corrected_rgb, mean_brightness)
        
        # Step 9: Final exposure and contrast adjustment
        final_corrected = apply_exposure_adjustment(gamma_corrected, mean_brightness)
        
        logger.info("Lighting correction pipeline completed successfully")
        return final_corrected
        
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

def apply_advanced_white_balance(image_array: np.ndarray, mean_brightness: float) -> np.ndarray:
    """
    Apply advanced white balance correction optimized based on image brightness
    """
    try:
        # Convert to float for calculations
        image_float = image_array.astype(np.float64)
        
        # Adaptive masking based on brightness
        if mean_brightness > 180:  # Very bright image - likely light skin
            # Focus on mid-tones to avoid overexposure
            mask = (image_float[:, :, 0] > 50) & (image_float[:, :, 0] < 240) & \
                   (image_float[:, :, 1] > 50) & (image_float[:, :, 1] < 240) & \
                   (image_float[:, :, 2] > 50) & (image_float[:, :, 2] < 240)
            correction_strength = 0.5  # Gentle correction for bright images
        elif mean_brightness < 100:  # Dark image
            # Include more of the darker range
            mask = (image_float[:, :, 0] > 10) & (image_float[:, :, 0] < 200) & \
                   (image_float[:, :, 1] > 10) & (image_float[:, :, 1] < 200) & \
                   (image_float[:, :, 2] > 10) & (image_float[:, :, 2] < 200)
            correction_strength = 0.8  # Stronger correction for dark images
        else:  # Medium brightness
            # Standard masking
            mask = (image_float[:, :, 0] > 30) & (image_float[:, :, 0] < 250) & \
                   (image_float[:, :, 1] > 30) & (image_float[:, :, 1] < 250) & \
                   (image_float[:, :, 2] > 30) & (image_float[:, :, 2] < 250)
            correction_strength = 0.7  # Moderate correction
        
        if np.sum(mask) > 0:
            mean_r = np.mean(image_float[:, :, 0][mask])
            mean_g = np.mean(image_float[:, :, 1][mask])
            mean_b = np.mean(image_float[:, :, 2][mask])
        else:
            # Fallback to full image if mask is empty
            mean_r = np.mean(image_float[:, :, 0])
            mean_g = np.mean(image_float[:, :, 1])
            mean_b = np.mean(image_float[:, :, 2])
        
        # Calculate scaling factors with adaptive correction
        gray_world_mean = (mean_r + mean_g + mean_b) / 3
        
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
        
        logger.info(f"Applied adaptive white balance with strength {correction_strength:.1f}")
        return balanced_image
        
    except Exception as e:
        logger.warning(f"Advanced white balance correction failed: {e}, using original image")
        return image_array

def apply_adaptive_clahe(l_channel: np.ndarray, mean_brightness: float, std_brightness: float) -> np.ndarray:
    """
    Apply adaptive CLAHE based on image characteristics
    """
    try:
        # Determine CLAHE parameters based on image characteristics
        if mean_brightness > 200:  # Very bright image
            clip_limit = 1.2  # Very gentle for bright images
            tile_grid_size = (12, 12)  # Larger tiles for smoother correction
        elif mean_brightness > 150:  # Moderately bright
            clip_limit = 1.8
            tile_grid_size = (10, 10)
        elif mean_brightness > 100:  # Medium brightness
            clip_limit = 2.5
            tile_grid_size = (8, 8)
        elif mean_brightness > 50:  # Dark image
            clip_limit = 3.5
            tile_grid_size = (6, 6)
        else:  # Very dark image
            clip_limit = 4.0  # Stronger correction for very dark images
            tile_grid_size = (4, 4)  # Smaller tiles for more localized correction
        
        # Adjust based on contrast (standard deviation)
        if std_brightness > 60:  # High contrast
            clip_limit *= 0.7  # Reduce to avoid over-enhancement
        elif std_brightness < 20:  # Low contrast
            clip_limit *= 1.3  # Increase to enhance details
        
        # Create and apply CLAHE
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
        enhanced_l = clahe.apply(l_channel)
        
        logger.info(f"Applied adaptive CLAHE: clip_limit={clip_limit:.1f}, tile_size={tile_grid_size}")
        return enhanced_l
        
    except Exception as e:
        logger.warning(f"Adaptive CLAHE failed: {e}, using original L channel")
        return l_channel

def apply_shadow_highlight_balancing(l_channel: np.ndarray, mean_brightness: float) -> np.ndarray:
    """
    Apply shadow and highlight balancing to handle exposure extremes
    """
    try:
        # Convert to float for calculations
        l_float = l_channel.astype(np.float32) / 255.0
        
        # Define shadow and highlight thresholds
        shadow_threshold = 0.3
        highlight_threshold = 0.7
        
        # Adjust thresholds based on overall brightness
        if mean_brightness > 180:  # Bright image
            shadow_threshold = 0.2
            highlight_threshold = 0.8
            shadow_strength = 0.3  # Gentle shadow lifting
            highlight_strength = 0.7  # Stronger highlight recovery
        elif mean_brightness < 100:  # Dark image
            shadow_threshold = 0.4
            highlight_threshold = 0.6
            shadow_strength = 0.8  # Strong shadow lifting
            highlight_strength = 0.2  # Gentle highlight recovery
        else:  # Medium brightness
            shadow_strength = 0.5
            highlight_strength = 0.5
        
        # Create masks for shadows and highlights
        shadow_mask = l_float < shadow_threshold
        highlight_mask = l_float > highlight_threshold
        
        # Apply shadow lifting
        if np.any(shadow_mask):
            shadow_factor = 1.0 + shadow_strength * (shadow_threshold - l_float[shadow_mask]) / shadow_threshold
            l_float[shadow_mask] *= shadow_factor
        
        # Apply highlight recovery
        if np.any(highlight_mask):
            highlight_factor = 1.0 - highlight_strength * (l_float[highlight_mask] - highlight_threshold) / (1.0 - highlight_threshold)
            l_float[highlight_mask] *= highlight_factor
        
        # Convert back to uint8
        balanced_l = (np.clip(l_float, 0, 1) * 255).astype(np.uint8)
        
        logger.info(f"Applied shadow/highlight balancing: shadow_strength={shadow_strength:.1f}, highlight_strength={highlight_strength:.1f}")
        return balanced_l
        
    except Exception as e:
        logger.warning(f"Shadow/highlight balancing failed: {e}, using original L channel")
        return l_channel

def apply_adaptive_gamma_correction(image_array: np.ndarray, mean_brightness: float) -> np.ndarray:
    """
    Apply adaptive gamma correction based on image brightness
    """
    try:
        # Determine gamma value based on brightness
        if mean_brightness > 200:  # Very bright
            gamma = 1.05  # Very subtle correction
        elif mean_brightness > 150:  # Moderately bright
            gamma = 1.1
        elif mean_brightness > 100:  # Medium brightness
            gamma = 1.2
        elif mean_brightness > 50:  # Dark
            gamma = 0.8  # Brighten dark images
        else:  # Very dark
            gamma = 0.7  # Strong brightening
        
        # Apply gamma correction
        gamma_corrected = np.power(image_array / 255.0, gamma) * 255.0
        gamma_corrected = np.clip(gamma_corrected, 0, 255).astype(np.uint8)
        
        logger.info(f"Applied adaptive gamma correction: gamma={gamma:.2f}")
        return gamma_corrected
        
    except Exception as e:
        logger.warning(f"Adaptive gamma correction failed: {e}, using original image")
        return image_array

def apply_exposure_adjustment(image_array: np.ndarray, mean_brightness: float) -> np.ndarray:
    """
    Apply final exposure and contrast adjustment for optimal output
    """
    try:
        # Convert to float for calculations
        image_float = image_array.astype(np.float32)
        
        # Determine exposure and contrast adjustments
        if mean_brightness > 200:  # Very bright
            exposure_adjustment = 0.95  # Slight darkening
            contrast_factor = 0.98  # Slight contrast reduction
        elif mean_brightness > 150:  # Moderately bright
            exposure_adjustment = 0.98
            contrast_factor = 1.0
        elif mean_brightness > 100:  # Medium brightness
            exposure_adjustment = 1.0
            contrast_factor = 1.05  # Slight contrast boost
        elif mean_brightness > 50:  # Dark
            exposure_adjustment = 1.1  # Brightening
            contrast_factor = 1.1  # Contrast boost
        else:  # Very dark
            exposure_adjustment = 1.2  # Strong brightening
            contrast_factor = 1.15  # Strong contrast boost
        
        # Apply exposure adjustment
        image_float *= exposure_adjustment
        
        # Apply contrast adjustment (around midpoint)
        midpoint = 127.5
        image_float = (image_float - midpoint) * contrast_factor + midpoint
        
        # Clip and convert back to uint8
        adjusted_image = np.clip(image_float, 0, 255).astype(np.uint8)
        
        logger.info(f"Applied exposure adjustment: exposure={exposure_adjustment:.2f}, contrast={contrast_factor:.2f}")
        return adjusted_image
        
    except Exception as e:
        logger.warning(f"Exposure adjustment failed: {e}, using original image")
        return image_array
def analyze_skin_tone_lab(image_array: np.ndarray) -> Dict:
    """
    Enhanced skin tone analysis using LAB color space for better perceptual accuracy.
    """
    try:
        # Convert image to LAB color space
        lab_image = cv2.cvtColor(image_array, cv2.COLOR_RGB2LAB)
        
        # Extract L, A, B channels
        l_channel, a_channel, b_channel = cv2.split(lab_image)
        
        # Analyze skin tone using the L channel, focusing on lightness
        lightness_median = np.median(l_channel)
        
        # Check for brightness and adjust analysis as needed
        if lightness_median < 50:
            logger.info("Image appears dark; applying gentle lighting correction")
            processed_image = apply_gentle_lighting_correction(image_array)
            lab_image = cv2.cvtColor(processed_image, cv2.COLOR_RGB2LAB)
            l_channel, a_channel, b_channel = cv2.split(lab_image)
        
        # Calculate median color in A and B channels for skin tone
        median_a = np.median(a_channel)
        median_b = np.median(b_channel)
        final_color_lab = np.array([lightness_median, median_a, median_b])
        
        # Convert LAB to RGB to find closest Monk skin tone
        final_color_rgb = cv2.cvtColor(np.uint8([[final_color_lab]]), cv2.COLOR_LAB2RGB)[0][0]
        
        # Enhanced Monk tone matching
        closest_monk = find_closest_monk_tone_enhanced(final_color_rgb)
        
        # Advanced confidence scoring
        confidence = calculate_advanced_confidence_lab(final_color_lab, lightness_median)
        
        return {
            'monk_skin_tone': closest_monk['monk_id'],
            'monk_tone_display': closest_monk['monk_name'],
            'monk_hex': closest_monk['monk_hex'],
            'derived_hex_code': closest_monk['derived_hex'],
            'dominant_rgb': final_color_rgb.astype(int).tolist(),
            'confidence': confidence,
            'success': True
        }
    except Exception as e:
        logger.error(f"Error in LAB skin tone analysis: {e}")
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
    Advanced skin color extraction with improved handling for all skin tones
    """
    skin_colors = []
    h, w = image_array.shape[:2]
    
    # Method 1: Multi-range HSV detection for all skin tones
    hsv = cv2.cvtColor(image_array, cv2.COLOR_RGB2HSV)
    
    # Expanded skin detection ranges covering full spectrum
    skin_ranges = [
        # Very light skin (almost white) - Monk 1-2
        ([0, 0, 235], [30, 25, 255]),
        ([0, 5, 220], [25, 40, 255]),
        # Light skin - Monk 2-3  
        ([0, 10, 200], [30, 60, 245]),
        ([0, 15, 180], [25, 80, 230]),
        # Light-medium skin - Monk 3-4
        ([0, 20, 160], [30, 100, 220]),
        ([0, 25, 140], [25, 120, 200]),
        # Medium skin - Monk 4-6
        ([0, 30, 120], [30, 140, 180]),
        ([0, 35, 100], [25, 160, 160]),
        # Medium-dark skin - Monk 6-8
        ([0, 40, 80], [30, 180, 140]),
        ([0, 45, 60], [25, 200, 120]),
        # Dark skin - Monk 8-10
        ([0, 50, 40], [30, 220, 100]),
        ([0, 55, 20], [25, 255, 80])
    ]
    
    combined_mask = None
    for lower, upper in skin_ranges:
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
    Analyze extracted colors with balanced approach for all skin tones
    """
    if not skin_colors:
        # Ultimate fallback - use center region analysis
        h, w = image_array.shape[:2]
        center = image_array[h//3:2*h//3, w//3:2*w//3]
        
        # Check overall brightness to determine approach
        gray = cv2.cvtColor(center, cv2.COLOR_RGB2GRAY)
        overall_brightness = np.mean(gray)
        
        if overall_brightness > 200:  # Very bright image - likely light skin
            # Use brightest regions
            brightest_mask = gray > np.percentile(gray, 75)
            if np.sum(brightest_mask) > 0:
                return np.mean(center[brightest_mask], axis=0)
        elif overall_brightness < 100:  # Dark image - likely dark skin
            # Use medium-bright regions to avoid shadows
            medium_mask = (gray > np.percentile(gray, 40)) & (gray < np.percentile(gray, 85))
            if np.sum(medium_mask) > 0:
                return np.mean(center[medium_mask], axis=0)
        
        # Default fallback
        return np.mean(center.reshape(-1, 3), axis=0)
    
    skin_colors_array = np.array(skin_colors)
    brightness_scores = np.mean(skin_colors_array, axis=1)
    overall_brightness = np.mean(brightness_scores)
    
    # Adaptive weighting based on overall brightness
    if overall_brightness > 220:  # Very light skin tones
        # Prioritize lighter samples
        weights = np.power(brightness_scores / 255.0, 0.3)
    elif overall_brightness < 120:  # Dark skin tones
        # More balanced weighting, avoid over-emphasizing lighter samples
        weights = np.power(brightness_scores / 255.0, 0.8)
    else:  # Medium skin tones
        # Balanced approach
        weights = np.power(brightness_scores / 255.0, 0.5)
    
    weights = weights / np.sum(weights)  # Normalize
    
    # Calculate weighted average
    final_color = np.average(skin_colors_array, axis=0, weights=weights)
    
    # Adaptive post-processing based on detected brightness
    if overall_brightness > 220 and np.mean(final_color) < 200:
        # For very light skin, ensure result isn't too dark
        light_colors = skin_colors_array[brightness_scores > 210]
        if len(light_colors) > 0:
            final_color = np.mean(light_colors, axis=0)
    elif overall_brightness < 120 and np.mean(final_color) > 140:
        # For dark skin, ensure result isn't too light  
        dark_colors = skin_colors_array[brightness_scores < 140]
        if len(dark_colors) > 0:
            final_color = np.mean(dark_colors, axis=0)
    
    return final_color

def find_closest_monk_tone_enhanced(rgb_color: np.ndarray) -> Dict:
    """
    Enhanced Monk tone matching with improved calibration for all skin tones
    """
    # Log the detected color
    logger.info(f"Detected skin color: RGB({rgb_color[0]:.1f}, {rgb_color[1]:.1f}, {rgb_color[2]:.1f})")
    
    # Calculate brightness and undertone characteristics
    avg_brightness = np.mean(rgb_color)
    max_channel = np.max(rgb_color)
    min_channel = np.min(rgb_color)
    color_range = max_channel - min_channel
    
    logger.info(f"Brightness analysis: avg={avg_brightness:.1f}, max={max_channel:.1f}, min={min_channel:.1f}, range={color_range:.1f}")
    
    # Improved brightness thresholds based on actual Monk scale values
    # Convert Monk hex values to brightness levels for reference
    monk_brightnesses = {}
    for monk_name, monk_hex in MONK_SKIN_TONES.items():
        monk_rgb = np.array(hex_to_rgb(monk_hex))
        monk_brightnesses[monk_name] = np.mean(monk_rgb)
    
    # Find the closest match using improved algorithm
    min_distance = float('inf')
    closest_monk = None
    
    for monk_name, monk_hex in MONK_SKIN_TONES.items():
        monk_rgb = np.array(hex_to_rgb(monk_hex))
        
        # Multi-factor distance calculation
        # 1. Euclidean distance in RGB space
        euclidean_distance = np.sqrt(np.sum((rgb_color - monk_rgb) ** 2))
        
        # 2. Brightness difference (heavily weighted for extreme ends)
        brightness_diff = abs(avg_brightness - np.mean(monk_rgb))
        
        # 3. Color saturation difference
        input_saturation = color_range / max_channel if max_channel > 0 else 0
        monk_saturation = (np.max(monk_rgb) - np.min(monk_rgb)) / np.max(monk_rgb) if np.max(monk_rgb) > 0 else 0
        saturation_diff = abs(input_saturation - monk_saturation)
        
        # 4. Weighted combination with emphasis on brightness for extreme tones
        if avg_brightness > 230:  # Very light skin
            # Heavily weight brightness for very light skin
            distance = euclidean_distance * 0.3 + brightness_diff * 2.0 + saturation_diff * 50
        elif avg_brightness < 100:  # Very dark skin
            # Heavily weight brightness for very dark skin  
            distance = euclidean_distance * 0.3 + brightness_diff * 2.5 + saturation_diff * 30
        else:  # Medium skin tones
            # Balanced weighting for medium tones
            distance = euclidean_distance * 0.7 + brightness_diff * 1.0 + saturation_diff * 20
        
        logger.info(f"{monk_name}: euclidean={euclidean_distance:.2f}, brightness_diff={brightness_diff:.2f}, sat_diff={saturation_diff:.3f}, total={distance:.2f}")
        
        if distance < min_distance:
            min_distance = distance
            closest_monk = monk_name
    
    # Additional validation for extreme cases
    if avg_brightness > 240 and closest_monk not in ['Monk 1', 'Monk 2']:
        logger.info(f"Very light skin detected (brightness={avg_brightness:.1f}), forcing Monk 1-2 range")
        # Force to lightest appropriate tone
        light_options = ['Monk 1', 'Monk 2']
        min_dist = float('inf')
        for option in light_options:
            monk_rgb = np.array(hex_to_rgb(MONK_SKIN_TONES[option]))
            dist = np.sqrt(np.sum((rgb_color - monk_rgb) ** 2))
            if dist < min_dist:
                min_dist = dist
                closest_monk = option
    
    elif avg_brightness < 80 and closest_monk not in ['Monk 8', 'Monk 9', 'Monk 10']:
        logger.info(f"Very dark skin detected (brightness={avg_brightness:.1f}), forcing Monk 8-10 range")
        # Force to darkest appropriate tone
        dark_options = ['Monk 8', 'Monk 9', 'Monk 10']
        min_dist = float('inf')
        for option in dark_options:
            monk_rgb = np.array(hex_to_rgb(MONK_SKIN_TONES[option]))
            dist = np.sqrt(np.sum((rgb_color - monk_rgb) ** 2))
            if dist < min_dist:
                min_dist = dist
                closest_monk = option
    
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

def calculate_comprehensive_confidence_score(image_array: np.ndarray, final_color_lab: np.ndarray, lightness: float) -> Dict:
    """
    Calculate comprehensive confidence score (0-100%) based on multiple quality factors:
    - Color cluster coherence analysis
    - Face detection quality score
    - Lighting condition assessment
    """
    try:
        logger.info("Starting comprehensive confidence analysis")
        
        # Initialize scores
        color_coherence_score = 0.0
        face_detection_score = 0.0
        lighting_quality_score = 0.0
        
        # 1. COLOR CLUSTER COHERENCE ANALYSIS (40% weight)
        color_coherence_score = analyze_color_cluster_coherence(image_array)
        logger.info(f"Color coherence score: {color_coherence_score:.2f}")
        
        # 2. FACE DETECTION QUALITY SCORE (35% weight)
        face_detection_score = assess_face_detection_quality(image_array)
        logger.info(f"Face detection quality score: {face_detection_score:.2f}")
        
        # 3. LIGHTING CONDITION ASSESSMENT (25% weight)
        lighting_quality_score = evaluate_lighting_conditions(image_array)
        logger.info(f"Lighting quality score: {lighting_quality_score:.2f}")
        
        # Calculate weighted final confidence (0-100%)
        final_confidence = (
            color_coherence_score * 0.40 +
            face_detection_score * 0.35 +
            lighting_quality_score * 0.25
        )
        
        # Additional LAB color space consistency bonus
        lab_consistency_bonus = calculate_lab_consistency_bonus(final_color_lab, lightness)
        final_confidence = min(100.0, final_confidence + lab_consistency_bonus)
        
        logger.info(f"Final comprehensive confidence score: {final_confidence:.1f}%")
        
        return {
            'overall_confidence': round(final_confidence, 1),
            'color_coherence': round(color_coherence_score, 1),
            'face_detection_quality': round(face_detection_score, 1),
            'lighting_quality': round(lighting_quality_score, 1),
            'lab_consistency_bonus': round(lab_consistency_bonus, 1)
        }
        
    except Exception as e:
        logger.error(f"Error in comprehensive confidence calculation: {e}")
        return {
            'overall_confidence': 50.0,
            'color_coherence': 50.0,
            'face_detection_quality': 50.0,
            'lighting_quality': 50.0,
            'lab_consistency_bonus': 0.0,
            'error': str(e)
        }

def analyze_color_cluster_coherence(image_array: np.ndarray) -> float:
    """
    Analyze color cluster coherence to determine skin tone prediction reliability.
    Returns score 0-100 where higher scores indicate more coherent skin tone regions.
    """
    try:
        h, w = image_array.shape[:2]
        
        # Extract multiple face regions for coherence analysis
        face_regions = [
            image_array[h//6:h//3, w//3:2*w//3],      # Upper forehead
            image_array[h//3:h//2, w//4:3*w//4],      # Mid-face (cheeks)
            image_array[h//2:2*h//3, w//3:2*w//3],    # Lower face
            image_array[2*h//5:3*h//5, 2*w//5:3*w//5] # Central nose area
        ]
        
        region_colors = []
        region_variances = []
        
        for region in face_regions:
            if region.size > 100:  # Ensure region has enough pixels
                # Convert to LAB for better color analysis
                region_lab = cv2.cvtColor(region, cv2.COLOR_RGB2LAB)
                
                # Calculate mean color and variance for each channel
                mean_color = np.mean(region_lab.reshape(-1, 3), axis=0)
                color_variance = np.var(region_lab.reshape(-1, 3), axis=0)
                
                region_colors.append(mean_color)
                region_variances.append(np.mean(color_variance))
        
        if len(region_colors) < 2:
            return 30.0  # Low confidence if not enough regions
        
        # Calculate coherence between regions
        region_colors = np.array(region_colors)
        
        # 1. Inter-region color consistency (how similar are the mean colors?)
        color_distances = []
        for i in range(len(region_colors)):
            for j in range(i + 1, len(region_colors)):
                distance = np.sqrt(np.sum((region_colors[i] - region_colors[j]) ** 2))
                color_distances.append(distance)
        
        mean_color_distance = np.mean(color_distances) if color_distances else 50
        
        # Lower distance = higher coherence
        inter_region_score = max(0, 100 - (mean_color_distance * 2))
        
        # 2. Intra-region color consistency (how uniform is each region?)
        mean_variance = np.mean(region_variances) if region_variances else 500
        intra_region_score = max(0, 100 - (mean_variance / 10))
        
        # 3. K-means clustering analysis for skin tone grouping
        try:
            from sklearn.cluster import KMeans
            
            # Sample pixels from all regions
            all_pixels = []
            for region in face_regions:
                if region.size > 0:
                    region_lab = cv2.cvtColor(region, cv2.COLOR_RGB2LAB)
                    pixels = region_lab.reshape(-1, 3)
                    # Sample up to 1000 pixels per region
                    if len(pixels) > 1000:
                        indices = np.random.choice(len(pixels), 1000, replace=False)
                        pixels = pixels[indices]
                    all_pixels.extend(pixels)
            
            if len(all_pixels) > 100:
                all_pixels = np.array(all_pixels)
                
                # Perform K-means clustering with k=3 (skin, shadow, highlight)
                kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
                cluster_labels = kmeans.fit_predict(all_pixels)
                
                # Calculate cluster coherence
                cluster_sizes = np.bincount(cluster_labels)
                dominant_cluster_ratio = np.max(cluster_sizes) / len(all_pixels)
                
                # Higher dominant cluster ratio = better coherence
                clustering_score = dominant_cluster_ratio * 100
            else:
                clustering_score = 50
                
        except ImportError:
            # Fallback if sklearn is not available
            clustering_score = 60
        except Exception as e:
            logger.warning(f"K-means clustering failed: {e}")
            clustering_score = 50
        
        # Combine all coherence measures
        final_coherence_score = (
            inter_region_score * 0.4 +
            intra_region_score * 0.3 +
            clustering_score * 0.3
        )
        
        return min(100.0, max(0.0, final_coherence_score))
        
    except Exception as e:
        logger.warning(f"Color coherence analysis failed: {e}")
        return 40.0

def assess_face_detection_quality(image_array: np.ndarray) -> float:
    """
    Assess the quality of face detection for skin tone analysis.
    Returns score 0-100 based on face detection confidence and image quality.
    """
    try:
        # Try to use MediaPipe for face detection if available
        try:
            import mediapipe as mp
            
            mp_face_detection = mp.solutions.face_detection
            mp_drawing = mp.solutions.drawing_utils
            
            with mp_face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.5) as face_detection:
                # Convert RGB to BGR for MediaPipe
                image_bgr = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
                results = face_detection.process(image_bgr)
                
                if results.detections:
                    # Get the most confident detection
                    best_detection = max(results.detections, key=lambda x: x.score[0])
                    detection_confidence = best_detection.score[0]
                    
                    # Analyze bounding box quality
                    bbox = best_detection.location_data.relative_bounding_box
                    
                    # Calculate face area relative to image
                    h, w = image_array.shape[:2]
                    face_area_ratio = (bbox.width * bbox.height)
                    
                    # Ideal face area is 20-60% of image
                    if 0.15 <= face_area_ratio <= 0.7:
                        area_score = 100
                    elif 0.1 <= face_area_ratio < 0.15 or 0.7 < face_area_ratio <= 0.8:
                        area_score = 80
                    else:
                        area_score = 60
                    
                    # Check face centering
                    face_center_x = bbox.xmin + bbox.width / 2
                    face_center_y = bbox.ymin + bbox.height / 2
                    
                    # Penalty for faces too close to edges
                    center_penalty = 0
                    if face_center_x < 0.2 or face_center_x > 0.8:
                        center_penalty += 10
                    if face_center_y < 0.2 or face_center_y > 0.8:
                        center_penalty += 10
                    
                    # Combine detection confidence, area, and centering
                    face_quality_score = (
                        detection_confidence * 100 * 0.5 +
                        area_score * 0.3 +
                        max(0, 100 - center_penalty) * 0.2
                    )
                    
                    return min(100.0, face_quality_score)
                else:
                    # No face detected with MediaPipe
                    return 20.0
                    
        except ImportError:
            # Fallback to OpenCV Haar cascades if MediaPipe not available
            logger.info("MediaPipe not available, using OpenCV face detection")
            
            # Try to load Haar cascade
            try:
                face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
                
                faces = face_cascade.detectMultiScale(
                    gray,
                    scaleFactor=1.1,
                    minNeighbors=5,
                    minSize=(50, 50)
                )
                
                if len(faces) > 0:
                    # Get the largest face
                    largest_face = max(faces, key=lambda x: x[2] * x[3])
                    x, y, w, h = largest_face
                    
                    # Calculate face quality metrics
                    img_h, img_w = image_array.shape[:2]
                    face_area_ratio = (w * h) / (img_w * img_h)
                    
                    # Basic quality assessment
                    if 0.1 <= face_area_ratio <= 0.6:
                        return 75.0
                    elif 0.05 <= face_area_ratio < 0.1 or 0.6 < face_area_ratio <= 0.8:
                        return 60.0
                    else:
                        return 45.0
                else:
                    return 25.0
                    
            except Exception as e:
                logger.warning(f"OpenCV face detection failed: {e}")
                return 35.0
        
        # Additional image quality checks
        h, w = image_array.shape[:2]
        
        # Check image resolution
        resolution_score = 100
        if w < 200 or h < 200:
            resolution_score = 40
        elif w < 400 or h < 400:
            resolution_score = 70
        
        # Check if image is too blurry (Laplacian variance)
        gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
        blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        if blur_score > 500:
            sharpness_score = 100
        elif blur_score > 200:
            sharpness_score = 80
        elif blur_score > 100:
            sharpness_score = 60
        else:
            sharpness_score = 30
        
        # Combine all quality factors
        return min(100.0, (resolution_score * 0.3 + sharpness_score * 0.7))
        
    except Exception as e:
        logger.warning(f"Face detection quality assessment failed: {e}")
        return 50.0

def evaluate_lighting_conditions(image_array: np.ndarray) -> float:
    """
    Evaluate lighting conditions for optimal skin tone detection.
    Returns score 0-100 where higher scores indicate better lighting.
    """
    try:
        # Convert to grayscale for brightness analysis
        gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
        
        # 1. Overall brightness assessment
        mean_brightness = np.mean(gray)
        brightness_score = 0
        
        if 80 <= mean_brightness <= 180:  # Optimal range
            brightness_score = 100
        elif 60 <= mean_brightness < 80 or 180 < mean_brightness <= 200:
            brightness_score = 80
        elif 40 <= mean_brightness < 60 or 200 < mean_brightness <= 220:
            brightness_score = 60
        else:
            brightness_score = 30
        
        # 2. Contrast and detail preservation
        contrast_score = np.std(gray)
        if 30 <= contrast_score <= 70:  # Good contrast
            contrast_quality = 100
        elif 20 <= contrast_score < 30 or 70 < contrast_score <= 90:
            contrast_quality = 80
        elif 10 <= contrast_score < 20 or 90 < contrast_score <= 110:
            contrast_quality = 60
        else:
            contrast_quality = 40
        
        # 3. Check for overexposure/underexposure
        overexposed_pixels = np.sum(gray > 240) / gray.size
        underexposed_pixels = np.sum(gray < 15) / gray.size
        
        exposure_penalty = 0
        if overexposed_pixels > 0.1:  # More than 10% overexposed
            exposure_penalty += min(30, overexposed_pixels * 200)
        if underexposed_pixels > 0.1:  # More than 10% underexposed
            exposure_penalty += min(30, underexposed_pixels * 200)
        
        exposure_score = max(0, 100 - exposure_penalty)
        
        # 4. Color temperature assessment (check for color casts)
        # Analyze RGB channel balance
        mean_r = np.mean(image_array[:, :, 0])
        mean_g = np.mean(image_array[:, :, 1])
        mean_b = np.mean(image_array[:, :, 2])
        
        # Calculate color balance score
        max_channel = max(mean_r, mean_g, mean_b)
        min_channel = min(mean_r, mean_g, mean_b)
        
        if max_channel > 0:
            color_balance_ratio = min_channel / max_channel
            if color_balance_ratio > 0.8:  # Well balanced
                color_balance_score = 100
            elif color_balance_ratio > 0.6:
                color_balance_score = 80
            elif color_balance_ratio > 0.4:
                color_balance_score = 60
            else:
                color_balance_score = 40
        else:
            color_balance_score = 50
        
        # 5. Shadow/highlight distribution analysis
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        hist_normalized = hist.flatten() / np.sum(hist)
        
        # Check for good tonal distribution
        shadows = np.sum(hist_normalized[:64])      # 0-25% range
        midtones = np.sum(hist_normalized[64:192])  # 25-75% range
        highlights = np.sum(hist_normalized[192:])   # 75-100% range
        
        # Ideal distribution has strong midtones with moderate shadows/highlights
        if midtones > 0.4 and shadows < 0.4 and highlights < 0.4:
            distribution_score = 100
        elif midtones > 0.3:
            distribution_score = 80
        else:
            distribution_score = 60
        
        # Combine all lighting quality factors
        final_lighting_score = (
            brightness_score * 0.25 +
            contrast_quality * 0.20 +
            exposure_score * 0.25 +
            color_balance_score * 0.15 +
            distribution_score * 0.15
        )
        
        return min(100.0, max(0.0, final_lighting_score))
        
    except Exception as e:
        logger.warning(f"Lighting condition evaluation failed: {e}")
        return 50.0

def calculate_lab_consistency_bonus(final_color_lab: np.ndarray, lightness: float) -> float:
    """
    Calculate bonus points based on LAB color space consistency.
    Returns bonus score 0-15 points.
    """
    try:
        # Analyze LAB channel relationships
        l_val, a_val, b_val = final_color_lab
        
        # Check if the color values are within expected skin tone ranges
        bonus = 0
        
        # L channel should be reasonable for skin tones (20-95)
        if 20 <= l_val <= 95:
            bonus += 5
        
        # A channel for skin tones typically ranges from -10 to +25
        if -10 <= a_val <= 25:
            bonus += 5
        
        # B channel for skin tones typically ranges from -5 to +35
        if -5 <= b_val <= 35:
            bonus += 5
        
        return bonus
        
    except Exception as e:
        logger.warning(f"LAB consistency bonus calculation failed: {e}")
        return 0

def calculate_advanced_confidence_lab(final_color_lab: np.ndarray, lightness: float) -> float:
    """
    Legacy function maintained for backward compatibility.
    Now calls the comprehensive confidence system.
    """
    try:
        # Create a dummy image array for the comprehensive system
        # This is a fallback when only LAB data is available
        dummy_image = np.ones((100, 100, 3), dtype=np.uint8) * 128
        
        comprehensive_result = calculate_comprehensive_confidence_score(
            dummy_image, final_color_lab, lightness
        )
        
        # Return confidence as decimal (0-1) for backward compatibility
        return comprehensive_result['overall_confidence'] / 100.0
        
    except Exception as e:
        logger.warning(f"Error in legacy confidence calculation: {e}")
        return 0.5
        
        
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
    # Randomly select from ALL available Monk skin tones instead of just a few
    all_tone_names = list(MONK_SKIN_TONES.keys())
    selected_tone = random.choice(all_tone_names)
    
    monk_number = selected_tone.split()[1]
    monk_id = f"Monk{monk_number.zfill(2)}"
    monk_hex = MONK_SKIN_TONES[selected_tone]
    
    logger.warning(f"Using random fallback skin tone from all available options: {selected_tone}")
    
    return {
        'monk_skin_tone': monk_id,
        'monk_tone_display': selected_tone,
        'monk_hex': monk_hex,
        'derived_hex_code': monk_hex,
        'dominant_rgb': list(hex_to_rgb(monk_hex)),
        'confidence': 0.2,  # Lower confidence for random fallback
        'success': False,  # Indicate this is a fallback
        'message': 'Using random fallback skin tone due to analysis failure'
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
def load_data_file(primary_path, fallback_path, default_df=None, show_warnings=False):
    """Load a data file with fallback options."""
    if os.path.exists(primary_path):
        return pd.read_csv(primary_path).fillna("")
    elif os.path.exists(fallback_path):
        return pd.read_csv(fallback_path).fillna("")
    else:
        if show_warnings:
            print(f"Warning: Neither {primary_path} nor {fallback_path} found.")
        return default_df if default_df is not None else pd.DataFrame()

# Load CSV data for H&M products (commented out - using database now)
# df_hm = load_data_file(
#     "../processed_data/hm_products_hm_products.csv",
#     "hm_products2.csv",
#     pd.DataFrame(columns=["Product Name", "Price", "Image URL", "Product Type", "brand", "gender", "baseColour", "masterCategory", "subCategory"])
# )
df_hm = pd.DataFrame(columns=["Product Name", "Price", "Image URL", "Product Type", "brand", "gender", "baseColour", "masterCategory", "subCategory"])

# Load CSV data for Ulta & Sephora products
df_sephora = load_data_file(
    "processed_data/all_makeup_products.csv",
    "ulta_with_mst_index.csv",
    pd.DataFrame(columns=["product", "brand", "price", "imgSrc", "mst", "hex", "desc", "product_type"])
)

# Load outfit data from the specified CSV files (commented out - coming soon feature)
# df_outfit1 = load_data_file(
#     "../processed_data/outfit_products_outfit1.csv",
#     "outfit_products_outfit1.csv",
#     pd.DataFrame(columns=["products", "brand", "Product Type", "gender", "baseColour", "masterCategory", "subCategory"])
# )
df_outfit1 = pd.DataFrame(columns=["products", "brand", "Product Type", "gender", "baseColour", "masterCategory", "subCategory"])

# df_outfit2 = load_data_file(
#     "../processed_data/outfit_products_outfit2.csv",
#     "outfit_products_outfit2.csv",
#     pd.DataFrame(columns=["products", "brand", "Product Type", "gender", "baseColour", "masterCategory", "subCategory"])
# )
df_outfit2 = pd.DataFrame(columns=["products", "brand", "Product Type", "gender", "baseColour", "masterCategory", "subCategory"])

# Load apparel data (commented out - coming soon feature) 
# df_apparel = load_data_file(
#     "processed_data/outfit_products.csv",
#     "apparel.csv",
#     pd.DataFrame(columns=["Product Name", "Price", "Image URL", "gender", "baseColour", "masterCategory", "subCategory"])
# )
df_apparel = pd.DataFrame(columns=["Product Name", "Price", "Image URL", "gender", "baseColour", "masterCategory", "subCategory"])

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

@app.get("/api/color-palettes-db")
async def get_color_palettes_from_db(
    skin_tone: str = Query(None, description="Skin tone category (e.g., 'Clear Winter', 'Warm Spring')"),
    monk_tone: str = Query(None, description="Monk skin tone (e.g., 'Monk01', 'Monk03')"),
    hex_color: str = Query(None, description="Hex color code of the skin tone (e.g., '#f6ede4')"),
    db: Session = Depends(get_database)
):
    """
    Get comprehensive color palettes from the database based on skin tone.
    
    Returns color palettes, hex codes, and suggestions from PostgreSQL database.
    """
    try:
        seasonal_type = None
        
        # Determine seasonal type from various inputs
        if skin_tone:
            seasonal_type = skin_tone
        elif monk_tone:
            # Handle different formats (e.g., "Monk03", "Monk 3")
            monk_id = monk_tone
            if " " in monk_tone:
                parts = monk_tone.split()
                if len(parts) >= 2 and parts[0].lower() == "monk":
                    try:
                        monk_num = int(parts[1])
                        monk_id = f"Monk{monk_num:02d}"
                    except ValueError:
                        monk_id = monk_tone
            
            # Get seasonal type from monk tone mapping
            if monk_id in monk_to_seasonal:
                seasonal_type = monk_to_seasonal[monk_id]
                
        # Get color palette data
        palette_query = db.query(ColorPalette)
        if seasonal_type:
            palette_query = palette_query.filter(ColorPalette.skin_tone == seasonal_type)
        
        palettes = palette_query.all()
        
        # Get hex color data
        hex_data_query = db.query(ColorHexData)
        if seasonal_type:
            hex_data_query = hex_data_query.filter(ColorHexData.seasonal_type == seasonal_type)
        
        hex_data_results = hex_data_query.all()
        
        # Get color suggestions
        suggestions_query = db.query(ColorSuggestions)
        if seasonal_type:
            suggestions_query = suggestions_query.filter(ColorSuggestions.skin_tone == seasonal_type)
        
        suggestions_results = suggestions_query.all()
        
        # Compile comprehensive response
        colors_that_suit = []
        colors_to_avoid = []
        additional_hex_codes = []
        text_suggestions = []
        
        # Add palette colors
        if palettes:
            palette = palettes[0]
            colors_that_suit.extend(palette.flattering_colors or [])
            colors_to_avoid.extend(palette.colors_to_avoid or [])
            description = palette.description
        else:
            description = f"Color recommendations for {seasonal_type or 'your skin tone'}"
        
        # Add hex color data
        for hex_data in hex_data_results:
            additional_hex_codes.extend(hex_data.hex_codes or [])
        
        # Add text suggestions
        for suggestion in suggestions_results:
            if suggestion.suitable_colors_text:
                text_suggestions.append(suggestion.suitable_colors_text)
        
        # If no specific data found, provide default comprehensive palette
        if not colors_that_suit and not additional_hex_codes:
            colors_that_suit = [
                {"name": "Navy Blue", "hex": "#000080"},
                {"name": "Forest Green", "hex": "#228B22"},
                {"name": "Burgundy", "hex": "#800020"},
                {"name": "Charcoal Gray", "hex": "#36454F"},
                {"name": "Cream White", "hex": "#F5F5DC"},
                {"name": "Soft Pink", "hex": "#FFB6C1"}
            ]
        
        # Convert hex codes to color objects if needed
        hex_color_objects = []
        for i, hex_code in enumerate(additional_hex_codes[:10]):  # Limit to 10 additional colors
            hex_color_objects.append({
                "name": f"Recommended Color {i+1}",
                "hex": hex_code
            })
        
        # Merge all colors (avoid duplicates)
        all_colors = colors_that_suit.copy()
        existing_hex = {color["hex"] for color in all_colors}
        
        for hex_color_obj in hex_color_objects:
            if hex_color_obj["hex"] not in existing_hex:
                all_colors.append(hex_color_obj)
                existing_hex.add(hex_color_obj["hex"])
        
        response = {
            "colors_that_suit": all_colors,
            "colors_to_avoid": colors_to_avoid,
            "seasonal_type": seasonal_type,
            "monk_skin_tone": monk_tone,
            "description": description,
            "text_suggestions": text_suggestions,
            "additional_hex_codes": additional_hex_codes,
            "message": "Comprehensive color recommendations from database",
            "data_sources": {
                "palettes": len(palettes),
                "hex_data_sets": len(hex_data_results),
                "text_suggestions": len(suggestions_results)
            }
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error fetching color palettes from database: {e}")
        return {
            "colors_that_suit": [
                {"name": "Navy Blue", "hex": "#000080"},
                {"name": "Forest Green", "hex": "#228B22"},
                {"name": "Burgundy", "hex": "#800020"},
                {"name": "Charcoal Gray", "hex": "#36454F"}
            ],
            "message": "Error loading from database, showing default colors",
            "error": str(e)
        }

@app.get("/api/color-recommendations")
async def get_color_recommendations(
    skin_tone: str = Query(None, description="Skin tone category (e.g., 'Winter', 'Summer', 'Monk01-10')"),
    hex_color: str = Query(None, description="Hex color code of the skin tone (e.g., '#f6ede4')")
):
    """
    Get comprehensive color recommendations based on Monk skin tone and seasonal color analysis.
    
    Returns colors that suit the user's skin tone with scientific color theory backing.
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
    
    # Load color recommendations from JSON file
    color_recommendations_file = os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', 'color_recommendations.json')
    enhanced_palettes = {}
    
    if os.path.exists(color_recommendations_file):
        try:
            with open(color_recommendations_file, 'r', encoding='utf-8') as f:
                color_data = json.load(f)
                
            # Map skin tones to seasonal types and load their color palettes
            skin_tone_to_seasonal = {
                'Fair': {'Cool': 'Cool Winter', 'Warm': 'Warm Spring', 'Neutral': 'Light Spring'},
                'Medium': {'Cool': 'Cool Summer', 'Warm': 'Warm Autumn', 'Neutral': 'Soft Autumn'}, 
                'Olive': {'Cool': 'Deep Winter', 'Warm': 'Deep Autumn', 'Neutral': 'Soft Autumn'},
                'Dark': {'Cool': 'Deep Winter', 'Warm': 'Deep Autumn', 'Neutral': 'Deep Winter'},
                'Deep': {'Cool': 'Clear Winter', 'Warm': 'Warm Autumn', 'Neutral': 'Deep Winter'}
            }
            
            # Convert the loaded data to seasonal types
            for skin_tone, undertones in color_data.items():
                for undertone, colors in undertones.items():
                    seasonal_key = skin_tone_to_seasonal.get(skin_tone, {}).get(undertone, f"{skin_tone} {undertone}")
                    enhanced_palettes[seasonal_key] = colors
                    
            logger.info(f"Loaded {len(enhanced_palettes)} seasonal color palettes from JSON file")
            
        except Exception as e:
            logger.error(f"Error loading color recommendations file: {e}")
    
    # Fallback enhanced color palettes for each seasonal type
    if not enhanced_palettes:
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
    
    # Default response with scientific color recommendations based on universal color theory
    return {
        "colors_that_suit": [
            {"name": "Navy Blue", "hex": "#000080"},
            {"name": "Forest Green", "hex": "#228B22"},
            {"name": "Burgundy", "hex": "#800020"},
            {"name": "Charcoal Gray", "hex": "#36454F"},
            {"name": "Cream White", "hex": "#F5F5DC"},
            {"name": "Deep Purple", "hex": "#301934"},
            {"name": "Teal", "hex": "#008080"},
            {"name": "Soft Pink", "hex": "#FFB6C1"},
            {"name": "Royal Blue", "hex": "#4169E1"},
            {"name": "Emerald Green", "hex": "#50C878"},
            {"name": "Coral", "hex": "#FF7F50"},
            {"name": "Golden Yellow", "hex": "#FFD700"}
        ],
        "seasonal_type": "Universal",
        "message": "These universally flattering colors complement most skin tones. For personalized recommendations, please provide your Monk skin tone (Monk01-10)."
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
        
        # Analyze skin tone using LAB color space for better accuracy
        result = analyze_skin_tone_lab(image_array)
        
        logger.info(f"Skin tone analysis result: {result}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in analyze_skin_tone endpoint: {e}")
        return get_fallback_result()

# Health and monitoring endpoints
@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "message": "Skin tone analysis API is running",
        "available_tones": list(MONK_SKIN_TONES.keys())
    }

@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with system information"""
    return await get_health_endpoint()

@app.get("/metrics")
async def get_system_metrics():
    """Get Prometheus-style application metrics"""
    return await get_metrics_endpoint()

@app.get("/stats")
async def get_system_stats():
    """Get detailed system statistics"""
    return await get_system_stats_endpoint()

# Advanced Recommendation Endpoints
@app.post("/api/advanced-recommendations")
async def get_advanced_recommendations(request: dict):
    """Get advanced personalized recommendations using ML engine."""
    try:
        # Get recommendation engine instance
        rec_engine = get_recommendation_engine()
        
        # Extract parameters from request
        skin_tone = request.get('skin_tone', 'Monk 5')
        user_preferences = request.get('user_preferences', {})
        n_recommendations = request.get('limit', 10)
        
        # Get personalized recommendations
        recommendations = rec_engine.get_personalized_recommendations(
            skin_tone=skin_tone,
            user_preferences=user_preferences,
            n_recommendations=n_recommendations
        )
        
        return {
            "success": True,
            "data": recommendations,
            "message": "Advanced recommendations generated successfully"
        }
        
    except Exception as e:
        logger.error(f"Error in advanced recommendations: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to generate recommendations"
        }

@app.get("/api/trending-items")
async def get_trending_items(
    product_type: str = Query('makeup', description="Product type: makeup or outfit"),
    limit: int = Query(10, description="Number of trending items to return")
):
    """Get trending items using ML engine."""
    try:
        # Get recommendation engine instance
        rec_engine = get_recommendation_engine()
        
        # Get trending items
        trending_items = rec_engine.get_trending_items(
            product_type=product_type,
            n_items=limit
        )
        
        return {
            "success": True,
            "data": trending_items,
            "total_items": len(trending_items),
            "message": f"Retrieved {len(trending_items)} trending {product_type} items"
        }
        
    except Exception as e:
        logger.error(f"Error getting trending items: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to retrieve trending items"
        }

@app.post("/api/user-feedback")
async def add_user_feedback(request: dict):
    """Add user feedback for improving recommendations."""
    try:
        # Get recommendation engine instance
        rec_engine = get_recommendation_engine()
        
        # Extract parameters
        user_id = request.get('user_id')
        item_id = request.get('item_id')
        rating = request.get('rating')
        interaction_type = request.get('interaction_type', 'rating')
        
        if not all([user_id, item_id, rating]):
            return {
                "success": False,
                "message": "Missing required fields: user_id, item_id, rating"
            }
        
        # Add feedback
        rec_engine.add_user_feedback(
            user_id=user_id,
            item_id=item_id,
            rating=float(rating),
            interaction_type=interaction_type
        )
        
        return {
            "success": True,
            "message": "User feedback added successfully"
        }
        
    except Exception as e:
        logger.error(f"Error adding user feedback: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to add user feedback"
        }

@app.get("/api/content-recommendations")
async def get_content_based_recommendations(
    product_type: str = Query('makeup', description="Product type: makeup or outfit"),
    item_index: int = Query(0, description="Index of item to find similar items for"),
    limit: int = Query(10, description="Number of recommendations to return")
):
    """Get content-based recommendations."""
    try:
        # Get recommendation engine instance
        rec_engine = get_recommendation_engine()
        
        # Get content-based recommendations
        recommendations = rec_engine.content_based_recommendations(
            product_type=product_type,
            item_idx=item_index,
            n_recommendations=limit
        )
        
        return {
            "success": True,
            "data": recommendations,
            "total_items": len(recommendations),
            "message": f"Retrieved {len(recommendations)} content-based recommendations"
        }
        
    except Exception as e:
        logger.error(f"Error getting content recommendations: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to retrieve content-based recommendations"
        }

# A/B Testing System Endpoints
@app.post("/api/ab-test/create")
async def create_ab_test_experiment(request: dict):
    """Create a new A/B test experiment."""
    try:
        experiment_name = request.get('experiment_name')
        control_algorithm = request.get('control_algorithm', 'collaborative')
        test_algorithm = request.get('test_algorithm', 'content_based')
        traffic_split = request.get('traffic_split', 0.5)
        target_metric = request.get('target_metric', 'click_rate')
        description = request.get('description', '')
        
        if not experiment_name:
            return {
                "success": False,
                "message": "experiment_name is required"
            }
        
        # Create experiment using A/B testing system
        experiment = create_ab_test(
            experiment_name=experiment_name,
            control_algorithm=RecommendationAlgorithm[control_algorithm.upper()],
            test_algorithm=RecommendationAlgorithm[test_algorithm.upper()],
            traffic_split=traffic_split,
            target_metric=target_metric,
            description=description
        )
        
        return {
            "success": True,
            "data": {
                "experiment_id": experiment.experiment_id,
                "experiment_name": experiment.experiment_name,
                "control_algorithm": experiment.control_algorithm.name,
                "test_algorithm": experiment.test_algorithm.name,
                "traffic_split": experiment.traffic_split,
                "target_metric": experiment.target_metric,
                "status": experiment.status,
                "created_at": experiment.start_time.isoformat()
            },
            "message": "A/B test experiment created successfully"
        }
        
    except Exception as e:
        logger.error(f"Error creating A/B test: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to create A/B test experiment"
        }

@app.get("/api/ab-test/recommendations")
async def get_ab_test_recommendations(
    user_id: str = Query(..., description="User ID for variant assignment"),
    experiment_name: str = Query(..., description="Name of the A/B test experiment"),
    product_type: str = Query('makeup', description="Product type: makeup or outfit"),
    skin_tone: str = Query(None, description="User's skin tone"),
    limit: int = Query(10, description="Number of recommendations to return")
):
    """Get recommendations for a user based on their A/B test variant."""
    try:
        # Prepare user preferences
        user_preferences = {
            'skin_tone': skin_tone,
            'product_type': product_type
        }
        
        # Get A/B test recommendations
        result = get_ab_test_recommendations(
            user_id=user_id,
            experiment_name=experiment_name,
            user_preferences=user_preferences,
            n_recommendations=limit
        )
        
        return {
            "success": True,
            "data": result['recommendations'],
            "variant": result['variant'],
            "algorithm_used": result['algorithm'].name,
            "experiment_name": experiment_name,
            "total_items": len(result['recommendations']),
            "message": f"Retrieved {len(result['recommendations'])} recommendations using {result['variant']} variant"
        }
        
    except Exception as e:
        logger.error(f"Error getting A/B test recommendations: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to retrieve A/B test recommendations"
        }

@app.post("/api/ab-test/track-event")
async def track_ab_test_event(request: dict):
    """Track user events for A/B test analysis."""
    try:
        user_id = request.get('user_id')
        experiment_name = request.get('experiment_name')
        event_type = request.get('event_type')  # 'view', 'click', 'purchase', 'rating'
        item_id = request.get('item_id')
        value = request.get('value', 1.0)  # rating value or purchase amount
        
        if not all([user_id, experiment_name, event_type]):
            return {
                "success": False,
                "message": "Missing required fields: user_id, experiment_name, event_type"
            }
        
        # Track the event
        track_ab_test_event(
            user_id=user_id,
            experiment_name=experiment_name,
            event_type=event_type,
            item_id=item_id,
            value=value
        )
        
        return {
            "success": True,
            "message": f"Event '{event_type}' tracked successfully for user {user_id}"
        }
        
    except Exception as e:
        logger.error(f"Error tracking A/B test event: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to track A/B test event"
        }

@app.get("/api/ab-test/experiments")
async def list_ab_test_experiments():
    """List all A/B test experiments."""
    try:
        experiments = ab_testing_system.list_experiments()
        
        experiments_data = []
        for exp in experiments:
            experiments_data.append({
                "experiment_id": exp.experiment_id,
                "experiment_name": exp.experiment_name,
                "control_algorithm": exp.control_algorithm.name,
                "test_algorithm": exp.test_algorithm.name,
                "traffic_split": exp.traffic_split,
                "target_metric": exp.target_metric,
                "status": exp.status,
                "created_at": exp.start_time.isoformat(),
                "description": exp.description,
                "total_users": len(exp.user_assignments)
            })
        
        return {
            "success": True,
            "data": experiments_data,
            "total_experiments": len(experiments_data),
            "message": f"Retrieved {len(experiments_data)} A/B test experiments"
        }
        
    except Exception as e:
        logger.error(f"Error listing A/B test experiments: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to retrieve A/B test experiments"
        }

@app.get("/api/ab-test/results/{experiment_name}")
async def get_ab_test_results(experiment_name: str):
    """Get results and analysis for a specific A/B test experiment."""
    try:
        results = ab_testing_system.get_experiment_results(experiment_name)
        
        if not results:
            return {
                "success": False,
                "message": f"No results found for experiment: {experiment_name}"
            }
        
        return {
            "success": True,
            "data": results,
            "experiment_name": experiment_name,
            "message": f"Retrieved results for experiment: {experiment_name}"
        }
        
    except Exception as e:
        logger.error(f"Error getting A/B test results: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to retrieve results for experiment: {experiment_name}"
        }

@app.post("/api/ab-test/stop/{experiment_name}")
async def stop_ab_test_experiment(experiment_name: str):
    """Stop a running A/B test experiment."""
    try:
        success = ab_testing_system.stop_experiment(experiment_name)
        
        if success:
            return {
                "success": True,
                "message": f"Experiment '{experiment_name}' stopped successfully"
            }
        else:
            return {
                "success": False,
                "message": f"Failed to stop experiment '{experiment_name}' - experiment not found or already stopped"
            }
        
    except Exception as e:
        logger.error(f"Error stopping A/B test experiment: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to stop experiment: {experiment_name}"
        }

@app.get("/api/ab-test/user-variant/{user_id}")
async def get_user_ab_test_variants(user_id: str):
    """Get all active A/B test variants for a specific user."""
    try:
        experiments = ab_testing_system.list_experiments()
        user_variants = []
        
        for exp in experiments:
            if exp.status == 'active' and user_id in exp.user_assignments:
                user_variants.append({
                    "experiment_name": exp.experiment_name,
                    "variant": exp.user_assignments[user_id],
                    "algorithm": exp.control_algorithm.name if exp.user_assignments[user_id] == 'control' else exp.test_algorithm.name
                })
        
        return {
            "success": True,
            "data": user_variants,
            "user_id": user_id,
            "total_active_tests": len(user_variants),
            "message": f"Retrieved {len(user_variants)} active A/B test assignments for user {user_id}"
        }
        
    except Exception as e:
        logger.error(f"Error getting user A/B test variants: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to retrieve A/B test variants for user: {user_id}"
        }
