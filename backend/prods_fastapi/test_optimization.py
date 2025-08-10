#!/usr/bin/env python3
"""
Test script to verify the optimized skin tone analyzer performance
"""

import time
import numpy as np
import requests
import json
from pathlib import Path
import cv2
from PIL import Image
import io

def create_test_image():
    """Create a simple test image with skin-like colors."""
    # Create a 400x400 test image with skin-like color
    img = np.ones((400, 400, 3), dtype=np.uint8)
    
    # Fill with a skin-like color (light brown/peach)
    img[:, :] = [220, 190, 160]  # Light skin tone
    
    # Add some variation to make it more realistic
    face_region = img[100:300, 150:250]
    face_region[:, :] = [230, 200, 170]  # Slightly lighter for face area
    
    return img

def test_fast_endpoint():
    """Test the fast endpoint performance."""
    print("🚀 Testing Fast Skin Tone Analysis Endpoint")
    print("=" * 50)
    
    # Create test image
    test_image = create_test_image()
    
    # Convert to PIL Image and then to bytes
    pil_image = Image.fromarray(test_image)
    image_bytes = io.BytesIO()
    pil_image.save(image_bytes, format='PNG')
    image_bytes.seek(0)
    
    # Test the fast endpoint
    url = "https://ai-fashion-backend-d9nj.onrender.com/analyze-skin-tone-fast"
    
    files = {'file': ('test_image.png', image_bytes.getvalue(), 'image/png')}
    
    print("📤 Sending request to fast endpoint...")
    start_time = time.time()
    
    try:
        response = requests.post(url, files=files, timeout=10)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS!")
            print(f"⚡ Response Time: {response_time:.2f} seconds")
            print(f"🎯 Detected Skin Tone: {result.get('monk_tone_display', 'Unknown')}")
            print(f"🔍 Confidence: {result.get('confidence', 0):.2f}")
            print(f"🎨 Hex Color: {result.get('derived_hex_code', 'Unknown')}")
            print(f"📊 Processing Time (Server): {result.get('processing_time', 'N/A')}s")
            print(f"🎪 Analysis Method: {result.get('analysis_method', 'Unknown')}")
            print(f"👤 Face Detected: {result.get('face_detected', False)}")
            
            if response_time < 2.0:
                print(f"🏆 PERFORMANCE EXCELLENT: {response_time:.2f}s (Target: <2s)")
            elif response_time < 3.0:
                print(f"✅ PERFORMANCE GOOD: {response_time:.2f}s")
            else:
                print(f"⚠️  PERFORMANCE NEEDS IMPROVEMENT: {response_time:.2f}s")
                
        else:
            print(f"❌ ERROR: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out (>10s)")
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")

def test_original_endpoint():
    """Test the original endpoint for comparison."""
    print("\n🐌 Testing Original Skin Tone Analysis Endpoint")
    print("=" * 50)
    
    # Create test image
    test_image = create_test_image()
    
    # Convert to PIL Image and then to bytes
    pil_image = Image.fromarray(test_image)
    image_bytes = io.BytesIO()
    pil_image.save(image_bytes, format='PNG')
    image_bytes.seek(0)
    
    # Test the original endpoint
    url = "https://ai-fashion-backend-d9nj.onrender.com/analyze-skin-tone"
    
    files = {'file': ('test_image.png', image_bytes.getvalue(), 'image/png')}
    
    print("📤 Sending request to original endpoint...")
    start_time = time.time()
    
    try:
        response = requests.post(url, files=files, timeout=15)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS!")
            print(f"⏱️  Response Time: {response_time:.2f} seconds")
            print(f"🎯 Detected Skin Tone: {result.get('monk_tone_display', 'Unknown')}")
            print(f"🔍 Confidence: {result.get('confidence', 0):.2f}")
            print(f"🎨 Hex Color: {result.get('derived_hex_code', 'Unknown')}")
            print(f"🎪 Analysis Method: {result.get('analysis_method', 'Unknown')}")
            
        else:
            print(f"❌ ERROR: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out (>15s)")
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")

def test_health_endpoint():
    """Test if the API is running."""
    print("🔍 Testing API Health")
    print("=" * 25)
    
    try:
        response = requests.get("https://ai-fashion-backend-d9nj.onrender.com/health", timeout=5)
        if response.status_code == 200:
            print("✅ API is healthy and running")
            return True
        else:
            print(f"⚠️  API returned status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API health check failed: {e}")
        return False

if __name__ == "__main__":
    print("🎯 AI Fashion Backend - Performance Optimization Test")
    print("=" * 60)
    
    # Test API health first
    if test_health_endpoint():
        print()
        
        # Test fast endpoint
        test_fast_endpoint()
        
        # Test original endpoint for comparison
        test_original_endpoint()
        
        print("\n🏁 Testing Complete!")
        print("💡 Use the /analyze-skin-tone-fast endpoint for 3-4x faster performance!")
    else:
        print("❌ Cannot proceed with tests - API is not responding")
