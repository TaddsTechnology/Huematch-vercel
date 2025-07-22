#!/usr/bin/env python3
"""
Database initialization script for the Fashion AI application.
This script creates database tables and initializes them with color palette data.
"""

import os
import sys

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    from prods_fastapi.database import create_tables, init_color_palette_data
except ImportError:
    from database import create_tables, init_color_palette_data

def main():
    """Initialize the database"""
    print("Initializing database...")
    
    try:
        # Create tables
        print("Creating database tables...")
        create_tables()
        print("Database tables created successfully!")
        
        # Initialize color palette data
        print("Initializing color palette data...")
        init_color_palette_data()
        print("Color palette data initialized successfully!")
        
        print("Database initialization completed!")
        return True
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
