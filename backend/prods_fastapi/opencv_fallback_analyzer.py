import cv2
import numpy as np
import logging
from typing import List, Dict, Tuple, Optional
import colorsys

logger = logging.getLogger(__name__)

class OpenCVFallbackAnalyzer:
    """
    Fallback skin tone analyzer using only OpenCV for face detection.
    This works when MediaPipe or other heavy dependencies are not available.
    """
    
    def __init__(self):
        """Initialize the fallback analyzer with OpenCV Haar cascades."""
        try:
            # Load Haar cascade for face detection (comes with OpenCV)
            self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
            self.profile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_profileface.xml')
            self.available = True
            logger.info("OpenCV fallback analyzer initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenCV cascades: {e}")
            self.available = False
    
    def detect_face_opencv(self, image: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
        """Detect face using OpenCV Haar cascades."""
        if not self.available:
            return None
            
        try:
            # Convert to grayscale for cascade detection
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            
            # Detect faces with different scale factors for better results
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(50, 50),
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            
            # If no frontal face found, try profile detection
            if len(faces) == 0:
                faces = self.profile_cascade.detectMultiScale(
                    gray,
                    scaleFactor=1.1,
                    minNeighbors=5,
                    minSize=(50, 50)
                )
            
            if len(faces) > 0:
                # Use the largest face found
                face = max(faces, key=lambda f: f[2] * f[3])
                x, y, w, h = face
                
                # Add padding for better skin region
                padding = 0.15
                x = max(0, int(x - w * padding))
                y = max(0, int(y - h * padding))
                w = min(image.shape[1] - x, int(w * (1 + 2 * padding)))
                h = min(image.shape[0] - y, int(h * (1 + 2 * padding)))
                
                return (x, y, w, h)
                
        except Exception as e:
            logger.warning(f"OpenCV face detection failed: {e}")
        
        return None
    
    def detect_face_center_fallback(self, image: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
        """Fallback method that assumes face is in center of image."""
        try:
            h, w = image.shape[:2]
            
            # Assume face is in the center 60% of the image
            face_w = int(w * 0.6)
            face_h = int(h * 0.6)
            x = int((w - face_w) / 2)
            y = int((h - face_h) / 2)
            
            return (x, y, face_w, face_h)
        except Exception as e:
            logger.warning(f"Center fallback detection failed: {e}")
            return None
    
    def detect_face(self, image: np.ndarray) -> Optional[np.ndarray]:
        """Detect face using multiple fallback methods."""
        # Try OpenCV cascade first
        bbox = self.detect_face_opencv(image)
        
        # Fallback to center detection if cascade fails
        if bbox is None:
            logger.info("OpenCV cascade detection failed, using center fallback")
            bbox = self.detect_face_center_fallback(image)
        
        if bbox is None:
            logger.warning("All face detection methods failed")
            return None
        
        x, y, w, h = bbox
        face_region = image[y:y+h, x:x+w]
        
        # Ensure minimum face size
        if face_region.shape[0] < 30 or face_region.shape[1] < 30:
            logger.warning("Detected face region too small")
            return None
        
        return face_region
    
    def apply_lighting_correction(self, image: np.ndarray) -> np.ndarray:
        """Apply lighting correction optimized for all skin tones."""
        try:
            # Convert to LAB color space for better lighting correction
            lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
            l, a, b = cv2.split(lab)
            
            # Apply CLAHE to L channel with optimized parameters
            clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
            l_corrected = clahe.apply(l)
            
            # Merge back
            lab_corrected = cv2.merge([l_corrected, a, b])
            rgb_corrected = cv2.cvtColor(lab_corrected, cv2.COLOR_LAB2RGB)
            
            # Adaptive gamma correction based on image brightness
            mean_brightness = np.mean(rgb_corrected)
            
            if mean_brightness < 80:  # Very dark
                gamma = 1.3
            elif mean_brightness < 120:  # Dark
                gamma = 1.1
            elif mean_brightness < 180:  # Medium
                gamma = 1.0
            else:  # Bright
                gamma = 0.9
            
            if gamma != 1.0:
                rgb_corrected = np.power(rgb_corrected / 255.0, gamma) * 255.0
                rgb_corrected = np.clip(rgb_corrected, 0, 255).astype(np.uint8)
            
            return rgb_corrected
            
        except Exception as e:
            logger.warning(f"Lighting correction failed: {e}")
            return image
    
    def extract_skin_regions(self, face_image: np.ndarray) -> List[np.ndarray]:
        """Extract multiple skin regions from face with improved skin filtering."""
        h, w = face_image.shape[:2]
        
        # Define skin regions optimized for different face sizes
        regions = {
            'forehead': (int(0.25*w), int(0.1*h), int(0.5*w), int(0.2*h)),
            'left_cheek': (int(0.15*w), int(0.3*h), int(0.3*w), int(0.3*h)),
            'right_cheek': (int(0.55*w), int(0.3*h), int(0.3*w), int(0.3*h)),
            'nose_area': (int(0.4*w), int(0.25*h), int(0.2*w), int(0.25*h)),
            'chin': (int(0.3*w), int(0.65*h), int(0.4*w), int(0.2*h))
        }
        
        region_colors = []
        
        for region_name, (x, y, rw, rh) in regions.items():
            try:
                if x + rw <= w and y + rh <= h and x >= 0 and y >= 0:
                    region = face_image[y:y+rh, x:x+rw]
                    
                    if region.size > 50:  # Ensure enough pixels
                        # Improved skin color filtering in YCbCr space - optimized for light skin
                        region_ycbcr = cv2.cvtColor(region, cv2.COLOR_RGB2YCrCb)
                        
                        # Enhanced skin color range specifically for light/fair skin tones
                        lower_skin = np.array([0, 125, 70])  # More inclusive for light skin
                        upper_skin = np.array([255, 180, 135])  # Extended range for fair tones
                        
                        skin_mask = cv2.inRange(region_ycbcr, lower_skin, upper_skin)
                        
                        # Improved RGB filtering for light skin detection
                        r, g, b = cv2.split(region)
                        
                        # More inclusive RGB ratios for light skin
                        rgb_mask = (
                            (r >= g) & (g >= b) &  # Basic skin tone ratios
                            (r > 100) & (g > 80) & (b > 60) &  # Light skin thresholds
                            (r < 255) & (g < 255) & (b < 255)  # Avoid overexposure
                        )
                        
                        # For very light skin, also include pixels with high overall brightness
                        brightness_mask = (r + g + b) > 450  # Very bright pixels
                        light_skin_mask = rgb_mask | brightness_mask
                        
                        # Combine masks
                        combined_mask = cv2.bitwise_and(skin_mask, light_skin_mask.astype(np.uint8) * 255)
                        
                        if np.sum(combined_mask > 0) > 30:  # Enough skin pixels
                            skin_pixels = region[combined_mask > 0]
                            if len(skin_pixels) > 10:
                                region_color = np.mean(skin_pixels, axis=0)
                                region_colors.append(region_color)
                                logger.debug(f"Extracted color from {region_name}: {region_color}")
                            
            except Exception as e:
                logger.warning(f"Failed to process region {region_name}: {e}")
                continue
        
        return region_colors
    
    def cluster_skin_colors(self, region_colors: List[np.ndarray]) -> np.ndarray:
        """Find dominant skin color using weighted averaging."""
        if not region_colors:
            return np.array([200, 180, 160])  # Default neutral skin tone
        
        try:
            # Convert to numpy array
            colors_array = np.array(region_colors)
            
            # Calculate weights based on color consistency
            weights = []
            for color in region_colors:
                # Give higher weight to colors that are closer to the median
                distances = [np.linalg.norm(color - other_color) for other_color in region_colors]
                weight = 1.0 / (1.0 + np.mean(distances))
                weights.append(weight)
            
            weights = np.array(weights)
            weights = weights / np.sum(weights)  # Normalize
            
            # Weighted average
            dominant_color = np.average(colors_array, axis=0, weights=weights)
            
            return dominant_color
            
        except Exception as e:
            logger.warning(f"Color clustering failed: {e}")
            # Simple average fallback
            return np.mean(region_colors, axis=0)
    
    def calculate_confidence_score(self, face_image: np.ndarray, final_color: np.ndarray, 
                                 region_colors: List[np.ndarray]) -> float:
        """Calculate confidence score for the skin tone detection."""
        try:
            confidence_factors = []
            
            # Factor 1: Number of regions successfully analyzed
            region_factor = min(1.0, len(region_colors) / 3.0)  # Expect at least 3 regions
            confidence_factors.append(region_factor * 0.3)
            
            # Factor 2: Color consistency across regions
            if len(region_colors) > 1:
                color_std = np.std([np.mean(color) for color in region_colors])
                consistency_score = max(0, 1 - (color_std / 40))
                confidence_factors.append(consistency_score * 0.25)
            
            # Factor 3: Image quality (sharpness)
            gray = cv2.cvtColor(face_image, cv2.COLOR_RGB2GRAY)
            sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
            sharpness_score = min(1.0, sharpness / 300)
            confidence_factors.append(sharpness_score * 0.2)
            
            # Factor 4: Color reasonableness (skin-like colors)
            brightness = np.mean(final_color)
            if 60 <= brightness <= 240:  # Reasonable skin tone range
                brightness_score = 1.0
            else:
                brightness_score = max(0, 1 - abs(brightness - 150) / 100)
            confidence_factors.append(brightness_score * 0.15)
            
            # Factor 5: Base detection confidence
            confidence_factors.append(0.1)  # Base score for successful detection
            
            total_confidence = sum(confidence_factors)
            return min(1.0, total_confidence)
            
        except Exception as e:
            logger.warning(f"Confidence calculation failed: {e}")
            return 0.4  # Default moderate confidence
    
    def find_closest_monk_tone(self, rgb_color: np.ndarray, monk_tones: Dict[str, str]) -> Tuple[str, float]:
        """Find the closest Monk skin tone using color space analysis."""
        try:
            min_distance = float('inf')
            closest_monk = "Monk 4"  # Default middle tone
            
            # Convert to LAB for better perceptual distance
            lab_color = cv2.cvtColor(np.uint8([[rgb_color]]), cv2.COLOR_RGB2LAB)[0][0]
            
            for monk_name, hex_color in monk_tones.items():
                try:
                    # Convert hex to RGB
                    hex_clean = hex_color.lstrip('#')
                    monk_rgb = np.array([
                        int(hex_clean[0:2], 16),
                        int(hex_clean[2:4], 16),
                        int(hex_clean[4:6], 16)
                    ])
                    
                    # Convert to LAB
                    monk_lab = cv2.cvtColor(np.uint8([[monk_rgb]]), cv2.COLOR_RGB2LAB)[0][0]
                    
                    # Calculate perceptual distance in LAB space
                    lab_distance = np.sqrt(np.sum((lab_color - monk_lab) ** 2))
                    
                    # Additional RGB distance for comparison
                    rgb_distance = np.sqrt(np.sum((rgb_color - monk_rgb) ** 2))
                    
                    # Weighted combination
                    combined_distance = lab_distance * 0.7 + rgb_distance * 0.3
                    
                    if combined_distance < min_distance:
                        min_distance = combined_distance
                        closest_monk = monk_name
                        
                except Exception as color_e:
                    logger.warning(f"Error processing monk tone {monk_name}: {color_e}")
                    continue
            
            return closest_monk, min_distance
            
        except Exception as e:
            logger.warning(f"Monk tone matching failed: {e}")
            return "Monk 4", 50.0
    
    def analyze_skin_tone(self, image: np.ndarray, monk_tones: Dict[str, str]) -> Dict:
        """Main method to analyze skin tone using OpenCV-only approach."""
        try:
            logger.info("Starting OpenCV fallback skin tone analysis...")
            
            # Step 1: Detect face
            face_image = self.detect_face(image)
            if face_image is None:
                raise ValueError("No face detected in the image")
            
            logger.info(f"Face detected with size: {face_image.shape}")
            
            # Step 2: Apply lighting correction
            corrected_face = self.apply_lighting_correction(face_image)
            
            # Step 3: Extract skin regions
            region_colors = self.extract_skin_regions(corrected_face)
            logger.info(f"Extracted {len(region_colors)} skin regions")
            
            if not region_colors:
                # Fallback to center region analysis
                h, w = corrected_face.shape[:2]
                center_region = corrected_face[h//4:3*h//4, w//4:3*w//4]
                avg_color = np.mean(center_region.reshape(-1, 3), axis=0)
                logger.info("Using center region fallback")
            else:
                # Step 4: Find dominant color
                avg_color = self.cluster_skin_colors(region_colors)
            
            logger.info(f"Dominant color: {avg_color}")
            
            # Step 5: Find closest Monk tone
            closest_monk, min_distance = self.find_closest_monk_tone(avg_color, monk_tones)
            
            # Step 6: Calculate confidence
            confidence = self.calculate_confidence_score(face_image, avg_color, region_colors)
            
            # Format response
            monk_number = closest_monk.split()[1] if ' ' in closest_monk else closest_monk[-1]
            monk_id = f"Monk{monk_number.zfill(2)}"
            
            # Convert RGB to hex
            derived_hex = '#{:02x}{:02x}{:02x}'.format(
                int(avg_color[0]), int(avg_color[1]), int(avg_color[2])
            )
            
            logger.info(f"Analysis result: {monk_id}, confidence: {confidence:.2f}")
            
            return {
                'monk_skin_tone': monk_id,
                'monk_tone_display': closest_monk,
                'monk_hex': monk_tones.get(closest_monk, '#eadaba'),
                'derived_hex_code': derived_hex,
                'dominant_rgb': avg_color.astype(int).tolist(),
                'confidence': round(confidence, 2),
                'success': True,
                'analysis_method': 'opencv_fallback',
                'regions_analyzed': len(region_colors),
                'face_detected': True
            }
            
        except Exception as e:
            logger.error(f"OpenCV fallback analysis failed: {e}")
            return {
                'monk_skin_tone': 'Monk04',
                'monk_tone_display': 'Monk 4',
                'monk_hex': monk_tones.get('Monk 4', '#eadaba'),
                'derived_hex_code': '#eadaba',
                'dominant_rgb': [234, 218, 186],
                'confidence': 0.3,
                'success': False,
                'error': str(e),
                'analysis_method': 'opencv_fallback',
                'face_detected': False
            }
