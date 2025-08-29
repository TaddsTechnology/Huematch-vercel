import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Your PostgreSQL database connection
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://fashion_4vl9_user:FCxnsalymIDJ6jW06YpF6gN3ueSmXS2Q@dpg-d2ff1remcj7s73eojhsg-a.oregon-postgres.render.com/fashion_4vl9"
)

def get_db_connection():
    """Get database connection with error handling."""
    try:
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        return SessionLocal()
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None

def execute_query(query, params=None):
    """Execute a database query with error handling."""
    db = get_db_connection()
    if not db:
        return None
    
    try:
        cursor = db.connection().connection.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        results = cursor.fetchall()
        return results
    except Exception as e:
        logger.error(f"Query execution failed: {e}")
        return None
    finally:
        if db:
            db.close()
