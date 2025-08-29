#!/usr/bin/env python3
"""
Test script for verifying light skin tone detection improvements.
This script tests both the enhanced and OpenCV fallback analyzers with simulated light skin tone images.
"""

import cv2
import numpy as np
import logging

# Try to import analyzers gracefully
ENHANCED_AVAILABLE = True
FALLBACK_AVAILABLE = True

try:
    from enhanced_skin_tone_analyzer import EnhancedSkinToneAnalyzer
except ImportError as e:
    print(f"Enhanced analyzer not available: {e}")
    EnhancedSkinToneAnalyzer = None
    ENHANCED_AVAILABLE = False

try:
    from opencv_fallback_analyzer import OpenCVFallbackAnalyzer
except ImportError as e:
    print(f"Fallback analyzer not available: {e}")
    OpenCVFallbackAnalyzer = None
    FALLBACK_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define Monk skin tone colors for testing
MONK_TONES = {
    'Monk 1': '#f6ede4',
    'Monk 2': '#f3e7db',
    'Monk 3': '#f7ead0',
    'Monk 4': '#eadaba',
    'Monk 5': '#d7bd96',
    'Monk 6': '#a07e56',
    'Monk 7': '#825c43',
    'Monk 8': '#604134',
    'Monk 9': '#3a312a',
    'Monk 10': '#292420'
}

def create_test_face_image(skin_rgb: tuple, size: tuple = (400, 400), add_noise: bool = True) -> np.ndarray:
    """Create a synthetic face-like image with specified skin color."""
    height, width = size
    image = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Create face oval
    center_x, center_y = width // 2, height // 2
    face_width, face_height = width // 3, height // 2
    
    # Generate face mask
    y, x = np.ogrid[:height, :width]
    face_mask = ((x - center_x) ** 2 / face_width ** 2 + 
                 (y - center_y) ** 2 / face_height ** 2) <= 1
    
    # Fill face with skin color
    r, g, b = skin_rgb
    image[face_mask] = [r, g, b]
    
    # Add some facial features (darker areas for eyes, nose)
    if face_mask.any():
        # Eyes
        eye_y = center_y - face_height // 4
        left_eye_x = center_x - face_width // 3
        right_eye_x = center_x + face_width // 3
        
        eye_radius = 15
        cv2.circle(image, (left_eye_x, eye_y), eye_radius, (max(0, r-50), max(0, g-50), max(0, b-50)), -1)
        cv2.circle(image, (right_eye_x, eye_y), eye_radius, (max(0, r-50), max(0, g-50), max(0, b-50)), -1)
        
        # Nose
        nose_y = center_y
        cv2.circle(image, (center_x, nose_y), 8, (max(0, r-20), max(0, g-20), max(0, b-20)), -1)
        
        # Mouth
        mouth_y = center_y + face_height // 3
        cv2.ellipse(image, (center_x, mouth_y), (25, 10), 0, 0, 360, (max(0, r-30), max(0, g-30), max(0, b-30)), -1)
    
    # Add realistic noise for testing robustness
    if add_noise:
        noise = np.random.normal(0, 5, image.shape).astype(np.int16)
        image = np.clip(image.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    
    return image

def test_light_skin_variations():
    """Test various light skin tone variations."""
    print("🧪 Testing Light Skin Tone Detection Improvements")
    print("=" * 60)
    
    # Initialize analyzers
    enhanced_analyzer = EnhancedSkinToneAnalyzer() if ENHANCED_AVAILABLE else None
    fallback_analyzer = OpenCVFallbackAnalyzer() if FALLBACK_AVAILABLE else None
    
    if not enhanced_analyzer and not fallback_analyzer:
        print("❌ No analyzers available for testing!")
        return {'enhanced': [], 'fallback': []}
    
    # Define test cases for light skin tones
    light_skin_tests = [
        {
            'name': 'Very Fair (Monk 1 target)',
            'rgb': (246, 237, 228),  # Very light
            'expected_monk': 'Monk 1'
        },
        {
            'name': 'Fair (Monk 2 target)', 
            'rgb': (243, 231, 219),  # Light
            'expected_monk': 'Monk 2'
        },
        {
            'name': 'Light Beige (Monk 3 target)',
            'rgb': (247, 234, 208),  # Light beige
            'expected_monk': 'Monk 3'
        },
        {
            'name': 'Pale with Pink Undertones',
            'rgb': (255, 220, 210),  # Very pale with pink
            'expected_monk': 'Monk 1'
        },
        {
            'name': 'Cool Fair Tone',
            'rgb': (240, 235, 230),  # Cool undertones
            'expected_monk': 'Monk 2'
        },
        {
            'name': 'Warm Light Tone',
            'rgb': (250, 240, 210),  # Warm undertones
            'expected_monk': 'Monk 3'
        }
    ]
    
    results = {'enhanced': [], 'fallback': []}
    for i, test_case in enumerate(light_skin_tests):
        print(f"\n🎯 Test {i+1}: {test_case['name']}")
        print(f"   Target RGB: {test_case['rgb']}")
        print(f"   Expected: {test_case['expected_monk']}")
        
        # Create test image
        test_image = create_test_face_image(test_case['rgb'])
        
        # Test Enhanced Analyzer
        if enhanced_analyzer:
            try:
                enhanced_result = enhanced_analyzer.analyze_skin_tone(test_image, MONK_TONES)
                results['enhanced'].append({
                    'test': test_case['name'],
                    'result': enhanced_result,
                    'success': enhanced_result['success']
                })
                
                print(f"   ✅ Enhanced: {enhanced_result['monk_tone_display']} "
                      f"(confidence: {enhanced_result['confidence']})")
                if not enhanced_result['success']:
                    print(f"      ❌ Error: {enhanced_result.get('error', 'Unknown')}")
                    
            except Exception as e:
                print(f"   ❌ Enhanced failed: {e}")
                results['enhanced'].append({
                    'test': test_case['name'],
                    'result': None,
                    'success': False,
                    'error': str(e)
                })
        else:
            print("   ⏭️ Enhanced: Not available")
        
        # Test Fallback Analyzer
        if fallback_analyzer:
            try:
                fallback_result = fallback_analyzer.analyze_skin_tone(test_image, MONK_TONES)
                results['fallback'].append({
                    'test': test_case['name'],
                    'result': fallback_result,
                    'success': fallback_result['success']
                })
                
                print(f"   ✅ Fallback: {fallback_result['monk_tone_display']} "
                      f"(confidence: {fallback_result['confidence']})")
                if not fallback_result['success']:
                    print(f"      ❌ Error: {fallback_result.get('error', 'Unknown')}")
                    
            except Exception as e:
                print(f"   ❌ Fallback failed: {e}")
                results['fallback'].append({
                    'test': test_case['name'],
                    'result': None,
                    'success': False,
                    'error': str(e)
                })
        else:
            print("   ⏭️ Fallback: Not available")
    
    # Print summary
    print(f"\n📊 SUMMARY")
    print("=" * 60)
    
    enhanced_successes = sum(1 for r in results['enhanced'] if r['success'])
    fallback_successes = sum(1 for r in results['fallback'] if r['success'])
    
    print(f"Enhanced Analyzer: {enhanced_successes}/{len(light_skin_tests)} tests passed")
    print(f"Fallback Analyzer: {fallback_successes}/{len(light_skin_tests)} tests passed")
    
    # Detailed results
    print(f"\n📋 DETAILED RESULTS")
    print("-" * 60)
    
    for i, test_case in enumerate(light_skin_tests):
        print(f"\n{test_case['name']}:")
        
        if i < len(results['enhanced']) and results['enhanced'][i]['success']:
            result = results['enhanced'][i]['result']
            print(f"  Enhanced: {result['monk_tone_display']} | "
                  f"Confidence: {result['confidence']} | "
                  f"RGB: {result['dominant_rgb']}")
        else:
            print(f"  Enhanced: Failed")
            
        if i < len(results['fallback']) and results['fallback'][i]['success']:
            result = results['fallback'][i]['result']
            print(f"  Fallback: {result['monk_tone_display']} | "
                  f"Confidence: {result['confidence']} | "
                  f"RGB: {result['dominant_rgb']}")
        else:
            print(f"  Fallback: Failed")
    
    return results

def test_extreme_light_cases():
    """Test extreme light skin cases that were previously problematic."""
    print(f"\n🔬 Testing Extreme Light Cases")
    print("-" * 60)
    
    extreme_cases = [
        {'name': 'Extremely Pale', 'rgb': (255, 250, 245)},
        {'name': 'Albino-like', 'rgb': (255, 255, 250)},
        {'name': 'Pink Fair', 'rgb': (255, 230, 225)},
        {'name': 'Cool Very Fair', 'rgb': (245, 240, 240)}
    ]
    
    enhanced_analyzer = EnhancedSkinToneAnalyzer() if ENHANCED_AVAILABLE else None
    fallback_analyzer = OpenCVFallbackAnalyzer() if FALLBACK_AVAILABLE else None
    
    if not enhanced_analyzer and not fallback_analyzer:
        print("❌ No analyzers available for extreme case testing!")
        return
    
    for case in extreme_cases:
        print(f"\n⚡ {case['name']} - RGB: {case['rgb']}")
        test_image = create_test_face_image(case['rgb'])
        
        # Test analyzers that are available
        analyzers_to_test = []
        if enhanced_analyzer:
            analyzers_to_test.append(('Enhanced', enhanced_analyzer))
        if fallback_analyzer:
            analyzers_to_test.append(('Fallback', fallback_analyzer))
            
        for analyzer_name, analyzer in analyzers_to_test:
            try:
                result = analyzer.analyze_skin_tone(test_image, MONK_TONES)
                if result['success']:
                    print(f"   {analyzer_name}: {result['monk_tone_display']} (conf: {result['confidence']})")
                else:
                    print(f"   {analyzer_name}: Failed - {result.get('error', 'Unknown error')}")
            except Exception as e:
                print(f"   {analyzer_name}: Exception - {e}")

if __name__ == "__main__":
    try:
        # Run main light skin tests
        test_results = test_light_skin_variations()
        
        # Run extreme cases
        test_extreme_light_cases()
        
        print(f"\n🎉 Light Skin Detection Testing Complete!")
        print("Check the results above to verify proper detection of light/fair skin tones.")
        
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        print(f"❌ Testing failed: {e}")
