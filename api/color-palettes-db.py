from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import math
import os
from typing import List, Optional, Dict, Any
import numpy as np
from webcolors import hex_to_rgb, rgb_to_hex
import logging
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import colorsys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Color Palettes DB API",
    version="1.0.0",
    description="Color palette recommendations with enhanced skin tone support"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    max_age=3600
)

# Enhanced Monk Scale colors with better representation for light skin tones
ENHANCED_MONK_SKIN_TONES = {
    'Monk01': {
        'hex': '#f6ede4',
        'name': 'Very Light',
        'undertone': 'cool',
        'seasonal_type': 'Light Summer',
        'rgb': (246, 237, 228),
        'description': 'Very fair with cool pink undertones'
    },
    'Monk02': {
        'hex': '#f3e7db', 
        'name': 'Light',
        'undertone': 'neutral_cool',
        'seasonal_type': 'Light Spring',
        'rgb': (243, 231, 219),
        'description': 'Fair with neutral to cool undertones'
    },
    'Monk03': {
        'hex': '#f7ead0',
        'name': 'Light Medium',
        'undertone': 'warm',
        'seasonal_type': 'Warm Spring',
        'rgb': (247, 234, 208),
        'description': 'Light with warm peachy undertones'
    },
    'Monk04': {
        'hex': '#eadaba',
        'name': 'Medium Light',
        'undertone': 'warm',
        'seasonal_type': 'Clear Spring',
        'rgb': (234, 218, 186),
        'description': 'Light to medium with golden undertones'
    },
    'Monk05': {
        'hex': '#d7bd96',
        'name': 'Medium',
        'undertone': 'warm',
        'seasonal_type': 'Soft Autumn',
        'rgb': (215, 189, 150),
        'description': 'Medium with neutral to warm undertones'
    },
    'Monk06': {
        'hex': '#a07e56',
        'name': 'Medium Dark',
        'undertone': 'warm',
        'seasonal_type': 'Warm Autumn',
        'rgb': (160, 126, 86),
        'description': 'Medium to deep with warm golden undertones'
    },
    'Monk07': {
        'hex': '#825c43',
        'name': 'Dark',
        'undertone': 'warm',
        'seasonal_type': 'Deep Autumn',
        'rgb': (130, 92, 67),
        'description': 'Deep with warm rich undertones'
    },
    'Monk08': {
        'hex': '#604134',
        'name': 'Dark Medium',
        'undertone': 'neutral',
        'seasonal_type': 'Deep Winter',
        'rgb': (96, 65, 52),
        'description': 'Deep with neutral to warm undertones'
    },
    'Monk09': {
        'hex': '#3a312a',
        'name': 'Very Dark',
        'undertone': 'cool',
        'seasonal_type': 'Cool Winter',
        'rgb': (58, 49, 42),
        'description': 'Deep with cool undertones'
    },
    'Monk10': {
        'hex': '#292420',
        'name': 'Deepest',
        'undertone': 'neutral',
        'seasonal_type': 'Clear Winter',
        'rgb': (41, 36, 32),
        'description': 'Very deep with neutral to cool undertones'
    }
}

# Comprehensive color palettes with better light skin tone support
COMPREHENSIVE_COLOR_PALETTES = {
    'Light Summer': {
        'recommended': [
            {'name': 'Powder Blue', 'hex': '#B0E0E6', 'category': 'pastels'},
            {'name': 'Soft Pink', 'hex': '#F8BBD9', 'category': 'pastels'},
            {'name': 'Lavender', 'hex': '#E6E6FA', 'category': 'pastels'},
            {'name': 'Mint Green', 'hex': '#F5FFFA', 'category': 'pastels'},
            {'name': 'Light Gray', 'hex': '#D3D3D3', 'category': 'neutrals'},
            {'name': 'Soft White', 'hex': '#FFFDD0', 'category': 'neutrals'},
            {'name': 'Rose Quartz', 'hex': '#F7CAC9', 'category': 'pastels'},
            {'name': 'Serenity Blue', 'hex': '#92A8D1', 'category': 'pastels'},
            {'name': 'Light Coral', 'hex': '#F08080', 'category': 'pastels'},
            {'name': 'Soft Yellow', 'hex': '#FFFFE0', 'category': 'pastels'},
            {'name': 'Dusty Rose', 'hex': '#DCAE96', 'category': 'muted'},
            {'name': 'Cool Gray', 'hex': '#8C8C8C', 'category': 'neutrals'}
        ],
        'avoid': [
            {'name': 'Pure Black', 'hex': '#000000'},
            {'name': 'Bright Orange', 'hex': '#FF8C00'},
            {'name': 'Hot Pink', 'hex': '#FF69B4'},
            {'name': 'Electric Blue', 'hex': '#0080FF'}
        ],
        'description': 'Light, soft, and muted colors with blue undertones work best for Light Summer types.'
    },
    
    'Light Spring': {
        'recommended': [
            {'name': 'Peach', 'hex': '#FFCBA4', 'category': 'warm'},
            {'name': 'Light Coral', 'hex': '#F08080', 'category': 'warm'},
            {'name': 'Warm White', 'hex': '#FDF6E3', 'category': 'neutrals'},
            {'name': 'Soft Gold', 'hex': '#FFD700', 'category': 'warm'},
            {'name': 'Light Turquoise', 'hex': '#AFEEEE', 'category': 'cool'},
            {'name': 'Warm Beige', 'hex': '#F5DEB3', 'category': 'neutrals'},
            {'name': 'Light Green', 'hex': '#90EE90', 'category': 'fresh'},
            {'name': 'Salmon Pink', 'hex': '#FA8072', 'category': 'warm'},
            {'name': 'Light Yellow', 'hex': '#FFFFE0', 'category': 'warm'},
            {'name': 'Aqua', 'hex': '#00FFFF', 'category': 'fresh'},
            {'name': 'Warm Gray', 'hex': '#A0A0A0', 'category': 'neutrals'},
            {'name': 'Ivory', 'hex': '#FFFFF0', 'category': 'neutrals'}
        ],
        'avoid': [
            {'name': 'Pure Black', 'hex': '#000000'},
            {'name': 'Navy Blue', 'hex': '#000080'},
            {'name': 'Burgundy', 'hex': '#800020'},
            {'name': 'Dark Brown', 'hex': '#654321'}
        ],
        'description': 'Clear, fresh colors with warmth complement Light Spring types beautifully.'
    },
    
    'Warm Spring': {
        'recommended': [
            {'name': 'Golden Yellow', 'hex': '#FFD700', 'category': 'warm'},
            {'name': 'Coral', 'hex': '#FF7F50', 'category': 'warm'},
            {'name': 'Warm Orange', 'hex': '#FF8C00', 'category': 'warm'},
            {'name': 'Peach', 'hex': '#FFCBA4', 'category': 'warm'},
            {'name': 'Light Brown', 'hex': '#DEB887', 'category': 'earth'},
            {'name': 'Warm Red', 'hex': '#DC143C', 'category': 'warm'},
            {'name': 'Turquoise', 'hex': '#40E0D0', 'category': 'bright'},
            {'name': 'Light Green', 'hex': '#90EE90', 'category': 'fresh'},
            {'name': 'Warm White', 'hex': '#FDF6E3', 'category': 'neutrals'},
            {'name': 'Camel', 'hex': '#C19A6B', 'category': 'earth'},
            {'name': 'Ivory', 'hex': '#FFFFF0', 'category': 'neutrals'},
            {'name': 'Light Khaki', 'hex': '#F0E68C', 'category': 'earth'}
        ],
        'avoid': [
            {'name': 'Pure Black', 'hex': '#000000'},
            {'name': 'Cool Pink', 'hex': '#FF1493'},
            {'name': 'Navy Blue', 'hex': '#000080'},
            {'name': 'Purple', 'hex': '#800080'}
        ],
        'description': 'Warm, clear colors with golden undertones enhance Warm Spring complexions.'
    },
    
    'Clear Spring': {
        'recommended': [
            {'name': 'Bright Yellow', 'hex': '#FFFF00', 'category': 'bright'},
            {'name': 'True Red', 'hex': '#FF0000', 'category': 'bright'},
            {'name': 'Royal Blue', 'hex': '#4169E1', 'category': 'bright'},
            {'name': 'Emerald Green', 'hex': '#50C878', 'category': 'bright'},
            {'name': 'Hot Pink', 'hex': '#FF69B4', 'category': 'bright'},
            {'name': 'Orange', 'hex': '#FFA500', 'category': 'bright'},
            {'name': 'Turquoise', 'hex': '#40E0D0', 'category': 'bright'},
            {'name': 'Purple', 'hex': '#800080', 'category': 'bright'},
            {'name': 'Pure White', 'hex': '#FFFFFF', 'category': 'neutrals'},
            {'name': 'Light Gray', 'hex': '#D3D3D3', 'category': 'neutrals'},
            {'name': 'Navy Blue', 'hex': '#000080', 'category': 'classic'},
            {'name': 'Black', 'hex': '#000000', 'category': 'classic'}
        ],
        'avoid': [
            {'name': 'Dusty Rose', 'hex': '#DCAE96'},
            {'name': 'Olive Green', 'hex': '#808000'},
            {'name': 'Beige', 'hex': '#F5F5DC'},
            {'name': 'Muted Colors', 'hex': '#696969'}
        ],
        'description': 'Clear, bright, and saturated colors work best for Clear Spring types.'
    },
    
    'Soft Autumn': {
        'recommended': [
            {'name': 'Warm Beige', 'hex': '#F5DEB3', 'category': 'earth'},
            {'name': 'Soft Brown', 'hex': '#A0522D', 'category': 'earth'},
            {'name': 'Muted Green', 'hex': '#6B8E23', 'category': 'earth'},
            {'name': 'Dusty Rose', 'hex': '#DCAE96', 'category': 'muted'},
            {'name': 'Soft Gold', 'hex': '#DAA520', 'category': 'warm'},
            {'name': 'Teal', 'hex': '#008080', 'category': 'jewel'},
            {'name': 'Rust', 'hex': '#B7410E', 'category': 'earth'},
            {'name': 'Sage Green', 'hex': '#9CAF88', 'category': 'earth'},
            {'name': 'Warm Gray', 'hex': '#A0A0A0', 'category': 'neutrals'},
            {'name': 'Cream', 'hex': '#FFFDD0', 'category': 'neutrals'},
            {'name': 'Camel', 'hex': '#C19A6B', 'category': 'earth'},
            {'name': 'Soft Coral', 'hex': '#F88379', 'category': 'warm'}
        ],
        'avoid': [
            {'name': 'Pure Black', 'hex': '#000000'},
            {'name': 'Pure White', 'hex': '#FFFFFF'},
            {'name': 'Bright Pink', 'hex': '#FF1493'},
            {'name': 'Electric Blue', 'hex': '#0080FF'}
        ],
        'description': 'Muted, warm colors with golden undertones complement Soft Autumn types.'
    },
    
    'Warm Autumn': {
        'recommended': [
            {'name': 'Burnt Orange', 'hex': '#CC5500', 'category': 'warm'},
            {'name': 'Deep Gold', 'hex': '#B8860B', 'category': 'warm'},
            {'name': 'Rust Red', 'hex': '#B7410E', 'category': 'earth'},
            {'name': 'Forest Green', 'hex': '#228B22', 'category': 'earth'},
            {'name': 'Chocolate Brown', 'hex': '#7B3F00', 'category': 'earth'},
            {'name': 'Warm Yellow', 'hex': '#FFBF00', 'category': 'warm'},
            {'name': 'Olive Green', 'hex': '#808000', 'category': 'earth'},
            {'name': 'Copper', 'hex': '#B87333', 'category': 'earth'},
            {'name': 'Warm Red', 'hex': '#DC143C', 'category': 'warm'},
            {'name': 'Mustard Yellow', 'hex': '#FFDB58', 'category': 'warm'},
            {'name': 'Terracotta', 'hex': '#E2725B', 'category': 'earth'},
            {'name': 'Warm Beige', 'hex': '#F5DEB3', 'category': 'neutrals'}
        ],
        'avoid': [
            {'name': 'Pure Black', 'hex': '#000000'},
            {'name': 'Icy Blue', 'hex': '#B0E0E6'},
            {'name': 'Cool Pink', 'hex': '#FF1493'},
            {'name': 'Purple', 'hex': '#800080'}
        ],
        'description': 'Rich, warm, earthy colors with golden undertones suit Warm Autumn types.'
    },
    
    'Deep Autumn': {
        'recommended': [
            {'name': 'Deep Brown', 'hex': '#654321', 'category': 'earth'},
            {'name': 'Forest Green', 'hex': '#013220', 'category': 'earth'},
            {'name': 'Burgundy', 'hex': '#800020', 'category': 'deep'},
            {'name': 'Navy Blue', 'hex': '#000080', 'category': 'deep'},
            {'name': 'Deep Gold', 'hex': '#B8860B', 'category': 'warm'},
            {'name': 'Rust', 'hex': '#B7410E', 'category': 'earth'},
            {'name': 'Deep Teal', 'hex': '#004D40', 'category': 'jewel'},
            {'name': 'Chocolate', 'hex': '#7B3F00', 'category': 'earth'},
            {'name': 'Burnt Orange', 'hex': '#CC5500', 'category': 'warm'},
            {'name': 'Deep Purple', 'hex': '#301934', 'category': 'deep'},
            {'name': 'Olive', 'hex': '#6B8E23', 'category': 'earth'},
            {'name': 'Warm Gray', 'hex': '#696969', 'category': 'neutrals'}
        ],
        'avoid': [
            {'name': 'Pastels', 'hex': '#FFB6C1'},
            {'name': 'Light Pink', 'hex': '#FFB6C1'},
            {'name': 'Baby Blue', 'hex': '#89CFF0'},
            {'name': 'Mint Green', 'hex': '#98FB98'}
        ],
        'description': 'Deep, rich colors with warm undertones complement Deep Autumn types.'
    },
    
    'Deep Winter': {
        'recommended': [
            {'name': 'Pure White', 'hex': '#FFFFFF', 'category': 'neutrals'},
            {'name': 'True Black', 'hex': '#000000', 'category': 'neutrals'},
            {'name': 'Royal Blue', 'hex': '#4169E1', 'category': 'jewel'},
            {'name': 'Emerald Green', 'hex': '#50C878', 'category': 'jewel'},
            {'name': 'Ruby Red', 'hex': '#E0115F', 'category': 'jewel'},
            {'name': 'Sapphire Blue', 'hex': '#0F52BA', 'category': 'jewel'},
            {'name': 'Deep Purple', 'hex': '#301934', 'category': 'jewel'},
            {'name': 'Hot Pink', 'hex': '#FF69B4', 'category': 'bright'},
            {'name': 'Bright Yellow', 'hex': '#FFFF00', 'category': 'bright'},
            {'name': 'Navy Blue', 'hex': '#000080', 'category': 'classic'},
            {'name': 'Deep Teal', 'hex': '#004D40', 'category': 'jewel'},
            {'name': 'Charcoal Gray', 'hex': '#36454F', 'category': 'neutrals'}
        ],
        'avoid': [
            {'name': 'Warm Brown', 'hex': '#A0522D'},
            {'name': 'Orange', 'hex': '#FFA500'},
            {'name': 'Warm Beige', 'hex': '#F5DEB3'},
            {'name': 'Olive Green', 'hex': '#808000'}
        ],
        'description': 'Bold, dramatic colors with cool undertones work best for Deep Winter types.'
    },
    
    'Cool Winter': {
        'recommended': [
            {'name': 'Icy Blue', 'hex': '#B0E0E6', 'category': 'cool'},
            {'name': 'Pure White', 'hex': '#FFFFFF', 'category': 'neutrals'},
            {'name': 'True Black', 'hex': '#000000', 'category': 'neutrals'},
            {'name': 'Magenta', 'hex': '#FF00FF', 'category': 'bright'},
            {'name': 'Cool Pink', 'hex': '#FF1493', 'category': 'cool'},
            {'name': 'Royal Blue', 'hex': '#4169E1', 'category': 'jewel'},
            {'name': 'Purple', 'hex': '#800080', 'category': 'jewel'},
            {'name': 'Emerald', 'hex': '#50C878', 'category': 'jewel'},
            {'name': 'Cool Gray', 'hex': '#808080', 'category': 'neutrals'},
            {'name': 'Navy Blue', 'hex': '#000080', 'category': 'classic'},
            {'name': 'Deep Teal', 'hex': '#008B8B', 'category': 'jewel'},
            {'name': 'Silver', 'hex': '#C0C0C0', 'category': 'neutrals'}
        ],
        'avoid': [
            {'name': 'Orange', 'hex': '#FFA500'},
            {'name': 'Warm Brown', 'hex': '#A0522D'},
            {'name': 'Peach', 'hex': '#FFCBA4'},
            {'name': 'Warm Yellow', 'hex': '#FFBF00'}
        ],
        'description': 'Cool, clear colors with blue undertones complement Cool Winter types.'
    },
    
    'Clear Winter': {
        'recommended': [
            {'name': 'Pure Black', 'hex': '#000000', 'category': 'neutrals'},
            {'name': 'Pure White', 'hex': '#FFFFFF', 'category': 'neutrals'},
            {'name': 'True Red', 'hex': '#FF0000', 'category': 'bright'},
            {'name': 'Royal Blue', 'hex': '#4169E1', 'category': 'bright'},
            {'name': 'Emerald Green', 'hex': '#50C878', 'category': 'jewel'},
            {'name': 'Hot Pink', 'hex': '#FF69B4', 'category': 'bright'},
            {'name': 'Purple', 'hex': '#800080', 'category': 'jewel'},
            {'name': 'Bright Yellow', 'hex': '#FFFF00', 'category': 'bright'},
            {'name': 'Navy Blue', 'hex': '#000080', 'category': 'classic'},
            {'name': 'Deep Teal', 'hex': '#008B8B', 'category': 'jewel'},
            {'name': 'Magenta', 'hex': '#FF00FF', 'category': 'bright'},
            {'name': 'Cool Gray', 'hex': '#696969', 'category': 'neutrals'}
        ],
        'avoid': [
            {'name': 'Dusty Colors', 'hex': '#A0A0A0'},
            {'name': 'Warm Brown', 'hex': '#A0522D'},
            {'name': 'Muted Green', 'hex': '#6B8E23'},
            {'name': 'Beige', 'hex': '#F5F5DC'}
        ],
        'description': 'Clear, contrasting colors with high intensity work best for Clear Winter types.'
    }
}

def find_closest_monk_tone(hex_color: str) -> str:
    """Find the closest Monk skin tone for a given hex color using improved algorithm."""
    try:
        # Convert hex to RGB
        target_rgb = np.array(hex_to_rgb(hex_color))
        
        # Calculate color distance using LAB color space for better perceptual accuracy
        def rgb_to_lab(rgb):
            """Convert RGB to LAB color space for better color matching."""
            # Normalize RGB
            rgb = rgb / 255.0
            
            # Convert to XYZ
            def f(t):
                return t**(1/3) if t > 0.008856 else (7.787 * t + 16/116)
            
            # Simplified conversion (for basic comparison)
            x = rgb[0] * 0.4124 + rgb[1] * 0.3576 + rgb[2] * 0.1805
            y = rgb[0] * 0.2126 + rgb[1] * 0.7152 + rgb[2] * 0.0722
            z = rgb[0] * 0.0193 + rgb[1] * 0.1192 + rgb[2] * 0.9505
            
            # Convert to LAB
            fx = f(x / 0.95047)
            fy = f(y / 1.00000)
            fz = f(z / 1.08883)
            
            l = 116 * fy - 16
            a = 500 * (fx - fy)
            b = 200 * (fy - fz)
            
            return np.array([l, a, b])
        
        target_lab = rgb_to_lab(target_rgb)
        min_distance = float('inf')
        closest_monk = 'Monk05'  # Default fallback
        
        for monk_id, tone_data in ENHANCED_MONK_SKIN_TONES.items():
            monk_rgb = np.array(tone_data['rgb'])
            monk_lab = rgb_to_lab(monk_rgb)
            
            # Calculate perceptual distance
            distance = np.sqrt(np.sum((target_lab - monk_lab) ** 2))
            
            if distance < min_distance:
                min_distance = distance
                closest_monk = monk_id
                
        return closest_monk
        
    except Exception as e:
        logger.error(f"Error in find_closest_monk_tone: {e}")
        return 'Monk05'

def get_database_colors():
    """Get colors from database with fallback."""
    try:
        DATABASE_URL = os.getenv(
            "DATABASE_URL", 
            "postgresql://fashion_jvy9_user:0d2Nn5mvyw6KMBDT21l9olpHaxrTPEzh@dpg-d1vhvpbuibrs739dkn3g-a.oregon-postgres.render.com/fashion_jvy9"
        )
        
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        try:
            cursor = db.connection().connection.cursor()
            cursor.execute("""
                SELECT hex_code, color_name, color_family, monk_tones, brightness_level
                FROM comprehensive_colors 
                WHERE hex_code IS NOT NULL 
                AND color_name IS NOT NULL
                ORDER BY color_name
                LIMIT 1000
            """)
            
            results = cursor.fetchall()
            return results if results else []
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Database error: {e}")
        return []

@app.get("/")
def root():
    return {
        "message": "Color Palettes DB API",
        "status": "healthy",
        "endpoints": ["/api/color-palettes-db"]
    }

@app.get("/api/color-palettes-db")
def get_color_palettes_db(
    skin_tone: Optional[str] = Query(None, description="Monk skin tone (e.g., Monk01) or seasonal type"),
    hex_color: Optional[str] = Query(None, description="Hex color to analyze"),
    limit: int = Query(100, ge=10, le=500, description="Maximum colors to return")
):
    """
    Get comprehensive color palette recommendations based on skin tone.
    Supports both Monk skin tone IDs and seasonal color types.
    """
    try:
        logger.info(f"Color palettes request: skin_tone={skin_tone}, hex_color={hex_color}, limit={limit}")
        
        # Determine the seasonal type
        seasonal_type = None
        monk_tone = None
        
        if skin_tone:
            # Check if it's already a seasonal type
            if skin_tone in COMPREHENSIVE_COLOR_PALETTES:
                seasonal_type = skin_tone
            # Check if it's a Monk tone
            elif skin_tone in ENHANCED_MONK_SKIN_TONES:
                monk_tone = skin_tone
                seasonal_type = ENHANCED_MONK_SKIN_TONES[skin_tone]['seasonal_type']
            # Try to match partial Monk tone names
            else:
                for monk_id, tone_data in ENHANCED_MONK_SKIN_TONES.items():
                    if skin_tone.lower() in monk_id.lower() or skin_tone.lower() in tone_data['seasonal_type'].lower():
                        monk_tone = monk_id
                        seasonal_type = tone_data['seasonal_type']
                        break
        
        # If hex color is provided, find the closest Monk tone
        if hex_color and not seasonal_type:
            monk_tone = find_closest_monk_tone(hex_color)
            seasonal_type = ENHANCED_MONK_SKIN_TONES[monk_tone]['seasonal_type']
        
        # Default fallback
        if not seasonal_type:
            seasonal_type = 'Soft Autumn'
            monk_tone = 'Monk05'
        
        logger.info(f"Determined: seasonal_type={seasonal_type}, monk_tone={monk_tone}")
        
        # Get the color palette
        if seasonal_type in COMPREHENSIVE_COLOR_PALETTES:
            palette = COMPREHENSIVE_COLOR_PALETTES[seasonal_type]
            
            # Get colors from database if available
            db_colors = get_database_colors()
            database_recommendations = []
            
            if db_colors:
                for row in db_colors:
                    hex_code, color_name, color_family, monk_tones_str, brightness_level = row
                    if monk_tone and monk_tones_str and monk_tone in str(monk_tones_str):
                        database_recommendations.append({
                            'name': color_name,
                            'hex': hex_code,
                            'color_family': color_family or 'unknown',
                            'brightness_level': brightness_level or 'medium',
                            'source': 'database'
                        })
            
            # Combine palette colors with database colors
            all_recommended = []
            
            # Add palette colors first
            for color in palette['recommended'][:limit//2]:
                all_recommended.append({
                    'name': color['name'],
                    'hex': color['hex'],
                    'category': color.get('category', 'unknown'),
                    'source': 'palette'
                })
            
            # Add database colors
            remaining_limit = limit - len(all_recommended)
            all_recommended.extend(database_recommendations[:remaining_limit])
            
            # Prepare response
            response_data = {
                'colors_that_suit': all_recommended,
                'colors': all_recommended,  # Legacy support
                'colors_to_avoid': palette['avoid'],
                'seasonal_type': seasonal_type,
                'monk_skin_tone': monk_tone,
                'description': palette['description'],
                'message': f"Found {len(all_recommended)} color recommendations for {seasonal_type} ({monk_tone or 'skin tone'})",
                'total_colors': len(all_recommended),
                'database_colors_count': len(database_recommendations),
                'palette_colors_count': len([c for c in all_recommended if c.get('source') == 'palette']),
                'success': True
            }
            
            return JSONResponse(content=response_data)
        
        else:
            # Fallback response
            fallback_colors = [
                {'name': 'Navy Blue', 'hex': '#000080', 'source': 'fallback'},
                {'name': 'Forest Green', 'hex': '#228B22', 'source': 'fallback'},
                {'name': 'Burgundy', 'hex': '#800020', 'source': 'fallback'},
                {'name': 'Soft Coral', 'hex': '#F88379', 'source': 'fallback'},
                {'name': 'Dusty Rose', 'hex': '#DCAE96', 'source': 'fallback'}
            ]
            
            return JSONResponse(content={
                'colors_that_suit': fallback_colors,
                'colors': fallback_colors,
                'colors_to_avoid': [
                    {'name': 'Pure Black', 'hex': '#000000'},
                    {'name': 'Bright Orange', 'hex': '#FF8C00'}
                ],
                'seasonal_type': seasonal_type or 'Universal',
                'monk_skin_tone': monk_tone or skin_tone,
                'description': 'Universal color recommendations',
                'message': f"Showing {len(fallback_colors)} universal color recommendations",
                'total_colors': len(fallback_colors),
                'success': True,
                'fallback': True
            })
            
    except Exception as e:
        logger.error(f"Error in color palettes endpoint: {e}")
        
        # Emergency fallback
        emergency_colors = [
            {'name': 'Classic Navy', 'hex': '#001f3f', 'source': 'emergency'},
            {'name': 'Forest Green', 'hex': '#2d5016', 'source': 'emergency'},
            {'name': 'Burgundy', 'hex': '#800020', 'source': 'emergency'},
            {'name': 'Soft Gray', 'hex': '#808080', 'source': 'emergency'},
            {'name': 'Cream White', 'hex': '#F5F5DC', 'source': 'emergency'}
        ]
        
        return JSONResponse(
            status_code=200,  # Return 200 with error info instead of 500
            content={
                'colors_that_suit': emergency_colors,
                'colors': emergency_colors,
                'colors_to_avoid': [],
                'seasonal_type': 'Universal',
                'monk_skin_tone': skin_tone or 'Unknown',
                'description': 'Emergency color recommendations due to system error',
                'message': f'System error occurred, showing emergency recommendations. Error: {str(e)}',
                'total_colors': len(emergency_colors),
                'success': False,
                'error': str(e)
            }
        )

# Export for Vercel
handler = app
