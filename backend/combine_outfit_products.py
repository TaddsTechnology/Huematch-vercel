#!/usr/bin/env python3
"""
Combine all outfit products from JSON and CSV files into a single comprehensive CSV file.

This script will:
1. Load products from Twirl Around World JSON file
2. Load products from existing CSV files (H&M, outfit1, outfit2, etc.)
3. Standardize the data format
4. Remove duplicates
5. Save to a single comprehensive CSV file
"""

import json
import pandas as pd
import os
import ast
from pathlib import Path
import logging
import re

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OutfitCombiner:
    def __init__(self, base_dir=None):
        """Initialize the outfit combiner with base directory."""
        self.base_dir = base_dir or Path(__file__).parent
        self.all_products = []
        self.standardized_products = []
        
    def load_twirl_json(self, json_path):
        """Load products from Twirl Around World JSON file."""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract products from the JSON structure
            products = []
            if isinstance(data, list) and len(data) > 0:
                if 'products' in data[0]:
                    products = data[0]['products']
                else:
                    products = data
            
            logger.info(f"Loaded {len(products)} products from {json_path}")
            return products
            
        except Exception as e:
            logger.error(f"Error loading JSON file {json_path}: {e}")
            return []
    
    def load_csv_products(self, csv_path):
        """Load products from CSV file."""
        try:
            df = pd.read_csv(csv_path)
            products = df.to_dict('records')
            logger.info(f"Loaded {len(products)} products from {csv_path}")
            return products
            
        except Exception as e:
            logger.error(f"Error loading CSV file {csv_path}: {e}")
            return []
    
    def parse_json_products_column(self, products_str):
        """Parse JSON string from products column in CSV files."""
        try:
            if pd.isna(products_str) or products_str == '':
                return []
            
            # Try to parse as JSON string
            products = ast.literal_eval(products_str)
            if isinstance(products, list):
                return products
            return []
            
        except Exception as e:
            logger.warning(f"Could not parse products string: {e}")
            return []
    
    def standardize_product(self, product, source="unknown"):
        """Standardize product data to common format."""
        standardized = {
            'brand': '',
            'product_name': '',
            'price': '',
            'gender': '',
            'image_url': '',
            'base_colour': '',
            'product_type': '',
            'sub_category': '',
            'master_category': '',
            'source': source
        }
        
        # Handle different field names and formats
        field_mappings = {
            'brand': ['brand', 'Brand'],
            'product_name': ['product_name', 'Product Name', 'Product_Name', 'name'],
            'price': ['price', 'Price'],
            'gender': ['gender', 'Gender'],
            'image_url': ['image_url', 'Image URL', 'Image_URL', 'images', 'imgSrc'],
            'base_colour': ['base_colour', 'baseColour', 'color', 'Color'],
            'product_type': ['product_type', 'Product Type', 'Product_Type', 'type'],
            'sub_category': ['sub_category', 'subCategory', 'Sub Category'],
            'master_category': ['master_category', 'masterCategory', 'Master Category', 'category']
        }
        
        for std_field, possible_fields in field_mappings.items():
            for field in possible_fields:
                if field in product and product[field] and pd.notna(product[field]):
                    standardized[std_field] = str(product[field]).strip()
                    break
        
        # Clean up empty values
        for key, value in standardized.items():
            if value == '' or value == 'nan' or pd.isna(value):
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
    
    def clean_price(self, price_str):
        """Clean and standardize price format."""
        if not price_str or pd.isna(price_str):
            return ''
        
        price_str = str(price_str).strip()
        
        # Extract numeric value from price string
        price_match = re.search(r'[\d,]+\.?\d*', price_str)
        if price_match:
            numeric_part = price_match.group()
            # Remove commas and convert to float
            try:
                price_value = float(numeric_part.replace(',', ''))
                # Determine currency
                if 'Rs.' in price_str or '₹' in price_str:
                    return f"Rs. {price_value:.2f}"
                elif '$' in price_str:
                    return f"${price_value:.2f}"
                elif '£' in price_str:
                    return f"£{price_value:.2f}"
                else:
                    return f"${price_value:.2f}"  # Default to USD
            except ValueError:
                return price_str
        
        return price_str
    
    def remove_duplicates(self, products):
        """Remove duplicate products based on name and brand."""
        seen = set()
        unique_products = []
        
        for product in products:
            key = (product['brand'].lower(), product['product_name'].lower())
            if key not in seen:
                seen.add(key)
                unique_products.append(product)
        
        logger.info(f"Removed {len(products) - len(unique_products)} duplicate products")
        return unique_products
    
    def combine_all_products(self):
        """Combine products from all sources."""
        logger.info("Starting to combine all outfit products...")
        
        # Load from Twirl Around World JSON
        twirl_json_path = self.base_dir / "datasets" / "product twirl.json"
        if twirl_json_path.exists():
            twirl_products = self.load_twirl_json(twirl_json_path)
            for product in twirl_products:
                standardized = self.standardize_product(product, "twirl_json")
                self.all_products.append(standardized)
        
        # Load from Twirl Around World CSV
        twirl_csv_path = self.base_dir / "datasets" / "product_twirl.csv"
        if twirl_csv_path.exists():
            twirl_csv_products = self.load_csv_products(twirl_csv_path)
            for product in twirl_csv_products:
                standardized = self.standardize_product(product, "twirl_csv")
                self.all_products.append(standardized)
        
        # Load from H&M products
        hm_paths = [
            self.base_dir / "processed_data" / "hm_products_hm_products.csv",
            self.base_dir / "processed_data" / "hm_products_hm_products2.csv"
        ]
        
        for hm_path in hm_paths:
            if hm_path.exists():
                hm_products = self.load_csv_products(hm_path)
                for product in hm_products:
                    standardized = self.standardize_product(product, "hm")
                    self.all_products.append(standardized)
        
        # Load from outfit CSV files
        outfit_paths = [
            self.base_dir / "processed_data" / "outfit_products_outfit1.csv",
            self.base_dir / "processed_data" / "outfit_products_outfit2.csv",
            self.base_dir / "processed_data" / "all_outfits.csv",
            self.base_dir / "processed_data" / "sample_outfits.csv"
        ]
        
        for outfit_path in outfit_paths:
            if outfit_path.exists():
                outfit_data = self.load_csv_products(outfit_path)
                for row in outfit_data:
                    # Check if this has a 'products' column with JSON data
                    if 'products' in row:
                        products_list = self.parse_json_products_column(row['products'])
                        for product in products_list:
                            standardized = self.standardize_product(product, f"outfit_{outfit_path.stem}")
                            self.all_products.append(standardized)
                    else:
                        # Regular product row
                        standardized = self.standardize_product(row, f"outfit_{outfit_path.stem}")
                        self.all_products.append(standardized)
        
        # Clean prices
        for product in self.all_products:
            product['price'] = self.clean_price(product['price'])
        
        # Remove duplicates
        self.all_products = self.remove_duplicates(self.all_products)
        
        logger.info(f"Combined {len(self.all_products)} unique products from all sources")
        
        return self.all_products
    
    def save_combined_csv(self, output_path):
        """Save combined products to CSV file."""
        if not self.all_products:
            logger.warning("No products to save!")
            return
        
        df = pd.DataFrame(self.all_products)
        
        # Reorder columns for better readability
        column_order = [
            'brand', 'product_name', 'price', 'gender', 'image_url', 
            'base_colour', 'product_type', 'sub_category', 'master_category', 'source'
        ]
        
        df = df[column_order]
        
        # Save to CSV
        df.to_csv(output_path, index=False, encoding='utf-8')
        logger.info(f"Saved {len(df)} products to {output_path}")
        
        # Print summary statistics
        print(f"\n=== SUMMARY ===")
        print(f"Total products: {len(df)}")
        print(f"Unique brands: {df['brand'].nunique()}")
        print(f"Products by gender:")
        print(df['gender'].value_counts())
        print(f"\nProducts by master category:")
        print(df['master_category'].value_counts())
        print(f"\nProducts by source:")
        print(df['source'].value_counts())
        
        return df


def main():
    """Main function to run the outfit combiner."""
    # Initialize combiner
    base_dir = Path(__file__).parent
    combiner = OutfitCombiner(base_dir)
    
    # Combine all products
    products = combiner.combine_all_products()
    
    # Save to CSV
    output_path = base_dir / "processed_data" / "all_combined_outfits.csv"
    output_path.parent.mkdir(exist_ok=True)
    
    df = combiner.save_combined_csv(output_path)
    
    print(f"\n✅ Successfully created combined outfits CSV file: {output_path}")
    print(f"📊 Total products: {len(df)}")
    print(f"🏷️  Unique brands: {df['brand'].nunique()}")


if __name__ == "__main__":
    main()
