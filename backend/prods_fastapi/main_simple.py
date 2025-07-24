# Simplified FastAPI application for Render deployment
from fastapi import FastAPI, Query, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import json
import math
import os
from typing import List, Optional, Dict
import numpy as np
import cv2
from webcolors import hex_to_rgb, rgb_to_hex
import io
from PIL import Image
import logging
import random
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI Fashion Backend",
    version="1.0.0",
    description="AI Fashion recommendation system with skin tone analysis"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Monk skin tone scale
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

# Basic color mapping
color_mapping = {
    "Red": "Red",
    "Blue": "Blue", 
    "Green": "Green",
    "Black": "Black",
    "White": "White",
    "Pink": "Pink",
    "Yellow": "Yellow",
    "Purple": "Purple",
    "Orange": "Orange",
    "Brown": "Brown"
}

@app.get("/")
def home():
    return {"message": "Welcome to the AI Fashion API!", "status": "healthy"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "AI Fashion Backend is running"}

@app.get("/color-suggestions")
def get_color_suggestions(skin_tone: str = Query(None)):
    """Get color suggestions for a specific skin tone."""
    suggestions = [
        {"skin_tone": "Fair", "suitable_colors": "Navy Blue, Emerald Green, Ruby Red, Cool Pink"},
        {"skin_tone": "Medium", "suitable_colors": "Warm Brown, Orange, Coral, Olive Green"},
        {"skin_tone": "Dark", "suitable_colors": "Bright Yellow, Royal Blue, Magenta, White"},
        {"skin_tone": "Deep", "suitable_colors": "Vibrant Colors, Jewel Tones, Bright Contrasts"}
    ]
    
    if skin_tone:
        filtered = [s for s in suggestions if skin_tone.lower() in s["skin_tone"].lower()]
        return {"data": filtered, "total_items": len(filtered)}
    
    return {"data": suggestions, "total_items": len(suggestions)}

@app.get("/data/")
def get_makeup_data(
    mst: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(24, ge=1, le=100)
):
    """Get makeup products with pagination."""
    # Generate sample makeup products
    brands = ["Fenty Beauty", "MAC", "NARS", "Maybelline", "L'Oreal", "Dior"]
    products = ["Foundation", "Concealer", "Lipstick", "Mascara", "Blush", "Highlighter"]
    
    sample_data = []
    for i in range(100):  # Generate 100 sample products
        brand = random.choice(brands)
        product_type = random.choice(products)
        price = f"${random.randint(15, 50)}.{random.randint(10, 99)}"
        
        sample_data.append({
            "product_name": f"{brand} {product_type}",
            "brand": brand,
            "price": price,
            "image_url": f"https://via.placeholder.com/150/FF{random.randint(1000, 9999)}/FFFFFF?text={brand.replace(' ', '+')}",
            "mst": mst or f"Monk{random.randint(1, 10):02d}",
            "desc": f"Beautiful {product_type.lower()} from {brand}"
        })
    
    # Apply pagination
    total_items = len(sample_data)
    total_pages = math.ceil(total_items / limit)
    start_idx = (page - 1) * limit
    end_idx = min(start_idx + limit, total_items)
    
    paginated_data = sample_data[start_idx:end_idx]
    
    return {
        "data": paginated_data,
        "total_items": total_items,
        "total_pages": total_pages,
        "page": page,
        "limit": limit
    }

@app.get("/apparel")
def get_apparel(
    gender: str = Query(None),
    color: List[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(24, ge=1, le=100)
):
    """Get apparel products."""
    # Generate sample apparel
    brands = ["H&M", "Zara", "Nike", "Adidas", "Uniqlo", "Gap"]
    types = ["T-Shirt", "Jeans", "Dress", "Jacket", "Sweater", "Pants"]
    colors = ["Black", "White", "Blue", "Red", "Green", "Gray"]
    
    sample_data = []
    for i in range(50):
        brand = random.choice(brands)
        product_type = random.choice(types)
        base_color = random.choice(colors)
        price = f"${random.randint(20, 80)}.{random.randint(10, 99)}"
        
        sample_data.append({
            "Product Name": f"{brand} {product_type}",
            "Price": price,
            "Image URL": f"https://via.placeholder.com/150/{random.randint(100000, 999999)}/FFFFFF?text={product_type.replace(' ', '+')}",
            "Product Type": product_type,
            "baseColour": base_color,
            "brand": brand,
            "gender": gender or random.choice(["Men", "Women", "Unisex"])
        })
    
    # Apply pagination
    total_items = len(sample_data)
    total_pages = math.ceil(total_items / limit)
    start_idx = (page - 1) * limit
    end_idx = min(start_idx + limit, total_items)
    
    paginated_data = sample_data[start_idx:end_idx]
    
    return {
        "data": paginated_data,
        "page": page,
        "limit": limit,
        "total_items": total_items,
        "total_pages": total_pages
    }

@app.get("/api/color-recommendations")
async def get_color_recommendations(
    skin_tone: str = Query(None),
    hex_color: str = Query(None)
):
    """Get color recommendations based on skin tone."""
    
    # Default color recommendations
    color_palettes = {
        "Monk01": [
            {"name": "Soft Pink", "hex": "#FFB6C1"},
            {"name": "Light Blue", "hex": "#ADD8E6"},
            {"name": "Cream", "hex": "#F5F5DC"},
            {"name": "Lavender", "hex": "#E6E6FA"}
        ],
        "Monk05": [
            {"name": "Warm Coral", "hex": "#FF7F50"},
            {"name": "Golden Yellow", "hex": "#FFD700"},
            {"name": "Olive Green", "hex": "#808000"},
            {"name": "Rust", "hex": "#B7410E"}
        ],
        "Monk10": [
            {"name": "Bright Yellow", "hex": "#FFFF00"},
            {"name": "Royal Blue", "hex": "#4169E1"},
            {"name": "Emerald Green", "hex": "#50C878"},
            {"name": "Magenta", "hex": "#FF00FF"}
        ]
    }
    
    # Default universal colors
    default_colors = [
        {"name": "Navy Blue", "hex": "#000080"},
        {"name": "Forest Green", "hex": "#228B22"},
        {"name": "Burgundy", "hex": "#800020"},
        {"name": "Charcoal Gray", "hex": "#36454F"},
        {"name": "Cream White", "hex": "#F5F5DC"},
        {"name": "Soft Pink", "hex": "#FFB6C1"}
    ]
    
    # Determine which colors to return
    if skin_tone and skin_tone in color_palettes:
        colors = color_palettes[skin_tone]
    else:
        colors = default_colors
    
    return {
        "colors_that_suit": colors,
        "seasonal_type": "Universal",
        "monk_skin_tone": skin_tone,
        "message": "Color recommendations based on your skin tone"
    }

def apply_lighting_correction(image_array: np.ndarray) -> np.ndarray:
    """Apply CLAHE and lighting correction for better skin tone detection."""
    try:
        # Convert to LAB color space for better lighting correction
        lab_image = cv2.cvtColor(image_array, cv2.COLOR_RGB2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab_image)
        
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l_channel_corrected = clahe.apply(l_channel)
        
        # Merge channels back
        corrected_lab = cv2.merge([l_channel_corrected, a_channel, b_channel])
        
        # Convert back to RGB
        corrected_rgb = cv2.cvtColor(corrected_lab, cv2.COLOR_LAB2RGB)
        
        # Apply gentle gamma correction for very light skin tones
        gamma = 1.2  # Slightly brighten to better detect light skin
        corrected_rgb = np.power(corrected_rgb / 255.0, gamma) * 255.0
        corrected_rgb = np.clip(corrected_rgb, 0, 255).astype(np.uint8)
        
        return corrected_rgb
        
    except Exception as e:
        logger.warning(f"Lighting correction failed: {e}, using original image")
        return image_array

def extract_multi_region_colors(image_array: np.ndarray) -> List[np.ndarray]:
    """Extract skin colors from multiple face regions for better accuracy."""
    h, w = image_array.shape[:2]
    
    # Define multiple face regions (optimized for light skin detection)
    regions = [
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
    
    region_colors = []
    
    for region in regions:
        if region.size > 100:  # Ensure region has enough pixels
            # For light skin, focus on brighter pixels
            region_gray = cv2.cvtColor(region, cv2.COLOR_RGB2GRAY)
            
            # Use adaptive thresholding for light skin detection
            light_threshold = np.percentile(region_gray, 75)  # Top 25% brightest pixels
            light_mask = region_gray > light_threshold
            
            if np.sum(light_mask) > 50:  # Enough light pixels
                light_pixels = region[light_mask]
                region_color = np.mean(light_pixels, axis=0)
                region_colors.append(region_color)
    
    return region_colors

def calculate_confidence_score(image_array: np.ndarray, final_color: np.ndarray, closest_distance: float) -> float:
    """Calculate confidence score based on multiple factors."""
    try:
        # Base confidence from color distance (closer = higher confidence)
        distance_confidence = max(0, 1 - (closest_distance / 200))  # Normalize to 0-1
        
        # Check image quality (sharpness)
        gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
        sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
        sharpness_confidence = min(1.0, sharpness / 500)  # Good sharpness > 500
        
        # Check brightness consistency (for light skin detection)
        brightness_std = np.std(final_color)
        consistency_confidence = max(0, 1 - (brightness_std / 50))  # Lower std = more consistent
        
        # Overall brightness check (light skin should be bright)
        avg_brightness = np.mean(final_color)
        if avg_brightness > 200:  # Very light skin
            brightness_bonus = 0.2
        elif avg_brightness > 180:  # Light skin
            brightness_bonus = 0.1
        else:
            brightness_bonus = 0
        
        # Weighted combination
        final_confidence = (
            distance_confidence * 0.4 +
            sharpness_confidence * 0.3 +
            consistency_confidence * 0.3 +
            brightness_bonus
        )
        
        return min(1.0, final_confidence)  # Cap at 1.0
        
    except Exception as e:
        logger.warning(f"Confidence calculation failed: {e}")
        return 0.5  # Default confidence

def find_closest_monk_tone_enhanced(rgb_color: np.ndarray) -> tuple:
    """Enhanced Monk tone matching with better light skin detection."""
    min_distance = float('inf')
    closest_monk = "Monk 2"  # Default to lighter tone
    
    # Calculate average brightness
    avg_brightness = np.mean(rgb_color)
    
    # Enhanced distance calculation for light skin tones
    for monk_name, hex_color in MONK_SKIN_TONES.items():
        monk_rgb = np.array(hex_to_rgb(hex_color))
        
        # Standard Euclidean distance
        euclidean_distance = np.sqrt(np.sum((rgb_color - monk_rgb) ** 2))
        
        # Brightness-weighted distance (favor similar brightness levels)
        brightness_diff = abs(avg_brightness - np.mean(monk_rgb))
        
        # For very light skin (>220), heavily weight brightness similarity
        if avg_brightness > 220:
            combined_distance = euclidean_distance * 0.3 + brightness_diff * 1.5
        # For light skin (180-220), moderately weight brightness
        elif avg_brightness > 180:
            combined_distance = euclidean_distance * 0.6 + brightness_diff * 1.0
        # For darker skin, use standard distance
        else:
            combined_distance = euclidean_distance
        
        if combined_distance < min_distance:
            min_distance = combined_distance
            closest_monk = monk_name
    
    return closest_monk, min_distance

def analyze_skin_tone_enhanced(image_array: np.ndarray) -> Dict:
    """Enhanced skin tone analysis with LAB color space, CLAHE, multi-region analysis, and confidence scoring."""
    try:
        logger.info("Starting enhanced skin tone analysis...")
        
        # Step 1: Apply lighting correction
        corrected_image = apply_lighting_correction(image_array)
        
        # Step 2: Extract colors from multiple regions
        region_colors = extract_multi_region_colors(corrected_image)
        
        if not region_colors:
            # Fallback to center region if no regions found
            h, w = corrected_image.shape[:2]
            center_region = corrected_image[h//4:3*h//4, w//4:3*w//4]
            avg_color = np.mean(center_region.reshape(-1, 3), axis=0)
        else:
            # Step 3: Calculate weighted average of region colors
            region_colors_array = np.array(region_colors)
            
            # Weight regions by brightness for light skin detection
            brightness_weights = np.mean(region_colors_array, axis=1)
            
            # Normalize weights
            if np.sum(brightness_weights) > 0:
                brightness_weights = brightness_weights / np.sum(brightness_weights)
                avg_color = np.average(region_colors_array, axis=0, weights=brightness_weights)
            else:
                avg_color = np.mean(region_colors_array, axis=0)
        
        # Step 4: Convert to LAB color space for final analysis
        lab_color = cv2.cvtColor(np.uint8([[avg_color]]), cv2.COLOR_RGB2LAB)[0][0]
        
        # Step 5: Find closest Monk tone with enhanced algorithm
        closest_monk, min_distance = find_closest_monk_tone_enhanced(avg_color)
        
        # Step 6: Calculate confidence score
        confidence = calculate_confidence_score(image_array, avg_color, min_distance)
        
        # Format response
        monk_number = closest_monk.split()[1]
        monk_id = f"Monk{monk_number.zfill(2)}"
        derived_hex = rgb_to_hex((int(avg_color[0]), int(avg_color[1]), int(avg_color[2])))
        
        logger.info(f"Enhanced analysis result: {monk_id}, confidence: {confidence:.2f}")
        
        return {
            'monk_skin_tone': monk_id,
            'monk_tone_display': closest_monk,
            'monk_hex': MONK_SKIN_TONES[closest_monk],
            'derived_hex_code': derived_hex,
            'dominant_rgb': avg_color.astype(int).tolist(),
            'confidence': round(confidence, 2),
            'success': True,
            'analysis_method': 'enhanced_lab_clahe_multi_region',
            'regions_analyzed': len(region_colors) if region_colors else 1
        }
        
    except Exception as e:
        logger.error(f"Error in enhanced skin tone analysis: {e}")
        return {
            'monk_skin_tone': 'Monk02',  # Default to lighter tone for errors
            'monk_tone_display': 'Monk 2',
            'monk_hex': MONK_SKIN_TONES['Monk 2'],
            'derived_hex_code': '#f3e7db',
            'dominant_rgb': [243, 231, 219],
            'confidence': 0.3,
            'success': False,
            'error': str(e)
        }

# Keep the simple version as fallback
def analyze_skin_tone_simple(image_array: np.ndarray) -> Dict:
    """Simplified skin tone analysis (fallback method)."""
    try:
        # Get average color of the image center
        h, w = image_array.shape[:2]
        center_region = image_array[h//4:3*h//4, w//4:3*w//4]
        
        # Calculate average RGB
        avg_color = np.mean(center_region.reshape(-1, 3), axis=0)
        
        # Find closest Monk skin tone
        min_distance = float('inf')
        closest_monk = "Monk 2"  # Default to lighter tone
        
        for monk_name, hex_color in MONK_SKIN_TONES.items():
            monk_rgb = np.array(hex_to_rgb(hex_color))
            distance = np.sqrt(np.sum((avg_color - monk_rgb) ** 2))
            
            if distance < min_distance:
                min_distance = distance
                closest_monk = monk_name
        
        # Format response
        monk_number = closest_monk.split()[1]
        monk_id = f"Monk{monk_number.zfill(2)}"
        derived_hex = rgb_to_hex((int(avg_color[0]), int(avg_color[1]), int(avg_color[2])))
        
        return {
            'monk_skin_tone': monk_id,
            'monk_tone_display': closest_monk,
            'monk_hex': MONK_SKIN_TONES[closest_monk],
            'derived_hex_code': derived_hex,
            'dominant_rgb': avg_color.astype(int).tolist(),
            'confidence': 0.6,
            'success': True,
            'analysis_method': 'simple_rgb'
        }
        
    except Exception as e:
        logger.error(f"Error in simple skin tone analysis: {e}")
        return {
            'monk_skin_tone': 'Monk02',
            'monk_tone_display': 'Monk 2',
            'monk_hex': MONK_SKIN_TONES['Monk 2'],
            'derived_hex_code': '#f3e7db',
            'dominant_rgb': [243, 231, 219],
            'confidence': 0.3,
            'success': False,
            'error': str(e)
        }

@app.post("/analyze-skin-tone")
async def analyze_skin_tone(file: UploadFile = File(...)):
    """Analyze skin tone from uploaded image."""
    try:
        # Validate file type
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read and process image
        image_data = await file.read()
        image = Image.open(io.BytesIO(image_data))
        
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        image_array = np.array(image)
        
        # Try enhanced analysis first, fallback to simple if it fails
        try:
            result = analyze_skin_tone_enhanced(image_array)
            if result['success']:
                return result
        except Exception as e:
            logger.warning(f"Enhanced analysis failed: {e}, falling back to simple analysis")
        
        # Fallback to simple analysis
        result = analyze_skin_tone_simple(image_array)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in analyze_skin_tone endpoint: {e}")
        return {
            'monk_skin_tone': 'Monk05',
            'monk_tone_display': 'Monk 5',
            'monk_hex': '#d7bd96',
            'derived_hex_code': '#d7bd96',
            'dominant_rgb': [215, 189, 150],
            'confidence': 0.5,
            'success': False,
            'error': str(e)
        }

# Additional endpoints for compatibility
@app.get("/products")
def get_products(product_type: str = Query(None), random: bool = Query(False)):
    """Get H&M style products."""
    return []

@app.get("/makeup-types")
def get_makeup_types():
    """Get available makeup types."""
    return {
        "types": ["Foundation", "Concealer", "Lipstick", "Mascara", "Blush", "Highlighter", "Eyeshadow"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
