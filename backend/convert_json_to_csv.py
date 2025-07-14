import json
import csv
import os

def convert_json_to_csv():
    # Read the JSON file
    json_file_path = 'datasets/product twirl.json'
    csv_file_path = 'datasets/product_twirl.csv'
    
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract products array
        products = data[0]['products']
        
        # Get all unique keys from all products to create headers
        all_keys = set()
        for product in products:
            all_keys.update(product.keys())
        
        # Convert to sorted list for consistent column order
        headers = sorted(list(all_keys))
        
        # Write to CSV
        with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            
            for product in products:
                # Fill missing keys with empty string
                row = {key: product.get(key, '') for key in headers}
                writer.writerow(row)
        
        print(f"Successfully converted {len(products)} products to CSV")
        print(f"CSV file saved at: {csv_file_path}")
        
        # Print some stats
        print(f"\nDataset Statistics:")
        print(f"Total products: {len(products)}")
        
        # Count by category
        categories = {}
        for product in products:
            cat = product.get('master_category', 'Unknown')
            categories[cat] = categories.get(cat, 0) + 1
        
        print("\nProducts by category:")
        for cat, count in sorted(categories.items()):
            print(f"  {cat}: {count}")
        
        # Count by brand
        brands = {}
        for product in products:
            brand = product.get('brand', 'Unknown')
            brands[brand] = brands.get(brand, 0) + 1
        
        print("\nProducts by brand:")
        for brand, count in sorted(brands.items()):
            print(f"  {brand}: {count}")
            
    except FileNotFoundError:
        print(f"Error: Could not find file {json_file_path}")
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in file {json_file_path}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    convert_json_to_csv()
