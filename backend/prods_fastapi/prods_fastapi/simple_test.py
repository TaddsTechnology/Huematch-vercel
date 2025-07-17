import sys
sys.path.append('.')
from main import analyze_skin_tone_simple
import numpy as np

# Test with a simple solid color image
test_color = (130, 92, 67)  # Monk 7
print(f"Testing with RGB{test_color}")

# Create a simple image
image_array = np.full((256, 256, 3), test_color, dtype=np.uint8)

# Analyze skin tone
result = analyze_skin_tone_simple(image_array)
print(f"Result: {result['monk_tone_display']} ({result['monk_skin_tone']})")
print(f"Confidence: {result['confidence']:.2f}")
print(f"Dominant RGB: {result['dominant_rgb']}")
print(f"Success: {result['success']}")
