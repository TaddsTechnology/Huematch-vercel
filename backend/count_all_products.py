#!/usr/bin/env python3
"""
Comprehensive product counter for AI-Fashion backend.
Counts all outfit and makeup products from all CSV and JSON files.
"""

import pandas as pd
import json
import os
import ast
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProductCounter:
    def __init__(self, base_dir=None):
        """Initialize the product counter."""
        self.base_dir = base_dir or Path(__file__).parent
        self.outfit_count = 0
        self.makeup_count = 0
        self.total_products = 0
        self.product_breakdown = {}
        self.brands = set()
        self.categories = set()
        
    def count_csv_products(self, file_path, product_type="outfit"):
        """Count products from a CSV file."""
        try:
            if not os.path.exists(file_path):
                logger.warning(f"File not found: {file_path}")
                return 0
                
            df = pd.read_csv(file_path)
            count = len(df)
            
            # Extract brands and categories
            if 'brand' in df.columns:
                self.brands.update(df['brand'].dropna().unique())
            if 'Brand' in df.columns:
                self.brands.update(df['Brand'].dropna().unique())
                
            # Extract categories
            for cat_col in ['master_category', 'masterCategory', 'Product Type', 'product_type']:
                if cat_col in df.columns:
                    self.categories.update(df[cat_col].dropna().unique())
            
            logger.info(f"✅ {file_path}: {count} products")
            self.product_breakdown[file_path] = count
            
            if product_type == "outfit":
                self.outfit_count += count
            else:
                self.makeup_count += count
                
            return count
            
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
            return 0
    
    def count_json_products(self, file_path, product_type="outfit"):
        """Count products from a JSON file."""
        try:
            if not os.path.exists(file_path):
                logger.warning(f"File not found: {file_path}")
                return 0
                
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            count = 0
            
            # Handle different JSON structures
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        if 'products' in item:
                            # Structure: [{"products": [...]}]
                            products = item['products']
                            if isinstance(products, list):
                                count += len(products)
                                # Extract brands
                                for product in products:
                                    if 'brand' in product:
                                        self.brands.add(product['brand'])
                                    if 'master_category' in product:
                                        self.categories.add(product['master_category'])
                        else:
                            # Structure: [{product1}, {product2}, ...]
                            count += 1
                            if 'brand' in item:
                                self.brands.add(item['brand'])
                            if 'master_category' in item:
                                self.categories.add(item['master_category'])
            elif isinstance(data, dict):
                if 'products' in data:
                    count = len(data['products'])
                else:
                    count = 1
            
            logger.info(f"✅ {file_path}: {count} products")
            self.product_breakdown[file_path] = count
            
            if product_type == "outfit":
                self.outfit_count += count
            else:
                self.makeup_count += count
                
            return count
            
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
            return 0
    
    def scan_directory(self, directory):
        """Scan directory for product files."""
        dir_path = Path(directory)
        if not dir_path.exists():
            logger.warning(f"Directory not found: {directory}")
            return
            
        logger.info(f"🔍 Scanning directory: {directory}")
        
        # Find all CSV and JSON files
        csv_files = list(dir_path.glob("*.csv"))
        json_files = list(dir_path.glob("*.json"))
        
        for csv_file in csv_files:
            filename = csv_file.name.lower()
            
            # Determine if it's makeup or outfit based on filename
            if any(makeup_keyword in filename for makeup_keyword in 
                   ['makeup', 'sephora', 'ulta', 'beauty', 'cosmetic']):
                self.count_csv_products(str(csv_file), "makeup")
            else:
                self.count_csv_products(str(csv_file), "outfit")
        
        for json_file in json_files:
            filename = json_file.name.lower()
            
            # Determine if it's makeup or outfit based on filename
            if any(makeup_keyword in filename for makeup_keyword in 
                   ['makeup', 'sephora', 'ulta', 'beauty', 'cosmetic']):
                self.count_json_products(str(json_file), "makeup")
            else:
                self.count_json_products(str(json_file), "outfit")
    
    def count_all_products(self):
        """Count all products across the entire backend folder."""
        logger.info("🚀 Starting comprehensive product count...")
        
        # Main directories to scan
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
        
        # Calculate total
        self.total_products = self.outfit_count + self.makeup_count
        
        return self.generate_report()
    
    def generate_report(self):
        """Generate a comprehensive report."""
        report = {
            "summary": {
                "total_outfit_products": self.outfit_count,
                "total_makeup_products": self.makeup_count,
                "total_products": self.total_products,
                "unique_brands": len(self.brands),
                "unique_categories": len(self.categories)
            },
            "detailed_breakdown": self.product_breakdown,
            "brands": sorted(list(self.brands)),
            "categories": sorted(list(self.categories))
        }
        
        return report
    
    def print_report(self):
        """Print a formatted report."""
        print("\n" + "="*80)
        print("📊 AI-FASHION BACKEND - COMPLETE PRODUCT INVENTORY")
        print("="*80)
        
        print(f"\n🎯 SUMMARY:")
        print(f"   👗 Total Outfit Products: {self.outfit_count:,}")
        print(f"   💄 Total Makeup Products: {self.makeup_count:,}")
        print(f"   📦 TOTAL PRODUCTS: {self.total_products:,}")
        print(f"   🏷️  Unique Brands: {len(self.brands)}")
        print(f"   📂 Unique Categories: {len(self.categories)}")
        
        print(f"\n📋 DETAILED BREAKDOWN BY FILE:")
        for file_path, count in self.product_breakdown.items():
            filename = Path(file_path).name
            print(f"   • {filename}: {count:,} products")
        
        print(f"\n🏷️  BRANDS FOUND ({len(self.brands)}):")
        brands_list = sorted(list(self.brands))
        for i, brand in enumerate(brands_list, 1):
            print(f"   {i:2d}. {brand}")
        
        print(f"\n📂 CATEGORIES FOUND ({len(self.categories)}):")
        categories_list = sorted(list(self.categories))
        for i, category in enumerate(categories_list, 1):
            print(f"   {i:2d}. {category}")
        
        print("\n" + "="*80)
        
        # Save report to file
        report_data = self.generate_report()
        with open('product_inventory_report.json', 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print("💾 Detailed report saved to: product_inventory_report.json")
        print("="*80)

def main():
    """Main function to run the product counter."""
    counter = ProductCounter()
    counter.count_all_products()
    counter.print_report()

if __name__ == "__main__":
    main()
