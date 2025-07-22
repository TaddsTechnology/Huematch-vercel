#!/usr/bin/env python3
"""
Test script for validating the enhanced skin tone detection algorithm.
Specifically designed to test light skin tone detection improvements.
"""

import os
import sys
import json
import time
from pathlib import Path
import cv2
import numpy as np

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

try:
    from enhanced_skin_analysis import EnhancedSkinAnalyzer
    print("✓ Successfully imported EnhancedSkinAnalyzer")
except ImportError as e:
    print(f"✗ Failed to import EnhancedSkinAnalyzer: {e}")
    sys.exit(1)

class LightSkinToneTestSuite:
    """Test suite for validating light skin tone detection improvements."""
    
    def __init__(self):
        self.analyzer = EnhancedSkinAnalyzer()
        self.test_results = []
        self.monk_scale_names = {
            1: "Very Light",
            2: "Light", 
            3: "Light-Medium",
            4: "Medium",
            5: "Medium-Dark",
            6: "Dark",
            7: "Very Dark",
            8: "Deep",
            9: "Very Deep",
            10: "Deepest"
        }
        
    def create_test_image(self, rgb_color, size=(400, 400)):
        """Create a test image with specified RGB color."""
        image = np.full((size[1], size[0], 3), rgb_color, dtype=np.uint8)
        return image
    
    def test_light_skin_rgb_values(self):
        """Test the algorithm with various light skin RGB values."""
        print("\n🧪 Testing Light Skin RGB Values:")
        print("=" * 60)
        
        # Light skin tone RGB values for testing
        light_skin_samples = [
            # Very light skin tones (should be Monk 1-2)
            ([255, 245, 230], "Very Light Porcelain", 1),
            ([255, 240, 220], "Light Ivory", 1),
            ([248, 235, 210], "Light Beige", 2),
            ([245, 230, 200], "Light Peach", 2),
            
            # Light-medium skin tones (should be Monk 3-4)
            ([235, 220, 185], "Light Medium", 3),
            ([230, 210, 175], "Light Tan", 3),
            ([225, 200, 165], "Medium Light", 4),
            ([220, 195, 155], "Medium Beige", 4),
        ]
        
        for rgb_color, description, expected_monk in light_skin_samples:
            print(f"\n📊 Testing {description} RGB{rgb_color}:")
            
            # Create test image
            test_image = self.create_test_image(rgb_color)
            
            # Analyze skin tone
            try:
                result = self.analyzer.analyze_skin_tone(test_image)
                
                if result and 'monk_tone' in result:
                    detected_monk = result['monk_tone']
                    confidence = result.get('confidence', 0)
                    
                    # Check if detection is within acceptable range for light skin
                    is_accurate = abs(detected_monk - expected_monk) <= 1
                    accuracy_symbol = "✓" if is_accurate else "✗"
                    
                    print(f"  {accuracy_symbol} Expected: Monk {expected_monk} ({self.monk_scale_names[expected_monk]})")
                    print(f"  {accuracy_symbol} Detected: Monk {detected_monk} ({self.monk_scale_names[detected_monk]})")
                    print(f"  {accuracy_symbol} Confidence: {confidence:.2f}")
                    
                    # Store result
                    self.test_results.append({
                        'description': description,
                        'rgb_color': rgb_color,
                        'expected_monk': expected_monk,
                        'detected_monk': detected_monk,
                        'confidence': confidence,
                        'accurate': is_accurate
                    })
                    
                else:
                    print(f"  ✗ Failed to analyze skin tone")
                    
            except Exception as e:
                print(f"  ✗ Error analyzing {description}: {str(e)}")
    
    def test_image_files(self, image_dir=None):
        """Test with actual image files if available."""
        print("\n📸 Testing Image Files:")
        print("=" * 60)
        
        if image_dir is None:
            # Try common image directories
            possible_dirs = [
                Path("test_images"),
                Path("images"),
                Path("samples"),
                Path("../test_images"),
                Path("../frontend/public/images")
            ]
            
            for dir_path in possible_dirs:
                if dir_path.exists():
                    image_dir = dir_path
                    break
        
        if image_dir is None or not Path(image_dir).exists():
            print("  ℹ️  No test images directory found. Skipping image file tests.")
            return
        
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
        image_files = []
        
        for ext in image_extensions:
            image_files.extend(Path(image_dir).glob(f"*{ext}"))
            image_files.extend(Path(image_dir).glob(f"*{ext.upper()}"))
        
        if not image_files:
            print(f"  ℹ️  No image files found in {image_dir}")
            return
        
        for image_path in image_files[:5]:  # Test first 5 images
            print(f"\n📷 Testing {image_path.name}:")
            
            try:
                # Load image
                image = cv2.imread(str(image_path))
                if image is None:
                    print(f"  ✗ Failed to load image: {image_path}")
                    continue
                
                # Convert BGR to RGB
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                
                # Analyze skin tone
                start_time = time.time()
                result = self.analyzer.analyze_skin_tone(image_rgb)
                analysis_time = time.time() - start_time
                
                if result and 'monk_tone' in result:
                    monk_tone = result['monk_tone']
                    confidence = result.get('confidence', 0)
                    
                    print(f"  ✓ Monk Tone: {monk_tone} ({self.monk_scale_names[monk_tone]})")
                    print(f"  ✓ Confidence: {confidence:.2f}")
                    print(f"  ✓ Analysis Time: {analysis_time:.3f}s")
                    
                    # Additional details if available
                    if 'skin_color_rgb' in result:
                        rgb = result['skin_color_rgb']
                        print(f"  ✓ Detected Skin RGB: {rgb}")
                    
                    if 'brightness' in result:
                        print(f"  ✓ Brightness: {result['brightness']:.2f}")
                        
                else:
                    print(f"  ✗ Failed to analyze skin tone in {image_path.name}")
                    
            except Exception as e:
                print(f"  ✗ Error processing {image_path.name}: {str(e)}")
    
    def print_summary(self):
        """Print test summary and statistics."""
        print("\n📊 Test Summary:")
        print("=" * 60)
        
        if not self.test_results:
            print("  ℹ️  No test results to summarize.")
            return
        
        total_tests = len(self.test_results)
        accurate_tests = sum(1 for result in self.test_results if result['accurate'])
        accuracy_rate = (accurate_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"  📈 Total Tests: {total_tests}")
        print(f"  ✓ Accurate Classifications: {accurate_tests}")
        print(f"  ✗ Inaccurate Classifications: {total_tests - accurate_tests}")
        print(f"  🎯 Accuracy Rate: {accuracy_rate:.1f}%")
        
        # Average confidence
        avg_confidence = np.mean([result['confidence'] for result in self.test_results])
        print(f"  📊 Average Confidence: {avg_confidence:.2f}")
        
        # Light skin tone focus
        light_skin_tests = [r for r in self.test_results if r['expected_monk'] <= 4]
        if light_skin_tests:
            light_accuracy = sum(1 for result in light_skin_tests if result['accurate'])
            light_accuracy_rate = (light_accuracy / len(light_skin_tests)) * 100
            print(f"  🌟 Light Skin Accuracy (Monk 1-4): {light_accuracy_rate:.1f}%")
        
        print("\n📋 Detailed Results:")
        for result in self.test_results:
            status = "✓" if result['accurate'] else "✗"
            print(f"  {status} {result['description']}: Expected M{result['expected_monk']} → Detected M{result['detected_monk']} (Conf: {result['confidence']:.2f})")
    
    def run_all_tests(self, image_dir=None):
        """Run all test suites."""
        print("🧪 Enhanced Light Skin Tone Detection Test Suite")
        print("=" * 60)
        print("Testing the refined algorithm optimized for light skin tones (Monk 1-4)")
        
        # Test RGB values
        self.test_light_skin_rgb_values()
        
        # Test image files
        self.test_image_files(image_dir)
        
        # Print summary
        self.print_summary()
        
        print("\n🎉 Testing Complete!")
        print("=" * 60)

def main():
    """Main function to run the test suite."""
    print("Starting Enhanced Skin Tone Detection Tests...")
    
    # Create test suite
    test_suite = LightSkinToneTestSuite()
    
    # Check if image directory argument is provided
    image_dir = sys.argv[1] if len(sys.argv) > 1 else None
    
    # Run all tests
    test_suite.run_all_tests(image_dir)

if __name__ == "__main__":
    main()
