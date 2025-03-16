import pandas as pd
import json
import os
import csv
from pathlib import Path
import random

def process_makeup_products():
    """
    Process makeup product data from datasets/makeup_product.csv, 
    datasets/makeup1.json, datasets/makeup2.json, and any Excel files
    """
    print("Processing makeup products...")
    
    # Create output directory if it doesn't exist
    os.makedirs('processed_data', exist_ok=True)
    
    all_makeup_products = []
    
    # Process CSV file
    csv_path = Path('../datasets/makeup_product.csv')
    if csv_path.exists():
        try:
            df_csv = pd.read_csv(csv_path)
            print(f"Read {len(df_csv)} products from CSV")
            
            # Add MST (Monk Skin Tone) column if it doesn't exist
            if 'mst' not in df_csv.columns:
                # Assign random MST values for demonstration
                mst_values = ['Light', 'Medium', 'Deep', 'Rich']
                df_csv['mst'] = [random.choice(mst_values) for _ in range(len(df_csv))]
            
            # Add description column if it doesn't exist
            if 'desc' not in df_csv.columns:
                df_csv['desc'] = df_csv['Product Name'].apply(
                    lambda x: f"Beautiful {x.lower()} for a flawless finish" if pd.notna(x) else ""
                )
            
            # Add hex color column if it doesn't exist
            if 'hex' not in df_csv.columns:
                # Generate random hex colors for demonstration
                def random_hex_color():
                    r = random.randint(0, 255)
                    g = random.randint(0, 255)
                    b = random.randint(0, 255)
                    return f"#{r:02x}{g:02x}{b:02x}"
                
                df_csv['hex'] = [random_hex_color() for _ in range(len(df_csv))]
            
            # Add product_type column if it doesn't exist
            if 'product_type' not in df_csv.columns:
                # Infer product type from product name
                def infer_product_type(name):
                    if pd.isna(name):
                        return "Unknown"
                    
                    name = name.lower()
                    if any(x in name for x in ['lipstick', 'lip gloss', 'lip']):
                        return "Lipstick"
                    elif any(x in name for x in ['foundation', 'base']):
                        return "Foundation"
                    elif any(x in name for x in ['mascara', 'lash']):
                        return "Mascara"
                    elif any(x in name for x in ['eyeshadow', 'eye shadow']):
                        return "Eyeshadow"
                    elif any(x in name for x in ['blush']):
                        return "Blush"
                    elif any(x in name for x in ['concealer']):
                        return "Concealer"
                    elif any(x in name for x in ['powder']):
                        return "Powder"
                    elif any(x in name for x in ['bronzer']):
                        return "Bronzer"
                    elif any(x in name for x in ['highlighter']):
                        return "Highlighter"
                    elif any(x in name for x in ['eyeliner']):
                        return "Eyeliner"
                    else:
                        return "Makeup"
                
                df_csv['product_type'] = df_csv['Product Name'].apply(infer_product_type)
            
            # Standardize column names
            column_mapping = {
                'Product Name': 'product',
                'brand': 'brand',
                'Image URL': 'imgSrc',
                'Price': 'price'
            }
            
            # Rename columns to match expected format
            for old_col, new_col in column_mapping.items():
                if old_col in df_csv.columns and new_col not in df_csv.columns:
                    df_csv[new_col] = df_csv[old_col]
            
            # Save processed CSV
            df_csv.to_csv('processed_data/makeup_products_csv.csv', index=False)
            print(f"Saved processed CSV with {len(df_csv)} products")
            
            # Add to combined list
            all_makeup_products.append(df_csv)
        except Exception as e:
            print(f"Error processing {csv_path}: {e}")
    else:
        print(f"Warning: {csv_path} not found")
    
    # Process Excel file
    excel_path = Path('../datasets/makeup_product.xlsx')
    if excel_path.exists():
        try:
            df_excel = pd.read_excel(excel_path)
            print(f"Read {len(df_excel)} products from Excel")
            
            # Add MST (Monk Skin Tone) column if it doesn't exist
            if 'mst' not in df_excel.columns:
                # Assign random MST values for demonstration
                mst_values = ['Light', 'Medium', 'Deep', 'Rich']
                df_excel['mst'] = [random.choice(mst_values) for _ in range(len(df_excel))]
            
            # Add description column if it doesn't exist
            if 'desc' not in df_excel.columns:
                df_excel['desc'] = df_excel['Product Name'].apply(
                    lambda x: f"Beautiful {x.lower()} for a flawless finish" if pd.notna(x) else ""
                )
            
            # Add hex color column if it doesn't exist
            if 'hex' not in df_excel.columns:
                df_excel['hex'] = [random_hex_color() for _ in range(len(df_excel))]
            
            # Add product_type column if it doesn't exist
            if 'product_type' not in df_excel.columns:
                df_excel['product_type'] = df_excel['Product Name'].apply(infer_product_type)
            
            # Standardize column names
            column_mapping = {
                'Product Name': 'product',
                'brand': 'brand',
                'Image URL': 'imgSrc',
                'Price': 'price'
            }
            
            # Rename columns to match expected format
            for old_col, new_col in column_mapping.items():
                if old_col in df_excel.columns and new_col not in df_excel.columns:
                    df_excel[new_col] = df_excel[old_col]
            
            # Save processed Excel
            df_excel.to_csv('processed_data/makeup_products_excel.csv', index=False)
            print(f"Saved processed Excel with {len(df_excel)} products")
            
            # Add to combined list
            all_makeup_products.append(df_excel)
        except Exception as e:
            print(f"Error processing {excel_path}: {e}")
    else:
        print(f"Warning: {excel_path} not found")
    
    # Process JSON files
    json_files = [
        Path('../datasets/makeup1.json'),
        Path('../datasets/makeup2.json')
    ]
    
    for json_path in json_files:
        if json_path.exists():
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Convert JSON to DataFrame
                df_json = pd.DataFrame(data)
                print(f"Read {len(df_json)} products from {json_path.name}")
                
                # Add MST (Monk Skin Tone) column if it doesn't exist
                if 'mst' not in df_json.columns:
                    # Assign random MST values for demonstration
                    mst_values = ['Light', 'Medium', 'Deep', 'Rich']
                    df_json['mst'] = [random.choice(mst_values) for _ in range(len(df_json))]
                
                # Add description column if it doesn't exist
                if 'desc' not in df_json.columns:
                    product_col = next((col for col in ['product', 'Product Name', 'name'] if col in df_json.columns), None)
                    if product_col:
                        df_json['desc'] = df_json[product_col].apply(
                            lambda x: f"Beautiful {x.lower()} for a flawless finish" if pd.notna(x) else ""
                        )
                    else:
                        df_json['desc'] = "Beautiful makeup product for a flawless finish"
                
                # Add hex color column if it doesn't exist
                if 'hex' not in df_json.columns:
                    df_json['hex'] = [random_hex_color() for _ in range(len(df_json))]
                
                # Add product_type column if it doesn't exist
                if 'product_type' not in df_json.columns:
                    product_col = next((col for col in ['product', 'Product Name', 'name'] if col in df_json.columns), None)
                    if product_col:
                        df_json['product_type'] = df_json[product_col].apply(infer_product_type)
                    else:
                        df_json['product_type'] = "Makeup"
                
                # Standardize column names
                column_mapping = {
                    'Product Name': 'product',
                    'name': 'product',
                    'brand': 'brand',
                    'Image URL': 'imgSrc',
                    'image': 'imgSrc',
                    'Price': 'price',
                    'price': 'price'
                }
                
                # Rename columns to match expected format
                for old_col, new_col in column_mapping.items():
                    if old_col in df_json.columns and new_col not in df_json.columns:
                        df_json[new_col] = df_json[old_col]
                
                # Save processed JSON
                output_file = f'processed_data/makeup_products_{json_path.stem}.csv'
                df_json.to_csv(output_file, index=False)
                print(f"Saved processed JSON with {len(df_json)} products to {output_file}")
                
                # Add to combined list
                all_makeup_products.append(df_json)
            except Exception as e:
                print(f"Error processing {json_path}: {e}")
        else:
            print(f"Warning: {json_path} not found")
    
    # Combine all makeup products
    if all_makeup_products:
        # Get a list of all columns across all DataFrames
        all_columns = set()
        for df in all_makeup_products:
            all_columns.update(df.columns)
        
        # Ensure all DataFrames have the same columns
        for i, df in enumerate(all_makeup_products):
            for col in all_columns:
                if col not in df.columns:
                    all_makeup_products[i][col] = ""
        
        # Concatenate all DataFrames
        combined_df = pd.concat(all_makeup_products, ignore_index=True)
        
        # Ensure required columns exist
        required_columns = ['product', 'brand', 'price', 'imgSrc', 'product_type']
        for col in required_columns:
            if col not in combined_df.columns:
                if col == 'product':
                    combined_df[col] = "Makeup Product"
                elif col == 'brand':
                    combined_df[col] = "Beauty Brand"
                elif col == 'price':
                    combined_df[col] = "$19.99"
                elif col == 'imgSrc':
                    combined_df[col] = ""
                elif col == 'product_type':
                    combined_df[col] = "Makeup"
        
        # Remove duplicates based on product name and brand
        combined_df = combined_df.drop_duplicates(subset=['product', 'brand'], keep='first')
        
        # Save combined DataFrame
        combined_df.to_csv('processed_data/all_makeup_products.csv', index=False)
        print(f"Saved combined makeup data with {len(combined_df)} products")
        
        # Create a sample file with a subset of products for testing
        sample_size = min(100, len(combined_df))
        sample_df = combined_df.sample(n=sample_size, random_state=42)
        sample_df.to_csv('processed_data/sample_makeup_products.csv', index=False)
        print(f"Saved sample makeup data with {len(sample_df)} products")
    else:
        print("No makeup products were processed.")

def process_outfit_data():
    """
    Process outfit data from datasets/outfit1.json, datasets/outfit2.json,
    and H&M product CSV files
    """
    print("Processing outfit data...")
    
    # Create output directory if it doesn't exist
    os.makedirs('processed_data', exist_ok=True)
    
    all_outfits = []
    
    # Process JSON files
    json_files = [
        Path('../datasets/outfit1.json'),
        Path('../datasets/outfit2.json')
    ]
    
    for json_path in json_files:
        if json_path.exists():
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Convert JSON to DataFrame
                df_json = pd.DataFrame(data)
                print(f"Read {len(df_json)} outfits from {json_path.name}")
                
                # Standardize column names
                column_mapping = {
                    'Product Name': 'product',
                    'name': 'product',
                    'Image URL': 'imgSrc',
                    'image': 'imgSrc',
                    'Price': 'price',
                    'price': 'price'
                }
                
                # Rename columns to match expected format
                for old_col, new_col in column_mapping.items():
                    if old_col in df_json.columns and new_col not in df_json.columns:
                        df_json[new_col] = df_json[old_col]
                
                # Add brand column if it doesn't exist
                if 'brand' not in df_json.columns:
                    df_json['brand'] = "Fashion Brand"
                
                # Add Product Type column if it doesn't exist
                if 'Product Type' not in df_json.columns:
                    # Infer product type from product name
                    def infer_product_type(name):
                        if pd.isna(name):
                            return "Clothing"
                        
                        name = name.lower()
                        if any(x in name for x in ['shirt', 'tee', 't-shirt', 'top', 'blouse']):
                            return "Shirt"
                        elif any(x in name for x in ['pant', 'trouser', 'jean', 'chino']):
                            return "Pants"
                        elif any(x in name for x in ['jacket', 'blazer', 'coat']):
                            return "Jacket"
                        elif any(x in name for x in ['dress']):
                            return "Dress"
                        elif any(x in name for x in ['skirt']):
                            return "Skirt"
                        elif any(x in name for x in ['shoe', 'sneaker', 'boot']):
                            return "Shoes"
                        elif any(x in name for x in ['bag', 'purse', 'handbag']):
                            return "Bag"
                        elif any(x in name for x in ['accessory', 'jewelry', 'watch']):
                            return "Accessory"
                        elif any(x in name for x in ['sweater', 'sweatshirt', 'hoodie']):
                            return "Sweater"
                        else:
                            return "Clothing"
                    
                    product_col = next((col for col in ['product', 'Product Name', 'name'] if col in df_json.columns), None)
                    if product_col:
                        df_json['Product Type'] = df_json[product_col].apply(infer_product_type)
                    else:
                        df_json['Product Type'] = "Clothing"
                
                # Add gender column if it doesn't exist
                if 'gender' not in df_json.columns:
                    # Infer gender from product name or use a default
                    def infer_gender(name):
                        if pd.isna(name):
                            return "Unisex"
                        
                        name = name.lower()
                        if any(x in name for x in ['women', 'woman', 'female', 'ladies']):
                            return "Women"
                        elif any(x in name for x in ['men', 'man', 'male', 'gentleman']):
                            return "Men"
                        else:
                            return "Unisex"
                    
                    product_col = next((col for col in ['product', 'Product Name', 'name'] if col in df_json.columns), None)
                    if product_col:
                        df_json['gender'] = df_json[product_col].apply(infer_gender)
                    else:
                        df_json['gender'] = "Unisex"
                
                # Add color column if it doesn't exist
                if 'baseColour' not in df_json.columns and 'color' not in df_json.columns:
                    # Infer color from product name or use a default
                    def infer_color(name):
                        if pd.isna(name):
                            return "Unknown"
                        
                        name = name.lower()
                        colors = ['black', 'white', 'red', 'blue', 'green', 'yellow', 'purple', 'pink', 
                                 'orange', 'brown', 'grey', 'gray', 'navy', 'beige', 'tan', 'gold', 'silver']
                        
                        for color in colors:
                            if color in name:
                                return color.capitalize()
                        
                        return "Unknown"
                    
                    product_col = next((col for col in ['product', 'Product Name', 'name'] if col in df_json.columns), None)
                    if product_col:
                        df_json['baseColour'] = df_json[product_col].apply(infer_color)
                    else:
                        df_json['baseColour'] = "Unknown"
                
                # Add category columns if they don't exist
                if 'masterCategory' not in df_json.columns:
                    df_json['masterCategory'] = df_json['Product Type'].apply(
                        lambda x: "Apparel" if x in ["Shirt", "Pants", "Jacket", "Dress", "Skirt", "Sweater"] 
                        else ("Accessories" if x in ["Bag", "Accessory"] else "Footwear" if x == "Shoes" else "Apparel")
                    )
                
                if 'subCategory' not in df_json.columns:
                    df_json['subCategory'] = df_json['Product Type']
                
                # Save processed JSON
                output_file = f'processed_data/outfit_products_{json_path.stem}.csv'
                df_json.to_csv(output_file, index=False)
                print(f"Saved processed outfits with {len(df_json)} items to {output_file}")
                
                # Add to combined list
                all_outfits.append(df_json)
            except Exception as e:
                print(f"Error processing {json_path}: {e}")
        else:
            print(f"Warning: {json_path} not found")
    
    # Process H&M product CSV files
    hm_files = [
        Path('prods_fastapi/hm_products.csv'),
        Path('prods_fastapi/hm_products2.csv')
    ]
    
    for hm_path in hm_files:
        if hm_path.exists():
            try:
                df_hm = pd.read_csv(hm_path)
                print(f"Read {len(df_hm)} products from {hm_path.name}")
                
                # Add brand column if it doesn't exist
                if 'brand' not in df_hm.columns:
                    df_hm['brand'] = "H&M"
                
                # Add gender column if it doesn't exist
                if 'gender' not in df_hm.columns:
                    # Infer gender from product name
                    df_hm['gender'] = df_hm['Product Name'].apply(infer_gender)
                
                # Add color column if it doesn't exist
                if 'baseColour' not in df_hm.columns and 'color' not in df_hm.columns:
                    df_hm['baseColour'] = df_hm['Product Name'].apply(infer_color)
                
                # Add category columns if they don't exist
                if 'Product Type' in df_hm.columns and pd.isna(df_hm['Product Type']).all():
                    df_hm['Product Type'] = df_hm['Product Name'].apply(infer_product_type)
                
                if 'masterCategory' not in df_hm.columns:
                    df_hm['masterCategory'] = df_hm['Product Type'].apply(
                        lambda x: "Apparel" if pd.notna(x) and x in ["Shirt", "Pants", "Jacket", "Dress", "Skirt", "Sweater"] 
                        else ("Accessories" if pd.notna(x) and x in ["Bag", "Accessory"] else "Footwear" if pd.notna(x) and x == "Shoes" else "Apparel")
                    )
                
                if 'subCategory' not in df_hm.columns:
                    df_hm['subCategory'] = df_hm['Product Type']
                
                # Save processed H&M products
                output_file = f'processed_data/hm_products_{hm_path.stem}.csv'
                df_hm.to_csv(output_file, index=False)
                print(f"Saved processed H&M products with {len(df_hm)} items to {output_file}")
                
                # Add to combined list
                all_outfits.append(df_hm)
            except Exception as e:
                print(f"Error processing {hm_path}: {e}")
        else:
            print(f"Warning: {hm_path} not found")
    
    # Combine all outfit products
    if all_outfits:
        # Get a list of all columns across all DataFrames
        all_columns = set()
        for df in all_outfits:
            all_columns.update(df.columns)
        
        # Ensure all DataFrames have the same columns
        for i, df in enumerate(all_outfits):
            for col in all_columns:
                if col not in df.columns:
                    all_outfits[i][col] = ""
        
        # Concatenate all DataFrames
        combined_df = pd.concat(all_outfits, ignore_index=True)
        
        # Ensure required columns exist
        required_columns = ['Product Name', 'Price', 'Image URL', 'brand', 'Product Type']
        for col in required_columns:
            if col not in combined_df.columns:
                if col == 'Product Name' and 'product' in combined_df.columns:
                    combined_df[col] = combined_df['product']
                elif col == 'Image URL' and 'imgSrc' in combined_df.columns:
                    combined_df[col] = combined_df['imgSrc']
                elif col == 'Product Name':
                    combined_df[col] = "Fashion Item"
                elif col == 'Price':
                    combined_df[col] = "$39.99"
                elif col == 'Image URL':
                    combined_df[col] = ""
                elif col == 'brand':
                    combined_df[col] = "Fashion Brand"
                elif col == 'Product Type':
                    combined_df[col] = "Clothing"
        
        # Remove duplicates based on product name and brand
        combined_df = combined_df.drop_duplicates(subset=['Product Name', 'brand'], keep='first')
        
        # Save combined DataFrame
        combined_df.to_csv('processed_data/all_outfits.csv', index=False)
        print(f"Saved combined outfit data with {len(combined_df)} items")
        
        # Create a sample file with a subset of products for testing
        sample_size = min(100, len(combined_df))
        sample_df = combined_df.sample(n=sample_size, random_state=42)
        sample_df.to_csv('processed_data/sample_outfits.csv', index=False)
        print(f"Saved sample outfit data with {len(sample_df)} items")
        
        # Copy to prods_fastapi directory for direct access
        combined_df.to_csv('prods_fastapi/outfit_products.csv', index=False)
        print(f"Copied outfit data to prods_fastapi directory")
    else:
        print("No outfit products were processed.")

def process_color_data():
    """
    Process color data from datasets/color 1.json and datasets/color 2.txt
    """
    print("Processing color data...")
    
    # Create output directory if it doesn't exist
    os.makedirs('processed_data', exist_ok=True)
    
    # Process JSON file
    json_path = Path('datasets/color 1.json')
    if json_path.exists():
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Extract color suggestions
                if data and isinstance(data, list) and 'color_suggestions' in data[0]:
                    color_suggestions = data[0]['color_suggestions']
                    
                    # Convert to DataFrame
                    df_colors = pd.DataFrame(color_suggestions)
                    
                    # Save as CSV
                    df_colors.to_csv('processed_data/color_suggestions.csv', index=False)
                    print(f"Saved color suggestions with {len(df_colors)} entries")
        except Exception as e:
            print(f"Error reading {json_path}: {e}")
    else:
        print(f"Warning: {json_path} not found")
    
    # Process TXT file (assuming it's JSON format in a .txt file)
    txt_path = Path('datasets/color 2.txt')
    if txt_path.exists():
        try:
            with open(txt_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Extract hex codes
                if 'colors' in data and isinstance(data['colors'], list):
                    # Assuming the structure has a 'hex_code' list in each color entry
                    color_data = []
                    for color_entry in data['colors']:
                        if 'hex_code' in color_entry and isinstance(color_entry['hex_code'], list):
                            for hex_code in color_entry['hex_code']:
                                color_data.append({'hex_code': hex_code})
                    
                    # Convert to DataFrame
                    df_hex_codes = pd.DataFrame(color_data)
                    
                    # Save as CSV
                    df_hex_codes.to_csv('processed_data/color_hex_codes.csv', index=False)
                    print(f"Saved color hex codes with {len(df_hex_codes)} entries")
        except Exception as e:
            print(f"Error reading {txt_path}: {e}")
    else:
        print(f"Warning: {txt_path} not found")

def copy_to_backend():
    """
    Copy processed data files to the backend directory
    """
    print("Copying processed data to backend directory...")
    
    # Create backend data directory if it doesn't exist
    os.makedirs('backend/prods_fastapi/data', exist_ok=True)
    
    # Copy all processed files to backend
    processed_dir = Path('processed_data')
    backend_dir = Path('backend/prods_fastapi')
    
    if processed_dir.exists():
        for file in processed_dir.glob('*.csv'):
            import shutil
            dest_path = backend_dir / file.name
            shutil.copy2(file, dest_path)
            print(f"Copied {file} to {dest_path}")

def main():
    """
    Main function to process all datasets
    """
    print("Starting dataset processing...")
    
    # Process all datasets
    process_makeup_products()
    process_outfit_data()
    process_color_data()
    
    # Copy processed data to backend
    copy_to_backend()
    
    print("Dataset processing complete!")

if __name__ == "__main__":
    main() 