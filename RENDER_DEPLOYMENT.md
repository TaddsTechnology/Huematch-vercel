# Render Deployment Configuration

## For Enhanced Skin Tone Detection with MediaPipe

### Render Service Configuration

1. **Python Version**: Use Python 3.11 or 3.12 (not 3.13) for MediaPipe compatibility
2. **Requirements File**: Use `requirements-render.txt` instead of `requirements.txt`
3. **Build Command**: 
   ```bash
   pip install -r requirements-render.txt
   ```
4. **Start Command**: 
   ```bash
   uvicorn backend.prods_fastapi.main:app --host 0.0.0.0 --port $PORT
   ```

### Environment Variables

Set these environment variables in your Render service:

- `PYTHON_VERSION=3.11.9` (or 3.12.x)
- Any other environment variables your app requires

### Dependencies Explanation

The `requirements-render.txt` file includes:

- **MediaPipe 0.10.8**: Advanced face detection for better accuracy
- **scikit-learn 1.5.1**: ML clustering for skin tone analysis  
- **OpenCV 4.10.0.84**: Image processing and fallback face detection
- **scipy 1.13.1**: Scientific computing for color space transformations

### Fallback System

The code is designed to gracefully handle missing dependencies:

1. **First**: Try Enhanced Analyzer with MediaPipe + scikit-learn
2. **Fallback**: Use OpenCV-only analyzer if heavy dependencies fail
3. **Last Resort**: Basic color analysis if all face detection fails

### Testing the Deployment

After deployment, test with various skin tones to ensure:
- Light skin → Monk 1-3
- Medium skin → Monk 4-7  
- Dark skin → Monk 8-10
- No more incorrect Monk 6 defaults

### Troubleshooting

If you still get Monk 6 issues on Render:
1. Check the logs for which analyzer is being used
2. Verify MediaPipe and scikit-learn are properly installed
3. Test the ITA calculation logs to see classification reasoning
