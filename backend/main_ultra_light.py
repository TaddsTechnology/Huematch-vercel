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

# Configure CORS - Proper frontend access configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173", 
        "https://huematch-vercel.vercel.app",  # Your exact Vercel frontend
        "https://app.taddstechnology.com",
        "https://ai-fashion-backend-d9nj.onrender.com",
        "http://localhost:8000",
        "https://localhost:8000"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "accept",
        "accept-language", 
        "content-language",
        "content-type",
        "authorization",
        "x-requested-with",
        "cache-control",
        "pragma",
        "origin",
        "user-agent",
        "dnt",
        "sec-fetch-mode",
        "sec-fetch-site",
        "sec-fetch-dest"
    ],
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
        "endpoints": ["/health", "/api/color-recommendations", "/api/color-palettes-db", "/data/", "/apparel", "/analyze-skin-tone"]
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

@app.get("/api/color-palettes-db")
def get_color_palettes_db(
    skin_tone: str = Query(None, description="Skin tone filter (e.g., Light Spring, Monk05)"),
    limit: int = Query(100, ge=10, le=500),
    category: str = Query(None, description="Category filter (recommended/avoid)"),
    color_family: str = Query(None, description="Color family filter")
):
    """Enhanced color palettes from database matching frontend expectations."""
    try:
        DATABASE_URL = os.getenv("DATABASE_URL")
        if not DATABASE_URL:
            # Fallback color palette without database
            seasonal_types = {
                'Monk01': 'Light Spring', 'Monk02': 'Light Spring', 'Monk03': 'Clear Spring',
                'Monk04': 'Warm Spring', 'Monk05': 'Soft Autumn', 'Monk06': 'Warm Autumn',
                'Monk07': 'Deep Autumn', 'Monk08': 'Deep Winter', 'Monk09': 'Cool Winter', 'Monk10': 'Clear Winter'
            }
            seasonal_type = seasonal_types.get(skin_tone, 'Universal')
            
            # Basic color recommendations by seasonal type
            color_recommendations = {
                'Light Spring': [
                    {'name': 'Soft Peach', 'hex': '#FFCBA4'},
                    {'name': 'Light Coral', 'hex': '#F08080'},
                    {'name': 'Powder Blue', 'hex': '#B0E0E6'},
                    {'name': 'Mint Green', 'hex': '#98FB98'},
                    {'name': 'Lavender', 'hex': '#E6E6FA'}
                ],
                'Clear Spring': [
                    {'name': 'Bright Red', 'hex': '#FF0000'},
                    {'name': 'Electric Blue', 'hex': '#0080FF'},
                    {'name': 'Emerald Green', 'hex': '#50C878'},
                    {'name': 'Hot Pink', 'hex': '#FF69B4'},
                    {'name': 'Bright Yellow', 'hex': '#FFFF00'}
                ],
                'Warm Spring': [
                    {'name': 'Warm Coral', 'hex': '#FF7F50'},
                    {'name': 'Golden Yellow', 'hex': '#FFD700'},
                    {'name': 'Warm Brown', 'hex': '#D2691E'},
                    {'name': 'Peach', 'hex': '#FFCBA4'},
                    {'name': 'Warm Green', 'hex': '#9ACD32'}
                ],
                'Soft Autumn': [
                    {'name': 'Muted Gold', 'hex': '#CFB53B'},
                    {'name': 'Sage Green', 'hex': '#87A96B'},
                    {'name': 'Warm Taupe', 'hex': '#8B7765'},
                    {'name': 'Dusty Rose', 'hex': '#C08081'},
                    {'name': 'Camel', 'hex': '#C19A6B'}
                ],
                'Universal': [
                    {'name': 'Navy Blue', 'hex': '#000080'},
                    {'name': 'Forest Green', 'hex': '#228B22'},
                    {'name': 'Burgundy', 'hex': '#800020'},
                    {'name': 'Charcoal', 'hex': '#36454F'},
                    {'name': 'Cream', 'hex': '#F5F5DC'}
                ]
            }
            
            colors = color_recommendations.get(seasonal_type, color_recommendations['Universal'])
            return {
                'colors_that_suit': colors,
                'colors': colors,
                'colors_to_avoid': [],
                'seasonal_type': seasonal_type,
                'monk_skin_tone': skin_tone,
                'description': f'Color recommendations for {seasonal_type} seasonal type',
                'message': f'Found {len(colors)} color recommendations (fallback mode)',
                'database_source': False
            }
        
        # Database query
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        try:
            cursor = db.connection().connection.cursor()
            
            # Build the query based on parameters
            query = """
                SELECT DISTINCT hex_code, color_name, category, color_family,
                       seasonal_palette, suitable_skin_tone
                FROM comprehensive_colors 
                WHERE hex_code IS NOT NULL 
                AND color_name IS NOT NULL
            """
            
            params = []
            
            if skin_tone:
                # Handle both seasonal types and Monk tones
                if 'Monk' in skin_tone:
                    query += " AND monk_tones::text LIKE %s"
                    params.append(f'%{skin_tone}%')
                else:
                    query += " AND seasonal_palette LIKE %s"
                    params.append(f'%{skin_tone}%')
            
            if category:
                query += " AND category = %s"
                params.append(category)
                
            if color_family:
                query += " AND color_family LIKE %s"
                params.append(f'%{color_family}%')
            
            query += " ORDER BY color_name LIMIT %s"
            params.append(limit)
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            # Process results
            recommended_colors = []
            colors_to_avoid = []
            
            for row in results:
                color_data = {
                    'name': row[1],
                    'hex': row[0],
                    'color_family': row[3] or 'unknown',
                    'seasonal_palette': row[4] or 'universal',
                    'source': 'database'
                }
                
                if row[2] == 'avoid':
                    colors_to_avoid.append(color_data)
                else:
                    recommended_colors.append(color_data)
            
            # Determine seasonal type
            seasonal_types = {
                'Monk01': 'Light Spring', 'Monk02': 'Light Spring', 'Monk03': 'Clear Spring',
                'Monk04': 'Warm Spring', 'Monk05': 'Soft Autumn', 'Monk06': 'Warm Autumn',
                'Monk07': 'Deep Autumn', 'Monk08': 'Deep Winter', 'Monk09': 'Cool Winter', 'Monk10': 'Clear Winter'
            }
            seasonal_type = seasonal_types.get(skin_tone, skin_tone or 'Universal')
            
            return {
                'colors_that_suit': recommended_colors,
                'colors': recommended_colors,
                'colors_to_avoid': colors_to_avoid,
                'seasonal_type': seasonal_type,
                'monk_skin_tone': skin_tone,
                'description': f'Database colors for {seasonal_type} seasonal type',
                'message': f'Found {len(recommended_colors)} recommended colors and {len(colors_to_avoid)} colors to avoid',
                'database_source': True
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Color palettes DB error: {e}")
        # Fallback response
        seasonal_types = {
            'Monk01': 'Light Spring', 'Monk02': 'Light Spring', 'Monk03': 'Clear Spring',
            'Monk04': 'Warm Spring', 'Monk05': 'Soft Autumn', 'Monk06': 'Warm Autumn',
            'Monk07': 'Deep Autumn', 'Monk08': 'Deep Winter', 'Monk09': 'Cool Winter', 'Monk10': 'Clear Winter'
        }
        seasonal_type = seasonal_types.get(skin_tone, 'Universal')
        
        fallback_colors = [
            {'name': 'Navy Blue', 'hex': '#000080', 'source': 'fallback_error'},
            {'name': 'Forest Green', 'hex': '#228B22', 'source': 'fallback_error'},
            {'name': 'Burgundy', 'hex': '#800020', 'source': 'fallback_error'}
        ]
        
        return {
            'colors_that_suit': fallback_colors,
            'colors': fallback_colors,
            'colors_to_avoid': [],
            'seasonal_type': seasonal_type,
            'monk_skin_tone': skin_tone,
            'message': 'Fallback colors due to database error',
            'error': str(e),
            'database_source': False
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

def detect_face_region(image_array: np.ndarray):
    """Simple face detection using color-based heuristics."""
    h, w = image_array.shape[:2]
    
    # Convert to YUV color space for better skin detection
    yuv = np.zeros_like(image_array)
    yuv[:,:,0] = 0.299 * image_array[:,:,0] + 0.587 * image_array[:,:,1] + 0.114 * image_array[:,:,2]  # Y
    yuv[:,:,1] = -0.14713 * image_array[:,:,0] - 0.28886 * image_array[:,:,1] + 0.436 * image_array[:,:,2]  # U
    yuv[:,:,2] = 0.615 * image_array[:,:,0] - 0.51499 * image_array[:,:,1] - 0.10001 * image_array[:,:,2]  # V
    
    # Skin detection in YUV space
    skin_mask = (
        (yuv[:,:,1] >= -15) & (yuv[:,:,1] <= 17) &
        (yuv[:,:,2] >= -10) & (yuv[:,:,2] <= 25) &
        (yuv[:,:,0] >= 50)  # Brightness threshold
    )
    
    # Find the largest contiguous skin region (simplified)
    skin_pixels = np.where(skin_mask)
    if len(skin_pixels[0]) < 100:  # Not enough skin pixels
        # Fallback to center region
        return image_array[h//3:2*h//3, w//3:2*w//3]
    
    # Get bounding box of skin region
    min_y, max_y = np.min(skin_pixels[0]), np.max(skin_pixels[0])
    min_x, max_x = np.min(skin_pixels[1]), np.max(skin_pixels[1])
    
    # Focus on upper portion (likely face)
    face_height = max_y - min_y
    face_region_end = min_y + int(face_height * 0.7)  # Top 70% of detected skin
    
    return image_array[min_y:face_region_end, min_x:max_x]

def analyze_skin_color(face_region: np.ndarray):
    """Advanced skin color analysis."""
    # Remove extreme outliers (shadows, highlights)
    face_flat = face_region.reshape(-1, 3)
    
    # Calculate percentiles to remove outliers
    p5 = np.percentile(face_flat, 5, axis=0)
    p95 = np.percentile(face_flat, 95, axis=0)
    
    # Filter pixels within reasonable range
    mask = np.all((face_flat >= p5) & (face_flat <= p95), axis=1)
    filtered_pixels = face_flat[mask]
    
    if len(filtered_pixels) < 10:
        # Fallback to simple average
        return np.mean(face_flat, axis=0)
    
    # Use median for more robust estimation
    skin_color = np.median(filtered_pixels, axis=0)
    
    # Slight adjustment for typical skin tone characteristics
    # Skin tones typically have more red/yellow than blue
    if skin_color[2] > skin_color[0]:  # If blue > red, adjust
        skin_color[2] = skin_color[2] * 0.9
        skin_color[0] = skin_color[0] * 1.05
    
    return skin_color

def enhanced_monk_matching(skin_rgb: np.ndarray):
    """Enhanced Monk skin tone matching with better algorithm."""
    # Define more accurate Monk skin tones
    monk_tones = {
        'Monk 1': {'rgb': [246, 237, 228], 'hex': '#f6ede4'},
        'Monk 2': {'rgb': [243, 231, 219], 'hex': '#f3e7db'},
        'Monk 3': {'rgb': [247, 234, 208], 'hex': '#f7ead0'},
        'Monk 4': {'rgb': [234, 207, 187], 'hex': '#eadaba'},
        'Monk 5': {'rgb': [215, 189, 150], 'hex': '#d7bd96'},
        'Monk 6': {'rgb': [160, 126, 86], 'hex': '#a07e56'},
        'Monk 7': {'rgb': [130, 92, 67], 'hex': '#825c43'},
        'Monk 8': {'rgb': [96, 65, 52], 'hex': '#604134'},
        'Monk 9': {'rgb': [58, 49, 42], 'hex': '#3a312a'},
        'Monk 10': {'rgb': [41, 36, 32], 'hex': '#292420'}
    }
    
    # Calculate brightness and undertone characteristics
    brightness = np.mean(skin_rgb)
    
    # Color analysis for undertones
    r, g, b = skin_rgb
    yellow_undertone = (r + g) / 2 - b
    red_undertone = r - (g + b) / 2
    
    logger.info(f"Skin analysis: RGB({r:.1f}, {g:.1f}, {b:.1f}), brightness={brightness:.1f}")
    
    # Pre-filter candidates based on brightness
    candidates = []
    if brightness >= 210:  # Very light
        candidates = ['Monk 1', 'Monk 2']
    elif brightness >= 180:  # Light
        candidates = ['Monk 1', 'Monk 2', 'Monk 3']
    elif brightness >= 150:  # Light-medium
        candidates = ['Monk 2', 'Monk 3', 'Monk 4']
    elif brightness >= 120:  # Medium
        candidates = ['Monk 4', 'Monk 5', 'Monk 6']
    elif brightness >= 90:   # Medium-dark
        candidates = ['Monk 5', 'Monk 6', 'Monk 7']
    elif brightness >= 70:   # Dark
        candidates = ['Monk 6', 'Monk 7', 'Monk 8']
    elif brightness >= 50:   # Very dark
        candidates = ['Monk 7', 'Monk 8', 'Monk 9']
    else:  # Deep
        candidates = ['Monk 8', 'Monk 9', 'Monk 10']
    
    # Find best match among candidates
    best_match = None
    min_distance = float('inf')
    
    for monk_name in candidates:
        monk_rgb = np.array(monk_tones[monk_name]['rgb'])
        
        # Multi-factor distance calculation
        # 1. Euclidean distance in RGB space
        euclidean_dist = np.sqrt(np.sum((skin_rgb - monk_rgb) ** 2))
        
        # 2. Brightness difference (weighted more heavily)
        monk_brightness = np.mean(monk_rgb)
        brightness_diff = abs(brightness - monk_brightness)
        
        # 3. Undertone similarity
        monk_yellow = (monk_rgb[0] + monk_rgb[1]) / 2 - monk_rgb[2]
        monk_red = monk_rgb[0] - (monk_rgb[1] + monk_rgb[2]) / 2
        
        undertone_diff = abs(yellow_undertone - monk_yellow) + abs(red_undertone - monk_red)
        
        # Weighted combination
        if brightness >= 180:  # Light skin - prioritize brightness
            distance = euclidean_dist * 0.3 + brightness_diff * 2.5 + undertone_diff * 0.5
        elif brightness >= 120:  # Medium skin - balanced
            distance = euclidean_dist * 0.5 + brightness_diff * 2.0 + undertone_diff * 0.8
        else:  # Dark skin - prioritize overall color matching
            distance = euclidean_dist * 0.7 + brightness_diff * 1.5 + undertone_diff * 1.0
        
        logger.info(f"{monk_name}: distance={distance:.2f} (euclidean={euclidean_dist:.1f}, brightness_diff={brightness_diff:.1f})")
        
        if distance < min_distance:
            min_distance = distance
            best_match = monk_name
    
    if not best_match:
        best_match = 'Monk 5'  # Safe fallback
    
    # Calculate confidence based on how close the match is
    confidence = max(0.4, 1.0 - (min_distance / 200))  # Scale distance to confidence
    confidence = min(confidence, 0.95)  # Cap at 95%
    
    return best_match, confidence, monk_tones[best_match]['hex']

def improved_skin_analysis(image_array: np.ndarray) -> Dict:
    """Improved skin tone analysis with better face detection and color analysis."""
    try:
        logger.info(f"Starting improved skin analysis on image shape: {image_array.shape}")
        
        # Step 1: Detect face/skin region
        face_region = detect_face_region(image_array)
        logger.info(f"Detected face region shape: {face_region.shape}")
        
        # Step 2: Analyze skin color
        skin_color = analyze_skin_color(face_region)
        logger.info(f"Analyzed skin color: RGB({skin_color[0]:.1f}, {skin_color[1]:.1f}, {skin_color[2]:.1f})")
        
        # Step 3: Match to Monk skin tone
        closest_monk, confidence, monk_hex = enhanced_monk_matching(skin_color)
        
        # Step 4: Generate derived hex from actual skin color
        derived_hex = rgb_to_hex(tuple(skin_color.astype(int)))
        
        # Format response
        monk_number = closest_monk.split()[1]
        monk_id = f"Monk{monk_number.zfill(2)}"
        
        logger.info(f"Final result: {monk_id} ({closest_monk}) with confidence {confidence:.2f}")
        
        return {
            'monk_skin_tone': monk_id,
            'monk_tone_display': closest_monk,
            'monk_hex': monk_hex,
            'derived_hex_code': derived_hex,
            'dominant_rgb': skin_color.astype(int).tolist(),
            'confidence': round(confidence, 2),
            'success': True,
            'method': 'improved_lightweight_analysis'
        }
        
    except Exception as e:
        logger.error(f"Improved skin analysis error: {e}")
        return {
            'monk_skin_tone': 'Monk05',
            'monk_tone_display': 'Monk 5',
            'monk_hex': '#d7bd96',
            'derived_hex_code': '#d7bd96',
            'dominant_rgb': [215, 189, 150],
            'confidence': 0.5,
            'success': False,
            'error': str(e),
            'method': 'fallback'
        }

@app.post("/analyze-skin-tone")
async def analyze_skin_tone(file: UploadFile = File(...)):
    """Improved lightweight skin tone analysis with better accuracy."""
    try:
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        logger.info(f"Processing skin tone analysis for file: {file.filename}")
        
        # Read image
        image_data = await file.read()
        image = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize image if too large (memory optimization)
        max_dimension = 1024
        if max(image.size) > max_dimension:
            ratio = max_dimension / max(image.size)
            new_size = tuple(int(dim * ratio) for dim in image.size)
            image = image.resize(new_size, Image.Resampling.LANCZOS)
            logger.info(f"Resized image to {new_size} for processing")
        
        # Convert to numpy array
        image_array = np.array(image)
        
        # Use improved analysis
        result = improved_skin_analysis(image_array)
        logger.info(f"Analysis complete: {result['monk_skin_tone']} with confidence {result['confidence']}")
        
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
            'error': str(e),
            'method': 'fallback_error'
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
