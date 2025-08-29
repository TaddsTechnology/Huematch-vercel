#!/usr/bin/env python3
"""
Improved Light Skin Tone Analyzer

This module provides enhanced skin tone analysis specifically optimized for detecting
very light and fair skin tones, addressing the issue where Monk 01-02 tones were
incorrectly classified as Monk 05.

Key improvements:
1. Better brightness-based preprocessing for very light skin
2. Enhanced skin detection masks for fair complexions
3. Improved ITA (Individual Typology Angle) classification
4. Multi-method validation for light skin tones
5. Better color space analysis for pale/fair skin detection
"""

import cv2
import numpy as np
import colorsys
import logging
from typing import Dict, List, Tuple, Optional, Any
from webcolors import hex_to_rgb, rgb_to_hex
import json

logger = logging.getLogger(__name__)

class ImprovedLightSkinAnalyzer:
    def __init__(self):
        """Initialize the improved light skin tone analyzer."""
        self.light_skin_thresholds = {
            'very_light_rgb_min': 200,  # Very light skin usually has RGB values above 200
            'light_rgb_min': 180,       # Light skin usually has RGB values above 180
            'brightness_threshold': 220, # Threshold for very bright/fair skin
        }
        
        # Enhanced Monk tone references with better light skin representation
        self.enhanced_monk_tones = {
            'Monk 1': {'hex': '#f6ede4', 'rgb': (246, 237, 228), 'ita_min': 55},
            'Monk 2': {'hex': '#f3e7db', 'rgb': (243, 231, 219), 'ita_min': 41},
            'Monk 3': {'hex': '#f7ead0', 'rgb': (247, 234, 208), 'ita_min': 28},
            'Monk 4': {'hex': '#eadaba', 'rgb': (234, 218, 186), 'ita_min': 10},
            'Monk 5': {'hex': '#d7bd96', 'rgb': (215, 189, 150), 'ita_min': -30},
        }
    
    def preprocess_for_light_skin(self, image: np.ndarray) -> np.ndarray:
        """Enhanced preprocessing specifically for light skin detection."""
        try:
            # Convert to LAB color space for better light skin processing
            lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
            l, a, b = cv2.split(lab)
            
            # Calculate average brightness
            avg_brightness = np.mean(l)
            
            # For very bright images (likely containing light skin), use minimal processing
            if avg_brightness > 180:
                # Very gentle CLAHE for light skin to preserve subtle variations
                clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
                l_enhanced = clahe.apply(l)
                
                # Minimal gamma correction to preserve light tones
                gamma = 0.98  # Slightly darken overexposed areas
                l_gamma = np.power(l_enhanced.astype(np.float32) / 255.0, gamma) * 255.0
                l_final = np.clip(l_gamma, 0, 255).astype(np.uint8)
            else:
                # Standard processing for darker images
                clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
                l_final = clahe.apply(l)
            
            # Merge back and convert to RGB
            lab_enhanced = cv2.merge([l_final, a, b])
            rgb_enhanced = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2RGB)
            
            return rgb_enhanced
            
        except Exception as e:
            logger.warning(f"Light skin preprocessing failed: {e}")
            return image
    
    def extract_light_skin_regions(self, face_image: np.ndarray) -> List[np.ndarray]:
        """Extract skin regions with enhanced detection for light skin tones."""
        h, w = face_image.shape[:2]
        region_colors = []
        
        # Define skin regions optimized for light skin detection
        regions = {
            'forehead': (int(0.25*w), int(0.15*h), int(0.5*w), int(0.2*h)),
            'left_cheek': (int(0.15*w), int(0.35*h), int(0.3*w), int(0.25*h)),
            'right_cheek': (int(0.55*w), int(0.35*h), int(0.3*w), int(0.25*h)),
            'nose_bridge': (int(0.42*w), int(0.3*h), int(0.16*w), int(0.25*h)),
            'chin': (int(0.35*w), int(0.65*h), int(0.3*w), int(0.2*h))
        }
        
        for region_name, (x, y, rw, rh) in regions.items():
            if x + rw <= w and y + rh <= h and x >= 0 and y >= 0:
                region = face_image[y:y+rh, x:x+rw]
                
                if region.size > 50:  # Ensure enough pixels
                    # Enhanced skin detection for light tones
                    region_colors_found = self.detect_light_skin_pixels(region)
                    if len(region_colors_found) > 0:
                        region_colors.extend(region_colors_found)
        
        return region_colors
    
    def detect_light_skin_pixels(self, region: np.ndarray) -> List[np.ndarray]:
        """Detect skin pixels with enhanced methods for light skin."""
        if region.size == 0:
            return []
        
        skin_colors = []
        
        # Method 1: RGB-based detection for very light skin
        r, g, b = cv2.split(region)
        
        # Light skin characteristics: R >= G >= B, high overall brightness
        light_skin_mask1 = (
            (r >= g) & (g >= b) &  # Basic skin tone ratios
            (r > 180) & (g > 150) & (b > 120) &  # Light skin thresholds
            ((r + g + b) > 500)  # High brightness
        )
        
        # Method 2: Enhanced YCbCr detection for light skin
        region_ycbcr = cv2.cvtColor(region, cv2.COLOR_RGB2YCrCb)
        y, cr, cb = cv2.split(region_ycbcr)
        
        # Expanded YCbCr ranges for light skin
        light_skin_mask2 = (
            (y > 120) &  # Higher luminance for light skin
            (cr >= 125) & (cr <= 165) &  # Adjusted Cr range
            (cb >= 95) & (cb <= 125)   # Adjusted Cb range
        )
        
        # Method 3: HSV-based detection
        region_hsv = cv2.cvtColor(region, cv2.COLOR_RGB2HSV)
        h, s, v = cv2.split(region_hsv)
        
        # Light skin in HSV: low saturation, high value, hue in skin range
        light_skin_mask3 = (
            ((h <= 25) | (h >= 160)) &  # Skin hue range
            (s <= 80) &  # Low saturation for light skin
            (v >= 180)   # High value/brightness
        )
        
        # Combine all masks
        combined_mask = light_skin_mask1 | light_skin_mask2 | light_skin_mask3
        
        # Extract skin pixels
        if np.sum(combined_mask) > 20:  # Minimum pixels required
            skin_pixels = region[combined_mask]
            if len(skin_pixels) > 10:
                # Add individual pixel colors for better averaging
                for pixel in skin_pixels[:50]:  # Limit to avoid too many samples
                    skin_colors.append(pixel.astype(np.float64))
        
        return skin_colors
    
    def calculate_enhanced_ita(self, rgb_color: np.ndarray) -> float:
        """Calculate Individual Typology Angle (ITA) with enhanced precision for light skin."""
        try:
            r, g, b = rgb_color.astype(np.uint8)
            
            # Convert to LAB color space
            lab = cv2.cvtColor(np.uint8([[[r, g, b]]]), cv2.COLOR_RGB2LAB)[0][0]
            L, a_val, b_val = lab.astype(np.float64)
            
            # Enhanced ITA calculation with special handling for light skin
            if abs(b_val) < 0.1:  # Avoid division by zero
                ita = 90 if L > 50 else -90
            else:
                ita = np.arctan2((L - 50), b_val) * 180 / np.pi
            
            # Apply light skin bias - boost ITA for very bright colors
            avg_brightness = np.mean(rgb_color)
            if avg_brightness > 220:
                ita += 10  # Boost towards lighter categories
            elif avg_brightness > 200:
                ita += 5   # Moderate boost
            
            return ita
            
        except Exception as e:
            logger.warning(f"Enhanced ITA calculation failed: {e}")
            return 0.0
    
    def classify_by_enhanced_ita(self, ita_value: float, avg_brightness: float) -> Tuple[str, float]:
        """Classify skin tone using enhanced ITA with brightness considerations."""
        
        # Enhanced thresholds optimized for light skin detection
        if ita_value > 60 or (ita_value > 50 and avg_brightness > 230):
            return "Monk 1", 0.95
        elif ita_value > 45 or (ita_value > 35 and avg_brightness > 210):
            return "Monk 2", 0.90
        elif ita_value > 30 or (ita_value > 20 and avg_brightness > 190):
            return "Monk 3", 0.85
        elif ita_value > 15:
            return "Monk 4", 0.80
        elif ita_value > -20:
            return "Monk 5", 0.75
        else:
            # Fallback for darker tones
            return "Monk 5", 0.70
    
    def multi_method_classification(self, rgb_color: np.ndarray) -> Dict[str, Any]:
        """Use multiple methods to classify skin tone and return the most confident result."""
        results = []
        
        # Method 1: Enhanced ITA
        try:
            ita = self.calculate_enhanced_ita(rgb_color)
            avg_brightness = np.mean(rgb_color)
            ita_result, ita_confidence = self.classify_by_enhanced_ita(ita, avg_brightness)
            results.append({
                'method': 'enhanced_ita',
                'result': ita_result,
                'confidence': ita_confidence,
                'details': {'ita': ita, 'brightness': avg_brightness}
            })
        except Exception as e:
            logger.warning(f"ITA method failed: {e}")
        
        # Method 2: Brightness-based classification
        try:
            brightness_result, brightness_confidence = self.classify_by_brightness(rgb_color)
            results.append({
                'method': 'brightness_based',
                'result': brightness_result,
                'confidence': brightness_confidence,
                'details': {'rgb_avg': np.mean(rgb_color)}
            })
        except Exception as e:
            logger.warning(f"Brightness method failed: {e}")
        
        # Method 3: Color space distance
        try:
            distance_result, distance_confidence = self.classify_by_color_distance(rgb_color)
            results.append({
                'method': 'color_distance',
                'result': distance_result,
                'confidence': distance_confidence,
                'details': {}
            })
        except Exception as e:
            logger.warning(f"Color distance method failed: {e}")
        
        # Select best result
        if not results:
            return {
                'result': 'Monk 2',
                'confidence': 0.5,
                'method': 'fallback',
                'all_results': []
            }
        
        # For very light skin, prioritize ITA method
        avg_brightness = np.mean(rgb_color)
        if avg_brightness > 200:
            ita_results = [r for r in results if r['method'] == 'enhanced_ita']
            if ita_results:
                best_result = ita_results[0]
            else:
                best_result = max(results, key=lambda x: x['confidence'])
        else:
            best_result = max(results, key=lambda x: x['confidence'])
        
        return {
            'result': best_result['result'],
            'confidence': best_result['confidence'],
            'method': best_result['method'],
            'details': best_result.get('details', {}),
            'all_results': results
        }
    
    def classify_by_brightness(self, rgb_color: np.ndarray) -> Tuple[str, float]:
        """Classify based on RGB brightness with enhanced light skin detection."""
        r, g, b = rgb_color
        avg_brightness = np.mean(rgb_color)
        
        # Enhanced brightness thresholds for better light skin detection
        if avg_brightness > 230:
            return "Monk 1", 0.90
        elif avg_brightness > 210:
            return "Monk 2", 0.85
        elif avg_brightness > 190:
            return "Monk 3", 0.80
        elif avg_brightness > 170:
            return "Monk 4", 0.75
        else:
            return "Monk 5", 0.70
    
    def classify_by_color_distance(self, rgb_color: np.ndarray) -> Tuple[str, float]:
        """Classify by calculating distance to reference Monk tones."""
        min_distance = float('inf')
        closest_monk = "Monk 2"
        
        for monk_name, monk_data in self.enhanced_monk_tones.items():
            monk_rgb = np.array(monk_data['rgb'])
            
            # Calculate Euclidean distance in RGB space
            distance = np.sqrt(np.sum((rgb_color - monk_rgb) ** 2))
            
            if distance < min_distance:
                min_distance = distance
                closest_monk = monk_name
        
        # Convert distance to confidence (closer = higher confidence)
        max_possible_distance = np.sqrt(3 * 255**2)  # Maximum possible RGB distance
        confidence = max(0.5, 1.0 - (min_distance / max_possible_distance))
        
        return closest_monk, confidence
    
    def analyze_skin_tone_improved(self, image: np.ndarray, monk_tones: Dict[str, str]) -> Dict[str, Any]:
        """
        Main method for improved skin tone analysis optimized for light skin.
        
        Args:
            image: Input image as numpy array (RGB)
            monk_tones: Dictionary mapping Monk tone names to hex colors
            
        Returns:
            Dictionary containing analysis results
        """
        try:
            logger.info("Starting improved light skin tone analysis...")
            
            # Step 1: Preprocess image for light skin detection
            processed_image = self.preprocess_for_light_skin(image)
            
            # Step 2: For this demo, assume face is center region (in production, use face detection)
            h, w = processed_image.shape[:2]
            face_region = processed_image[h//6:5*h//6, w//6:5*w//6]
            
            # Step 3: Extract skin regions with enhanced light skin detection
            region_colors = self.extract_light_skin_regions(face_region)
            
            if not region_colors:
                # Fallback: use center region
                logger.info("No skin regions detected, using center region fallback")
                center_h, center_w = face_region.shape[:2]
                center_region = face_region[center_h//3:2*center_h//3, center_w//3:2*center_w//3]
                avg_color = np.mean(center_region.reshape(-1, 3), axis=0)
            else:
                # Calculate average color from detected skin regions
                all_colors = np.array(region_colors)
                avg_color = np.mean(all_colors, axis=0)
            
            # Step 4: Multi-method classification
            classification_result = self.multi_method_classification(avg_color)
            
            # Step 5: Format final result
            monk_tone = classification_result['result']
            monk_number = monk_tone.split()[1]
            monk_id = f"Monk{monk_number.zfill(2)}"
            
            # Convert RGB to hex
            derived_hex = rgb_to_hex(tuple(avg_color.astype(int)))
            
            logger.info(f"Improved analysis result: {monk_id} via {classification_result['method']} "
                       f"(confidence: {classification_result['confidence']:.2f})")
            
            return {
                'monk_skin_tone': monk_id,
                'monk_tone_display': monk_tone,
                'monk_hex': monk_tones.get(monk_tone, '#f3e7db'),
                'derived_hex_code': derived_hex,
                'dominant_rgb': avg_color.astype(int).tolist(),
                'confidence': round(classification_result['confidence'], 2),
                'success': True,
                'analysis_method': f"improved_light_skin_{classification_result['method']}",
                'regions_analyzed': len(region_colors),
                'face_detected': True,
                'classification_details': classification_result.get('details', {}),
                'all_method_results': classification_result.get('all_results', [])
            }
            
        except Exception as e:
            logger.error(f"Improved skin tone analysis failed: {e}")
            return {
                'monk_skin_tone': 'Monk02',
                'monk_tone_display': 'Monk 2',
                'monk_hex': monk_tones.get('Monk 2', '#f3e7db'),
                'derived_hex_code': '#f3e7db',
                'dominant_rgb': [243, 231, 219],
                'confidence': 0.5,
                'success': False,
                'error': str(e),
                'face_detected': False
            }

# Test the improved analyzer
def test_improved_analyzer():
    """Test the improved analyzer with sample light skin colors."""
    analyzer = ImprovedLightSkinAnalyzer()
    
    # Sample test case for very light skin (like the blonde person in your image)
    test_colors = [
        {'name': 'Very Fair', 'rgb': np.array([250, 240, 230])},  # Very light
        {'name': 'Fair', 'rgb': np.array([245, 235, 225])},       # Fair
        {'name': 'Light', 'rgb': np.array([240, 220, 200])},      # Light
    ]
    
    monk_tones = {
        'Monk 1': '#f6ede4',
        'Monk 2': '#f3e7db', 
        'Monk 3': '#f7ead0',
        'Monk 4': '#eadaba',
        'Monk 5': '#d7bd96'
    }
    
    print("Testing Improved Light Skin Analyzer:")
    print("=" * 50)
    
    for test_case in test_colors:
        result = analyzer.multi_method_classification(test_case['rgb'])
        print(f"\n{test_case['name']} - RGB: {test_case['rgb']}")
        print(f"  Result: {result['result']} (confidence: {result['confidence']:.2f})")
        print(f"  Method: {result['method']}")
        if 'details' in result:
            print(f"  Details: {result['details']}")

if __name__ == "__main__":
    test_improved_analyzer()
