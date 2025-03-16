import json
import os
from typing import Dict, List, Any

def load_color_data():
    """
    Load color data from the JSON files in the datasets directory.
    Returns a dictionary with color mappings and seasonal color palettes.
    """
    # Define the paths to the color data files
    color_1_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'datasets', 'color 1.json')
    color_2_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'datasets', 'color 2.txt')
    
    # Initialize the color data dictionary
    color_data = {
        "color_mapping": {},
        "seasonal_palettes": {},
        "monk_hex_codes": {}
    }
    
    # Load color 1.json if it exists
    try:
        if os.path.exists(color_1_path):
            with open(color_1_path, 'r') as f:
                color_1_data = json.load(f)
                
            # Process color suggestions
            if color_1_data and isinstance(color_1_data, list) and len(color_1_data) > 0:
                for suggestion in color_1_data[0].get("color_suggestions", []):
                    skin_tone = suggestion.get("skin_tone", "")
                    suitable_colors = suggestion.get("suitable_colors", "").split(", ")
                    
                    # Add to seasonal palettes
                    if skin_tone:
                        color_data["seasonal_palettes"][skin_tone] = suitable_colors
                        
                        # Add to color mapping
                        for color in suitable_colors:
                            # Simple mapping - could be enhanced with more specific mappings
                            color_data["color_mapping"][color] = color
    except Exception as e:
        print(f"Error loading color 1.json: {e}")
    
    # Load color 2.txt if it exists
    try:
        if os.path.exists(color_2_path):
            with open(color_2_path, 'r') as f:
                color_2_data = json.load(f)
                
            # Process hex codes for different skin tones
            if "colors" in color_2_data:
                for color_entry in color_2_data["colors"]:
                    skin_tone = color_entry.get("suitable_skin_tone", "")
                    hex_codes = color_entry.get("hex_code", [])
                    
                    if skin_tone and hex_codes:
                        # Store hex codes by skin tone
                        color_data["monk_hex_codes"][skin_tone] = hex_codes
    except Exception as e:
        print(f"Error loading color 2.txt: {e}")
    
    return color_data

def get_color_mapping():
    """
    Get a comprehensive color mapping dictionary.
    """
    # Base color mapping
    color_mapping = {
        "Coral Red": "Red",
        "Turquoise": "Turquoise Blue",
        "Ocean Blue": "Blue",
        "Sage Green": "Green",
        "Soft Pink": "Pink",
        "Royal Purple": "Purple",
        "Indian Red": "Red",
        "Light Sea Green": "Sea Green",
        "Royal Blue": "Blue",
        "Dark Olive Green": "Olive",
        "Medium Violet Red": "Magenta",
        "Dark Orchid": "Purple",
        "Gold": "Gold",
        "Orange Red": "Orange",
        "Spring Green": "Green",
        "Deep Pink": "Pink",
        "Indigo": "Purple",
        "Dark Orange": "Orange",
        "Navy Blue": "Navy Blue",
        "Maroon": "Maroon",
        "Olive Green": "Olive",
        "Midnight Blue": "Navy Blue",
        "Saddle Brown": "Brown",
        "Purple": "Purple",
        "Red": "Red",
        "Lime": "Green",
        
        # Additional color mappings from color data files
        # Spring colors
        "Coral": "Coral",
        "Peach": "Peach",
        "Light Gold": "Gold",
        "Warm Turquoise": "Turquoise Blue",
        "Soft Green": "Green",
        
        # Summer colors
        "Lavender": "Purple",
        "Powder Blue": "Light Blue",
        "Dusty Rose": "Pink",
        "Slate Blue": "Blue",
        "Soft Plum": "Purple",
        "Moss Green": "Green",
        "Clear Blue": "Blue",
        "Soft Fuchsia": "Magenta",
        "Cool Pink": "Pink",
        
        # Autumn colors
        "Mustard": "Yellow",
        "Rust": "Orange",
        "Olive": "Olive",
        "Burnt Orange": "Orange",
        "Taupe": "Brown",
        "Terracotta": "Orange",
        "Burgundy": "Burgundy",
        "Chocolate": "Brown",
        "Deep Teal": "Teal",
        
        # Winter colors
        "Black": "Black",
        "Navy": "Navy Blue",
        "True White": "White",
        "Emerald": "Green",
        "Fuchsia": "Magenta",
        "Deep Purple": "Purple",
        "Rich Blue": "Blue",
        "Crisp White": "White",
        "Cool Red": "Red",
        "Cobalt Blue": "Blue",
        "Cherry": "Red",
        "Sapphire": "Blue",
        "Bright Navy": "Navy Blue",
        "Amethyst": "Purple",
        "Bottle-green": "Green",
        "Cool Ruby": "Red",
        "Hot Pink": "Pink",
        "True Red": "Red",
        "Violet": "Purple",
        "Azure": "Blue",
        "Ice Pink": "Pink",
        "Acid Yellow": "Yellow",
        "Light Grey Marle": "Grey",
        "Deep Claret": "Burgundy",
        "Forest Green": "Green",
        "Oakmoss": "Green",
        "Garnet": "Red",
        "Chestnut Red": "Red",
        
        # Additional specific color names
        "Mint": "Mint Green",
        "Warm Beige": "Beige",
        "Golden Yellow": "Yellow",
        "Apricot": "Peach",
        "Clear Yellow": "Yellow",
        "Bright Coral": "Coral"
    }
    
    # Try to load additional mappings from the color data files
    try:
        color_data = load_color_data()
        if "color_mapping" in color_data and color_data["color_mapping"]:
            # Merge the loaded color mapping with the base mapping
            color_mapping.update(color_data["color_mapping"])
    except Exception as e:
        print(f"Error getting color mapping: {e}")
    
    return color_mapping

def get_seasonal_palettes():
    """
    Get seasonal color palettes from the color data files.
    """
    try:
        color_data = load_color_data()
        return color_data.get("seasonal_palettes", {})
    except Exception as e:
        print(f"Error getting seasonal palettes: {e}")
        return {}

def get_monk_hex_codes():
    """
    Get Monk skin tone hex codes from the color data files.
    """
    try:
        color_data = load_color_data()
        return color_data.get("monk_hex_codes", {})
    except Exception as e:
        print(f"Error getting Monk hex codes: {e}")
        return {}

# Example of how to use these functions:
if __name__ == "__main__":
    # Load all color data
    all_color_data = load_color_data()
    print("Color data loaded successfully.")
    
    # Get color mapping
    mapping = get_color_mapping()
    print(f"Color mapping contains {len(mapping)} entries.")
    
    # Get seasonal palettes
    palettes = get_seasonal_palettes()
    print(f"Loaded {len(palettes)} seasonal palettes.")
    
    # Get Monk hex codes
    hex_codes = get_monk_hex_codes()
    print(f"Loaded hex codes for {len(hex_codes)} skin tones.") 