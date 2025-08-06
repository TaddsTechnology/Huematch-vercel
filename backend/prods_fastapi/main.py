from fastapi import FastAPI, Query, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
import numpy as np
import cv2
import math
from typing import List, Optional, Dict
from PIL import Image
import io
from webcolors import hex_to_rgb, rgb_to_hex
import logging
import mediapipe as mp
# import dlib  # Removed to avoid compilation issues
# face_recognition also removed to avoid dlib compilation issues
# Using MediaPipe and OpenCV for face detection instead
from enhanced_skin_tone_analyzer import EnhancedSkinToneAnalyzer

# Import services
from services.cloudinary_service import cloudinary_service
from services.sentry_service import EnhancedSentryService
from config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize enhanced skin tone analyzer
enhanced_analyzer = EnhancedSkinToneAnalyzer()

# Initialize database on startup
try:
    from database import create_tables, init_color_palette_data
    create_tables()
    init_color_palette_data()
    logger.info("Database initialized successfully")
except Exception as e:
    logger.warning(f"Database initialization failed: {e}")

# Import color router
from color_routes import color_router

# Create FastAPI app
app = FastAPI(
    title="AI Fashion Backend",
    version="1.0.0",
    description="AI Fashion recommendation system with skin tone analysis"
)

# Add Sentry middleware for error tracking
if settings.sentry_dsn:
    app.add_middleware(SentryAsgiMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the color routers
app.include_router(color_router)

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
        image_array[h//8:h//3, w//3:2*w//3],  # Forehead
        image_array[h//3:h//2, w//4:3*w//4],  # Upper cheeks
        image_array[h//3:2*h//3, 2*w//5:3*w//5],  # Nose bridge
        image_array[h//2:2*h//3, w//4:3*w//4],  # Lower cheeks
        image_array[2*h//3:5*h//6, 2*w//5:3*w//5]  # Chin area
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
        distance_confidence = max(0, 1 - (closest_distance / 200))  # Normalize to 0-1
        gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
        sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
        sharpness_confidence = min(1.0, sharpness / 500)  # Good sharpness
        brightness_std = np.std(final_color)
        consistency_confidence = max(0, 1 - (brightness_std / 50))
        avg_brightness = np.mean(final_color)
        brightness_bonus = 0.2 if avg_brightness > 200 else 0.1 if avg_brightness > 180 else 0

        final_confidence = (
            distance_confidence * 0.4 +
            sharpness_confidence * 0.3 +
            consistency_confidence * 0.3 +
            brightness_bonus
        )

        return min(1.0, final_confidence)

    except Exception as e:
        logger.warning(f"Confidence calculation failed: {e}")
        return 0.5


def find_closest_monk_tone_enhanced(rgb_color: np.ndarray) -> tuple:
    """Enhanced Monk tone matching with better light skin detection."""
    min_distance = float('inf')
    closest_monk = "Monk 2"

    avg_brightness = np.mean(rgb_color)

    for monk_name, hex_color in MONK_SKIN_TONES.items():
        monk_rgb = np.array(hex_to_rgb(hex_color))
        euclidean_distance = np.sqrt(np.sum((rgb_color - monk_rgb) ** 2))
        brightness_diff = abs(avg_brightness - np.mean(monk_rgb))

        if avg_brightness > 220:
            combined_distance = euclidean_distance * 0.3 + brightness_diff * 1.5
        elif avg_brightness > 180:
            combined_distance = euclidean_distance * 0.6 + brightness_diff * 1.0
        else:
            combined_distance = euclidean_distance

        if combined_distance < min_distance:
            min_distance = combined_distance
            closest_monk = monk_name

    return closest_monk, min_distance


# Old dlib-based function removed - now using enhanced_analyzer


@app.get("/")
def home():
    return {"message": "Welcome to the AI Fashion API!", "status": "healthy"}


@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "AI Fashion Backend is running"}


@app.get("/makeup-types")
def get_makeup_types():
    """Get available makeup types."""
    return {
        "types": ["Foundation", "Concealer", "Lipstick", "Mascara", "Blush", "Highlighter", "Eyeshadow"]
    }


@app.get("/products")
def get_products(product_type: str = Query(None), random: bool = Query(False)):
    """Get H&M style products."""
    return []


@app.get("/color-recommendations")
def get_color_recommendations(skin_tone: str = Query(None)):
    """Get color recommendations for skin tone based on database."""
    try:
        from database import SessionLocal, SkinToneMapping, ColorPalette
        
        if not skin_tone:
            # Return default recommendations if no skin tone provided
            return [
                {"hex_code": "#8B4513", "color_name": "Saddle Brown", "category": "recommended"},
                {"hex_code": "#A0522D", "color_name": "Sienna", "category": "recommended"},
                {"hex_code": "#CD853F", "color_name": "Peru", "category": "recommended"},
                {"hex_code": "#DEB887", "color_name": "Burlywood", "category": "recommended"},
                {"hex_code": "#D2691E", "color_name": "Chocolate", "category": "recommended"}
            ]
        
        db = SessionLocal()
        try:
            # First, try to find the seasonal type from monk tone mapping
            seasonal_type = None
            
            # Check if skin_tone is a monk tone (like "Monk 5" or "Monk05")
            if "monk" in skin_tone.lower():
                # Normalize monk tone format
                monk_number = ''.join(filter(str.isdigit, skin_tone))
                if monk_number:
                    monk_tone_formatted = f"Monk{monk_number.zfill(2)}"
                    
                    # Look up seasonal type for this monk tone
                    mapping = db.query(SkinToneMapping).filter(
                        SkinToneMapping.monk_tone == monk_tone_formatted
                    ).first()
                    
                    if mapping:
                        seasonal_type = mapping.seasonal_type
            else:
                # If not a monk tone, assume it's already a seasonal type
                seasonal_type = skin_tone
            
            if not seasonal_type:
                logger.warning(f"Could not find seasonal type for skin tone: {skin_tone}")
                # Return default recommendations
                return [
                    {"hex_code": "#8B4513", "color_name": "Saddle Brown", "category": "recommended"},
                    {"hex_code": "#A0522D", "color_name": "Sienna", "category": "recommended"},
                    {"hex_code": "#CD853F", "color_name": "Peru", "category": "recommended"}
                ]
            
            # Get color palette for this seasonal type
            palette = db.query(ColorPalette).filter(
                ColorPalette.skin_tone == seasonal_type
            ).first()
            
            if not palette:
                logger.warning(f"No color palette found for seasonal type: {seasonal_type}")
                # Return default recommendations
                return [
                    {"hex_code": "#8B4513", "color_name": "Saddle Brown", "category": "recommended"},
                    {"hex_code": "#A0522D", "color_name": "Sienna", "category": "recommended"}
                ]
            
            # Format the flattering colors for response
            recommendations = []
            if palette.flattering_colors:
                for color in palette.flattering_colors:
                    recommendations.append({
                        "hex_code": color.get("hex", ""),
                        "color_name": color.get("name", ""),
                        "category": "recommended"
                    })
            
            logger.info(f"Found {len(recommendations)} color recommendations for skin tone: {skin_tone} (seasonal type: {seasonal_type})")
            return recommendations
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error getting color recommendations: {e}")
        # Return fallback recommendations
        return [
            {"hex_code": "#8B4513", "color_name": "Saddle Brown", "category": "recommended"},
            {"hex_code": "#A0522D", "color_name": "Sienna", "category": "recommended"},
            {"hex_code": "#CD853F", "color_name": "Peru", "category": "recommended"}
        ]


@app.get("/api/color-recommendations")
def get_api_color_recommendations(
    skin_tone: str = Query(None),
    hex_color: str = Query(None),
    limit: int = Query(50, ge=10, le=100, description="Maximum number of colors to return")
):
    """Enhanced color recommendations combining multiple database tables - based on main_simple.py."""
    logger.info(f"Color recommendations request: skin_tone={skin_tone}, hex_color={hex_color}")
    
    try:
        # Database connection - use environment variable or fallback to known URL
        import os
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import sessionmaker
        import json
        
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
                
                # Step 1: Get seasonal type mapping
                cursor.execute("""
                    SELECT seasonal_type 
                    FROM skin_tone_mappings 
                    WHERE monk_tone = %s
                """, [skin_tone])
                
                mapping = cursor.fetchone()
                if mapping:
                    seasonal_type = mapping[0]
                    logger.info(f"Found seasonal type: {seasonal_type} for {skin_tone}")
                
                # Step 2: Get colors from color_palettes (seasonal-specific)
                if seasonal_type != "Universal":
                    cursor.execute("""
                        SELECT flattering_colors 
                        FROM color_palettes 
                        WHERE skin_tone = %s
                    """, [seasonal_type])
                    
                    palette = cursor.fetchone()
                    if palette and palette[0]:
                        flattering_colors = palette[0] if isinstance(palette[0], list) else json.loads(palette[0])
                        for color in flattering_colors:
                            all_colors.append({
                                "hex_code": color.get("hex", "#000000"),
                                "color_name": color.get("name", "Unknown Color"),
                                "category": "recommended",
                                "source": "seasonal_palette",
                                "seasonal_type": seasonal_type
                            })
                        sources_used.append(f"color_palettes ({len(flattering_colors)} colors)")
                        logger.info(f"Added {len(flattering_colors)} colors from color_palettes")
                
                # Step 3: Get colors from comprehensive_colors (Monk tone matching)
                cursor.execute("""
                    SELECT DISTINCT hex_code, color_name, color_family, brightness_level
                    FROM comprehensive_colors 
                    WHERE monk_tones::text LIKE %s
                    AND hex_code IS NOT NULL
                    AND color_name IS NOT NULL
                    ORDER BY color_name
                    LIMIT 40
                """, [f'%{skin_tone}%'])
                
                comp_results = cursor.fetchall()
                for row in comp_results:
                    # Avoid duplicates by checking hex codes
                    if not any(color["hex_code"].lower() == row[0].lower() for color in all_colors):
                        all_colors.append({
                            "hex_code": row[0],
                            "color_name": row[1],
                            "category": "recommended",
                            "source": "comprehensive_colors",
                            "color_family": row[2] or "unknown",
                            "brightness_level": row[3] or "medium",
                            "monk_compatible": skin_tone
                        })
                
                if comp_results:
                    sources_used.append(f"comprehensive_colors ({len(comp_results)} colors)")
                    logger.info(f"Added {len(comp_results)} colors from comprehensive_colors")
                
                # Step 4: Get additional colors from main colors table (seasonal matching)
                if seasonal_type != "Universal":
                    cursor.execute("""
                        SELECT DISTINCT hex_code, color_name, seasonal_palette, category, suitable_skin_tone
                        FROM colors 
                        WHERE (seasonal_palette = %s OR suitable_skin_tone LIKE %s)
                        AND category = 'recommended'
                        AND hex_code IS NOT NULL
                        AND color_name IS NOT NULL
                        ORDER BY color_name
                        LIMIT 30
                    """, [seasonal_type, f'%{skin_tone}%'])
                    
                    colors_results = cursor.fetchall()
                    for row in colors_results:
                        # Avoid duplicates
                        if not any(color["hex_code"].lower() == row[0].lower() for color in all_colors):
                            all_colors.append({
                                "hex_code": row[0],
                                "color_name": row[1],
                                "category": row[3],
                                "source": "colors_table",
                                "seasonal_palette": row[2] or seasonal_type,
                                "suitable_skin_tone": row[4] or "universal"
                            })
                    
                    if colors_results:
                        sources_used.append(f"colors table ({len(colors_results)} colors)")
                        logger.info(f"Added {len(colors_results)} colors from colors table")
            
            # Default/Universal colors if no skin tone provided or limited results
            if len(all_colors) < 10:
                default_query = text("""
                    SELECT DISTINCT hex_code, color_name, color_family, brightness_level
                    FROM comprehensive_colors 
                    WHERE color_family IN ('blue', 'green', 'red', 'purple', 'neutral', 'brown', 'pink')
                    AND brightness_level IN ('medium', 'dark', 'light')
                    AND hex_code IS NOT NULL
                    AND color_name IS NOT NULL
                    ORDER BY color_name
                    LIMIT 25
                """)
                
                default_result = db.execute(default_query)
                default_colors = default_result.fetchall()
                
                for row in default_colors:
                    # Avoid duplicates
                    if not any(color["hex_code"].lower() == row[0].lower() for color in all_colors):
                        all_colors.append({
                            "hex_code": row[0],
                            "color_name": row[1],
                            "category": "recommended",
                            "source": "universal_colors",
                            "color_family": row[2] or "unknown",
                            "brightness_level": row[3] or "medium"
                        })
                
                if default_colors:
                    sources_used.append(f"universal_colors ({len(default_colors)} colors)")
                    logger.info(f"Added {len(default_colors)} universal colors")
            
            # Apply the limit while preserving diversity
            if len(all_colors) > limit:
                # Prioritize colors from seasonal palettes and comprehensive colors
                priority_colors = [c for c in all_colors if c["source"] in ["seasonal_palette", "comprehensive_colors"]]
                other_colors = [c for c in all_colors if c["source"] not in ["seasonal_palette", "comprehensive_colors"]]
                
                # Take priority colors first, then fill with others
                final_colors = priority_colors[:limit]
                remaining_slots = limit - len(final_colors)
                if remaining_slots > 0:
                    final_colors.extend(other_colors[:remaining_slots])
            else:
                final_colors = all_colors
            
            logger.info(f"Returning {len(final_colors)} colors from {len(sources_used)} sources")
            
            # Format the response to match frontend expectations
            formatted_response = {
                "colors_that_suit": [
                    {
                        "name": color.get("color_name", "Unknown Color"),
                        "hex": color.get("hex_code", "#000000")
                    } for color in final_colors
                ],
                "seasonal_type": seasonal_type,
                "monk_skin_tone": skin_tone,
                "message": f"Enhanced color recommendations for {skin_tone or 'universal skin tone'} from multiple database sources"
            }
            
            return formatted_response
            
        finally:
            db.close()
        
    except Exception as e:
        logger.error(f"Database error in color recommendations: {e}")
        # Comprehensive fallback colors
        fallback_colors = [
            {"hex_code": "#000080", "color_name": "Navy Blue", "category": "recommended"},
            {"hex_code": "#228B22", "color_name": "Forest Green", "category": "recommended"},
            {"hex_code": "#800020", "color_name": "Burgundy", "category": "recommended"},
            {"hex_code": "#36454F", "color_name": "Charcoal Gray", "category": "recommended"},
            {"hex_code": "#F5F5DC", "color_name": "Cream White", "category": "recommended"},
            {"hex_code": "#FFB6C1", "color_name": "Soft Pink", "category": "recommended"},
            {"hex_code": "#663399", "color_name": "Royal Purple", "category": "recommended"},
            {"hex_code": "#50C878", "color_name": "Emerald Green", "category": "recommended"},
            {"hex_code": "#FF6600", "color_name": "Deep Orange", "category": "recommended"},
            {"hex_code": "#8B4513", "color_name": "Chocolate Brown", "category": "recommended"}
        ]
        
        # Format fallback response to match frontend expectations
        fallback_response = {
            "colors_that_suit": [
                {
                    "name": color.get("color_name", "Unknown Color"),
                    "hex": color.get("hex_code", "#000000")
                } for color in (fallback_colors[:limit] if len(fallback_colors) > limit else fallback_colors)
            ],
            "seasonal_type": "Universal",
            "monk_skin_tone": skin_tone,
            "message": f"Fallback color recommendations due to database error"
        }
        
        return fallback_response


@app.get("/api/color-palettes-db")
def get_color_palettes_db(
    hex_color: str = Query(None),
    skin_tone: str = Query(None)
):
    """Get color palettes from database for specific skin tone - with fallback."""
    logger.info(f"Color palette request: skin_tone={skin_tone}, hex_color={hex_color}")
    
    # Default fallback palettes
    default_colors = [
        {"hex": "#F4A460", "name": "Sandy Brown"},
        {"hex": "#DDA0DD", "name": "Plum"},
        {"hex": "#98FB98", "name": "Pale Green"},
        {"hex": "#87CEEB", "name": "Sky Blue"},
        {"hex": "#F0E68C", "name": "Khaki"}
    ]
    
    if not skin_tone:
        return {
            "colors": default_colors,
            "seasonal_type": "Unknown",
            "description": "Default color palette - no skin tone provided"
        }
    
    try:
        # Try database approach first
        from database import SessionLocal, SkinToneMapping, ColorPalette
        
        db = SessionLocal()
        try:
            seasonal_type = None
            
            if "monk" in skin_tone.lower():
                monk_number = ''.join(filter(str.isdigit, skin_tone))
                if monk_number:
                    monk_tone_formatted = f"Monk{monk_number.zfill(2)}"
                    
                    mapping = db.query(SkinToneMapping).filter(
                        SkinToneMapping.monk_tone == monk_tone_formatted
                    ).first()
                    
                    if mapping:
                        seasonal_type = mapping.seasonal_type
            else:
                seasonal_type = skin_tone
            
            if seasonal_type:
                palette = db.query(ColorPalette).filter(
                    ColorPalette.skin_tone == seasonal_type
                ).first()
                
                if palette and palette.flattering_colors:
                    return {
                        "colors": palette.flattering_colors,
                        "colors_to_avoid": palette.colors_to_avoid or [],
                        "seasonal_type": seasonal_type,
                        "description": palette.description or f"Colors for {seasonal_type}"
                    }
        finally:
            db.close()
            
    except Exception as e:
        logger.warning(f"Database lookup failed: {e}")
    
    # Fallback response with appropriate colors based on skin tone
    return {
        "colors": default_colors,
        "colors_to_avoid": [],
        "seasonal_type": skin_tone or "Unknown",
        "description": f"Fallback color palette for {skin_tone or 'unknown skin tone'} - database not available"
    }


@app.post("/analyze-skin-tone")
async def analyze_skin_tone(file: UploadFile = File(...)):
    """Analyze skin tone from uploaded image."""
    try:
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")

        image_data = await file.read()
        image = Image.open(io.BytesIO(image_data))

        if image.mode != 'RGB':
            image = image.convert('RGB')

        image_array = np.array(image)
        
        # Store image in Cloudinary for ML dataset and user history
        upload_result = None
        try:
            import uuid
            unique_id = str(uuid.uuid4())[:8]
            public_id = f"skin_analysis/{unique_id}_{file.filename.replace(' ', '_') if file.filename else 'upload'}"
            upload_result = cloudinary_service.upload_image(image_data, public_id)
            logger.info(f"Image stored in Cloudinary: {upload_result.get('public_id') if upload_result else 'Failed'}")
        except Exception as e:
            logger.warning(f"Failed to store image in Cloudinary: {e}")

        try:
            result = enhanced_analyzer.analyze_skin_tone(image_array, MONK_SKIN_TONES)
            if result['success']:
                # Add Cloudinary URL to response if upload was successful
                if upload_result and upload_result.get('success'):
                    result['cloudinary_url'] = upload_result.get('url')
                    result['image_public_id'] = upload_result.get('public_id')
                return result
        except Exception as e:
            logger.warning(f"Enhanced analysis failed: {e}, falling back to simple analysis")
            
        # Fallback
        return {
            'monk_skin_tone': 'Monk02',
            'monk_tone_display': 'Monk 2',
            'monk_hex': MONK_SKIN_TONES['Monk 2'],
            'derived_hex_code': '#f3e7db',
            'dominant_rgb': [243, 231, 219],
            'confidence': 0.3,
            'success': False,
            'error': 'Fallback to default'
        }

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


if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
