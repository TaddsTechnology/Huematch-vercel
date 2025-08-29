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
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI Fashion API",
    version="1.0.0",
    description="AI Fashion recommendation system deployed on Vercel"
)

# Configure CORS for Vercel deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # More permissive for Vercel
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    max_age=3600
)

# Monk skin tone scale - now loaded from database
def get_monk_skin_tones():
    """Get Monk skin tones from database."""
    try:
        # Database connection 
        DATABASE_URL = os.getenv(
            "DATABASE_URL", 
            "postgresql://fashion_jvy9_user:0d2Nn5mvyw6KMBDT21l9olpHaxrTPEzh@dpg-d1vhvpbuibrs739dkn3g-a.oregon-postgres.render.com/fashion_jvy9"
        )
        
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        try:
            cursor = db.connection().connection.cursor()
            cursor.execute("SELECT monk_tone, hex_code FROM skin_tone_mappings ORDER BY monk_tone")
            mappings = cursor.fetchall()
            
            monk_tones = {}
            for row in mappings:
                # Convert Monk01 -> Monk 1 format
                display_name = row[0].replace('Monk0', 'Monk ').replace('Monk10', 'Monk 10')
                monk_tones[display_name] = row[1]
                
            if monk_tones:
                return monk_tones
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Failed to load Monk skin tones from database: {e}")
    
    # Emergency fallback - minimal set
    return {
        'Monk 1': '#f6ede4',
        'Monk 5': '#d7bd96', 
        'Monk 10': '#292420'
    }

# Initialize monk tones on startup
MONK_SKIN_TONES = get_monk_skin_tones()

@app.get("/")
def home():
    return {
        "message": "AI Fashion API running on Vercel", 
        "status": "healthy",
        "platform": "vercel",
        "endpoints": [
            "/health",
            "/api/color-recommendations",
            "/data/",
            "/apparel",
            "/analyze-skin-tone"
        ]
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "AI Fashion API is running on Vercel"}

@app.get("/api/color-recommendations")
def get_color_recommendations(
    skin_tone: str = Query(None),
    hex_color: str = Query(None),
    limit: int = Query(50, ge=10, le=100, description="Maximum number of colors to return")
):
    """Get color recommendations based on skin tone."""
    try:
        # Database connection
        DATABASE_URL = os.getenv(
            "DATABASE_URL", 
            "postgresql://fashion_jvy9_user:0d2Nn5mvyw6KMBDT21l9olpHaxrTPEzh@dpg-d1vhvpbuibrs739dkn3g-a.oregon-postgres.render.com/fashion_jvy9"
        )
        
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        try:
            all_colors = []
            seasonal_type = "Universal"
            sources_used = []
            
            if skin_tone:
                cursor = db.connection().connection.cursor()
                
                # Get colors from comprehensive_colors table
                cursor.execute("""
                    SELECT DISTINCT hex_code, color_name, color_family, brightness_level
                    FROM comprehensive_colors 
                    WHERE monk_tones::text LIKE %s
                    AND hex_code IS NOT NULL
                    AND color_name IS NOT NULL
                    ORDER BY color_name
                    LIMIT %s
                """, [f'%{skin_tone}%', limit])
                
                results = cursor.fetchall()
                for row in results:
                    all_colors.append({
                        "name": row[1],
                        "hex": row[0],
                        "source": "comprehensive_colors",
                        "color_family": row[2] or "unknown",
                        "brightness_level": row[3] or "medium"
                    })
                
                if results:
                    sources_used.append(f"comprehensive_colors ({len(results)} colors)")
            
            # Fallback colors if no results
            if not all_colors:
                all_colors = [
                    {"name": "Navy Blue", "hex": "#000080", "source": "fallback"},
                    {"name": "Forest Green", "hex": "#228B22", "source": "fallback"},
                    {"name": "Burgundy", "hex": "#800020", "source": "fallback"},
                    {"name": "Charcoal Gray", "hex": "#36454F", "source": "fallback"},
                    {"name": "Cream White", "hex": "#F5F5DC", "source": "fallback"}
                ]
                sources_used.append("hardcoded_fallback")
            
            return {
                "colors": all_colors[:limit],
                "total_colors": len(all_colors[:limit]),
                "seasonal_type": seasonal_type,
                "monk_skin_tone": skin_tone,
                "sources_used": sources_used
            }
            
        finally:
            db.close()
        
    except Exception as e:
        logger.error(f"Error in color recommendations: {e}")
        # Fallback response
        fallback_colors = [
            {"name": "Navy Blue", "hex": "#000080", "source": "fallback"},
            {"name": "Forest Green", "hex": "#228B22", "source": "fallback"},
            {"name": "Burgundy", "hex": "#800020", "source": "fallback"},
            {"name": "Charcoal Gray", "hex": "#36454F", "source": "fallback"},
            {"name": "Cream White", "hex": "#F5F5DC", "source": "fallback"}
        ]
        
        return {
            "colors": fallback_colors,
            "total_colors": len(fallback_colors),
            "seasonal_type": "Universal",
            "monk_skin_tone": skin_tone,
            "sources_used": ["hardcoded_fallback_error"],
            "error": str(e)
        }

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

# Simple skin tone analysis function
def analyze_skin_tone_simple(image_array: np.ndarray) -> Dict:
    """Simple skin tone analysis for Vercel deployment."""
    try:
        # Get average color of the image center
        h, w = image_array.shape[:2]
        center_region = image_array[h//4:3*h//4, w//4:3*w//4]
        
        # Calculate average RGB
        avg_color = np.mean(center_region.reshape(-1, 3), axis=0)
        
        # Find closest Monk skin tone
        min_distance = float('inf')
        closest_monk = "Monk 2"
        
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
            'success': True,
            'analysis_method': 'simple_rgb_vercel'
        }
        
    except Exception as e:
        logger.error(f"Error in simple skin tone analysis: {e}")
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

# Export for Vercel
handler = app
