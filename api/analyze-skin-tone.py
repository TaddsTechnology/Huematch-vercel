from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import json

app = FastAPI()

@app.post("/api/analyze-skin-tone")
async def analyze_skin_tone(file: UploadFile = File(...)):
    """Analyze skin tone from uploaded image."""
    try:
        # For now, return mock data since we don't have the heavy ML dependencies
        # This simulates the skin tone analysis
        
        # Mock Monk skin tone analysis result
        mock_result = {
            "monk_skin_tone": "Monk 3",
            "hex_color": "#d4a574",
            "rgb_color": [212, 165, 116],
            "confidence": 0.85,
            "analysis": {
                "dominant_color": "#d4a574",
                "secondary_colors": ["#c19660", "#e6b888"],
                "brightness": "medium",
                "undertone": "warm"
            },
            "recommendations": [
                {
                    "name": "Warm Coral",
                    "hex": "#ff6b6b",
                    "category": "blush"
                },
                {
                    "name": "Golden Brown",
                    "hex": "#8b4513", 
                    "category": "eyeshadow"
                },
                {
                    "name": "Nude Pink",
                    "hex": "#e6a0a0",
                    "category": "lipstick"
                }
            ],
            "status": "success",
            "platform": "vercel"
        }
        
        return JSONResponse(content=mock_result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

# Export for Vercel
handler = app
