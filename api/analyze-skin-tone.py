from fastapi import FastAPI
from fastapi.responses import JSONResponse
import random

app = FastAPI()

@app.post("/api/analyze-skin-tone")
@app.get("/api/analyze-skin-tone")  # Allow GET for testing
def analyze_skin_tone():
    """Analyze skin tone - returns mock data for now."""
    # Generate different mock results
    monk_tones = [
        {"tone": "Monk 1", "hex": "#f6ede4", "name": "Very Light"},
        {"tone": "Monk 3", "hex": "#d4a574", "name": "Light Medium"},
        {"tone": "Monk 5", "hex": "#c19660", "name": "Medium"},
        {"tone": "Monk 7", "hex": "#8b4513", "name": "Medium Deep"},
        {"tone": "Monk 10", "hex": "#292420", "name": "Very Deep"}
    ]
    
    selected_tone = random.choice(monk_tones)
    
    mock_result = {
        "monk_skin_tone": selected_tone["tone"],
        "hex_color": selected_tone["hex"],
        "skin_tone_name": selected_tone["name"],
        "rgb_color": [int(selected_tone["hex"][1:3], 16), int(selected_tone["hex"][3:5], 16), int(selected_tone["hex"][5:7], 16)],
        "confidence": round(random.uniform(0.75, 0.95), 2),
        "analysis": {
            "dominant_color": selected_tone["hex"],
            "brightness": "medium",
            "undertone": random.choice(["warm", "cool", "neutral"])
        },
        "recommendations": [
            {"name": "Coral Blush", "hex": "#ff6b6b", "category": "blush"},
            {"name": "Brown Eyeshadow", "hex": "#8b4513", "category": "eyeshadow"},
            {"name": "Pink Lipstick", "hex": "#e6a0a0", "category": "lipstick"}
        ],
        "status": "success",
        "platform": "vercel"
    }
    
    return JSONResponse(content=mock_result)

# Export for Vercel
handler = app
