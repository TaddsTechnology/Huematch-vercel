#!/usr/bin/env python3
"""
Advanced Product Combiner for AI-Fashion Backend
Properly combines outfit and makeup products with intelligent column mapping
"""

import pandas as pd
import json
import os
import ast
from pathlib import Path
import logging
import re

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AdvancedProductCombiner:
    def __init__(self, base_dir=None):
        """Initialize the advanced product combiner."""
        self.base_dir = base_dir or Path(__file__).parent
        self.outfit_products = []
        self.makeup_products = []
        
        # Define column mappings for different data sources
        self.outfit_column_mappings = {
            'brand': ['brand', 'Brand', 'BRAND'],
            'product_name': ['product_name', 'Product Name', 'productDisplayName', 'products', 'Product', 'PRODUCT_NAME'],
            'price': ['price', 'Price', 'PRICE'],
            'gender': ['gender', 'Gender', 'GENDER'],
            'image_url': ['image_url', 'Image URL', 'images', 'imgSrc', 'IMAGE_URL'],
            'base_colour': ['base_colour', 'baseColour', 'Base Colour', 'COLOR', 'color'],
            'product_type': ['product_type', 'Product Type', 'productType', 'subCategory', 'PRODUCT_TYPE'],
            'sub_category': ['sub_category', 'subCategory', 'Sub Category', 'SUB_CATEGORY'],
            'master_category': ['master_category', 'masterCategory', 'Master Category', 'MASTER_CATEGORY'],
            'season': ['season', 'Season', 'SEASON'],
            'year': ['year', 'Year', 'YEAR'],
            'usage': ['usage', 'Usage', 'USAGE'],
            'source': ['source', 'Source', 'SOURCE']
        }
        
        self.makeup_column_mappings = {
            'brand': ['brand', 'Brand', 'BRAND'],
            'product_name': ['product_name', 'product', 'Product', 'Product Name', 'PRODUCT_NAME'],
            'price': ['price', 'Price', 'PRICE'],
            'image_url': ['imgSrc', 'image_url', 'images', 'Image URL', 'IMAGE_URL'],
            'product_type': ['product_type', 'Product Type', 'category', 'Category', 'PRODUCT_TYPE'],
            'shade': ['shade', 'Shade', 'mst', 'MST', 'SHADE'],
            'color_hex': ['hex', 'color_hex', 'Color Hex', 'HEX', 'COLOR_HEX'],
            'description': ['description', 'desc', 'Description', 'DESCRIPTION'],
            'url': ['url', 'URL', 'product_url', 'Product URL'],
            'image_alt': ['imgAlt', 'image_alt', 'Image Alt', 'IMAGE_ALT'],
            'source': ['source', 'Source', 'SOURCE']
        }
    
    def get_column_value(self, row, column_mappings, target_column):
        """Get value from row using column mappings."""
        for possible_column in column_mappings.get(target_column, []):
            if possible_column in row and pd.notna(row[possible_column]):
                value = row[possible_column]
                # Clean up the value
                if isinstance(value, str):
                    value = value.strip()
                    if value.lower() in ['', 'null', 'none', 'nan', 'n/a']:
                        continue
                return value
        return None
    
    def process_outfit_product(self, row, source_file="unknown"):
        """Process a single outfit product row."""
        return {
            'brand': self.get_column_value(row, self.outfit_column_mappings, 'brand') or "Unknown Brand",
            'product_name': self.get_column_value(row, self.outfit_column_mappings, 'product_name') or "Unnamed Product",
            'price': self.get_column_value(row, self.outfit_column_mappings, 'price') or "Price not available",
            'gender': self.get_column_value(row, self.outfit_column_mappings, 'gender') or "Unisex",
            'image_url': self.get_column_value(row, self.outfit_column_mappings, 'image_url') or "No image",
            'base_colour': self.get_column_value(row, self.outfit_column_mappings, 'base_colour') or "Color not specified",
            'product_type': self.get_column_value(row, self.outfit_column_mappings, 'product_type') or "General Apparel",
            'sub_category': self.get_column_value(row, self.outfit_column_mappings, 'sub_category') or "General",
            'master_category': self.get_column_value(row, self.outfit_column_mappings, 'master_category') or "Apparel",
            'season': self.get_column_value(row, self.outfit_column_mappings, 'season') or "All Season",
            'year': self.get_column_value(row, self.outfit_column_mappings, 'year') or "Current",
            'usage': self.get_column_value(row, self.outfit_column_mappings, 'usage') or "Casual",
            'source': source_file
        }
    
    def process_makeup_product(self, row, source_file="unknown"):
        """Process a single makeup product row."""
        return {
            'brand': self.get_column_value(row, self.makeup_column_mappings, 'brand') or "Unknown Brand",
            'product_name': self.get_column_value(row, self.makeup_column_mappings, 'product_name') or "Unnamed Product",
            'price': self.get_column_value(row, self.makeup_column_mappings, 'price') or "Price not available",
            'image_url': self.get_column_value(row, self.makeup_column_mappings, 'image_url') or "No image",
            'product_type': self.get_column_value(row, self.makeup_column_mappings, 'product_type') or "Beauty Product",
            'shade': self.get_column_value(row, self.makeup_column_mappings, 'shade') or "Shade not specified",
            'color_hex': self.get_column_value(row, self.makeup_column_mappings, 'color_hex') or "Color not available",
            'description': self.get_column_value(row, self.makeup_column_mappings, 'description') or "No description",
            'url': self.get_column_value(row, self.makeup_column_mappings, 'url') or "No URL",
            'image_alt': self.get_column_value(row, self.makeup_column_mappings, 'image_alt') or "No alt text",
            'source': source_file
        }
    
    def is_makeup_file(self, filename):
        """Determine if a file contains makeup products."""
        makeup_keywords = ['makeup', 'sephora', 'ulta', 'beauty', 'cosmetic', 'foundation', 'lipstick', 'mascara']
        return any(keyword in filename.lower() for keyword in makeup_keywords)
    
    def load_csv_file(self, file_path, product_type):
        """Load products from a CSV file."""
        try:
            df = pd.read_csv(file_path)
            logger.info(f"Loading {len(df)} products from {file_path}")
            
            source_file = Path(file_path).stem
            
            for _, row in df.iterrows():
                try:
                    if product_type == "outfit":
                        product = self.process_outfit_product(row, source_file)
                        self.outfit_products.append(product)
                    else:
                        product = self.process_makeup_product(row, source_file)
                        self.makeup_products.append(product)
                except Exception as e:
                    logger.warning(f"Error processing row in {file_path}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
    
    def load_json_file(self, file_path, product_type):
        """Load products from a JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            source_file = Path(file_path).stem
            products_loaded = 0
            
            # Handle different JSON structures
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        if 'products' in item and isinstance(item['products'], list):
                            # Structure: [{"products": [...]}]
                            for product_data in item['products']:
                                try:
                                    if product_type == "outfit":
                                        product = self.process_outfit_product(product_data, source_file)
                                        self.outfit_products.append(product)
                                    else:
                                        product = self.process_makeup_product(product_data, source_file)
                                        self.makeup_products.append(product)
                                    products_loaded += 1
                                except Exception as e:
                                    logger.warning(f"Error processing product in {file_path}: {e}")
                                    continue
                        else:
                            # Structure: [{product1}, {product2}, ...]
                            try:
                                if product_type == "outfit":
                                    product = self.process_outfit_product(item, source_file)
                                    self.outfit_products.append(product)
                                else:
                                    product = self.process_makeup_product(item, source_file)
                                    self.makeup_products.append(product)
                                products_loaded += 1
                            except Exception as e:
                                logger.warning(f"Error processing item in {file_path}: {e}")
                                continue
            elif isinstance(data, dict):
                if 'products' in data and isinstance(data['products'], list):
                    for product_data in data['products']:
                        try:
                            if product_type == "outfit":
                                product = self.process_outfit_product(product_data, source_file)
                                self.outfit_products.append(product)
                            else:
                                product = self.process_makeup_product(product_data, source_file)
                                self.makeup_products.append(product)
                            products_loaded += 1
                        except Exception as e:
                            logger.warning(f"Error processing product in {file_path}: {e}")
                            continue
                else:
                    # Single product
                    try:
                        if product_type == "outfit":
                            product = self.process_outfit_product(data, source_file)
                            self.outfit_products.append(product)
                        else:
                            product = self.process_makeup_product(data, source_file)
                            self.makeup_products.append(product)
                        products_loaded += 1
                    except Exception as e:
                        logger.warning(f"Error processing single product in {file_path}: {e}")
            
            logger.info(f"Loaded {products_loaded} products from {file_path}")
                    
        except Exception as e:
            logger.error(f"Error reading JSON file {file_path}: {e}")
    
    def scan_directory(self, directory):
        """Scan directory for product files."""
        dir_path = Path(directory)
        if not dir_path.exists():
            logger.warning(f"Directory not found: {directory}")
            return
            
        logger.info(f"Scanning directory: {directory}")
        
        # Find all CSV and JSON files
        csv_files = list(dir_path.glob("*.csv"))
        json_files = list(dir_path.glob("*.json"))
        
        for csv_file in csv_files:
            if self.is_makeup_file(csv_file.name):
                self.load_csv_file(str(csv_file), "makeup")
            else:
                self.load_csv_file(str(csv_file), "outfit")
        
        for json_file in json_files:
            if self.is_makeup_file(json_file.name):
                self.load_json_file(str(json_file), "makeup")
            else:
                self.load_json_file(str(json_file), "outfit")
    
    def save_products_to_csv(self, products, filename, product_type):
        """Save products to CSV file."""
        if not products:
            logger.warning(f"No {product_type} products to save")
            return
            
        df = pd.DataFrame(products)
        
        # Remove duplicates based on product_name and brand
        initial_count = len(df)
        df = df.drop_duplicates(subset=['product_name', 'brand'], keep='first')
        final_count = len(df)
        
        if initial_count > final_count:
            logger.info(f"Removed {initial_count - final_count} duplicate {product_type} products")
        
        df.to_csv(filename, index=False)
        logger.info(f"Saved {final_count} {product_type} products to {filename}")
    
    def combine_all_products(self):
        """Combine all products from all directories."""
        logger.info("🚀 Starting advanced product combination...")
        
        # Directories to scan
        directories_to_scan = [
            self.base_dir / "processed_data",
            self.base_dir / "unprocessed_data", 
            self.base_dir / "datasets",
            self.base_dir / "prods_fastapi",
            self.base_dir / "prods_fastapi" / "processed_data",
            self.base_dir  # Root directory
        ]
        
        # Scan each directory
        for directory in directories_to_scan:
            self.scan_directory(directory)
        
        # Save combined products
        self.save_products_to_csv(self.outfit_products, "final_outfits_combined.csv", "outfit")
        self.save_products_to_csv(self.makeup_products, "final_makeup_combined.csv", "makeup")
        
        # Print summary
        print("\n" + "="*80)
        print("🎉 ADVANCED PRODUCT COMBINATION COMPLETE!")
        print("="*80)
        print(f"✅ Total Outfit Products: {len(self.outfit_products):,}")
        print(f"✅ Total Makeup Products: {len(self.makeup_products):,}")
        print(f"✅ Total Combined Products: {len(self.outfit_products) + len(self.makeup_products):,}")
        print("\n📄 Files Created:")
        print("   • final_outfits_combined.csv")
        print("   • final_makeup_combined.csv")
        print("="*80)

def main():
    """Main function to run the advanced product combiner."""
    combiner = AdvancedProductCombiner()
    combiner.combine_all_products()

if __name__ == "__main__":
    main()
