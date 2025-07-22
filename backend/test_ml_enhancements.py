#!/usr/bin/env python3
"""
Test script for all ML enhancements in the AI Fashion platform
"""

import sys
import os
import numpy as np
import cv2
import logging
from pathlib import Path

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_enhanced_skin_analysis():
    """Test the enhanced skin analysis with multi-region processing."""
    logger.info("Testing Enhanced Skin Analysis...")
    
    try:
        from enhanced_skin_analysis import EnhancedSkinAnalyzer
        
        # Initialize the analyzer (will use a fallback if model.h5 is not found)
        analyzer = EnhancedSkinAnalyzer()
        
        # Create a test image (simulate a face image)
        test_image = np.ones((200, 200, 3), dtype=np.uint8) * 200  # Light skin tone simulation
        test_image = cv2.cvtColor(test_image, cv2.COLOR_RGB2BGR)
        
        # Save test image temporarily
        test_image_path = "temp_test_image.jpg"
        cv2.imwrite(test_image_path, test_image)
        
        # Test skin tone analysis
        result = analyzer.analyze_image(test_image_path)
        
        if 'error' not in result:
            logger.info("✅ Enhanced Skin Analysis: SUCCESS")
            logger.info(f"   - Detected {result['total_faces']} faces")
            logger.info(f"   - Primary result: {result['primary_result']['monk_tone']}")
            logger.info(f"   - Confidence: {result['primary_result']['confidence']:.2f}")
        else:
            logger.warning(f"⚠️ Enhanced Skin Analysis: {result['error']}")
            
        # Clean up
        if os.path.exists(test_image_path):
            os.remove(test_image_path)
            
    except Exception as e:
        logger.error(f"❌ Enhanced Skin Analysis FAILED: {e}")

def test_advanced_recommendation_engine():
    """Test the advanced recommendation engine."""
    logger.info("Testing Advanced Recommendation Engine...")
    
    try:
        from advanced_recommendation_engine import get_recommendation_engine
        
        # Get the recommendation engine
        rec_engine = get_recommendation_engine()
        
        # Test personalized recommendations
        recommendations = rec_engine.get_personalized_recommendations(
            skin_tone="Monk 3",
            user_preferences={
                'season': 'Summer',
                'style': 'casual',
                'preferred_brands': ['Sephora', 'MAC'],
                'budget_range': [20, 80]
            },
            n_recommendations=5
        )
        
        if recommendations and 'recommendations' in recommendations:
            logger.info("✅ Advanced Recommendation Engine: SUCCESS")
            makeup_count = len(recommendations['recommendations']['makeup'])
            outfit_count = len(recommendations['recommendations']['outfits'])
            logger.info(f"   - Makeup recommendations: {makeup_count}")
            logger.info(f"   - Outfit recommendations: {outfit_count}")
            logger.info(f"   - Recommendation method: {recommendations['metadata']['recommendation_method']}")
        else:
            logger.warning("⚠️ Advanced Recommendation Engine: No recommendations returned")
            
        # Test trending items
        trending_makeup = rec_engine.get_trending_items(product_type='makeup', n_items=3)
        trending_outfits = rec_engine.get_trending_items(product_type='outfit', n_items=3)
        
        logger.info(f"   - Trending makeup items: {len(trending_makeup)}")
        logger.info(f"   - Trending outfit items: {len(trending_outfits)}")
        
        # Test user feedback
        rec_engine.add_user_feedback(
            user_id="test_user_123",
            item_id="test_item_456",
            rating=4.5,
            interaction_type="rating"
        )
        logger.info("   - User feedback test: SUCCESS")
        
    except Exception as e:
        logger.error(f"❌ Advanced Recommendation Engine FAILED: {e}")

def test_fastapi_integration():
    """Test FastAPI integration with new endpoints."""
    logger.info("Testing FastAPI Integration...")
    
    try:
        import requests
        import json
        
        # Test if we can import the main FastAPI app
        from prods_fastapi.main import app
        logger.info("✅ FastAPI Import: SUCCESS")
        
        # Note: To fully test the FastAPI endpoints, you would need to run the server
        # and make actual HTTP requests. This is a basic import test.
        
        logger.info("   - FastAPI app imported successfully")
        logger.info("   - New ML endpoints should be available:")
        logger.info("     • /api/advanced-recommendations")
        logger.info("     • /api/trending-items")
        logger.info("     • /api/user-feedback")
        logger.info("     • /api/content-recommendations")
        
    except Exception as e:
        logger.error(f"❌ FastAPI Integration FAILED: {e}")

def test_data_availability():
    """Test if required data files are available."""
    logger.info("Testing Data Availability...")
    
    data_files = [
        "processed_data/all_makeup_products.csv",
        "processed_data/all_combined_outfits.csv",
        "processed_data/seasonal_palettes.json",
        "../processed_data/all_makeup_products.csv",
        "../processed_data/all_combined_outfits.csv",
        "../processed_data/seasonal_palettes.json"
    ]
    
    found_files = []
    for file_path in data_files:
        if os.path.exists(file_path):
            found_files.append(file_path)
            logger.info(f"   ✅ Found: {file_path}")
    
    if found_files:
        logger.info(f"✅ Data Availability: {len(found_files)} data files found")
    else:
        logger.warning("⚠️ Data Availability: No data files found - recommendations may use synthetic data")

def test_lighting_correction():
    """Test the improved lighting correction algorithms."""
    logger.info("Testing Lighting Correction...")
    
    try:
        from prods_fastapi.main import apply_lighting_correction, apply_white_balance
        
        # Create a test image with poor lighting
        test_image = np.random.randint(50, 100, (100, 100, 3), dtype=np.uint8)
        
        # Test CLAHE correction
        corrected_clahe = apply_lighting_correction(test_image)
        
        # Test white balance correction
        corrected_wb = apply_white_balance(test_image)
        
        # Verify that corrections were applied (check if images are different)
        clahe_different = not np.array_equal(test_image, corrected_clahe)
        wb_different = not np.array_equal(test_image, corrected_wb)
        
        if clahe_different and wb_different:
            logger.info("✅ Lighting Correction: SUCCESS")
            logger.info("   - CLAHE correction applied")
            logger.info("   - White balance correction applied")
        else:
            logger.warning("⚠️ Lighting Correction: Corrections may not be working properly")
            
    except Exception as e:
        logger.error(f"❌ Lighting Correction FAILED: {e}")

def run_all_tests():
    """Run all tests for ML enhancements."""
    logger.info("=" * 60)
    logger.info("🚀 STARTING ML ENHANCEMENTS TEST SUITE")
    logger.info("=" * 60)
    
    # Test individual components
    test_data_availability()
    print()
    
    test_lighting_correction()
    print()
    
    test_enhanced_skin_analysis()
    print()
    
    test_advanced_recommendation_engine()
    print()
    
    test_fastapi_integration()
    print()
    
    logger.info("=" * 60)
    logger.info("🏁 TEST SUITE COMPLETED")
    logger.info("=" * 60)
    logger.info("📋 NEXT STEPS:")
    logger.info("1. Install enhanced dependencies: pip install -r requirements_enhanced_ml.txt")
    logger.info("2. Start the FastAPI server: python -m uvicorn prods_fastapi.main:app --reload")
    logger.info("3. Test the new endpoints with a tool like Postman or curl")
    logger.info("4. Upload test images to verify skin tone analysis improvements")
    logger.info("5. Monitor recommendation quality with user feedback")

if __name__ == "__main__":
    run_all_tests()
