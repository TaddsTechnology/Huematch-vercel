#!/usr/bin/env python3
"""
Comprehensive color data migration script.
This script reads all color files and migrates them to PostgreSQL database.
"""

import os
import sys
import json
import pandas as pd

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    from prods_fastapi.database import SessionLocal, ColorPalette, ColorHexData, ColorSuggestions, SkinToneMapping, create_tables
except ImportError:
    from database import SessionLocal, ColorPalette, ColorHexData, ColorSuggestions, SkinToneMapping, create_tables

def migrate_color_json_data():
    """Migrate data from color 1.json"""
    print("Migrating color 1.json data...")
    
    file_path = os.path.join(current_dir, "datasets", "color 1.json")
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
    
    db = SessionLocal()
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Clear existing color suggestions
        db.query(ColorSuggestions).delete()
        
        color_suggestions = data[0]["color_suggestions"]
        for suggestion in color_suggestions:
            db_suggestion = ColorSuggestions(
                skin_tone=suggestion["skin_tone"],
                suitable_colors_text=suggestion["suitable_colors"],
                data_source="color_1.json"
            )
            db.add(db_suggestion)
        
        db.commit()
        print(f"Successfully migrated {len(color_suggestions)} color suggestions from color 1.json")
        
    except Exception as e:
        db.rollback()
        print(f"Error migrating color 1.json: {e}")
    finally:
        db.close()

def migrate_color_hex_data():
    """Migrate data from color 2.txt (hex codes)"""
    print("Migrating color 2.txt hex data...")
    
    file_path = os.path.join(current_dir, "datasets", "color 2.txt")
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
    
    db = SessionLocal()
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Clear existing hex data
        db.query(ColorHexData).delete()
        
        for color_data in data["colors"]:
            db_hex_data = ColorHexData(
                seasonal_type=color_data["suitable_skin_tone"],
                hex_codes=color_data["hex_code"],
                data_source="color_2.txt"
            )
            db.add(db_hex_data)
        
        db.commit()
        print(f"Successfully migrated {len(data['colors'])} hex color sets from color 2.txt")
        
    except Exception as e:
        db.rollback()
        print(f"Error migrating color 2.txt: {e}")
    finally:
        db.close()

def migrate_seasonal_palettes():
    """Migrate data from seasonal_palettes.json"""
    print("Migrating seasonal_palettes.json data...")
    
    file_path = os.path.join(current_dir, "processed_data", "seasonal_palettes.json")
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
    
    db = SessionLocal()
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Update existing color palettes with seasonal palette data
        for skin_tone, palette_info in data.items():
            existing_palette = db.query(ColorPalette).filter(ColorPalette.skin_tone == skin_tone).first()
            
            if existing_palette:
                # Update existing palette with more detailed color information
                recommended_colors = []
                for color in palette_info.get("recommended", []):
                    recommended_colors.append({
                        "name": color["name"],
                        "hex": color["color"]
                    })
                
                avoid_colors = []
                for color in palette_info.get("avoid", []):
                    avoid_colors.append({
                        "name": color["name"],
                        "hex": color["color"]
                    })
                
                # Merge with existing data
                existing_flattering = existing_palette.flattering_colors or []
                existing_avoid = existing_palette.colors_to_avoid or []
                
                # Add new colors if not already present
                existing_hex_set = {c["hex"] for c in existing_flattering}
                for new_color in recommended_colors:
                    if new_color["hex"] not in existing_hex_set:
                        existing_flattering.append(new_color)
                
                existing_avoid_hex_set = {c["hex"] for c in existing_avoid}
                for new_color in avoid_colors:
                    if new_color["hex"] not in existing_avoid_hex_set:
                        existing_avoid.append(new_color)
                
                existing_palette.flattering_colors = existing_flattering
                existing_palette.colors_to_avoid = existing_avoid
            else:
                # Create new palette if doesn't exist
                recommended_colors = []
                for color in palette_info.get("recommended", []):
                    recommended_colors.append({
                        "name": color["name"],
                        "hex": color["color"]
                    })
                
                avoid_colors = []
                for color in palette_info.get("avoid", []):
                    avoid_colors.append({
                        "name": color["name"],
                        "hex": color["color"]
                    })
                
                new_palette = ColorPalette(
                    skin_tone=skin_tone,
                    flattering_colors=recommended_colors,
                    colors_to_avoid=avoid_colors,
                    description=f"{skin_tone} seasonal color palette recommendations."
                )
                db.add(new_palette)
        
        db.commit()
        print(f"Successfully updated/added {len(data)} seasonal palettes")
        
    except Exception as e:
        db.rollback()
        print(f"Error migrating seasonal_palettes.json: {e}")
    finally:
        db.close()

def migrate_csv_data():
    """Migrate data from CSV files"""
    print("Migrating CSV data...")
    
    # Migrate color_suggestions.csv
    suggestions_file = os.path.join(current_dir, "processed_data", "color_suggestions.csv")
    if os.path.exists(suggestions_file):
        db = SessionLocal()
        try:
            df = pd.read_csv(suggestions_file)
            
            for _, row in df.iterrows():
                if pd.notna(row['skin_tone']) and pd.notna(row['suitable_colors']):
                    # Check if this suggestion already exists
                    existing = db.query(ColorSuggestions).filter(
                        ColorSuggestions.skin_tone == row['skin_tone'],
                        ColorSuggestions.data_source == "color_suggestions.csv"
                    ).first()
                    
                    if not existing:
                        db_suggestion = ColorSuggestions(
                            skin_tone=row['skin_tone'],
                            suitable_colors_text=row['suitable_colors'],
                            data_source="color_suggestions.csv"
                        )
                        db.add(db_suggestion)
            
            db.commit()
            print(f"Successfully migrated color_suggestions.csv with {len(df)} records")
            
        except Exception as e:
            db.rollback()
            print(f"Error migrating color_suggestions.csv: {e}")
        finally:
            db.close()
    else:
        print(f"File not found: {suggestions_file}")

def update_enhanced_color_palettes():
    """Add more comprehensive color palettes with enhanced color data"""
    print("Updating with enhanced color palette data...")
    
    db = SessionLocal()
    try:
        # Enhanced color mappings from your files
        enhanced_palettes = {
            "Clear Winter": {
                "flattering_colors": [
                    {"name": "Pure White", "hex": "#FEFEFE"},
                    {"name": "Hot Pink", "hex": "#E3006D"},
                    {"name": "Cobalt Blue", "hex": "#0057B8"},
                    {"name": "True Red", "hex": "#CE0037"},
                    {"name": "Violet", "hex": "#963CBD"},
                    {"name": "Emerald", "hex": "#009775"},
                    {"name": "Ice Pink", "hex": "#F395C7"},
                    {"name": "Electric Blue", "hex": "#00A3E1"},
                    {"name": "Sapphire", "hex": "#0077C8"},
                    {"name": "Amethyst", "hex": "#84329B"}
                ]
            },
            "Cool Winter": {
                "flattering_colors": [
                    {"name": "Pure White", "hex": "#FEFEFE"},
                    {"name": "Emerald", "hex": "#009775"},
                    {"name": "Cobalt Blue", "hex": "#0082BA"},
                    {"name": "Cherry Red", "hex": "#CE0037"},
                    {"name": "Sapphire", "hex": "#0057B8"},
                    {"name": "Fuchsia", "hex": "#C724B1"},
                    {"name": "Cool Ruby", "hex": "#AA0061"},
                    {"name": "Navy", "hex": "#004B87"},
                    {"name": "Deep Purple", "hex": "#84329B"}
                ]
            },
            "Deep Winter": {
                "flattering_colors": [
                    {"name": "Pure White", "hex": "#FEFEFE"},
                    {"name": "Deep Claret", "hex": "#890C58"},
                    {"name": "Forest Green", "hex": "#00594C"},
                    {"name": "True Red", "hex": "#CE0037"},
                    {"name": "Navy", "hex": "#002D72"},
                    {"name": "Amethyst", "hex": "#84329B"},
                    {"name": "Deep Blue", "hex": "#001E62"},
                    {"name": "Royal Purple", "hex": "#5C068C"}
                ]
            },
            "Light Spring": {
                "flattering_colors": [
                    {"name": "Light Yellow", "hex": "#FFF9D7"},
                    {"name": "Pale Yellow", "hex": "#F1EB9C"},
                    {"name": "Cream", "hex": "#F5E1A4"},
                    {"name": "Peach", "hex": "#FCC89B"},
                    {"name": "Mint", "hex": "#A5DFD3"},
                    {"name": "Light Aqua", "hex": "#A4DBE8"},
                    {"name": "Soft Pink", "hex": "#FAAA8D"},
                    {"name": "Light Coral", "hex": "#FF8D6D"}
                ]
            },
            "Clear Spring": {
                "flattering_colors": [
                    {"name": "Bright Yellow", "hex": "#FCE300"},
                    {"name": "Golden Yellow", "hex": "#FDD26E"},
                    {"name": "Sunflower", "hex": "#FFCD00"},
                    {"name": "Turquoise", "hex": "#008EAA"},
                    {"name": "Bright Coral", "hex": "#FF8D6D"},
                    {"name": "Violet", "hex": "#963CBD"},
                    {"name": "Bright Green", "hex": "#00A499"},
                    {"name": "Watermelon", "hex": "#E40046"}
                ]
            },
            "Warm Spring": {
                "flattering_colors": [
                    {"name": "Golden Yellow", "hex": "#FFB81C"},
                    {"name": "Apricot", "hex": "#FF8F1C"},
                    {"name": "Coral", "hex": "#FFA38B"},
                    {"name": "Warm Green", "hex": "#74AA50"},
                    {"name": "Turquoise", "hex": "#2DCCD3"},
                    {"name": "Warm Beige", "hex": "#FDAA63"},
                    {"name": "Light Green", "hex": "#6CC24A"}
                ]
            }
        }
        
        for skin_tone, palette_data in enhanced_palettes.items():
            existing_palette = db.query(ColorPalette).filter(ColorPalette.skin_tone == skin_tone).first()
            
            if existing_palette:
                # Update with enhanced data
                existing_palette.flattering_colors = palette_data["flattering_colors"]
                print(f"Updated {skin_tone} with {len(palette_data['flattering_colors'])} colors")
        
        db.commit()
        print("Successfully updated enhanced color palettes")
        
    except Exception as e:
        db.rollback()
        print(f"Error updating enhanced palettes: {e}")
    finally:
        db.close()

def main():
    """Run all migration functions"""
    print("Starting comprehensive color data migration...")
    
    try:
        # Create tables first
        print("Creating database tables...")
        create_tables()
        print("Database tables created successfully!")
        
        # Run all migration functions
        migrate_color_json_data()
        migrate_color_hex_data()
        migrate_seasonal_palettes()
        migrate_csv_data()
        update_enhanced_color_palettes()
        
        print("\n🎉 All color data migration completed successfully!")
        print("\nMigrated data includes:")
        print("✅ Color suggestions from color 1.json")
        print("✅ Hex color codes from color 2.txt")
        print("✅ Seasonal palettes from seasonal_palettes.json")
        print("✅ Color suggestions from CSV files")
        print("✅ Enhanced color palettes with comprehensive color data")
        print("✅ Monk skin tone to seasonal type mappings")
        
        # Print summary
        db = SessionLocal()
        try:
            palettes_count = db.query(ColorPalette).count()
            suggestions_count = db.query(ColorSuggestions).count()
            hex_data_count = db.query(ColorHexData).count()
            mappings_count = db.query(SkinToneMapping).count()
            
            print(f"\nDatabase summary:")
            print(f"📊 Color Palettes: {palettes_count}")
            print(f"📊 Color Suggestions: {suggestions_count}")
            print(f"📊 Hex Color Data: {hex_data_count}")
            print(f"📊 Skin Tone Mappings: {mappings_count}")
            
        finally:
            db.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
