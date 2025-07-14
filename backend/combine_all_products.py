#!/usr/bin/env python3
"""
Combine all outfit and makeup products into separate CSV files with a standardized structure.
"""

import pandas as pd
import os
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProductCombiner:
    def __init__(self, base_dir=None):
        """Initialize the product combiner."""
        self.base_dir = base_dir or Path(__file__).parent
        self.outfit_products = []
        self.makeup_products = []

    def combine_csv_files(self, directory, output_file, product_type="outfit"):
        """Combine products from CSV files into a single file."""
        dir_path = Path(directory)
        if not dir_path.exists():
            logger.warning(f"Directory not found: {directory}")
            return

        # Find all CSV files
        csv_files = list(dir_path.glob("*.csv"))

        for csv_file in csv_files:
            filename = csv_file.name.lower()

            # Determine if it's makeup or outfit based on product type and file name
            if product_type == "makeup" and any(keyword in filename for keyword in ['makeup', 'sephora', 'ulta', 'beauty', 'cosmetic']):
                self._load_csv_file(csv_file, product_type)
            elif product_type == "outfit" and not any(keyword in filename for keyword in ['makeup', 'sephora', 'ulta', 'beauty', 'cosmetic']):
                self._load_csv_file(csv_file, product_type)

        # Save combined products to file
        self._save_combined_file(output_file, product_type)

    def _load_csv_file(self, file_path, product_type):
        """Load products from a CSV file."""
        try:
            df = pd.read_csv(file_path)
            logger.info(f"Loaded {len(df)} products from {file_path}")
            for _, row in df.iterrows():
                product = self._create_product_dict(row, product_type)
                if product_type == "outfit":
                    self.outfit_products.append(product)
                else:
                    self.makeup_products.append(product)
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")

    def _create_product_dict(self, row, product_type):
        """Create a standardized product dictionary."""
        if product_type == "outfit":
            return {
                "brand": row.get('brand', 'N/A'),
                "product_name": row.get('product_name', row.get('Product Name', 'N/A')),
                "price": row.get('price', row.get('Price', 'N/A')),
                "gender": row.get('gender', 'Unisex'),
                "image_url": row.get('image_url', row.get('Image URL', 'N/A')),
                "base_colour": row.get('base_colour', row.get('baseColour', 'N/A')),
                "product_type": row.get('product_type', row.get('Product Type', 'N/A')),
                "sub_category": row.get('sub_category', row.get('subCategory', 'N/A')),
                "master_category": row.get('master_category', row.get('masterCategory', 'N/A'))
            }
        elif product_type == "makeup":
            return {
                "brand": row.get('brand', 'N/A'),
                "product_name": row.get('product_name', row.get('Product', 'N/A')),
                "price": row.get('price', row.get('Price', 'N/A')),
                "image_url": row.get('imgSrc', row.get('images', 'N/A')),
                "product_type": row.get('product_type', row.get('Product Type', 'N/A')),
                "shade": row.get('shade', row.get('mst', 'N/A')),
                "color_hex": row.get('hex', 'N/A'),
                "description": row.get('desc', 'N/A')
            }

    def _save_combined_file(self, output_file, product_type):
        """Save combined products to a CSV file."""
        if product_type == "outfit":
            df = pd.DataFrame(self.outfit_products)
        else:
            df = pd.DataFrame(self.makeup_products)

        df.fillna('N/A', inplace=True)
        df.to_csv(output_file, index=False)
        logger.info(f"Combined {product_type} products saved to {output_file}")

    def combine_all_products(self):
        """Combine all outfit and makeup products and save to files."""
        outfit_output = self.base_dir / 'combined_outfits.csv'
        makeup_output = self.base_dir / 'combined_makeup.csv'

        self.combine_csv_files(self.base_dir / "processed_data", outfit_output, "outfit")
        self.combine_csv_files(self.base_dir / "prods_fastapi", makeup_output, "makeup")

        logger.info(f"All products combined!")

def main():
    """Main function to run the product combiner."""
    combiner = ProductCombiner()
    combiner.combine_all_products()

if __name__ == "__main__":
    main()

