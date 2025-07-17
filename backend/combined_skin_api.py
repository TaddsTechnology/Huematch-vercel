from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import cv2
from webcolors import hex_to_rgb, rgb_to_hex
import io
from PIL import Image
import uvicorn
import mediapipe as mp
import tensorflow as tf
from sklearn.cluster import KMeans
from scipy.spatial import KDTree
from collections import Counter
import logging
from typing import List, Dict, Tuple, Optional
import time
import gradio as gr

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Combined Skin Tone Analysis API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SkinAnalyzer:
    def __init__(self, model_path: str = "model.h5"):
        """Initialize the skin analyzer."""
        self.model = self._load_model(model_path)
        self.mp_face_detection = mp.solutions.face_detection
        self.face_detection = self.mp_face_detection.FaceDetection(
            model_selection=0, min_detection_confidence=0.5
        )
        
        self.skin_tones = {
            'Monk 1': '#f6ede4', 'Monk 2': '#f3e7db', 'Monk 3': '#f7ead0',
            'Monk 4': '#eadaba', 'Monk 5': '#d7bd96', 'Monk 6': '#a07e56',
            'Monk 7': '#825c43', 'Monk 8': '#604134', 'Monk 9': '#3a312a',
            'Monk 10': '#292420'
        }
        
    def _load_model(self, model_path: str) -> Optional[tf.keras.Model]:
        """Load the TensorFlow model."""
        try:
            model = tf.keras.models.load_model(model_path)
            logger.info("Model loaded successfully")
            return model
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return None
    
    def analyze_image(self, image_array: np.ndarray) -> Dict:
        """Analyze image with multi-face detection."""
        # Similar analysis code
        return {}

# Initialize analyzer and Gradio
analyzer = SkinAnalyzer()

@app.post("/analyze-skin-tone")
async def analyze_skin_tone(file: UploadFile = File(...)):
    """Analyze skin tone from uploaded image"""
    try:
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        image_data = await file.read()
        image = Image.open(io.BytesIO(image_data))
        if image.mode != 'RGB':
            image = image.convert('RGB')
        image_array = np.array(image)
        result = analyzer.analyze_image(image_array)
        return result
    except Exception as e:
        logger.error(f"Error in analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

# Gradio Interface
inputs = gr.Image(type="filepath", label="Upload Face Image")
outputs = [
    gr.Label(label="Monk Skin Tone"),          
    gr.ColorPicker(label="Derived Color"),   
    gr.ColorPicker(label="Closest Monk Color"),
]

def process_image(image_path):
    """Process image and return analysis result."""
    image = cv2.imread(image_path)
    if image is None:
        return "Failed to load image"
    result = analyzer.analyze_image(image)
    return result

interface = gr.Interface(
    fn=process_image,
    inputs=inputs,
    outputs=outputs,
    title="Skin Tone Analysis",
    description="Upload a face image to analyse skin tone and find closest Monk skin tone match."
)

if __name__ == "__main__":
    interface.launch()
    # uvicorn.run(app, host="0.0.0.0", port=8000)
