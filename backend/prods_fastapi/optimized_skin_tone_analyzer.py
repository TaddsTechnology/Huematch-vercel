import cv2
import numpy as np
import mediapipe as mp
from typing import List, Dict, Tuple, Optional
import logging
import asyncio
import concurrent.futures
from functools import lru_cache
import time

logger = logging.getLogger(__name__)

class OptimizedSkinToneAnalyzer:
    def __init__(self):
        """Initialize the optimized skin tone analyzer."""
        self.mp_face_detection = mp.solutions.face_detection
        # Pre-initialize MediaPipe to avoid initialization overhead
        self._face_detector = None
        
    @property
    def face_detector(self):
        """Lazy initialization of face detector to avoid overhead."""
        if self._face_detector is None:
            self._face_detector = self.mp_face_detection.FaceDetection(
                model_selection=1, min_detection_confidence=0.6
            )
        return self._face_detector
    
    @lru_cache(maxsize=128)
    def _cached_monk_tone_distance(self, r: int, g: int, b: int, monk_hex: str) -> float:
        """Cache distance calculations for monk tones."""
        monk_rgb = np.array([
            int(monk_hex[1:3], 16),
            int(monk_hex[3:5], 16), 
            int(monk_hex[5:7], 16)
        ])
        rgb_color = np.array([r, g, b])
        return float(np.sqrt(np.sum((rgb_color - monk_rgb) ** 2)))
    
    def detect_face_fast(self, image: np.ndarray) -> Optional[np.ndarray]:
        """Fast face detection with minimal processing."""
        try:
            # Resize image for faster processing if too large
            h, w = image.shape[:2]
            if max(h, w) > 800:
                scale = 800 / max(h, w)
                new_w, new_h = int(w * scale), int(h * scale)
                resized_image = cv2.resize(image, (new_w, new_h))
            else:
                resized_image = image
                scale = 1.0
            
            # Convert BGR to RGB for MediaPipe
            rgb_image = cv2.cvtColor(resized_image, cv2.COLOR_BGR2RGB)
            results = self.face_detector.process(rgb_image)
            
            if results.detections:
                detection = results.detections[0]  # Use first face
                bboxC = detection.location_data.relative_bounding_box
                rh, rw = resized_image.shape[:2]
                
                # Convert back to original image coordinates
                x = int((bboxC.xmin * rw) / scale)
                y = int((bboxC.ymin * rh) / scale)
                w_box = int((bboxC.width * rw) / scale)
                h_box = int((bboxC.height * rh) / scale)
                
                # Add minimal padding
                padding = 0.05
                x = max(0, int(x - w_box * padding))
                y = max(0, int(y - h_box * padding))
                w_box = min(w - x, int(w_box * (1 + 2 * padding)))
                h_box = min(h - y, int(h_box * (1 + 2 * padding)))
                
                face_region = image[y:y+h_box, x:x+w_box]
                return face_region if face_region.size > 2500 else None  # Minimum size check
                
        except Exception as e:
            logger.warning(f"Fast face detection failed: {e}")
        return None
    
    def extract_skin_color_fast(self, face_image: np.ndarray) -> np.ndarray:
        """Fast skin color extraction using simplified approach."""
        try:
            h, w = face_image.shape[:2]
            
            # Define key skin regions (fewer regions for speed)
            regions = [
                face_image[int(0.15*h):int(0.35*h), int(0.2*w):int(0.8*w)],  # Forehead
                face_image[int(0.4*h):int(0.6*h), int(0.15*w):int(0.45*w)],   # Left cheek
                face_image[int(0.4*h):int(0.6*h), int(0.55*w):int(0.85*w)],   # Right cheek
            ]
            
            all_colors = []
            for region in regions:
                if region.size > 100:
                    # Simple average without complex masking
                    region_color = np.mean(region.reshape(-1, 3), axis=0)
                    all_colors.append(region_color)
            
            if all_colors:
                return np.mean(all_colors, axis=0)
            else:
                # Fallback to center region
                center_region = face_image[h//4:3*h//4, w//4:3*w//4]
                return np.mean(center_region.reshape(-1, 3), axis=0)
                
        except Exception as e:
            logger.warning(f"Fast skin extraction failed: {e}")
            return np.array([200, 180, 160])  # Default color
    
    def find_closest_monk_tone_fast(self, rgb_color: np.ndarray, monk_tones: Dict[str, str]) -> Tuple[str, float]:
        """Fast monk tone matching with caching."""
        try:
            r, g, b = int(rgb_color[0]), int(rgb_color[1]), int(rgb_color[2])
            min_distance = float('inf')
            closest_monk = "Monk 2"
            
            for monk_name, hex_color in monk_tones.items():
                distance = self._cached_monk_tone_distance(r, g, b, hex_color)
                if distance < min_distance:
                    min_distance = distance
                    closest_monk = monk_name
            
            return closest_monk, min_distance
            
        except Exception as e:
            logger.warning(f"Fast monk tone matching failed: {e}")
            return "Monk 4", 50.0
    
    def calculate_simple_confidence(self, distance: float, face_detected: bool) -> float:
        """Simple confidence calculation."""
        base_confidence = 0.8 if face_detected else 0.3
        distance_penalty = min(0.4, distance / 100)
        return max(0.1, base_confidence - distance_penalty)
    
    def analyze_skin_tone_fast(self, image: np.ndarray, monk_tones: Dict[str, str]) -> Dict:
        """Fast skin tone analysis with minimal processing."""
        start_time = time.time()
        
        try:
            # Step 1: Fast face detection
            face_image = self.detect_face_fast(image)
            face_detected = face_image is not None
            
            if face_image is None:
                # Fallback to center crop
                h, w = image.shape[:2]
                face_image = image[h//4:3*h//4, w//4:3*w//4]
            
            # Step 2: Fast skin color extraction
            avg_color = self.extract_skin_color_fast(face_image)
            
            # Step 3: Fast monk tone matching
            closest_monk, distance = self.find_closest_monk_tone_fast(avg_color, monk_tones)
            
            # Step 4: Simple confidence calculation
            confidence = self.calculate_simple_confidence(distance, face_detected)
            
            # Format response
            monk_number = closest_monk.split()[1]
            monk_id = f"Monk{monk_number.zfill(2)}"
            
            derived_hex = '#{:02x}{:02x}{:02x}'.format(
                int(avg_color[0]), int(avg_color[1]), int(avg_color[2])
            )
            
            processing_time = time.time() - start_time
            logger.info(f"Fast analysis completed in {processing_time:.2f}s: {monk_id}")
            
            return {
                'monk_skin_tone': monk_id,
                'monk_tone_display': closest_monk,
                'monk_hex': monk_tones[closest_monk],
                'derived_hex_code': derived_hex,
                'dominant_rgb': avg_color.astype(int).tolist(),
                'confidence': round(confidence, 2),
                'success': True,
                'analysis_method': 'optimized_fast',
                'face_detected': face_detected,
                'processing_time': round(processing_time, 3)
            }
            
        except Exception as e:
            logger.error(f"Fast skin tone analysis failed: {e}")
            return {
                'monk_skin_tone': 'Monk04',
                'monk_tone_display': 'Monk 4',
                'monk_hex': monk_tones.get('Monk 4', '#eadaba'),
                'derived_hex_code': '#eadaba',
                'dominant_rgb': [234, 218, 186],
                'confidence': 0.3,
                'success': False,
                'error': str(e),
                'face_detected': False,
                'processing_time': round(time.time() - start_time, 3)
            }


class AsyncOptimizedAnalyzer:
    """Async wrapper for skin tone analysis with background processing."""
    
    def __init__(self):
        self.analyzer = OptimizedSkinToneAnalyzer()
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
    
    async def analyze_skin_tone_async(self, image: np.ndarray, monk_tones: Dict[str, str]) -> Dict:
        """Async skin tone analysis."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, 
            self.analyzer.analyze_skin_tone_fast, 
            image, 
            monk_tones
        )
    
    async def upload_to_cloudinary_async(self, image_data: bytes, public_id: str, cloudinary_service) -> Dict:
        """Async cloudinary upload."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            cloudinary_service.upload_image,
            image_data,
            public_id
        )
