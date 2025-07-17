import requests
import json
import time
from pathlib import Path

def test_enhanced_api():
    """Test the enhanced API functionality."""
    base_url = "http://localhost:8002"
    
    print("🧪 Testing Enhanced Skin Tone Analysis API")
    print("=" * 50)
    
    # Test 1: Health check
    print("\n1. Testing health check...")
    try:
        response = requests.get(f"{base_url}/health-enhanced")
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Health check passed")
            print(f"   Model loaded: {health_data['model_loaded']}")
            print(f"   Face detection ready: {health_data['face_detection_ready']}")
            print(f"   Version: {health_data['version']}")
            print(f"   Features: {', '.join(health_data['features'])}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")
    
    # Test 2: Supported features
    print("\n2. Testing supported features...")
    try:
        response = requests.get(f"{base_url}/supported-features")
        if response.status_code == 200:
            features_data = response.json()
            print("✅ Features endpoint working")
            print("   Available features:")
            for feature, details in features_data['features'].items():
                print(f"     • {feature}: {details['description']}")
        else:
            print(f"❌ Features check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Features check error: {e}")
    
    # Test 3: Image analysis (you would need to provide a test image)
    print("\n3. Testing image analysis...")
    test_image_path = "test_image.jpg"  # Replace with actual test image
    
    if Path(test_image_path).exists():
        try:
            with open(test_image_path, 'rb') as f:
                files = {'file': ('test.jpg', f, 'image/jpeg')}
                start_time = time.time()
                response = requests.post(f"{base_url}/analyze-skin-tone-enhanced", files=files)
                processing_time = time.time() - start_time
                
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Image analysis successful")
                print(f"   Processing time: {processing_time:.2f}s")
                print(f"   Faces detected: {result['total_faces_detected']}")
                print(f"   Monk tone: {result['monk_tone_display']}")
                print(f"   Confidence: {result['confidence']:.2f}")
                print(f"   Detailed metrics:")
                for metric, value in result['detailed_metrics'].items():
                    print(f"     • {metric}: {value:.2f}")
            else:
                print(f"❌ Image analysis failed: {response.status_code}")
                print(f"   Error: {response.text}")
        except Exception as e:
            print(f"❌ Image analysis error: {e}")
    else:
        print(f"⚠️  Test image not found: {test_image_path}")
        print("   Place a test image in the same directory to test image analysis")
    
    print("\n" + "=" * 50)
    print("🏁 Testing complete!")

def compare_apis():
    """Compare original vs enhanced API performance."""
    print("\n📊 API Performance Comparison")
    print("=" * 40)
    
    # Test same image on both APIs
    test_image_path = "test_image.jpg"
    
    if not Path(test_image_path).exists():
        print("⚠️  Test image not found for comparison")
        return
    
    # Original API
    print("\n🔄 Testing Original API (port 8001)...")
    try:
        with open(test_image_path, 'rb') as f:
            files = {'file': ('test.jpg', f, 'image/jpeg')}
            start_time = time.time()
            response = requests.post("http://localhost:8001/analyze-skin-tone", files=files)
            original_time = time.time() - start_time
            
        if response.status_code == 200:
            original_result = response.json()
            print(f"✅ Original API: {original_time:.2f}s")
            print(f"   Monk tone: {original_result.get('monk_tone_display', 'N/A')}")
        else:
            print(f"❌ Original API failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Original API error: {e}")
    
    # Enhanced API
    print("\n🚀 Testing Enhanced API (port 8002)...")
    try:
        with open(test_image_path, 'rb') as f:
            files = {'file': ('test.jpg', f, 'image/jpeg')}
            start_time = time.time()
            response = requests.post("http://localhost:8002/analyze-skin-tone-enhanced", files=files)
            enhanced_time = time.time() - start_time
            
        if response.status_code == 200:
            enhanced_result = response.json()
            print(f"✅ Enhanced API: {enhanced_time:.2f}s")
            print(f"   Monk tone: {enhanced_result.get('monk_tone_display', 'N/A')}")
            print(f"   Faces detected: {enhanced_result.get('total_faces_detected', 0)}")
            print(f"   Confidence: {enhanced_result.get('confidence', 0):.2f}")
        else:
            print(f"❌ Enhanced API failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Enhanced API error: {e}")

if __name__ == "__main__":
    print("🎨 Enhanced Skin Tone Analysis - Test Suite")
    print("Make sure both APIs are running:")
    print("- Original API: python skin_analysis_api.py (port 8001)")
    print("- Enhanced API: python enhanced_skin_api.py (port 8002)")
    print()
    
    test_enhanced_api()
    compare_apis()
