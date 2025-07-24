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

def analyze_skin_tone_simple(image_array: np.ndarray) -> Dict:
    """Simplified skin tone analysis."""
    try:
        # Get average color of the image center
        h, w = image_array.shape[:2]
        center_region = image_array[h//4:3*h//4, w//4:3*w//4]
        
        # Calculate average RGB
        avg_color = np.mean(center_region.reshape(-1, 3), axis=0)
        
        # Find closest Monk skin tone
        min_distance = float('inf')
        closest_monk = "Monk 5"  # Default
        
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
            'confidence': 0.8,
            'success': True
        }
        
    except Exception as e:
        logger.error(f"Error in skin tone analysis: {e}")
        return {
            'monk_skin_tone': 'Monk05',
            'monk_tone_display': 'Monk 5',
            'monk_hex': MONK_SKIN_TONES['Monk 5'],
            'derived_hex_code': '#d7bd96',
            'dominant_rgb': [215, 189, 150],
            'confidence': 0.5,
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
        
        # Analyze skin tone
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
