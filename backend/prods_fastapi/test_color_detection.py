#!/usr/bin/env python3
"""
Test script for color detection functionality
"""

import numpy as np
import cv2
import logging
from opencv_fallback_analyzer import OpenCVFallbackAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_image():
    """Create a simple test image with a face-like pattern"""
    # Create a 300x300 color image
    image = np.ones((300, 300, 3), dtype=np.uint8) * 200  # Light background
    
    # Draw a simple face-like oval in the center
    center = (150, 150)
    axes = (80, 100)  # width, height
    
    # Face color (simulate skin tone)
    face_color = (220, 180, 160)  # RGB skin tone
    
    # Draw filled ellipse for face
    cv2.ellipse(image, center, axes, 0, 0, 360, face_color, -1)
    
    # Add some darker regions for eyes
    cv2.circle(image, (120, 130), 10, (100, 100, 100), -1)  # left eye
    cv2.circle(image, (180, 130), 10, (100, 100, 100), -1)  # right eye
    
    # Add mouth
    cv2.ellipse(image, (150, 180), (20, 10), 0, 0, 180, (120, 100, 100), -1)
    
    return image

def test_fallback_analyzer():
    """Test the OpenCV fallback analyzer"""
    logger.info("Testing OpenCV fallback analyzer...")
    
    # Initialize analyzer
    analyzer = OpenCVFallbackAnalyzer()
    
    if not analyzer.available:
        logger.error("OpenCV fallback analyzer not available!")
        return False
    
    # Create test image
    test_image = create_test_image()
    
    # Define monk tones for testing
    monk_tones = {
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
    
    try:
        # Test skin tone analysis
        result = analyzer.analyze_skin_tone(test_image, monk_tones)
        
        logger.info(f"Analysis result: {result}")
        
        if result['success']:
            logger.info(f"✅ Success! Detected monk tone: {result['monk_tone_display']}")
            logger.info(f"   Confidence: {result['confidence']}")
            logger.info(f"   Method: {result['analysis_method']}")
            logger.info(f"   Regions analyzed: {result['regions_analyzed']}")
            return True
        else:
            logger.warning(f"❌ Analysis failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test failed with exception: {e}")
        return False

def test_enhanced_analyzer():
    """Test the enhanced analyzer if available"""
    logger.info("Testing enhanced analyzer...")
    
    try:
        from enhanced_skin_tone_analyzer import EnhancedSkinToneAnalyzer
        
        # Initialize analyzer
        analyzer = EnhancedSkinToneAnalyzer()
        
        # Create test image
        test_image = create_test_image()
        
        # Define monk tones for testing
        monk_tones = {
            'Monk 1': '#f6ede4',
            'Monk 2': '#f3e7db',
            'Monk 3': '#f7ead0',
            'Monk 4': '#eadaba',
            'Monk 5': '#d7bd96'
        }
        
        try:
            # Test skin tone analysis
            result = analyzer.analyze_skin_tone(test_image, monk_tones)
            
            logger.info(f"Enhanced analysis result: {result}")
            
            if result['success']:
                logger.info(f"✅ Enhanced analyzer success! Detected monk tone: {result['monk_tone_display']}")
                return True
            else:
                logger.warning(f"❌ Enhanced analysis failed: {result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Enhanced analyzer test failed: {e}")
            return False
            
    except ImportError as e:
        logger.info(f"Enhanced analyzer not available: {e}")
        return None

if __name__ == "__main__":
    print("🔍 Testing Color Detection Functionality")
    print("=" * 50)
    
    # Test fallback analyzer
    fallback_success = test_fallback_analyzer()
    
    # Test enhanced analyzer
    enhanced_success = test_enhanced_analyzer()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"  OpenCV Fallback Analyzer: {'✅ PASS' if fallback_success else '❌ FAIL'}")
    
    if enhanced_success is not None:
        print(f"  Enhanced Analyzer: {'✅ PASS' if enhanced_success else '❌ FAIL'}")
    else:
        print(f"  Enhanced Analyzer: ⚠️  NOT AVAILABLE")
    
    if fallback_success:
        print("\n🎉 Color detection is working! The system can analyze skin tones.")
        print("   Your Render deployment should work properly with the OpenCV fallback.")
    else:
        print("\n⚠️  Color detection has issues. Check the logs above for details.")
