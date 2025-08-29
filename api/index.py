from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.append(backend_path)
sys.path.append(os.path.join(backend_path, 'prods_fastapi'))

try:
    # Import the main app from your backend
    from prods_fastapi.main_simple import app as backend_app
    
    # Create a new app instance for Vercel
    app = FastAPI(
        title="AI Fashion API",
        version="1.0.0",
        description="AI Fashion recommendation system deployed on Vercel"
    )
    
    # Configure CORS for Vercel deployment
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # More permissive for Vercel
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
        max_age=3600
    )
    
    # Mount all routes from the original app
    for route in backend_app.routes:
        app.router.routes.append(route)
    
    # Add a health check specific to Vercel
    @app.get("/")
    def vercel_root():
        return {
            "message": "AI Fashion API running on Vercel", 
            "status": "healthy",
            "platform": "vercel"
        }
    
except ImportError as e:
    print(f"Import error: {e}")
    # Fallback minimal app if imports fail
    app = FastAPI(title="AI Fashion API - Fallback")
    
    @app.get("/")
    def fallback_root():
        return {"message": "AI Fashion API - Fallback mode", "error": str(e)}
    
    @app.get("/health")
    def fallback_health():
        return {"status": "limited", "message": "Running in fallback mode"}

# Export for Vercel
handler = app
