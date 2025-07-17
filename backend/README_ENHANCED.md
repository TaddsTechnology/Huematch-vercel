# 🎨 Enhanced Skin Tone Analysis System

An advanced skin tone detection system with multi-face detection, lighting correction, and confidence scoring.

## 🚀 New Features

### 1. Multi-Face Detection
- **MediaPipe Integration**: Automatically detects multiple faces in a single image
- **Face Confidence**: Each detected face comes with a confidence score
- **Bounding Box Information**: Precise face location coordinates
- **Best Face Selection**: Automatically selects the face with highest confidence

### 2. Lighting Correction
- **CLAHE (Contrast Limited Adaptive Histogram Equalization)**: Improves contrast in different lighting conditions
- **LAB Color Space**: Better color representation for skin tone analysis
- **Multiple Methods**: Support for histogram equalization and gamma correction
- **Automatic Processing**: No manual intervention required

### 3. Confidence Scoring
- **Multi-Metric Evaluation**: Combines multiple factors for overall confidence
- **Segmentation Quality**: Measures how well skin pixels are detected
- **Color Confidence**: Evaluates clustering consistency
- **Tone Similarity**: Measures similarity to Monk skin tones
- **Face Detection**: Incorporates face detection confidence

### 4. Advanced Color Analysis
- **Outlier Removal**: Filters out extreme values for better accuracy
- **Improved K-means**: Better clustering with multiple clusters
- **Brightness Filtering**: Removes pixels outside normal skin tone range
- **Cluster Validation**: Ensures reliable color extraction

## 📁 File Structure

```
backend/
├── enhanced_skin_analysis.py     # Enhanced Gradio interface
├── enhanced_skin_api.py          # Enhanced FastAPI server
├── setup_enhanced.py             # Setup and installation script
├── test_enhanced.py              # Testing suite
├── requirements_enhanced.txt     # Dependencies
├── README_ENHANCED.md           # This file
└── model.h5                     # Your trained segmentation model
```

## 🛠️ Installation

1. **Run the setup script**:
```bash
python setup_enhanced.py
```

2. **Or install manually**:
```bash
pip install -r requirements_enhanced.txt
```

## 🎯 Usage

### 1. Enhanced API Server
```bash
python enhanced_skin_api.py
```
- Runs on port 8002
- Endpoint: `/analyze-skin-tone-enhanced`
- Health check: `/health-enhanced`
- Features: `/supported-features`

### 2. Enhanced Gradio Interface
```bash
python enhanced_skin_analysis.py
```
- Beautiful web interface with detailed metrics
- Real-time confidence scoring
- Multi-face detection visualization

### 3. Testing
```bash
python test_enhanced.py
```
- Tests all API endpoints
- Compares original vs enhanced performance
- Validates all features

## 📊 API Response Format

### Enhanced API Response
```json
{
  "success": true,
  "monk_skin_tone": "Monk05",
  "monk_tone_display": "Monk 5",
  "monk_hex": "#d7bd96",
  "derived_hex_code": "#c8a882",
  "dominant_rgb": [200, 168, 130],
  "confidence": 0.87,
  "processing_time": 1.23,
  "total_faces_detected": 2,
  "detailed_metrics": {
    "segmentation_quality": 0.85,
    "color_confidence": 0.92,
    "tone_similarity": 0.88,
    "face_confidence": 0.95
  },
  "all_faces": [
    {
      "face_id": 1,
      "monk_tone": "Monk 5",
      "confidence": 0.87,
      "bbox": [150, 200, 300, 350]
    },
    {
      "face_id": 2,
      "monk_tone": "Monk 4",
      "confidence": 0.73,
      "bbox": [500, 180, 280, 320]
    }
  ]
}
```

## 🔧 Configuration

### Confidence Weights
```python
weights = {
    'segmentation': 0.25,  # How well skin is detected
    'color': 0.35,         # Color clustering quality
    'tone': 0.25,          # Similarity to Monk tones
    'face': 0.15           # Face detection confidence
}
```

### Face Detection Settings
```python
face_detection = mp.solutions.face_detection.FaceDetection(
    model_selection=0,           # 0 for close-range, 1 for full-range
    min_detection_confidence=0.5  # Minimum confidence threshold
)
```

### Lighting Correction
```python
clahe = cv2.createCLAHE(
    clipLimit=3.0,        # Contrast limit
    tileGridSize=(8, 8)   # Grid size for local enhancement
)
```

## 📈 Performance Improvements

| Feature | Original | Enhanced | Improvement |
|---------|----------|----------|-------------|
| Face Detection | Manual crop | Auto-detect | 🚀 Automatic |
| Lighting Handling | Basic | CLAHE correction | 🔧 Advanced |
| Confidence Score | None | Multi-metric | 📊 Detailed |
| Multi-face Support | No | Yes | 👥 Multiple |
| Error Handling | Basic | Comprehensive | 🛡️ Robust |

## 🧪 Testing Features

### 1. Health Check
```bash
curl http://localhost:8002/health-enhanced
```

### 2. Supported Features
```bash
curl http://localhost:8002/supported-features
```

### 3. Image Analysis
```bash
curl -X POST -F "file=@test_image.jpg" http://localhost:8002/analyze-skin-tone-enhanced
```

## 🔍 Confidence Metrics Explained

### Segmentation Quality (0-1)
- **High (0.8+)**: Large skin area detected
- **Medium (0.5-0.8)**: Moderate skin area
- **Low (<0.5)**: Small or poor skin detection

### Color Confidence (0-1)
- **High (0.8+)**: Consistent skin color clustering
- **Medium (0.5-0.8)**: Some color variation
- **Low (<0.5)**: High color variation

### Tone Similarity (0-1)
- **High (0.8+)**: Very close to Monk tone
- **Medium (0.5-0.8)**: Reasonable match
- **Low (<0.5)**: Distant from Monk tones

### Face Confidence (0-1)
- **High (0.8+)**: Clear face detection
- **Medium (0.5-0.8)**: Moderate detection
- **Low (<0.5)**: Weak face detection

## 🚨 Troubleshooting

### Common Issues

1. **Model not found**:
   - Ensure `model.h5` is in the backend directory
   - Check file permissions

2. **MediaPipe installation**:
   - Try: `pip install mediapipe --upgrade`
   - For M1 Mac: `pip install mediapipe-silicon`

3. **TensorFlow GPU**:
   - Install: `pip install tensorflow-gpu==2.15.0`
   - Verify: `tf.config.list_physical_devices('GPU')`

4. **Memory issues**:
   - Reduce image size before processing
   - Use smaller batch sizes

## 📋 Requirements

- Python 3.8+
- TensorFlow 2.15.0
- OpenCV 4.8.1+
- MediaPipe 0.10.7
- FastAPI 0.104.1
- Gradio 4.7.1
- Your trained model.h5 file

## 🎯 Future Enhancements

- [ ] Real-time video processing
- [ ] Batch image processing
- [ ] Advanced face recognition
- [ ] Skin condition analysis
- [ ] Custom color palette matching
- [ ] Mobile app integration

## 📄 License

This enhanced system builds upon your existing skin tone analysis project with advanced features for improved accuracy and usability.

---

**Made with ❤️ for better skin tone detection**
