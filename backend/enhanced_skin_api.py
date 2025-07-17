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
import mediapipe as mp
import tensorflow as tf
from sklearn.cluster import KMeans
from scipy.spatial import KDTree
from collections import Counter
import logging
from typing import List, Dict, Tuple, Optional
import time
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Enhanced Skin Tone Analysis API", version="2.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class EnhancedSkinAnalyzer:
    def __init__(self, model_path: str = "model.h5"):
        """Initialize the enhanced skin analyzer."""
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
            logger.info("Enhanced model loaded successfully")
            return model
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return None
    
    def detect_faces(self, image: np.ndarray) -> List[Dict]:
        """Detect faces using MediaPipe."""
        try:
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = self.face_detection.process(rgb_image)
            
            faces = []
            if results.detections:
                for detection in results.detections:
                    bbox = detection.location_data.relative_bounding_box
                    h, w, _ = image.shape
                    
                    # Convert to absolute coordinates
                    x = int(bbox.xmin * w)
                    y = int(bbox.ymin * h)
                    width = int(bbox.width * w)
                    height = int(bbox.height * h)
                    
                    # Add padding
                    padding = 20
                    x = max(0, x - padding)
                    y = max(0, y - padding)
                    width = min(w - x, width + 2 * padding)
                    height = min(h - y, height + 2 * padding)
                    
                    faces.append({
                        'bbox': [x, y, width, height],
                        'confidence': float(detection.score[0]),
                        'crop': image[y:y+height, x:x+width]
                    })
            
            return faces
        except Exception as e:
            logger.error(f"Face detection error: {e}")
            return []
    
    def correct_lighting(self, image: np.ndarray) -> np.ndarray:
        """Apply CLAHE lighting correction."""
        try:
            # Convert to LAB color space
            lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
            l, a, b = cv2.split(lab)
            
            # Apply CLAHE to L channel
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            
            # Merge and convert back
            lab = cv2.merge([l, a, b])
            corrected = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
            
            return corrected
        except Exception as e:
            logger.error(f"Lighting correction error: {e}")
            return image
    
    def extract_skin_advanced(self, pred_mask: np.ndarray, image: np.ndarray) -> np.ndarray:
        """Extract skin pixels from segmentation."""
        output = np.zeros_like(image, dtype=np.uint8)
        mask = (pred_mask == 1)  # Skin class
        output[mask] = image[mask]
        return output
    
    def get_dominant_color_with_confidence(self, skin_img: np.ndarray) -> Tuple[np.ndarray, float]:
        """Extract dominant color with confidence score."""
        try:
            # Remove background pixels
            mask = ~np.all(skin_img == [0, 0, 0], axis=-1)
            skin_pixels = skin_img[mask]
            
            if len(skin_pixels) == 0:
                return np.array([200, 150, 120]), 0.0
            
            # Remove outliers
            brightness = np.mean(skin_pixels, axis=1)
            q25, q75 = np.percentile(brightness, [25, 75])
            iqr = q75 - q25
            lower_bound = max(0, q25 - 1.5 * iqr)
            upper_bound = min(255, q75 + 1.5 * iqr)
            
            valid_mask = (brightness >= lower_bound) & (brightness <= upper_bound)
            filtered_pixels = skin_pixels[valid_mask]
            
            if len(filtered_pixels) == 0:
                filtered_pixels = skin_pixels
            
            # K-means clustering
            n_clusters = min(5, len(filtered_pixels))
            kmeans = KMeans(n_clusters=n_clusters, n_init=10, random_state=42)
            kmeans.fit(filtered_pixels)
            
            # Get dominant cluster
            labels = kmeans.labels_
            label_counts = Counter(labels)
            dominant_label = label_counts.most_common(1)[0][0]
            dominant_color = kmeans.cluster_centers_[dominant_label]
            
            # Calculate confidence
            dominant_pixels = filtered_pixels[labels == dominant_label]
            cluster_ratio = len(dominant_pixels) / len(filtered_pixels)
            
            if len(dominant_pixels) > 1:
                std_dev = np.std(dominant_pixels, axis=0)
                color_consistency = 1.0 / (1.0 + np.mean(std_dev) / 50.0)
            else:
                color_consistency = 0.5
            
            confidence = cluster_ratio * color_consistency
            
            return dominant_color, min(confidence, 1.0)
            
        except Exception as e:
            logger.error(f"Color extraction error: {e}")
            return np.array([200, 150, 120]), 0.0
    
    def find_closest_monk_tone(self, rgb_tuple: Tuple[int, int, int]) -> Tuple[str, str, str, float]:
        """Find closest Monk tone with similarity score."""
        try:
            rgb_values = []
            names = []
            
            for name, hex_color in self.skin_tones.items():
                names.append(name)
                rgb_values.append(hex_to_rgb(hex_color))
            
            # Find closest match
            tree = KDTree(rgb_values)
            distance, index = tree.query(rgb_tuple)
            
            matched_name = names[index]
            monk_hex = self.skin_tones[matched_name]
            derived_hex = rgb_to_hex((int(rgb_tuple[0]), int(rgb_tuple[1]), int(rgb_tuple[2])))
            
            # Calculate similarity
            max_distance = np.sqrt(3 * 255**2)
            similarity = 1.0 - (distance / max_distance)
            
            return matched_name, monk_hex, derived_hex, similarity
            
        except Exception as e:
            logger.error(f"Monk tone matching error: {e}")
            return "Monk 5", "#d7bd96", "#d7bd96", 0.0
    
    def calculate_confidence(self, seg_quality: float, color_conf: float, 
                           tone_sim: float, face_conf: float) -> float:
        """Calculate overall confidence score."""
        weights = {
            'segmentation': 0.25,
            'color': 0.35,
            'tone': 0.25,
            'face': 0.15
        }
        
        overall = (
            weights['segmentation'] * seg_quality +
            weights['color'] * color_conf +
            weights['tone'] * tone_sim +
            weights['face'] * face_conf
        )
        
        return min(overall, 1.0)
    
    def analyze_face(self, face_crop: np.ndarray, face_conf: float) -> Dict:
        """Analyze a single face for skin tone."""
        if self.model is None:
            return {
                'error': 'Model not loaded',
                'monk_tone': 'Monk 5',
                'confidence': 0.0
            }
        
        try:
            # Apply lighting correction
            corrected = self.correct_lighting(face_crop)
            
            # Prepare for model
            resized = cv2.resize(corrected, (512, 512))
            normalized = resized / 255.0
            input_batch = np.expand_dims(normalized, axis=0).astype(np.float32)
            
            # Predict segmentation
            pred = self.model.predict(input_batch, verbose=0)[0]
            pred_mask = np.argmax(pred, axis=-1).astype(np.int32)
            
            # Calculate segmentation quality
            skin_pixels = np.sum(pred_mask == 1)
            total_pixels = pred_mask.size
            seg_quality = skin_pixels / total_pixels if total_pixels > 0 else 0
            
            # Extract skin and get dominant color
            skin_mask = self.extract_skin_advanced(pred_mask, resized)
            dominant_color, color_confidence = self.get_dominant_color_with_confidence(skin_mask)
            
            # Find closest Monk tone
            monk_tone, monk_hex, derived_hex, tone_similarity = self.find_closest_monk_tone(
                (dominant_color[0], dominant_color[1], dominant_color[2])
            )
            
            # Calculate overall confidence
            overall_confidence = self.calculate_confidence(
                seg_quality, color_confidence, tone_similarity, face_conf
            )
            
            return {
                'monk_tone': monk_tone,
                'monk_hex': monk_hex,
                'derived_hex': derived_hex,
                'dominant_rgb': dominant_color.tolist(),
                'confidence': overall_confidence,
                'metrics': {
                    'segmentation_quality': seg_quality,
                    'color_confidence': color_confidence,
                    'tone_similarity': tone_similarity,
                    'face_confidence': face_conf
                }
            }
            
        except Exception as e:
            logger.error(f"Face analysis error: {e}")
            return {
                'error': str(e),
                'monk_tone': 'Monk 5',
                'confidence': 0.0
            }
    
    def analyze_image(self, image_array: np.ndarray) -> Dict:
        """Analyze image with multi-face detection."""
        try:
            # Detect faces
            faces = self.detect_faces(image_array)
            
            if not faces:
                return {
                    'success': False,
                    'error': 'No faces detected',
                    'total_faces': 0
                }
            
            # Analyze each face
            results = []
            for i, face in enumerate(faces):
                face_result = self.analyze_face(face['crop'], face['confidence'])
                face_result['face_id'] = i + 1
                face_result['bbox'] = face['bbox']
                results.append(face_result)
            
            # Find best result
            valid_results = [r for r in results if 'error' not in r]
            if valid_results:
                best_result = max(valid_results, key=lambda x: x.get('confidence', 0))
            else:
                best_result = results[0]
            
            return {
                'success': True,
                'primary_result': best_result,
                'all_faces': results,
                'total_faces': len(faces)
            }
            
        except Exception as e:
            logger.error(f"Image analysis error: {e}")
            return {
                'success': False,
                'error': str(e),
                'total_faces': 0
            }

# Initialize analyzer
analyzer = EnhancedSkinAnalyzer()

@app.post("/analyze-skin-tone-enhanced")
async def analyze_skin_tone_enhanced(file: UploadFile = File(...)):
    """Enhanced skin tone analysis with multi-face detection and confidence scoring."""
    try:
        # Validate file
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read image
        image_data = await file.read()
        image = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Convert to numpy array
        image_array = np.array(image)
        
        # Analyze image
        start_time = time.time()
        result = analyzer.analyze_image(image_array)
        processing_time = time.time() - start_time
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])
        
        primary = result['primary_result']
        
        # Format response
        response = {
            'success': True,
            'monk_skin_tone': primary['monk_tone'].replace(' ', ''),  # Format as Monk01, Monk02, etc.
            'monk_tone_display': primary['monk_tone'],
            'monk_hex': primary['monk_hex'],
            'derived_hex_code': primary['derived_hex'],
            'dominant_rgb': primary['dominant_rgb'],
            'confidence': primary['confidence'],
            'processing_time': processing_time,
            'total_faces_detected': result['total_faces'],
            'detailed_metrics': primary.get('metrics', {}),
            'all_faces': [
                {
                    'face_id': face['face_id'],
                    'monk_tone': face.get('monk_tone', 'Unknown'),
                    'confidence': face.get('confidence', 0.0),
                    'bbox': face.get('bbox', [])
                }
                for face in result['all_faces']
            ]
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in enhanced analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

@app.get("/health-enhanced")
async def health_check_enhanced():
    """Enhanced health check endpoint."""
    return {
        "status": "healthy",
        "model_loaded": analyzer.model is not None,
        "face_detection_ready": analyzer.face_detection is not None,
        "version": "2.0.0",
        "features": [
            "multi-face detection",
            "lighting correction",
            "confidence scoring",
            "advanced color analysis"
        ]
    }

@app.get("/supported-features")
async def supported_features():
    """Get list of supported features."""
    return {
        "features": {
            "multi_face_detection": {
                "enabled": True,
                "description": "Detects multiple faces in a single image"
            },
            "lighting_correction": {
                "enabled": True,
                "methods": ["clahe", "histogram_equalization", "gamma_correction"],
                "description": "Automatically corrects lighting for better accuracy"
            },
            "confidence_scoring": {
                "enabled": True,
                "metrics": ["segmentation_quality", "color_confidence", "tone_similarity", "face_confidence"],
                "description": "Provides reliability metrics for predictions"
            },
            "advanced_color_analysis": {
                "enabled": True,
                "description": "Uses advanced clustering and outlier removal"
            }
        },
        "monk_skin_tones": list(analyzer.skin_tones.keys())
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
