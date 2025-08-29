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
        "endpoints": ["/health", "/api/color-recommendations", "/api/color-palettes-db", "/color-suggestions", "/data/", "/apparel", "/analyze-skin-tone"]
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
                'Monk07': 'Deep Autumn', 'Monk08': 'Deep Winter', 'Monk09': 'Cool Winter', 'Monk10': 'Clear Winter',
                'Light Spring': 'Light Spring', 'Light Summer': 'Light Summer', 'Clear Spring': 'Clear Spring',
                'Warm Spring': 'Warm Spring', 'Soft Autumn': 'Soft Autumn', 'Warm Autumn': 'Warm Autumn',
                'Deep Autumn': 'Deep Autumn', 'Deep Winter': 'Deep Winter', 'Cool Winter': 'Cool Winter', 'Clear Winter': 'Clear Winter'
            }
            seasonal_type = seasonal_types.get(skin_tone, 'Universal')
            
            # Comprehensive color recommendations by seasonal type
            color_recommendations = {
                'Light Summer': [
                    {'name': 'Powder Blue', 'hex': '#B0E0E6'},
                    {'name': 'Soft Pink', 'hex': '#F8BBD9'},
                    {'name': 'Lavender', 'hex': '#E6E6FA'},
                    {'name': 'Light Gray', 'hex': '#D3D3D3'},
                    {'name': 'Dusty Rose', 'hex': '#DCAE96'}
                ],
                'Light Spring': [
                    {'name': 'Peach', 'hex': '#FFCBA4'},
                    {'name': 'Light Coral', 'hex': '#F08080'},
                    {'name': 'Warm White', 'hex': '#FDF6E3'},
                    {'name': 'Soft Gold', 'hex': '#FFD700'},
                    {'name': 'Light Turquoise', 'hex': '#AFEEEE'}
                ],
                'Clear Spring': [
                    {'name': 'Bright Yellow', 'hex': '#FFFF00'},
                    {'name': 'True Red', 'hex': '#FF0000'},
                    {'name': 'Royal Blue', 'hex': '#4169E1'},
                    {'name': 'Emerald Green', 'hex': '#50C878'},
                    {'name': 'Hot Pink', 'hex': '#FF69B4'}
                ],
                'Warm Spring': [
                    {'name': 'Golden Yellow', 'hex': '#FFD700'},
                    {'name': 'Coral', 'hex': '#FF7F50'},
                    {'name': 'Warm Orange', 'hex': '#FF8C00'},
                    {'name': 'Peach', 'hex': '#FFCBA4'},
                    {'name': 'Light Brown', 'hex': '#DEB887'}
                ],
                'Soft Autumn': [
                    {'name': 'Warm Beige', 'hex': '#F5DEB3'},
                    {'name': 'Soft Brown', 'hex': '#A0522D'},
                    {'name': 'Muted Green', 'hex': '#6B8E23'},
                    {'name': 'Dusty Rose', 'hex': '#DCAE96'},
                    {'name': 'Soft Gold', 'hex': '#DAA520'}
                ],
                'Warm Autumn': [
                    {'name': 'Burnt Orange', 'hex': '#CC5500'},
                    {'name': 'Deep Gold', 'hex': '#B8860B'},
                    {'name': 'Rust Red', 'hex': '#B7410E'},
                    {'name': 'Forest Green', 'hex': '#228B22'},
                    {'name': 'Chocolate Brown', 'hex': '#7B3F00'}
                ],
                'Deep Autumn': [
                    {'name': 'Deep Brown', 'hex': '#654321'},
                    {'name': 'Forest Green', 'hex': '#013220'},
                    {'name': 'Burgundy', 'hex': '#800020'},
                    {'name': 'Navy Blue', 'hex': '#000080'},
                    {'name': 'Deep Gold', 'hex': '#B8860B'}
                ],
                'Deep Winter': [
                    {'name': 'Pure White', 'hex': '#FFFFFF'},
                    {'name': 'True Black', 'hex': '#000000'},
                    {'name': 'Royal Blue', 'hex': '#4169E1'},
                    {'name': 'Emerald Green', 'hex': '#50C878'},
                    {'name': 'Ruby Red', 'hex': '#E0115F'}
                ],
                'Cool Winter': [
                    {'name': 'Icy Blue', 'hex': '#B0E0E6'},
                    {'name': 'Pure White', 'hex': '#FFFFFF'},
                    {'name': 'True Black', 'hex': '#000000'},
                    {'name': 'Magenta', 'hex': '#FF00FF'},
                    {'name': 'Cool Pink', 'hex': '#FF1493'}
                ],
                'Clear Winter': [
                    {'name': 'Pure Black', 'hex': '#000000'},
                    {'name': 'Pure White', 'hex': '#FFFFFF'},
                    {'name': 'True Red', 'hex': '#FF0000'},
                    {'name': 'Royal Blue', 'hex': '#4169E1'},
                    {'name': 'Emerald Green', 'hex': '#50C878'}
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
                'colors_to_avoid': [
                    {'name': 'Pure Black', 'hex': '#000000'},
                    {'name': 'Bright Orange', 'hex': '#FF8C00'}
                ],
                'seasonal_type': seasonal_type,
                'monk_skin_tone': skin_tone,
                'description': f'Color recommendations for {seasonal_type} seasonal type',
                'message': f'Found {len(colors)} color recommendations (fallback mode)',
                'database_source': False,
                'success': True
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
                hex_code, color_name, category, color_family, seasonal_palette, suitable_skin_tone = row
                color_data = {
                    'name': color_name,
                    'hex': hex_code,
                    'color_family': color_family or 'unknown',
                    'seasonal_palette': seasonal_palette,
                    'suitable_skin_tone': suitable_skin_tone,
                    'source': 'database'
                }
                
                if category == 'recommended' or category != 'avoid':
                    recommended_colors.append(color_data)
                else:
                    colors_to_avoid.append(color_data)
            
            # Determine seasonal type from data or parameter
            if results:
                seasonal_type = results[0][4] if results[0][4] else seasonal_types.get(skin_tone, 'Universal')
            else:
                seasonal_type = seasonal_types.get(skin_tone, 'Universal')
                
            return {
                'colors_that_suit': recommended_colors,
                'colors': recommended_colors,
                'colors_to_avoid': colors_to_avoid,
                'seasonal_type': seasonal_type,
                'monk_skin_tone': skin_tone,
                'description': f'Database color recommendations for {seasonal_type}',
                'message': f'Found {len(recommended_colors)} recommended colors from database',
                'database_source': True,
                'success': True,
                'total_colors': len(recommended_colors)
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error in color-palettes-db endpoint: {e}")
        # Emergency fallback
        emergency_colors = [
            {'name': 'Navy Blue', 'hex': '#000080', 'source': 'emergency'},
            {'name': 'Forest Green', 'hex': '#228B22', 'source': 'emergency'},
            {'name': 'Burgundy', 'hex': '#800020', 'source': 'emergency'},
            {'name': 'Soft Coral', 'hex': '#F88379', 'source': 'emergency'},
            {'name': 'Cream White', 'hex': '#F5F5DC', 'source': 'emergency'}
        ]
        
        return {
            'colors_that_suit': emergency_colors,
            'colors': emergency_colors,
            'colors_to_avoid': [],
            'seasonal_type': 'Universal',
            'monk_skin_tone': skin_tone or 'Unknown',
            'description': 'Emergency color recommendations due to system error',
            'message': f'System error occurred, showing emergency recommendations. Error: {str(e)}',
            'database_source': False,
            'success': False,
            'error': str(e)
        }

@app.get("/color-suggestions")
def get_color_suggestions(
    skin_tone: Optional[str] = Query(None, description="Seasonal type or descriptive skin tone"),
    hex_color: Optional[str] = Query(None, description="Hex color to analyze"),
    detailed: bool = Query(False, description="Return detailed analysis")
):
    """Get color suggestions based on skin tone analysis."""
    try:
        # Enhanced seasonal color recommendations
        seasonal_recommendations = {
            'Light Summer': {
                'skin_tone': 'Very light with cool undertones',
                'suitable_colors': [
                    'Powder blue enhances your cool undertones',
                    'Soft pink complements your delicate coloring',
                    'Lavender works beautifully with your light complexion',
                    'Rose quartz adds warmth without overwhelming',
                    'Cool gray provides sophisticated neutrals'
                ]
            },
            'Light Spring': {
                'skin_tone': 'Light with warm, fresh undertones', 
                'suitable_colors': [
                    'Peach complements your warm undertones perfectly',
                    'Light coral enhances your natural glow',
                    'Warm white is more flattering than cool white',
                    'Soft gold adds richness without heaviness',
                    'Light turquoise provides beautiful contrast'
                ]
            },
            'Clear Spring': {
                'skin_tone': 'Clear complexion that can handle bright colors',
                'suitable_colors': [
                    'Bright yellow showcases your clarity',
                    'True red is dramatic and flattering',
                    'Royal blue enhances your clear coloring',
                    'Emerald green is stunning on you',
                    'Hot pink adds vibrant energy'
                ]
            },
            'Warm Spring': {
                'skin_tone': 'Light to medium with golden undertones',
                'suitable_colors': [
                    'Golden yellow enhances your warm glow',
                    'Coral brings out your natural radiance',
                    'Peach is incredibly flattering',
                    'Warm orange adds vibrant energy',
                    'Light brown creates earthy sophistication'
                ]
            },
            'Soft Autumn': {
                'skin_tone': 'Medium tones with muted, warm undertones',
                'suitable_colors': [
                    'Warm beige harmonizes with your skin',
                    'Soft brown enhances your natural warmth',
                    'Muted green complements your earthiness',
                    'Dusty rose adds gentle color',
                    'Soft gold brings out your warmth'
                ]
            },
            'Warm Autumn': {
                'skin_tone': 'Rich, warm coloring with golden undertones',
                'suitable_colors': [
                    'Burnt orange celebrates your warmth',
                    'Deep gold enhances your richness',
                    'Rust red is incredibly flattering',
                    'Forest green provides earthy elegance',
                    'Chocolate brown is perfect for you'
                ]
            },
            'Deep Autumn': {
                'skin_tone': 'Deep, rich coloring with warm undertones',
                'suitable_colors': [
                    'Deep brown enhances your richness',
                    'Forest green provides stunning depth',
                    'Burgundy adds luxurious richness',
                    'Navy blue creates sophisticated looks',
                    'Deep gold brings out your warmth'
                ]
            },
            'Deep Winter': {
                'skin_tone': 'Deep coloring that can handle bold contrasts',
                'suitable_colors': [
                    'Pure white creates stunning contrast',
                    'True black is elegantly dramatic',
                    'Royal blue enhances your depth',
                    'Emerald green is magnificently bold',
                    'Ruby red adds jewel-like richness'
                ]
            },
            'Cool Winter': {
                'skin_tone': 'Cool undertones with ability to wear bold colors',
                'suitable_colors': [
                    'Icy blue enhances your cool beauty',
                    'Pure white creates perfect contrast',
                    'True black is elegantly sophisticated',
                    'Magenta brings out your intensity',
                    'Cool pink complements your undertones'
                ]
            },
            'Clear Winter': {
                'skin_tone': 'High contrast coloring that needs clear, intense colors',
                'suitable_colors': [
                    'Pure black creates dramatic elegance',
                    'Pure white provides perfect contrast',
                    'True red is boldly beautiful',
                    'Royal blue enhances your clarity',
                    'Emerald green is stunningly vibrant'
                ]
            }
        }
        
        # Map Monk tones to seasonal types
        monk_to_seasonal = {
            'Monk01': 'Light Summer', 'Monk02': 'Light Spring', 'Monk03': 'Warm Spring',
            'Monk04': 'Clear Spring', 'Monk05': 'Soft Autumn', 'Monk06': 'Warm Autumn',
            'Monk07': 'Deep Autumn', 'Monk08': 'Deep Winter', 'Monk09': 'Cool Winter', 'Monk10': 'Clear Winter'
        }
        
        seasonal_type = None
        
        # Determine seasonal type
        if skin_tone:
            # Direct match
            if skin_tone in seasonal_recommendations:
                seasonal_type = skin_tone
            # Check if it's a Monk tone
            elif skin_tone in monk_to_seasonal:
                seasonal_type = monk_to_seasonal[skin_tone]
            # Fuzzy matching
            else:
                for season in seasonal_recommendations.keys():
                    if skin_tone.lower() in season.lower() or season.lower() in skin_tone.lower():
                        seasonal_type = season
                        break
        
        # Default fallback
        if not seasonal_type:
            seasonal_type = 'Soft Autumn'
        
        # Get recommendations
        if seasonal_type in seasonal_recommendations:
            recommendations = seasonal_recommendations[seasonal_type]
            
            return {
                'data': [
                    {
                        'skin_tone': recommendations['skin_tone'],
                        'suitable_colors': '. '.join(recommendations['suitable_colors'])
                    }
                ],
                'seasonal_type': seasonal_type,
                'total_suggestions': len(recommendations['suitable_colors']),
                'success': True
            }
        
        else:
            # Universal fallback
            return {
                'data': [
                    {
                        'skin_tone': 'Universal recommendations',
                        'suitable_colors': 'Navy blue provides classic elegance. Soft coral adds warmth. Forest green offers earthy sophistication. Dusty rose brings gentle color. Warm gray creates perfect neutrals. These versatile colors work well with most skin tones.'
                    }
                ],
                'seasonal_type': 'Universal',
                'total_suggestions': 6,
                'success': True,
                'fallback': True
            }
            
    except Exception as e:
        logger.error(f"Error in color suggestions: {e}")
        
        # Emergency response
        return {
            'data': [
                {
                    'skin_tone': 'Emergency recommendations',
                    'suitable_colors': 'Navy blue, soft coral, warm gray, and dusty rose are universally flattering colors that work well with most skin tones.'
                }
            ],
            'seasonal_type': 'Universal',
            'total_suggestions': 4,
            'success': False,
            'error': str(e)
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
