import gradio as gr
import tensorflow as tf
from sklearn.cluster import KMeans
import numpy as np
import cv2
from webcolors import hex_to_rgb, rgb_to_hex
from scipy.spatial import KDTree
from collections import Counter
import mediapipe as mp
import logging
from typing import List, Dict, Tuple, Optional
import time
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedSkinAnalyzer:
    def __init__(self, model_path: str = "model.h5"):
        """Initialize the enhanced skin analyzer with multi-face detection and lighting correction."""
        self.model = self._load_model(model_path)
        self.mp_face_detection = mp.solutions.face_detection
        self.mp_drawing = mp.solutions.drawing_utils
        self.face_detection = self.mp_face_detection.FaceDetection(
            model_selection=0, min_detection_confidence=0.5
        )
        
        self.classes = [
            "background", "skin", "left eyebrow", "right eyebrow",
            "left eye", "right eye", "nose", "upper lip", "inner mouth",
            "lower lip", "hair"
        ]
        
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
    
    def detect_faces(self, image: np.ndarray) -> List[Dict]:
        """Detect faces in the image using MediaPipe."""
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.face_detection.process(rgb_image)
        
        faces = []
        if results.detections:
            for detection in results.detections:
                bbox = detection.location_data.relative_bounding_box
                h, w, _ = image.shape
                
                # Convert relative coordinates to absolute
                x = int(bbox.xmin * w)
                y = int(bbox.ymin * h)
                width = int(bbox.width * w)
                height = int(bbox.height * h)
                
                # Add padding for better skin detection
                padding = 20
                x = max(0, x - padding)
                y = max(0, y - padding)
                width = min(w - x, width + 2 * padding)
                height = min(h - y, height + 2 * padding)
                
                faces.append({
                    'bbox': (x, y, width, height),
                    'confidence': detection.score[0],
                    'crop': image[y:y+height, x:x+width]
                })
        
        return faces
    
    def correct_lighting(self, image: np.ndarray, method: str = 'clahe') -> np.ndarray:
        """Apply lighting correction to improve skin tone detection."""
        if method == 'clahe':
            # Convert to LAB color space for better lighting correction
            lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
            l, a, b = cv2.split(lab)
            
            # Apply CLAHE to L channel
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            
            # Merge channels and convert back to RGB
            lab = cv2.merge([l, a, b])
            corrected = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
            
        elif method == 'histogram_equalization':
            # Apply histogram equalization to each channel
            corrected = np.zeros_like(image)
            for i in range(3):
                corrected[:, :, i] = cv2.equalizeHist(image[:, :, i])
                
        elif method == 'gamma_correction':
            # Apply gamma correction
            gamma = 1.2
            corrected = np.power(image / 255.0, gamma) * 255.0
            corrected = corrected.astype(np.uint8)
            
        else:
            corrected = image
            
        return corrected
    
    def face_skin_extract(self, pred: np.ndarray, image_x: np.ndarray) -> np.ndarray:
        """Extract skin pixels from segmentation prediction."""
        output = np.zeros_like(image_x, dtype=np.uint8)
        mask = (pred == 1)  # Skin class
        output[mask] = image_x[mask]
        return output
    
    def extract_dominant_color_advanced(self, img: np.ndarray) -> Tuple[np.ndarray, float]:
        """Extract dominant color with confidence score."""
        # Remove black pixels (background)
        mask = ~np.all(img == [0, 0, 0], axis=-1)
        non_black_pixels = img[mask]
        
        if len(non_black_pixels) == 0:
            logger.warning("No skin pixels found")
            return np.array([200, 150, 120]), 0.0
        
        # Remove outliers (very dark or very bright pixels)
        brightness = np.mean(non_black_pixels, axis=1)
        q25, q75 = np.percentile(brightness, [25, 75])
        iqr = q75 - q25
        lower_bound = q25 - 1.5 * iqr
        upper_bound = q75 + 1.5 * iqr
        
        valid_mask = (brightness >= lower_bound) & (brightness <= upper_bound)
        filtered_pixels = non_black_pixels[valid_mask]
        
        if len(filtered_pixels) == 0:
            filtered_pixels = non_black_pixels
        
        # Use K-means clustering
        n_clusters = min(5, len(filtered_pixels))
        kmeans = KMeans(n_clusters=n_clusters, n_init=10, random_state=42)
        kmeans.fit(filtered_pixels)
        
        # Get cluster information
        labels = kmeans.labels_
        centers = kmeans.cluster_centers_
        
        # Find the most representative cluster (largest cluster)
        label_counts = Counter(labels)
        dominant_label = label_counts.most_common(1)[0][0]
        dominant_color = centers[dominant_label]
        
        # Calculate confidence based on cluster coherence
        dominant_pixels = filtered_pixels[labels == dominant_label]
        if len(dominant_pixels) > 1:
            std_dev = np.std(dominant_pixels, axis=0)
            confidence = 1.0 / (1.0 + np.mean(std_dev) / 50.0)  # Normalize std dev
        else:
            confidence = 0.5
        
        # Additional confidence factors
        cluster_ratio = len(dominant_pixels) / len(filtered_pixels)
        confidence *= cluster_ratio
        
        return dominant_color, min(confidence, 1.0)
    
    def find_closest_skin_tone(self, rgb_tuple: Tuple[int, int, int]) -> Tuple[str, str, str, float]:
        """Find the closest Monk skin tone with distance score."""
        rgb_values = []
        names = []
        
        for name, hex_color in self.skin_tones.items():
            names.append(name)
            rgb_values.append(hex_to_rgb(hex_color))
        
        # Use KDTree for efficient nearest neighbor search
        tree = KDTree(rgb_values)
        distance, index = tree.query(rgb_tuple)
        
        matched_name = names[index]
        monk_hex = self.skin_tones[matched_name]
        derived_hex = rgb_to_hex((int(rgb_tuple[0]), int(rgb_tuple[1]), int(rgb_tuple[2])))
        
        # Calculate similarity score (inverse of distance)
        max_distance = np.sqrt(3 * 255**2)  # Maximum possible RGB distance
        similarity = 1.0 - (distance / max_distance)
        
        return matched_name, monk_hex, derived_hex, similarity
    
    def calculate_overall_confidence(self, 
                                   segmentation_quality: float,
                                   color_confidence: float,
                                   tone_similarity: float,
                                   face_confidence: float) -> float:
        """Calculate overall confidence score."""
        weights = {
            'segmentation': 0.3,
            'color': 0.3,
            'tone': 0.2,
            'face': 0.2
        }
        
        overall = (
            weights['segmentation'] * segmentation_quality +
            weights['color'] * color_confidence +
            weights['tone'] * tone_similarity +
            weights['face'] * face_confidence
        )
        
        return min(overall, 1.0)
    
    def process_single_face(self, face_crop: np.ndarray, face_confidence: float) -> Dict:
        """Process a single face crop for skin tone analysis."""
        if self.model is None:
            return {
                'error': 'Model not loaded',
                'monk_tone': random.choice(list(self.skin_tones.keys())),
                'confidence': 0.0
            }
        
        try:
            # Apply lighting correction
            corrected_face = self.correct_lighting(face_crop, method='clahe')
            
            # Resize for model input
            resized_face = cv2.resize(corrected_face, (512, 512))
            normalized_face = resized_face / 255.0
            input_batch = np.expand_dims(normalized_face, axis=0).astype(np.float32)
            
            # Make prediction
            pred = self.model.predict(input_batch, verbose=0)[0]
            pred_mask = np.argmax(pred, axis=-1).astype(np.int32)
            
            # Calculate segmentation quality
            skin_pixels = np.sum(pred_mask == 1)
            total_pixels = pred_mask.size
            segmentation_quality = skin_pixels / total_pixels
            
            # Extract skin
            skin_mask = self.face_skin_extract(pred_mask, resized_face)
            
            # Extract dominant color with confidence
            dominant_color, color_confidence = self.extract_dominant_color_advanced(skin_mask)
            
            # Find closest skin tone
            monk_tone, monk_hex, derived_hex, tone_similarity = self.find_closest_skin_tone(
                (dominant_color[0], dominant_color[1], dominant_color[2])
            )
            
            # Calculate overall confidence
            overall_confidence = self.calculate_overall_confidence(
                segmentation_quality, color_confidence, tone_similarity, face_confidence
            )
            
            return {
                'monk_tone': monk_tone,
                'monk_hex': monk_hex,
                'derived_hex': derived_hex,
                'dominant_rgb': dominant_color.tolist(),
                'confidence': overall_confidence,
                'segmentation_quality': segmentation_quality,
                'color_confidence': color_confidence,
                'tone_similarity': tone_similarity,
                'face_confidence': face_confidence,
                'skin_mask': skin_mask
            }
            
        except Exception as e:
            logger.error(f"Error processing face: {e}")
            return {
                'error': str(e),
                'monk_tone': random.choice(list(self.skin_tones.keys())),
                'confidence': 0.0
            }
    
    def analyze_image(self, image_path: str) -> Dict:
        """Analyze image for skin tone with multi-face detection."""
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                return {'error': 'Failed to load image'}
            
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Detect faces
            faces = self.detect_faces(image)
            
            if not faces:
                return {'error': 'No faces detected in the image'}
            
            # Process each face
            results = []
            for i, face in enumerate(faces):
                face_result = self.process_single_face(face['crop'], face['confidence'])
                face_result['face_id'] = i + 1
                face_result['bbox'] = face['bbox']
                results.append(face_result)
            
            # Find the best result (highest confidence)
            best_result = max(results, key=lambda x: x.get('confidence', 0))
            
            return {
                'primary_result': best_result,
                'all_faces': results,
                'total_faces': len(faces),
                'processing_time': time.time()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            return {'error': str(e)}

# Global analyzer instance
analyzer = EnhancedSkinAnalyzer()

def process_image_enhanced(image_path: str):
    """Enhanced image processing function for Gradio interface."""
    if image_path is None:
        return "No image provided", "#f7ead0", "#f7ead0", "0.0", "No faces detected"
    
    start_time = time.time()
    result = analyzer.analyze_image(image_path)
    processing_time = time.time() - start_time
    
    if 'error' in result:
        return result['error'], "#f7ead0", "#f7ead0", "0.0", "Error occurred"
    
    primary = result['primary_result']
    
    # Format confidence score
    confidence_text = f"Confidence: {primary['confidence']:.2f}"
    
    # Format detailed results
    details = f"""
    🎯 **Analysis Results**
    
    👥 **Faces Detected:** {result['total_faces']}
    📊 **Overall Confidence:** {primary['confidence']:.2f}
    🎨 **Dominant RGB:** {primary['dominant_rgb']}
    
    📈 **Detailed Metrics:**
    • Segmentation Quality: {primary.get('segmentation_quality', 0):.2f}
    • Color Confidence: {primary.get('color_confidence', 0):.2f}
    • Tone Similarity: {primary.get('tone_similarity', 0):.2f}
    • Face Detection: {primary.get('face_confidence', 0):.2f}
    
    ⏱️ **Processing Time:** {processing_time:.2f}s
    """
    
    return (
        primary['monk_tone'],
        primary['derived_hex'],
        primary['monk_hex'],
        confidence_text,
        details
    )

# Gradio interface
def create_enhanced_interface():
    """Create enhanced Gradio interface."""
    with gr.Blocks(title="Enhanced Skin Tone Analyzer") as interface:
        gr.Markdown("""
        # 🎨 Enhanced Skin Tone Analyzer
        
        **Features:**
        - 👥 Multi-face detection
        - 💡 Automatic lighting correction
        - 📊 Confidence scoring
        - 🎯 Improved accuracy
        """)
        
        with gr.Row():
            with gr.Column():
                image_input = gr.Image(type="filepath", label="Upload Face Image")
                analyze_btn = gr.Button("🔍 Analyze Skin Tone", variant="primary")
                
            with gr.Column():
                monk_tone_output = gr.Label(label="🏷️ Monk Skin Tone")
                derived_color_output = gr.ColorPicker(label="🎨 Derived Color")
                monk_color_output = gr.ColorPicker(label="📋 Closest Monk Color")
                confidence_output = gr.Textbox(label="📊 Confidence Score")
                details_output = gr.Markdown(label="📈 Detailed Analysis")
        
        analyze_btn.click(
            fn=process_image_enhanced,
            inputs=[image_input],
            outputs=[monk_tone_output, derived_color_output, monk_color_output, confidence_output, details_output]
        )
        
        gr.Markdown("""
        ---
        ### 📝 How it works:
        1. **Face Detection**: Automatically detects multiple faces in the image
        2. **Lighting Correction**: Applies CLAHE correction for better color accuracy
        3. **Segmentation**: Uses trained model to identify skin pixels
        4. **Color Analysis**: Advanced clustering to find dominant skin tone
        5. **Confidence Scoring**: Provides reliability metrics for the prediction
        """)
    
    return interface

if __name__ == "__main__":
    interface = create_enhanced_interface()
    interface.launch(share=True)
