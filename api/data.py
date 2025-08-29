from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
import logging
import math

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Your PostgreSQL database connection
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://fashion_4vl9_user:FCxnsalymIDJ6jW06YpF6gN3ueSmXS2Q@dpg-d2ff1remcj7s73eojhsg-a.oregon-postgres.render.com/fashion_4vl9"
)

@app.get("/api/data")
def get_makeup_data(
    mst: str = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(24, ge=1, le=100)
):
    """Get makeup products with pagination from database."""
    try:
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        try:
            # Build query based on monk skin tone filter
            base_query = """
                SELECT product_name, brand, price, image_url, description
                FROM makeup_products
                WHERE 1=1
            """
            params = []
            
            if mst:
                base_query += " AND suitable_skin_tones LIKE %s"
                params.append(f'%{mst}%')
            
            # Count total items
            count_query = f"SELECT COUNT(*) FROM ({base_query}) as count_table"
            cursor = db.connection().connection.cursor()
            cursor.execute(count_query, params)
            total_items = cursor.fetchone()[0]
            
            # Add pagination
            offset = (page - 1) * limit
            paginated_query = f"{base_query} ORDER BY product_name LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            cursor.execute(paginated_query, params)
            results = cursor.fetchall()
            
            # Format results
            products = []
            for row in results:
                products.append({
                    "product_name": row[0],
                    "brand": row[1], 
                    "price": row[2],
                    "image_url": row[3] or f"https://via.placeholder.com/150/FF{hash(row[0]) % 10000:04d}/FFFFFF?text={row[1].replace(' ', '+')}",
                    "mst": mst,
                    "desc": row[4] or f"Beautiful product from {row[1]}"
                })
            
            total_pages = math.ceil(total_items / limit)
            
            return {
                "data": products,
                "total_items": total_items,
                "total_pages": total_pages,
                "page": page,
                "limit": limit,
                "status": "success"
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Database error: {e}")
        # Return fallback sample data
        sample_data = [
            {
                "product_name": "Fenty Beauty Foundation",
                "brand": "Fenty Beauty",
                "price": "$36.00",
                "image_url": "https://via.placeholder.com/150/FF6B6B/FFFFFF?text=Fenty+Beauty",
                "mst": mst or "Monk03",
                "desc": "Pro Filt'r Soft Matte Longwear Foundation"
            },
            {
                "product_name": "MAC Lipstick",
                "brand": "MAC",
                "price": "$19.00", 
                "image_url": "https://via.placeholder.com/150/4ECDC4/FFFFFF?text=MAC",
                "mst": mst or "Monk03",
                "desc": "Matte Lipstick - Ruby Woo"
            }
        ]
        
        return {
            "data": sample_data,
            "total_items": len(sample_data),
            "total_pages": 1,
            "page": page,
            "limit": limit,
            "status": "fallback",
            "error": str(e)
        }

# Export for Vercel
handler = app
