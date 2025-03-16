#!/usr/bin/env python
"""
Script to fix color data files for the HueMatch application.
This script ensures that all necessary color data files are created and properly formatted.
"""

import os
import json
import shutil
from pathlib import Path
import csv

def create_default_color_data():
    """Create default color data files if they don't exist."""
    # Create processed_data directory if it doesn't exist
    processed_data_dir = Path("processed_data")
    processed_data_dir.mkdir(exist_ok=True)
    
    # Create color_suggestions.csv with default data
    color_suggestions_path = processed_data_dir / "color_suggestions.csv"
    
    if not color_suggestions_path.exists():
        print(f"Creating default color data file: {color_suggestions_path}")
        
        # Define default color suggestions
        color_data = [
            ["skin_tone", "color_name", "hex_code", "is_recommended"],
            ["Light Spring", "Light Yellow", "#FFF9D7", "True"],
            ["Light Spring", "Pale Yellow", "#F1EB9C", "True"],
            ["Light Spring", "Cream Yellow", "#F5E1A4", "True"],
            ["Light Spring", "Peach", "#F8CFA9", "True"],
            ["Light Spring", "Black", "#000000", "False"],
            ["Light Spring", "Deep Purple", "#5C068C", "False"],
            
            ["Warm Spring", "Bright Yellow", "#FCE300", "True"],
            ["Warm Spring", "Golden Yellow", "#FDD26E", "True"],
            ["Warm Spring", "Sunflower Yellow", "#FFCD00", "True"],
            ["Warm Spring", "Amber", "#FFB81C", "True"],
            ["Warm Spring", "Black", "#000000", "False"],
            ["Warm Spring", "Navy Blue", "#003DA5", "False"],
            
            ["Clear Spring", "Light Yellow", "#FFF9D7", "True"],
            ["Clear Spring", "Bright Yellow", "#FCE300", "True"],
            ["Clear Spring", "Golden Yellow", "#FDD26E", "True"],
            ["Clear Spring", "Sunflower Yellow", "#FFCD00", "True"],
            ["Clear Spring", "Black", "#000000", "False"],
            ["Clear Spring", "Dark Brown", "#5C462B", "False"],
            
            ["Light Summer", "Powder Blue", "#C6DAE7", "True"],
            ["Light Summer", "Light Blue", "#99D6EA", "True"],
            ["Light Summer", "Sky Blue", "#9BCBEB", "True"],
            ["Light Summer", "Periwinkle", "#B8C9E1", "True"],
            ["Light Summer", "Black", "#000000", "False"],
            ["Light Summer", "Deep Purple", "#5C068C", "False"],
            
            ["Cool Summer", "Pink", "#F395C7", "True"],
            ["Cool Summer", "Rose", "#F57EB6", "True"],
            ["Cool Summer", "Orchid", "#E277CD", "True"],
            ["Cool Summer", "Lilac", "#C964CF", "True"],
            ["Cool Summer", "Black", "#000000", "False"],
            ["Cool Summer", "Orange", "#FF8200", "False"],
            
            ["Soft Summer", "Soft Pink", "#F1BDC8", "True"],
            ["Soft Summer", "Coral Pink", "#FFA3B5", "True"],
            ["Soft Summer", "Soft Blue", "#9BCBEB", "True"],
            ["Soft Summer", "Seafoam Green", "#6DCDB8", "True"],
            ["Soft Summer", "Black", "#000000", "False"],
            ["Soft Summer", "Orange", "#FF8200", "False"],
            
            ["Soft Autumn", "Soft Yellow", "#F5E1A4", "True"],
            ["Soft Autumn", "Peach", "#FCD299", "True"],
            ["Soft Autumn", "Beige", "#DFD1A7", "True"],
            ["Soft Autumn", "Sage", "#BBC592", "True"],
            ["Soft Autumn", "Black", "#000000", "False"],
            ["Soft Autumn", "Hot Pink", "#FF1493", "False"],
            
            ["Warm Autumn", "Golden Yellow", "#FFCD00", "True"],
            ["Warm Autumn", "Mustard", "#B4A91F", "True"],
            ["Warm Autumn", "Olive", "#A09958", "True"],
            ["Warm Autumn", "Rust", "#A6631B", "True"],
            ["Warm Autumn", "Black", "#000000", "False"],
            ["Warm Autumn", "Hot Pink", "#FF1493", "False"],
            
            ["Deep Autumn", "Rust", "#A6631B", "True"],
            ["Deep Autumn", "Copper", "#946037", "True"],
            ["Deep Autumn", "Brown", "#7C4D3A", "True"],
            ["Deep Autumn", "Brick Red", "#9A3324", "True"],
            ["Deep Autumn", "Pastel Pink", "#F395C7", "False"],
            ["Deep Autumn", "Light Blue", "#99D6EA", "False"],
            
            ["Clear Winter", "Pure White", "#FEFEFE", "True"],
            ["Clear Winter", "Bright Blue", "#00A3E1", "True"],
            ["Clear Winter", "Cobalt Blue", "#0077C8", "True"],
            ["Clear Winter", "True Red", "#E40046", "True"],
            ["Clear Winter", "Cream Yellow", "#F5E1A4", "False"],
            ["Clear Winter", "Moss Green", "#A09958", "False"],
            
            ["Cool Winter", "Pure White", "#FEFEFE", "True"],
            ["Cool Winter", "Royal Blue", "#0057B8", "True"],
            ["Cool Winter", "Navy Blue", "#004B87", "True"],
            ["Cool Winter", "Purple", "#84329B", "True"],
            ["Cool Winter", "Cream Yellow", "#F5E1A4", "False"],
            ["Cool Winter", "Moss Green", "#A09958", "False"],
            
            ["Deep Winter", "Pure White", "#FEFEFE", "True"],
            ["Deep Winter", "Royal Blue", "#0057B8", "True"],
            ["Deep Winter", "Navy Blue", "#004B87", "True"],
            ["Deep Winter", "Deep Blue", "#002D72", "True"],
            ["Deep Winter", "Cream Yellow", "#F5E1A4", "False"],
            ["Deep Winter", "Light Peach", "#FCC89B", "False"]
        ]
        
        # Write to CSV
        with open(color_suggestions_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(color_data)
    
    # Create color 1.json with default data
    datasets_dir = Path("datasets")
    datasets_dir.mkdir(exist_ok=True)
    
    color_1_path = datasets_dir / "color 1.json"
    if not color_1_path.exists():
        print(f"Creating default color 1.json file: {color_1_path}")
        
        color_1_data = [
            {
                "color_suggestions": [
                    {
                        "skin_tone": "Light Spring",
                        "suitable_colors": "Light Yellow, Pale Yellow, Cream Yellow, Peach, Light Peach, Light Green, Mint, Sky Blue"
                    },
                    {
                        "skin_tone": "Warm Spring",
                        "suitable_colors": "Bright Yellow, Golden Yellow, Sunflower Yellow, Amber, Honey, Orange, Warm Red, Fresh Green"
                    },
                    {
                        "skin_tone": "Clear Spring",
                        "suitable_colors": "Light Yellow, Bright Yellow, Golden Yellow, Sunflower Yellow, Amber, Orange, Warm Red, Turquoise"
                    },
                    {
                        "skin_tone": "Light Summer",
                        "suitable_colors": "Powder Blue, Light Blue, Sky Blue, Periwinkle, Light Pink, Lavender, Rose Pink, Mint Green"
                    },
                    {
                        "skin_tone": "Cool Summer",
                        "suitable_colors": "Pink, Rose, Orchid, Lilac, Mauve, Azure, Sky Blue, Turquoise"
                    },
                    {
                        "skin_tone": "Soft Summer",
                        "suitable_colors": "Soft Pink, Coral Pink, Soft Blue, Seafoam Green, Sage Green, Taupe, Mauve, Dusty Rose"
                    },
                    {
                        "skin_tone": "Soft Autumn",
                        "suitable_colors": "Soft Yellow, Peach, Beige, Sage, Olive, Moss Green, Camel, Terracotta"
                    },
                    {
                        "skin_tone": "Warm Autumn",
                        "suitable_colors": "Golden Yellow, Mustard, Olive, Rust, Copper, Brick Red, Burnt Orange, Pumpkin"
                    },
                    {
                        "skin_tone": "Deep Autumn",
                        "suitable_colors": "Rust, Copper, Brown, Brick Red, Dark Brown, Forest Green, Teal, Emerald"
                    },
                    {
                        "skin_tone": "Clear Winter",
                        "suitable_colors": "Pure White, Bright Blue, Cobalt Blue, True Red, Cherry Red, Fuchsia, Violet, Emerald"
                    },
                    {
                        "skin_tone": "Cool Winter",
                        "suitable_colors": "Pure White, Royal Blue, Navy Blue, Purple, Violet, Magenta, Hot Pink, Cool Red"
                    },
                    {
                        "skin_tone": "Deep Winter",
                        "suitable_colors": "Pure White, Royal Blue, Navy Blue, Deep Blue, Purple, Cool Red, Emerald, Deep Green"
                    }
                ]
            }
        ]
        
        with open(color_1_path, 'w') as f:
            json.dump(color_1_data, f, indent=2)
    
    # Create color 2.txt with default data
    color_2_path = datasets_dir / "color 2.txt"
    if not color_2_path.exists():
        print(f"Creating default color 2.txt file: {color_2_path}")
        
        color_2_data = {
            "monk_hex_codes": {
                "Monk01": "#f6ede4",
                "Monk02": "#f3e7db",
                "Monk03": "#f7ead0",
                "Monk04": "#eadaba",
                "Monk05": "#d7bd96",
                "Monk06": "#a07e56",
                "Monk07": "#825c43",
                "Monk08": "#604134",
                "Monk09": "#3a312a",
                "Monk10": "#292420"
            }
        }
        
        with open(color_2_path, 'w') as f:
            json.dump(color_2_data, f, indent=2)
    
    # Create seasonal_palettes.json with default data
    seasonal_palettes_path = processed_data_dir / "seasonal_palettes.json"
    if not seasonal_palettes_path.exists():
        print(f"Creating default seasonal palettes file: {seasonal_palettes_path}")
        
        seasonal_palettes_data = {
            "Light Spring": {
                "recommended": [
                    {"color": "#FFF9D7", "name": "Light Yellow"},
                    {"color": "#F1EB9C", "name": "Pale Yellow"},
                    {"color": "#F5E1A4", "name": "Cream Yellow"},
                    {"color": "#F8CFA9", "name": "Peach"}
                ],
                "avoid": [
                    {"color": "#000000", "name": "Black"},
                    {"color": "#5C068C", "name": "Deep Purple"}
                ]
            },
            "Warm Spring": {
                "recommended": [
                    {"color": "#FCE300", "name": "Bright Yellow"},
                    {"color": "#FDD26E", "name": "Golden Yellow"},
                    {"color": "#FFCD00", "name": "Sunflower Yellow"},
                    {"color": "#FFB81C", "name": "Amber"}
                ],
                "avoid": [
                    {"color": "#000000", "name": "Black"},
                    {"color": "#003DA5", "name": "Navy Blue"}
                ]
            },
            "Clear Spring": {
                "recommended": [
                    {"color": "#FFF9D7", "name": "Light Yellow"},
                    {"color": "#FCE300", "name": "Bright Yellow"},
                    {"color": "#FDD26E", "name": "Golden Yellow"},
                    {"color": "#FFCD00", "name": "Sunflower Yellow"}
                ],
                "avoid": [
                    {"color": "#000000", "name": "Black"},
                    {"color": "#5C462B", "name": "Dark Brown"}
                ]
            },
            "Light Summer": {
                "recommended": [
                    {"color": "#C6DAE7", "name": "Powder Blue"},
                    {"color": "#99D6EA", "name": "Light Blue"},
                    {"color": "#9BCBEB", "name": "Sky Blue"},
                    {"color": "#B8C9E1", "name": "Periwinkle"}
                ],
                "avoid": [
                    {"color": "#000000", "name": "Black"},
                    {"color": "#5C068C", "name": "Deep Purple"}
                ]
            },
            "Cool Summer": {
                "recommended": [
                    {"color": "#F395C7", "name": "Pink"},
                    {"color": "#F57EB6", "name": "Rose"},
                    {"color": "#E277CD", "name": "Orchid"},
                    {"color": "#C964CF", "name": "Lilac"}
                ],
                "avoid": [
                    {"color": "#000000", "name": "Black"},
                    {"color": "#FF8200", "name": "Orange"}
                ]
            },
            "Soft Summer": {
                "recommended": [
                    {"color": "#F1BDC8", "name": "Soft Pink"},
                    {"color": "#FFA3B5", "name": "Coral Pink"},
                    {"color": "#9BCBEB", "name": "Soft Blue"},
                    {"color": "#6DCDB8", "name": "Seafoam Green"}
                ],
                "avoid": [
                    {"color": "#000000", "name": "Black"},
                    {"color": "#FF8200", "name": "Orange"}
                ]
            },
            "Soft Autumn": {
                "recommended": [
                    {"color": "#F5E1A4", "name": "Soft Yellow"},
                    {"color": "#FCD299", "name": "Peach"},
                    {"color": "#DFD1A7", "name": "Beige"},
                    {"color": "#BBC592", "name": "Sage"}
                ],
                "avoid": [
                    {"color": "#000000", "name": "Black"},
                    {"color": "#FF1493", "name": "Hot Pink"}
                ]
            },
            "Warm Autumn": {
                "recommended": [
                    {"color": "#FFCD00", "name": "Golden Yellow"},
                    {"color": "#B4A91F", "name": "Mustard"},
                    {"color": "#A09958", "name": "Olive"},
                    {"color": "#A6631B", "name": "Rust"}
                ],
                "avoid": [
                    {"color": "#000000", "name": "Black"},
                    {"color": "#FF1493", "name": "Hot Pink"}
                ]
            },
            "Deep Autumn": {
                "recommended": [
                    {"color": "#A6631B", "name": "Rust"},
                    {"color": "#946037", "name": "Copper"},
                    {"color": "#7C4D3A", "name": "Brown"},
                    {"color": "#9A3324", "name": "Brick Red"}
                ],
                "avoid": [
                    {"color": "#F395C7", "name": "Pastel Pink"},
                    {"color": "#99D6EA", "name": "Light Blue"}
                ]
            },
            "Clear Winter": {
                "recommended": [
                    {"color": "#FEFEFE", "name": "Pure White"},
                    {"color": "#00A3E1", "name": "Bright Blue"},
                    {"color": "#0077C8", "name": "Cobalt Blue"},
                    {"color": "#E40046", "name": "True Red"}
                ],
                "avoid": [
                    {"color": "#F5E1A4", "name": "Cream Yellow"},
                    {"color": "#A09958", "name": "Moss Green"}
                ]
            },
            "Cool Winter": {
                "recommended": [
                    {"color": "#FEFEFE", "name": "Pure White"},
                    {"color": "#0057B8", "name": "Royal Blue"},
                    {"color": "#004B87", "name": "Navy Blue"},
                    {"color": "#84329B", "name": "Purple"}
                ],
                "avoid": [
                    {"color": "#F5E1A4", "name": "Cream Yellow"},
                    {"color": "#A09958", "name": "Moss Green"}
                ]
            },
            "Deep Winter": {
                "recommended": [
                    {"color": "#FEFEFE", "name": "Pure White"},
                    {"color": "#0057B8", "name": "Royal Blue"},
                    {"color": "#004B87", "name": "Navy Blue"},
                    {"color": "#002D72", "name": "Deep Blue"}
                ],
                "avoid": [
                    {"color": "#F5E1A4", "name": "Cream Yellow"},
                    {"color": "#FCC89B", "name": "Light Peach"}
                ]
            }
        }
        
        with open(seasonal_palettes_path, 'w') as f:
            json.dump(seasonal_palettes_data, f, indent=2)

def copy_color_data_to_backend():
    """Copy color data files to the backend directory."""
    # Source files
    processed_data_dir = Path("processed_data")
    datasets_dir = Path("datasets")
    
    # Destination directories
    backend_processed_data_dir = Path("backend/prods_fastapi/processed_data")
    backend_processed_data_dir.mkdir(exist_ok=True, parents=True)
    
    backend_datasets_dir = Path("backend/datasets")
    backend_datasets_dir.mkdir(exist_ok=True, parents=True)
    
    # Copy color_suggestions.csv
    color_suggestions_src = processed_data_dir / "color_suggestions.csv"
    color_suggestions_dst = backend_processed_data_dir / "color_suggestions.csv"
    if color_suggestions_src.exists():
        shutil.copy2(color_suggestions_src, color_suggestions_dst)
        print(f"Copied {color_suggestions_src} to {color_suggestions_dst}")
    
    # Copy seasonal_palettes.json
    seasonal_palettes_src = processed_data_dir / "seasonal_palettes.json"
    seasonal_palettes_dst = backend_processed_data_dir / "seasonal_palettes.json"
    if seasonal_palettes_src.exists():
        shutil.copy2(seasonal_palettes_src, seasonal_palettes_dst)
        print(f"Copied {seasonal_palettes_src} to {seasonal_palettes_dst}")
    
    # Copy color 1.json
    color_1_src = datasets_dir / "color 1.json"
    color_1_dst = backend_datasets_dir / "color 1.json"
    if color_1_src.exists():
        shutil.copy2(color_1_src, color_1_dst)
        print(f"Copied {color_1_src} to {color_1_dst}")
    
    # Copy color 2.txt
    color_2_src = datasets_dir / "color 2.txt"
    color_2_dst = backend_datasets_dir / "color 2.txt"
    if color_2_src.exists():
        shutil.copy2(color_2_src, color_2_dst)
        print(f"Copied {color_2_src} to {color_2_dst}")

def main():
    """Main function to fix color data files."""
    print("Fixing color data files...")
    create_default_color_data()
    copy_color_data_to_backend()
    print("Color data files fixed successfully.")

if __name__ == "__main__":
    main() 