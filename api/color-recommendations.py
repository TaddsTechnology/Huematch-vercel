from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Add backend path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.append(backend_path)
sys.path.append(os.path.join(backend_path, 'prods_fastapi'))

@app.get("/api/color-recommendations")
def get_color_recommendations(
    skin_tone: str = Query(None),
    hex_color: str = Query(None),
    limit: int = Query(50, ge=10, le=100)
):
    """Enhanced color recommendations endpoint for Vercel."""
    try:
        # Import here to handle import errors gracefully
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import sessionmaker
        import json
        
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
                
                # Get seasonal type mapping
                cursor.execute("""
                    SELECT seasonal_type 
                    FROM skin_tone_mappings 
                    WHERE monk_tone = %s
                """, [skin_tone])
                
                mapping = cursor.fetchone()
                if mapping:
                    seasonal_type = mapping[0]
                    logger.info(f"Found seasonal type: {seasonal_type} for {skin_tone}")
                
                # Get colors from comprehensive_colors
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
                    all_colors.append({
                        "name": row[1],
                        "hex": row[0],
                        "source": "comprehensive_colors",
                        "color_family": row[2] or "unknown",
                        "brightness_level": row[3] or "medium",
                        "monk_compatible": skin_tone
                    })
                
                if comp_results:
                    sources_used.append(f"comprehensive_colors ({len(comp_results)} colors)")
                    logger.info(f"Added {len(comp_results)} colors from comprehensive_colors")
            
            # Add default colors if needed
            if len(all_colors) < 10:
                default_colors = [
                    {"name": "Navy Blue", "hex": "#001f3f", "source": "default"},
                    {"name": "Forest Green", "hex": "#2d5016", "source": "default"},
                    {"name": "Deep Red", "hex": "#b91c1c", "source": "default"},
                    {"name": "Soft Pink", "hex": "#f8bbd9", "source": "default"},
                    {"name": "Warm Brown", "hex": "#8b4513", "source": "default"},
                ]
                all_colors.extend(default_colors)
            
            # Apply limit
            limited_colors = all_colors[:limit]
            
            return {
                "colors": limited_colors,
                "total_colors": len(limited_colors),
                "skin_tone": skin_tone,
                "seasonal_type": seasonal_type,
                "sources_used": sources_used,
                "status": "success"
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error in color recommendations: {e}")
        # Return fallback colors
        fallback_colors = [
            {"name": "Classic Navy", "hex": "#001f3f", "source": "fallback"},
            {"name": "Forest Green", "hex": "#2d5016", "source": "fallback"},
            {"name": "Deep Burgundy", "hex": "#800020", "source": "fallback"},
            {"name": "Soft Coral", "hex": "#ff7f7f", "source": "fallback"},
            {"name": "Warm Taupe", "hex": "#8b7355", "source": "fallback"},
        ]
        
        return {
            "colors": fallback_colors,
            "total_colors": len(fallback_colors),
            "skin_tone": skin_tone or "unknown",
            "seasonal_type": "Universal",
            "sources_used": ["fallback"],
            "status": "fallback",
            "error": str(e)
        }

# Export for Vercel
handler = app
