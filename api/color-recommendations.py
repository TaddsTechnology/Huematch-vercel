from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
import os

app = FastAPI()

@app.get("/api/color-recommendations")
def get_color_recommendations(
    skin_tone: str = Query(None),
    hex_color: str = Query(None),
    limit: int = Query(50, ge=10, le=100)
):
    """Color recommendations endpoint with database fallback."""
    try:
        # Try to import and use database
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        
        DATABASE_URL = os.getenv(
            "DATABASE_URL", 
            "postgresql://fashion_4vl9_user:FCxnsalymIDJ6jW06YpF6gN3ueSmXS2Q@dpg-d2ff1remcj7s73eojhsg-a.oregon-postgres.render.com/fashion_4vl9"
        )
        
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        try:
            cursor = db.connection().connection.cursor()
            
            # Try to get colors from database
            cursor.execute("""
                SELECT DISTINCT hex_code, color_name, color_family 
                FROM comprehensive_colors 
                WHERE hex_code IS NOT NULL
                AND color_name IS NOT NULL
                ORDER BY color_name
                LIMIT %s
            """, [limit])
            
            results = cursor.fetchall()
            
            if results:
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
                    "skin_tone": skin_tone,
                    "status": "success_db"
                }
        
        finally:
            db.close()
            
    except Exception as e:
        # Database failed, return fallback colors
        pass
    
    # Fallback colors for different skin tones
    fallback_colors = [
        {"name": "Classic Navy", "hex": "#001f3f", "source": "fallback"},
        {"name": "Forest Green", "hex": "#2d5016", "source": "fallback"},
        {"name": "Deep Burgundy", "hex": "#800020", "source": "fallback"},
        {"name": "Soft Coral", "hex": "#ff7f7f", "source": "fallback"},
        {"name": "Warm Taupe", "hex": "#8b7355", "source": "fallback"},
        {"name": "Royal Blue", "hex": "#4169e1", "source": "fallback"},
        {"name": "Emerald", "hex": "#50c878", "source": "fallback"},
        {"name": "Dusty Rose", "hex": "#dcae96", "source": "fallback"},
        {"name": "Golden Brown", "hex": "#996515", "source": "fallback"},
        {"name": "Plum", "hex": "#dda0dd", "source": "fallback"}
    ]
    
    # Filter based on limit
    limited_colors = fallback_colors[:limit]
    
    return {
        "colors": limited_colors,
        "total_colors": len(limited_colors),
        "skin_tone": skin_tone or "universal",
        "status": "fallback"
    }

# Export for Vercel
handler = app
