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
import colorsys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Color Suggestions API",
    version="1.0.0",
    description="Enhanced color suggestions with improved light skin tone support"
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

# Enhanced light skin tone algorithm with better color theory
def analyze_skin_undertone(hex_color: str) -> Dict[str, Any]:
    """Analyze skin undertone using advanced color theory."""
    try:
        rgb = hex_to_rgb(hex_color)
        r, g, b = rgb
        
        # Convert to HSV for better analysis
        h, s, v = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)
        h_degrees = h * 360
        
        # Calculate undertone based on hue and ratios
        undertone_analysis = {
            'dominant_hue': h_degrees,
            'saturation': s,
            'brightness': v,
            'rgb_ratios': {
                'red_green_ratio': r/g if g > 0 else 1,
                'red_blue_ratio': r/b if b > 0 else 1,
                'green_blue_ratio': g/b if b > 0 else 1
            }
        }
        
        # Determine undertone
        if r > g and r > b:
            if h_degrees < 30 or h_degrees > 330:
                undertone = 'warm' if s > 0.2 else 'neutral_warm'
            else:
                undertone = 'neutral'
        elif g > r and g > b:
            if 60 <= h_degrees <= 180:
                undertone = 'cool' if s > 0.15 else 'neutral_cool'
            else:
                undertone = 'neutral'
        else:  # b is dominant or balanced
            if 180 <= h_degrees <= 270:
                undertone = 'cool'
            else:
                undertone = 'neutral'
        
        # Special handling for very light skin tones
        if v > 0.9 and s < 0.15:  # Very light and low saturation
            # Check subtle color differences for light skin
            if r > g > b and (r - b) > 10:
                undertone = 'warm'
            elif b > r and (b - r) > 5:
                undertone = 'cool'
            else:
                undertone = 'neutral'
        
        undertone_analysis['undertone'] = undertone
        return undertone_analysis
        
    except Exception as e:
        logger.error(f"Error analyzing undertone: {e}")
        return {
            'undertone': 'neutral',
            'dominant_hue': 0,
            'saturation': 0,
            'brightness': 0.5,
            'rgb_ratios': {}
        }

# Enhanced seasonal color recommendations
ENHANCED_SEASONAL_RECOMMENDATIONS = {
    'Light Summer': {
        'skin_tone': 'Very light with cool undertones',
        'suitable_colors': [
            'Powder blue enhances your cool undertones',
            'Soft pink complements your delicate coloring',
            'Lavender works beautifully with your light complexion',
            'Rose quartz adds warmth without overwhelming',
            'Cool gray provides sophisticated neutrals',
            'Soft white is more flattering than pure white',
            'Light coral gives a healthy glow',
            'Dusty rose adds subtle warmth',
            'Mint green provides fresh contrast',
            'Pearl gray creates elegant looks'
        ]
    },
    
    'Light Spring': {
        'skin_tone': 'Light with warm, fresh undertones',
        'suitable_colors': [
            'Peach complements your warm undertones perfectly',
            'Light coral enhances your natural glow',
            'Warm white is more flattering than cool white',
            'Soft gold adds richness without heaviness',
            'Light turquoise provides beautiful contrast',
            'Salmon pink works wonderfully with your coloring',
            'Light yellow brightens your complexion',
            'Warm beige creates perfect neutrals',
            'Aqua brings out your eyes',
            'Ivory is ideal for professional looks'
        ]
    },
    
    'Warm Spring': {
        'skin_tone': 'Light to medium with golden undertones',
        'suitable_colors': [
            'Golden yellow enhances your warm glow',
            'Coral brings out your natural radiance',
            'Peach is incredibly flattering',
            'Warm orange adds vibrant energy',
            'Light brown creates earthy sophistication',
            'Turquoise provides stunning contrast',
            'Light green complements your warmth',
            'Camel creates perfect neutrals',
            'Warm red is bold and beautiful on you',
            'Light khaki works for casual elegance'
        ]
    },
    
    'Clear Spring': {
        'skin_tone': 'Clear complexion that can handle bright colors',
        'suitable_colors': [
            'Bright yellow showcases your clarity',
            'True red is dramatic and flattering',
            'Royal blue enhances your clear coloring',
            'Emerald green is stunning on you',
            'Hot pink adds vibrant energy',
            'Pure white creates crisp contrast',
            'Orange brings out your warmth',
            'Purple adds royal elegance',
            'Navy blue is a perfect classic',
            'Turquoise creates beautiful contrast'
        ]
    },
    
    'Soft Autumn': {
        'skin_tone': 'Medium tones with muted, warm undertones',
        'suitable_colors': [
            'Warm beige harmonizes with your skin',
            'Soft brown enhances your natural warmth',
            'Muted green complements your earthiness',
            'Dusty rose adds gentle color',
            'Soft gold brings out your warmth',
            'Teal provides rich contrast',
            'Rust adds autumn richness',
            'Sage green is beautifully harmonious',
            'Warm gray creates sophisticated looks',
            'Soft coral enhances your glow'
        ]
    },
    
    'Warm Autumn': {
        'skin_tone': 'Rich, warm coloring with golden undertones',
        'suitable_colors': [
            'Burnt orange celebrates your warmth',
            'Deep gold enhances your richness',
            'Rust red is incredibly flattering',
            'Forest green provides earthy elegance',
            'Chocolate brown is perfect for you',
            'Warm yellow brightens your complexion',
            'Olive green complements your earthiness',
            'Copper adds metallic warmth',
            'Terracotta enhances your natural tones',
            'Mustard yellow is bold and beautiful'
        ]
    },
    
    'Deep Autumn': {
        'skin_tone': 'Deep, rich coloring with warm undertones',
        'suitable_colors': [
            'Deep brown enhances your richness',
            'Forest green provides stunning depth',
            'Burgundy adds luxurious richness',
            'Navy blue creates sophisticated looks',
            'Deep gold brings out your warmth',
            'Rust adds earthy elegance',
            'Deep teal is beautifully dramatic',
            'Chocolate creates perfect neutrals',
            'Burnt orange enhances your depth',
            'Deep purple adds royal richness'
        ]
    },
    
    'Deep Winter': {
        'skin_tone': 'Deep coloring that can handle bold contrasts',
        'suitable_colors': [
            'Pure white creates stunning contrast',
            'True black is elegantly dramatic',
            'Royal blue enhances your depth',
            'Emerald green is magnificently bold',
            'Ruby red adds jewel-like richness',
            'Hot pink brings vibrant energy',
            'Bright yellow creates bold contrast',
            'Deep purple adds royal elegance',
            'Sapphire blue is beautifully intense',
            'Deep teal provides rich sophistication'
        ]
    },
    
    'Cool Winter': {
        'skin_tone': 'Cool undertones with ability to wear bold colors',
        'suitable_colors': [
            'Icy blue enhances your cool beauty',
            'Pure white creates perfect contrast',
            'True black is elegantly sophisticated',
            'Magenta brings out your intensity',
            'Cool pink complements your undertones',
            'Royal blue is regally beautiful',
            'Purple adds jewel-like richness',
            'Emerald green creates stunning contrast',
            'Cool gray provides perfect neutrals',
            'Silver adds metallic coolness'
        ]
    },
    
    'Clear Winter': {
        'skin_tone': 'High contrast coloring that needs clear, intense colors',
        'suitable_colors': [
            'Pure black creates dramatic elegance',
            'Pure white provides perfect contrast',
            'True red is boldly beautiful',
            'Royal blue enhances your clarity',
            'Emerald green is stunningly vibrant',
            'Hot pink adds electric energy',
            'Bright yellow creates bold statements',
            'Deep purple adds royal intensity',
            'Navy blue is classically elegant',
            'Magenta brings out your boldness'
        ]
    }
}

def determine_seasonal_type(undertone_analysis: Dict) -> str:
    """Determine seasonal color type based on undertone analysis."""
    undertone = undertone_analysis['undertone']
    brightness = undertone_analysis['brightness']
    saturation = undertone_analysis['saturation']
    
    # Light skin tones (high brightness)
    if brightness > 0.85:
        if undertone in ['cool', 'neutral_cool']:
            return 'Light Summer'
        elif undertone in ['warm', 'neutral_warm']:
            return 'Light Spring'
        elif undertone == 'neutral':
            return 'Light Spring' if saturation > 0.2 else 'Light Summer'
    
    # Medium-light skin tones
    elif brightness > 0.7:
        if undertone in ['warm', 'neutral_warm']:
            return 'Warm Spring' if saturation > 0.25 else 'Light Spring'
        elif undertone in ['cool', 'neutral_cool']:
            return 'Clear Spring' if saturation > 0.3 else 'Light Summer'
        else:
            return 'Clear Spring'
    
    # Medium skin tones
    elif brightness > 0.5:
        if undertone in ['warm', 'neutral_warm']:
            return 'Warm Autumn' if saturation > 0.3 else 'Soft Autumn'
        elif undertone in ['cool', 'neutral_cool']:
            return 'Cool Winter' if saturation > 0.4 else 'Deep Winter'
        else:
            return 'Soft Autumn'
    
    # Deeper skin tones
    else:
        if undertone in ['warm', 'neutral_warm']:
            return 'Deep Autumn'
        elif undertone in ['cool', 'neutral_cool']:
            return 'Cool Winter'
        else:
            return 'Deep Winter'

@app.get("/")
def root():
    return {
        "message": "Color Suggestions API",
        "status": "healthy",
        "endpoints": ["/color-suggestions"]
    }

@app.get("/color-suggestions")
def get_color_suggestions(
    skin_tone: Optional[str] = Query(None, description="Seasonal type or descriptive skin tone"),
    hex_color: Optional[str] = Query(None, description="Hex color to analyze"),
    detailed: bool = Query(False, description="Return detailed analysis")
):
    """
    Get color suggestions based on skin tone analysis.
    Enhanced algorithm with better light skin tone support.
    """
    try:
        logger.info(f"Color suggestions request: skin_tone={skin_tone}, hex_color={hex_color}")
        
        seasonal_type = None
        undertone_analysis = None
        
        # If hex color is provided, analyze it
        if hex_color:
            undertone_analysis = analyze_skin_undertone(hex_color)
            seasonal_type = determine_seasonal_type(undertone_analysis)
            logger.info(f"Analyzed hex {hex_color}: {seasonal_type}, undertone: {undertone_analysis['undertone']}")
        
        # If skin tone is provided, try to match it
        elif skin_tone:
            # Direct match
            if skin_tone in ENHANCED_SEASONAL_RECOMMENDATIONS:
                seasonal_type = skin_tone
            else:
                # Fuzzy matching for seasonal types
                for season in ENHANCED_SEASONAL_RECOMMENDATIONS.keys():
                    if skin_tone.lower() in season.lower() or season.lower() in skin_tone.lower():
                        seasonal_type = season
                        break
        
        # Default fallback
        if not seasonal_type:
            seasonal_type = 'Soft Autumn'
            logger.info(f"Using default seasonal type: {seasonal_type}")
        
        # Get recommendations
        if seasonal_type in ENHANCED_SEASONAL_RECOMMENDATIONS:
            recommendations = ENHANCED_SEASONAL_RECOMMENDATIONS[seasonal_type]
            
            # Format response
            response_data = {
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
            
            # Add detailed analysis if requested
            if detailed and undertone_analysis:
                response_data['analysis'] = {
                    'undertone': undertone_analysis['undertone'],
                    'dominant_hue': round(undertone_analysis['dominant_hue'], 1),
                    'saturation': round(undertone_analysis['saturation'], 3),
                    'brightness': round(undertone_analysis['brightness'], 3),
                    'hex_analyzed': hex_color
                }
            
            return JSONResponse(content=response_data)
        
        else:
            # Fallback response
            return JSONResponse(content={
                'data': [
                    {
                        'skin_tone': 'Universal recommendations',
                        'suitable_colors': 'Navy blue provides classic elegance. Soft coral adds warmth. Forest green offers earthy sophistication. Dusty rose brings gentle color. Warm gray creates perfect neutrals. These versatile colors work well with most skin tones.'
                    }
                ],
                'seasonal_type': seasonal_type or 'Universal',
                'total_suggestions': 6,
                'success': True,
                'fallback': True
            })
            
    except Exception as e:
        logger.error(f"Error in color suggestions: {e}")
        
        # Emergency response
        return JSONResponse(
            status_code=200,
            content={
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
        )

# Export for Vercel
handler = app
