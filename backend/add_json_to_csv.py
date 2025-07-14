#!/usr/bin/env python3
"""
Add new JSON products to the combined CSV file.

This script allows you to add new outfit products from JSON files to the existing combined CSV.
"""

import json
import pandas as pd
import os
import argparse
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_json_products(json_path):
    """Load products from JSON file."""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract products from the JSON structure
        products = []
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and 'products' in item:
                    products.extend(item['products'])
                else:
                    products.append(item)
        elif isinstance(data, dict):
            if 'products' in data:
                products = data['products']
            else:
                products = [data]
        else:
            products = [data]
        
        logger.info(f"Loaded {len(products)} products from {json_path}")
        return products
        
    except Exception as e:
        logger.error(f"Error loading JSON file {json_path}: {e}")
        return []

def standardize_product(product, source="json"):
    """Standardize product data to match CSV format."""
    standardized = {
        'brand': product.get('brand', ''),
        'product_name': product.get('product_name', product.get('name', '')),
        'price': product.get('price', ''),
        'gender': product.get('gender', 'Unisex'),
        'image_url': product.get('image_url', product.get('images', '')),
        'base_colour': product.get('base_colour', product.get('color', '')),
        'product_type': product.get('product_type', product.get('type', '')),
        'sub_category': product.get('sub_category', product.get('subcategory', '')),
        'master_category': product.get('master_category', product.get('category', 'Apparel')),
        'source': source
    }
    
    # Clean up empty values
    for key, value in standardized.items():
        if not value or pd.isna(value):
            standardized[key] = ''
    
    # Set default values for missing fields
    if not standardized['brand']:
        standardized['brand'] = 'Fashion Brand'
    if not standardized['gender']:
        standardized['gender'] = 'Unisex'
    if not standardized['master_category']:
        standardized['master_category'] = 'Apparel'
    if not standardized['product_type']:
        standardized['product_type'] = 'Clothing'
    
    return standardized

def add_json_to_csv(json_file, csv_file, output_file=None):
    """Add JSON products to existing CSV file."""
    # Load existing CSV
    try:
        df_existing = pd.read_csv(csv_file)
        logger.info(f"Loaded {len(df_existing)} existing products from {csv_file}")
    except Exception as e:
        logger.error(f"Error loading CSV file {csv_file}: {e}")
        return False
    
    # Load JSON products
    json_products = load_json_products(json_file)
    if not json_products:
        logger.error("No products found in JSON file")
        return False
    
    # Standardize JSON products
    standardized_products = []
    for product in json_products:
        standardized = standardize_product(product, f"json_{Path(json_file).stem}")
        standardized_products.append(standardized)
    
    # Create DataFrame from new products
    df_new = pd.DataFrame(standardized_products)
    
    # Combine with existing data
    df_combined = pd.concat([df_existing, df_new], ignore_index=True)
    
    # Remove duplicates based on brand and product_name
    df_combined = df_combined.drop_duplicates(subset=['brand', 'product_name'], keep='first')
    
    # Save to output file
    if output_file is None:
        output_file = csv_file
    
    df_combined.to_csv(output_file, index=False, encoding='utf-8')
    
    logger.info(f"Added {len(df_new)} new products")
    logger.info(f"Total products after deduplication: {len(df_combined)}")
    logger.info(f"Saved to {output_file}")
    
    return True

def main():
    """Main function to run the script."""
    parser = argparse.ArgumentParser(description='Add JSON products to combined CSV file')
    parser.add_argument('json_file', help='Path to JSON file containing new products')
    parser.add_argument('--csv_file', default='processed_data/all_combined_outfits.csv', 
                       help='Path to existing CSV file (default: processed_data/all_combined_outfits.csv)')
    parser.add_argument('--output_file', help='Path to output CSV file (default: same as csv_file)')
    
    args = parser.parse_args()
    
    # Convert to absolute paths
    base_dir = Path(__file__).parent
    json_file = Path(args.json_file)
    csv_file = base_dir / args.csv_file
    output_file = base_dir / args.output_file if args.output_file else csv_file
    
    # Check if files exist
    if not json_file.exists():
        logger.error(f"JSON file not found: {json_file}")
        return
    
    if not csv_file.exists():
        logger.error(f"CSV file not found: {csv_file}")
        return
    
    # Add JSON products to CSV
    success = add_json_to_csv(json_file, csv_file, output_file)
    
    if success:
        print(f"✅ Successfully added products from {json_file} to {output_file}")
    else:
        print(f"❌ Failed to add products from {json_file}")

if __name__ == "__main__":
    main()
