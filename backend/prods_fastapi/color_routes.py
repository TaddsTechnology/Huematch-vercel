# Color routes for the Fashion AI backend
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import psycopg2
from pydantic import BaseModel

# Create router for color endpoints
color_router = APIRouter(prefix="/api/colors", tags=["colors"])

# Database connection (use external Render.com database)
import os
DB_CONFIG = {
    'host': 'dpg-d1vhvpbuibrs739dkn3g-a.oregon-postgres.render.com',
    'database': 'fashion_jvy9',
    'user': 'fashion_jvy9_user',
    'password': '0d2Nn5mvyw6KMBDT21l9olpHaxrTPEzh',
    'port': '5432',
    'sslmode': 'require'  # External database needs SSL
}

# Pydantic models
class ColorRecommendation(BaseModel):
    hex_code: str
    color_name: Optional[str]
    suitable_skin_tone: Optional[str]
    seasonal_palette: Optional[str]
    category: Optional[str]

class MonkColor(BaseModel):
    hex_code: str
    color_name: str
    category: str

def connect_to_db():
    """Establish connection to PostgreSQL database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection error: {e}")

@color_router.get("/skin-tone/{skin_tone}", response_model=List[ColorRecommendation])
async def get_colors_by_skin_tone(
    skin_tone: str,
    limit: Optional[int] = Query(50, description="Number of colors to return"),
    category: Optional[str] = Query(None, description="Filter by category (recommended/avoid)")
):
    """Get colors for a specific skin tone"""
    conn = connect_to_db()
    
    try:
        cursor = conn.cursor()
        
        base_query = """
        SELECT hex_code, color_name, suitable_skin_tone, seasonal_palette, category
        FROM colors 
        WHERE (suitable_skin_tone ILIKE %s OR seasonal_palette ILIKE %s)
        """
        
        params = [f'%{skin_tone}%', f'%{skin_tone}%']
        
        if category:
            base_query += " AND category = %s"
            params.append(category)
        
        base_query += " ORDER BY category, color_name LIMIT %s;"
        params.append(limit)
        
        cursor.execute(base_query, params)
        results = cursor.fetchall()
        
        colors = []
        for row in results:
            colors.append(ColorRecommendation(
                hex_code=row[0],
                color_name=row[1],
                suitable_skin_tone=row[2],
                seasonal_palette=row[3],
                category=row[4]
            ))
        
        cursor.close()
        conn.close()
        
        return colors
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching colors: {e}")

@color_router.get("/recommendations/{skin_tone}", response_model=List[ColorRecommendation])
async def get_color_recommendations(
    skin_tone: str,
    limit: Optional[int] = Query(10, description="Number of recommendations to return")
):
    """Get top color recommendations for a skin tone"""
    conn = connect_to_db()
    
    try:
        cursor = conn.cursor()
        
        query = """
        SELECT hex_code, color_name, suitable_skin_tone, seasonal_palette, category
        FROM colors 
        WHERE (suitable_skin_tone ILIKE %s OR seasonal_palette ILIKE %s)
        AND category = 'recommended'
        ORDER BY color_name
        LIMIT %s;
        """
        
        cursor.execute(query, (f'%{skin_tone}%', f'%{skin_tone}%', limit))
        results = cursor.fetchall()
        
        recommendations = []
        for row in results:
            recommendations.append(ColorRecommendation(
                hex_code=row[0],
                color_name=row[1],
                suitable_skin_tone=row[2],
                seasonal_palette=row[3],
                category=row[4]
            ))
        
        cursor.close()
        conn.close()
        
        return recommendations
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching recommendations: {e}")

@color_router.get("/monk", response_model=List[MonkColor])
async def get_monk_colors():
    """Get monk-inspired colors"""
    conn = connect_to_db()
    
    try:
        cursor = conn.cursor()
        
        query = """
        SELECT hex_code, color_name, category
        FROM colors 
        WHERE suitable_skin_tone IS NULL AND seasonal_palette IS NULL
        AND color_name IN ('Monk Brown', 'Sienna', 'Peru Brown', 'Burlywood', 'Tan', 'Khaki Brown', 
                          'Dark Orange', 'Orange', 'Goldenrod', 'Dark Goldenrod', 'Maroon', 
                          'Dark Red', 'Saddle Brown', 'Dark Brown', 'Sepia', 'Coyote Brown', 
                          'Slate Gray', 'Light Slate Gray', 'Dim Gray', 'Gray')
        ORDER BY color_name;
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        colors = []
        for row in results:
            colors.append(MonkColor(
                hex_code=row[0],
                color_name=row[1],
                category=row[2]
            ))
        
        cursor.close()
        conn.close()
        
        return colors
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching monk colors: {e}")

@color_router.get("/hex/{hex_code}", response_model=ColorRecommendation)
async def get_color_by_hex(hex_code: str):
    """Get color information by hex code"""
    if not hex_code.startswith('#'):
        hex_code = '#' + hex_code
    
    conn = connect_to_db()
    
    try:
        cursor = conn.cursor()
        
        query = """
        SELECT hex_code, color_name, suitable_skin_tone, seasonal_palette, category
        FROM colors 
        WHERE hex_code = %s;
        """
        
        cursor.execute(query, (hex_code,))
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Color not found")
        
        color_info = ColorRecommendation(
            hex_code=result[0],
            color_name=result[1],
            suitable_skin_tone=result[2],
            seasonal_palette=result[3],
            category=result[4]
        )
        
        cursor.close()
        conn.close()
        
        return color_info
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching color: {e}")

@color_router.get("/all", response_model=List[ColorRecommendation])
async def get_all_colors(
    limit: Optional[int] = Query(100, description="Number of colors to return"),
    category: Optional[str] = Query(None, description="Filter by category"),
    skin_tone: Optional[str] = Query(None, description="Filter by skin tone")
):
    """Get all colors with optional filters"""
    conn = connect_to_db()
    
    try:
        cursor = conn.cursor()
        
        base_query = "SELECT hex_code, color_name, suitable_skin_tone, seasonal_palette, category FROM colors WHERE 1=1"
        params = []
        
        if category:
            base_query += " AND category = %s"
            params.append(category)
        
        if skin_tone:
            base_query += " AND (suitable_skin_tone ILIKE %s OR seasonal_palette ILIKE %s)"
            params.extend([f'%{skin_tone}%', f'%{skin_tone}%'])
        
        base_query += " ORDER BY suitable_skin_tone, color_name LIMIT %s;"
        params.append(limit)
        
        cursor.execute(base_query, params)
        results = cursor.fetchall()
        
        colors = []
        for row in results:
            colors.append(ColorRecommendation(
                hex_code=row[0],
                color_name=row[1],
                suitable_skin_tone=row[2],
                seasonal_palette=row[3],
                category=row[4]
            ))
        
        cursor.close()
        conn.close()
        
        return colors
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching colors: {e}")

# Add a separate router for color palettes
from fastapi import APIRouter
palette_router = APIRouter(prefix="/api", tags=["palettes"])

class ColorPaletteResponse(BaseModel):
    colors_that_suit: List[dict]
    colors_to_avoid: List[dict] = []
    seasonal_type: str
    monk_skin_tone: str
    message: str
    database_source: bool = True

@palette_router.get("/color-palettes-db")
async def get_color_palettes_db(
    skin_tone: Optional[str] = Query(None, description="Monk skin tone (e.g., Monk05) or seasonal type"),
    limit: Optional[int] = Query(500, description="Number of colors to return")
):
    """Get color palettes from database based on skin tone mapping"""
    if not skin_tone:
        raise HTTPException(status_code=400, detail="skin_tone parameter is required")
    
    conn = connect_to_db()
    
    try:
        cursor = conn.cursor()
        
        # Step 1: Determine seasonal type from Monk tone
        seasonal_type = skin_tone
        seasonal_type_map = {
            'Monk01': 'Light Spring',
            'Monk02': 'Light Spring', 
            'Monk03': 'Clear Spring',
            'Monk04': 'Warm Spring',
            'Monk05': 'Soft Autumn',
            'Monk06': 'Warm Autumn',
            'Monk07': 'Deep Autumn',
            'Monk08': 'Deep Winter',
            'Monk09': 'Cool Winter',
            'Monk10': 'Clear Winter'
        }
        
        if skin_tone in seasonal_type_map:
            seasonal_type = seasonal_type_map[skin_tone]
        
        # Step 2: Get colors from database for this seasonal type
        query = """
        SELECT hex_code, color_name, suitable_skin_tone, seasonal_palette, category
        FROM colors 
        WHERE (seasonal_palette ILIKE %s OR suitable_skin_tone ILIKE %s)
        AND category = 'recommended'
        AND hex_code IS NOT NULL
        AND color_name IS NOT NULL
        ORDER BY color_name
        LIMIT %s;
        """
        
        cursor.execute(query, (f'%{seasonal_type}%', f'%{seasonal_type}%', limit))
        results = cursor.fetchall()
        
        # Format colors for frontend
        colors_that_suit = []
        for row in results:
            colors_that_suit.append({
                "name": row[1],  # color_name
                "hex": row[0]   # hex_code
            })
        
        # Step 3: Get colors to avoid
        avoid_query = """
        SELECT hex_code, color_name
        FROM colors 
        WHERE (seasonal_palette ILIKE %s OR suitable_skin_tone ILIKE %s)
        AND category = 'avoid'
        AND hex_code IS NOT NULL
        AND color_name IS NOT NULL
        ORDER BY color_name
        LIMIT 20;
        """
        
        cursor.execute(avoid_query, (f'%{seasonal_type}%', f'%{seasonal_type}%'))
        avoid_results = cursor.fetchall()
        
        colors_to_avoid = []
        for row in avoid_results:
            colors_to_avoid.append({
                "name": row[1],  # color_name
                "hex": row[0]   # hex_code
            })
        
        cursor.close()
        conn.close()
        
        return {
            "colors_that_suit": colors_that_suit,
            "colors": colors_that_suit,  # Alias for compatibility
            "colors_to_avoid": colors_to_avoid,
            "seasonal_type": seasonal_type,
            "monk_skin_tone": skin_tone,
            "description": f"Based on your {seasonal_type} seasonal type and {skin_tone} skin tone, here are colors from our database that complement your complexion.",
            "message": f"Showing {len(colors_that_suit)} recommended colors and {len(colors_to_avoid)} colors to avoid from our comprehensive database.",
            "database_source": True
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching color palettes: {e}")

