from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import cv2
from webcolors import hex_to_rgb, rgb_to_hex
import io
from PIL import Image
import uvicorn
import tempfile
import os
import asyncio
from gradio_client import Client

app = FastAPI(title="Skin Tone Analysis API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Initialize Gradio client
gradio_client = None
GRADIO_URL = "http://localhost:7860"  # Default Gradio port

# Try to connect to Gradio app
try:
    gradio_client = Client(GRADIO_URL)
    print(f"Connected to Gradio app at {GRADIO_URL}")
except Exception as e:
    print(f"Could not connect to Gradio app at {GRADIO_URL}: {e}")
    gradio_client = None

classes = [
    "background", "skin", "left eyebrow", "right eyebrow",
    "left eye", "right eye", "nose", "upper lip", "inner mouth",
    "lower lip", "hair"
]

def face_skin_extract(pred, image_x):
    output = np.zeros_like(image_x, dtype=np.uint8)
    mask = (pred == 1)
    output[mask] = image_x[mask]
    return output

# Remove the old functions since we'll use Gradio client

def closest_tone_match(rgb_tuple):
    skin_tones = {
        'Monk 1': '#f6ede4', 'Monk 2': '#f3e7db', 'Monk 3': '#f7ead0', 
        'Monk 4': '#eadaba', 'Monk 5': '#d7bd96', 'Monk 6': '#a07e56', 
        'Monk 7': '#825c43', 'Monk 8': '#604134', 'Monk 9': '#3a312a', 
        'Monk 10': '#292420'
    }

    print(f"Input RGB tuple: {rgb_tuple}")
    
    rgb_values = []
    names = []
    for monk in skin_tones:
        names.append(monk)
        rgb_values.append(hex_to_rgb(skin_tones[monk]))
    
    print(f"Monk skin tone RGB values: {list(zip(names, rgb_values))}")
    
    kdt_db = KDTree(rgb_values)
    distance, index = kdt_db.query(rgb_tuple)
    
    print(f"Closest match index: {index}, distance: {distance}")
    print(f"Matched tone: {names[index]}")
    
    monk_hex = skin_tones[names[index]]
    derived_hex = rgb_to_hex((int(rgb_tuple[0]), int(rgb_tuple[1]), int(rgb_tuple[2])))
    
    print(f"Returning: {names[index]}, {monk_hex}, {derived_hex}")
    
    return names[index], monk_hex, derived_hex

def process_image_from_array(image_array):
    print(f"Processing image array with shape: {image_array.shape}")

    if gradio_client is None:
        raise RuntimeError("Gradio client not connected")

    try:
        # Use Gradio client to process image
        response = gradio_client.predict(image_array)
        monk_tone, derived_hex, monk_hex = response['monk_tone_display'], response['derived_hex_code'], response['monk_hex']
    except Exception as e:
        print(f"Error processing image with Gradio: {e}")
        monk_tone, derived_hex, monk_hex = "Monk 5", "#d7bd96", "#d7bd96"

    return monk_tone, derived_hex, monk_hex

@app.post("/analyze-skin-tone")
async def analyze_skin_tone(file: UploadFile = File(...)):
    """
    Analyze skin tone from uploaded image
    """
    try:
        # Validate file type
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read image data
        image_data = await file.read()
        
        # Convert to PIL Image
        image = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Convert to numpy array
        image_array = np.array(image)
        
        # Process the image
        monk_tone, derived_hex, monk_hex = process_image_from_array(image_array)
        
        # Parse monk tone to get the number and format consistently
        monk_number = monk_tone.split()[1]  # Get the number part
        monk_id = f"Monk{monk_number.zfill(2)}"  # Format as Monk01, Monk02, etc.
        
        response = {
            "monk_skin_tone": monk_id,
            "monk_tone_display": monk_tone,
            "monk_hex": monk_hex,
            "derived_hex_code": derived_hex,
            "dominant_rgb": list(hex_to_rgb(derived_hex)),
            "success": True
        }
        
        print(f"Returning response: {response}")
        return response
        
    except Exception as e:
        print(f"Error in analyze_skin_tone: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "message": "Skin tone analysis API is running"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
