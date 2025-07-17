#!/usr/bin/env python3
"""
Test script to analyze what RGB values are being extracted from skin tone analysis
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from main import analyze_skin_tone_simple
import numpy as np
from PIL import Image

def create_test_images():
    """Create test images with different skin tones"""
    
    # Create solid color images representing different skin tones
    test_skin_colors = [
        ("Very Light", (250, 240, 230)),    # Should be Monk 1-2
        ("Light", (235, 220, 200)),         # Should be Monk 3-4
        ("Medium Light", (210, 190, 160)),  # Should be Monk 4-5
        ("Medium", (180, 150, 120)),        # Should be Monk 5-6
        ("Medium Dark", (130, 92, 67)),     # Should be Monk 7
        ("Dark", (96, 65, 52)),             # Should be Monk 8
        ("Very Dark", (41, 36, 32)),        # Should be Monk 10
    ]
    
    print("=== Testing Image Analysis ===\n")
    
    for description, rgb_color in test_skin_colors:
        print(f"Testing {description}: RGB{rgb_color}")
        
        # Create a 256x256 image with the solid color
        image_array = np.full((256, 256, 3), rgb_color, dtype=np.uint8)
        
        # Add some noise to make it more realistic
        noise = np.random.randint(-10, 10, (256, 256, 3))
        image_array = np.clip(image_array.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        
        # Analyze skin tone
        result = analyze_skin_tone_simple(image_array)
        
        print(f"  Result: {result['monk_tone_display']} ({result['monk_skin_tone']})")
        print(f"  Confidence: {result['confidence']:.2f}")
        print(f"  Dominant RGB: {result['dominant_rgb']}")
        print(f"  Success: {result['success']}")
        print()

def test_different_lighting_conditions():
    """Test how different lighting conditions affect skin tone detection"""
    
    print("=== Testing Different Lighting Conditions ===\n")
    
    # Base medium skin tone
    base_color = np.array([180, 150, 120])
    
    lighting_conditions = [
        ("Normal", 1.0),
        ("Bright", 1.3),
        ("Dim", 0.7),
        ("Warm Light", 1.0, [1.1, 1.0, 0.9]),    # Warmer (more red/yellow)
        ("Cool Light", 1.0, [0.9, 1.0, 1.1]),    # Cooler (more blue)
    ]
    
    for condition in lighting_conditions:
        name = condition[0]
        brightness = condition[1]
        color_balance = condition[2] if len(condition) > 2 else [1.0, 1.0, 1.0]
        
        # Apply lighting effects
        adjusted_color = base_color * brightness
        adjusted_color = adjusted_color * np.array(color_balance)
        adjusted_color = np.clip(adjusted_color, 0, 255).astype(np.uint8)
        
        print(f"Testing {name}: RGB{tuple(adjusted_color)}")
        
        # Create image
        image_array = np.full((256, 256, 3), adjusted_color, dtype=np.uint8)
        
        # Analyze skin tone
        result = analyze_skin_tone_simple(image_array)
        
        print(f"  Result: {result['monk_tone_display']} ({result['monk_skin_tone']})")
        print(f"  Confidence: {result['confidence']:.2f}")
        print(f"  Dominant RGB: {result['dominant_rgb']}")
        print()

if __name__ == "__main__":
    create_test_images()
    test_different_lighting_conditions()
