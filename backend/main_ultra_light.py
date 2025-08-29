"""
Ultra-lightweight FastAPI app for 512MB Render free tier
Removed: TensorFlow, OpenCV, pandas, scikit-learn, etc.
"""
from fastapi import FastAPI, Query, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import json
import math
import os
from typing import List, Optional, Dict
import numpy as np
from webcolors import hex_to_rgb, rgb_to_hex
import io
from PIL import Image
import logging
import random
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI Fashion API - Lightweight",
    version="1.0.0",
    description="Lightweight AI Fashion API for 512MB deployment"
)

# Configure CORS - Add your Vercel frontend URL here
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173", 
        "https://*.vercel.app",  # Your Vercel frontend
        "*"  # For testing - remove in production
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    max_age=3600
)

# Fallback Monk skin tones (no database dependency for startup)
FALLBACK_MONK_TONES = {
    'Monk 1': '#f6ede4',
    'Monk 2': '#f3e7db',
    'Monk 3': '#f7ead0',
    'Monk 4': '#eee0c8',
    'Monk 5': '#d7bd96',
    'Monk 6': '#c99961',
    'Monk 7': '#b08442',
    'Monk 8': '#8b6914',
    'Monk 9': '#5d4013',
    'Monk 10': '#292420'
}

def get_monk_skin_tones():
    """Get Monk skin tones - try database first, fallback to hardcoded."""
    try:
        DATABASE_URL = os.getenv("DATABASE_URL")
        if not DATABASE_URL:
            return FALLBACK_MONK_TONES
            
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        try:
            cursor = db.connection().connection.cursor()
            cursor.execute("SELECT monk_tone, hex_code FROM skin_tone_mappings ORDER BY monk_tone")
            mappings = cursor.fetchall()
            
            monk_tones = {}
            for row in mappings:
                display_name = row[0].replace('Monk0', 'Monk ').replace('Monk10', 'Monk 10')
                monk_tones[display_name] = row[1]
                
            return monk_tones if monk_tones else FALLBACK_MONK_TONES
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Database unavailable, using fallback: {e}")
        return FALLBACK_MONK_TONES

# Initialize monk tones
MONK_SKIN_TONES = get_monk_skin_tones()

@app.get("/")
def home():
    return {
        "message": "AI Fashion API - Ultra Light Version", 
        "status": "healthy",
        "memory_optimized": True,
        "endpoints": ["/health", "/api/color-recommendations", "/data/", "/apparel", "/analyze-skin-tone"]
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "Lightweight API running", "memory": "512MB optimized"}

@app.get("/api/color-recommendations")
def get_color_recommendations(
    skin_tone: str = Query(None),
    limit: int = Query(20, ge=5, le=50)  # Reduced default limit
):
    """Lightweight color recommendations."""
    try:
        DATABASE_URL = os.getenv("DATABASE_URL")
        if not DATABASE_URL:
            # Fallback colors without database
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
                "monk_skin_tone": skin_tone,
                "source": "fallback_no_db"
            }
        
        # Database query (lightweight)
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        try:
            cursor = db.connection().connection.cursor()
            
            if skin_tone:
                cursor.execute("""
                    SELECT DISTINCT hex_code, color_name, color_family 
                    FROM comprehensive_colors 
                    WHERE monk_tones::text LIKE %s
                    AND hex_code IS NOT NULL
                    AND color_name IS NOT NULL
                    ORDER BY color_name
                    LIMIT %s
                """, [f'%{skin_tone}%', limit])
            else:
                cursor.execute("""
                    SELECT DISTINCT hex_code, color_name, color_family 
                    FROM comprehensive_colors 
                    WHERE hex_code IS NOT NULL
                    AND color_name IS NOT NULL
                    ORDER BY color_name
                    LIMIT %s
                """, [limit])
            
            results = cursor.fetchall()
            colors = []
            for row in results:
                colors.append({
                    "name": row[1],
                    "hex": row[0],
                    "color_family": row[2] or "unknown",
                    "source": "database"
                })
            
            return {
                "colors": colors,
                "total_colors": len(colors),
                "monk_skin_tone": skin_tone,
                "source": "database"
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Database error: {e}")
        # Fallback colors
        fallback_colors = [
            {"name": "Navy Blue", "hex": "#000080", "source": "fallback_error"},
            {"name": "Forest Green", "hex": "#228B22", "source": "fallback_error"},
            {"name": "Burgundy", "hex": "#800020", "source": "fallback_error"}
        ]
        return {
            "colors": fallback_colors,
            "total_colors": len(fallback_colors),
            "monk_skin_tone": skin_tone,
            "error": str(e)
        }

@app.get("/data/")
def get_makeup_data(
    mst: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(12, ge=1, le=50)  # Reduced limit
):
    """Lightweight makeup products."""
    brands = ["Fenty Beauty", "MAC", "NARS", "Maybelline"]  # Reduced brands
    products = ["Foundation", "Concealer", "Lipstick", "Mascara"]
    
    sample_data = []
    for i in range(40):  # Reduced from 100
        brand = random.choice(brands)
        product_type = random.choice(products)
        price = f"${random.randint(15, 40)}.99"
        
        sample_data.append({
            "product_name": f"{brand} {product_type}",
            "brand": brand,
            "price": price,
            "image_url": f"https://via.placeholder.com/150?text={brand.replace(' ', '+')}",
            "mst": mst or f"Monk{random.randint(1, 10):02d}"
        })
    
    # Pagination
    total_items = len(sample_data)
    total_pages = math.ceil(total_items / limit)
    start_idx = (page - 1) * limit
    end_idx = min(start_idx + limit, total_items)
    
    return {
        "data": sample_data[start_idx:end_idx],
        "total_items": total_items,
        "total_pages": total_pages,
        "page": page,
        "limit": limit
    }

@app.get("/apparel")
def get_apparel(
    gender: str = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(12, ge=1, le=30)
):
    """Lightweight apparel products."""
    brands = ["H&M", "Zara", "Uniqlo"]
    types = ["T-Shirt", "Jeans", "Sweater"]
    colors = ["Black", "White", "Blue", "Gray"]
    
    sample_data = []
    for i in range(30):  # Reduced from 50
        brand = random.choice(brands)
        product_type = random.choice(types)
        base_color = random.choice(colors)
        
        sample_data.append({
            "Product Name": f"{brand} {product_type}",
            "Price": f"${random.randint(20, 60)}.99",
            "Image URL": f"https://via.placeholder.com/150?text={product_type}",
            "Product Type": product_type,
            "baseColour": base_color,
            "brand": brand,
            "gender": gender or "Unisex"
        })
    
    # Pagination
    total_items = len(sample_data)
    start_idx = (page - 1) * limit
    end_idx = min(start_idx + limit, total_items)
    
    return {
        "data": sample_data[start_idx:end_idx],
        "total_items": total_items,
        "page": page,
        "limit": limit
    }

def simple_skin_analysis(image_array: np.ndarray) -> Dict:
    """Ultra-simple skin tone analysis without OpenCV."""
    try:
        # Get center region of image
        h, w = image_array.shape[:2]
        center_region = image_array[h//4:3*h//4, w//4:3*w//4]
        
        # Calculate average color
        avg_color = np.mean(center_region.reshape(-1, 3), axis=0)
        
        # Find closest Monk tone (simple distance)
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
            'confidence': 0.75,
            'success': True,
            'method': 'ultra_light_analysis'
        }
        
    except Exception as e:
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
    """Lightweight skin tone analysis."""
    try:
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read image
        image_data = await file.read()
        image = Image.open(io.BytesIO(image_data))
        
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Convert to numpy array
        image_array = np.array(image)
        
        # Analyze (lightweight)
        result = simple_skin_analysis(image_array)
        return result
        
    except Exception as e:
        logger.error(f"Skin tone analysis error: {e}")
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
