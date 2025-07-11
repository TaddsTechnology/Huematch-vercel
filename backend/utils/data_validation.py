"""
Data validation utilities for AI-Fashion backend.

This module provides comprehensive validation and error handling for data loading,
particularly for CSV and JSON files, with proper logging and fallback mechanisms.
"""

import pandas as pd
import json
import logging
import os
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import numpy as np
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataValidationError(Exception):
    """Custom exception for data validation errors."""
    pass


class CSVValidator:
    """Validator for CSV files with schema validation and error handling."""
    
    def __init__(self, schema: Dict[str, Any] = None):
        """
        Initialize CSV validator with optional schema.
        
        Args:
            schema: Dictionary defining expected columns and their types
        """
        self.schema = schema or {}
        
    def validate_csv_file(self, file_path: str, required_columns: List[str] = None) -> pd.DataFrame:
        """
        Validate and load a CSV file with comprehensive error handling.
        
        Args:
            file_path: Path to the CSV file
            required_columns: List of columns that must be present
            
        Returns:
            pd.DataFrame: Validated and cleaned DataFrame
            
        Raises:
            DataValidationError: If validation fails
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                raise DataValidationError(f"CSV file not found: {file_path}")
            
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                raise DataValidationError(f"CSV file is empty: {file_path}")
            
            # Load CSV with error handling
            try:
                df = pd.read_csv(file_path, encoding='utf-8')
            except UnicodeDecodeError:
                # Try alternative encodings
                for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                    try:
                        df = pd.read_csv(file_path, encoding=encoding)
                        logger.warning(f"Loaded {file_path} with encoding {encoding}")
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    raise DataValidationError(f"Could not decode CSV file: {file_path}")
            
            # Check if DataFrame is empty
            if df.empty:
                raise DataValidationError(f"CSV file contains no data: {file_path}")
            
            # Validate required columns
            if required_columns:
                missing_columns = set(required_columns) - set(df.columns)
                if missing_columns:
                    raise DataValidationError(
                        f"Missing required columns in {file_path}: {list(missing_columns)}"
                    )
            
            # Clean and validate data
            df = self._clean_dataframe(df)
            
            # Apply schema validation if provided
            if self.schema:
                df = self._apply_schema_validation(df, file_path)
            
            logger.info(f"Successfully validated CSV file: {file_path} ({len(df)} rows)")
            return df
            
        except Exception as e:
            if isinstance(e, DataValidationError):
                raise
            logger.error(f"Unexpected error validating CSV file {file_path}: {str(e)}")
            raise DataValidationError(f"Failed to validate CSV file {file_path}: {str(e)}")
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean DataFrame by handling missing values and data types."""
        # Replace various representations of missing values
        df = df.replace(['', 'NULL', 'null', 'N/A', 'n/a', 'NA', 'na'], np.nan)
        
        # Remove rows that are entirely empty
        df = df.dropna(how='all')
        
        # Strip whitespace from string columns
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].astype(str).str.strip()
            # Convert 'nan' strings back to NaN
            df[col] = df[col].replace('nan', np.nan)
        
        return df
    
    def _apply_schema_validation(self, df: pd.DataFrame, file_path: str) -> pd.DataFrame:
        """Apply schema validation to DataFrame."""
        validated_df = df.copy()
        
        for column, expected_type in self.schema.items():
            if column in validated_df.columns:
                try:
                    if expected_type == 'string':
                        validated_df[column] = validated_df[column].astype(str)
                    elif expected_type == 'float':
                        validated_df[column] = pd.to_numeric(validated_df[column], errors='coerce')
                    elif expected_type == 'int':
                        validated_df[column] = pd.to_numeric(validated_df[column], errors='coerce').astype('Int64')
                    elif expected_type == 'datetime':
                        validated_df[column] = pd.to_datetime(validated_df[column], errors='coerce')
                except Exception as e:
                    logger.warning(f"Failed to convert column {column} to {expected_type} in {file_path}: {str(e)}")
        
        return validated_df


class JSONValidator:
    """Validator for JSON files with schema validation and error handling."""
    
    def __init__(self, schema: Dict[str, Any] = None):
        """
        Initialize JSON validator with optional schema.
        
        Args:
            schema: Dictionary defining expected structure
        """
        self.schema = schema or {}
    
    def validate_json_file(self, file_path: str, required_keys: List[str] = None) -> Dict[str, Any]:
        """
        Validate and load a JSON file with comprehensive error handling.
        
        Args:
            file_path: Path to the JSON file
            required_keys: List of keys that must be present at root level
            
        Returns:
            Dict[str, Any]: Validated JSON data
            
        Raises:
            DataValidationError: If validation fails
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                raise DataValidationError(f"JSON file not found: {file_path}")
            
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                raise DataValidationError(f"JSON file is empty: {file_path}")
            
            # Load JSON with error handling
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except UnicodeDecodeError:
                # Try alternative encodings
                for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                    try:
                        with open(file_path, 'r', encoding=encoding) as f:
                            data = json.load(f)
                        logger.warning(f"Loaded {file_path} with encoding {encoding}")
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    raise DataValidationError(f"Could not decode JSON file: {file_path}")
            except json.JSONDecodeError as e:
                raise DataValidationError(f"Invalid JSON format in {file_path}: {str(e)}")
            
            # Validate required keys
            if required_keys and isinstance(data, dict):
                missing_keys = set(required_keys) - set(data.keys())
                if missing_keys:
                    raise DataValidationError(
                        f"Missing required keys in {file_path}: {list(missing_keys)}"
                    )
            
            # Clean and validate data
            data = self._clean_json_data(data)
            
            # Apply schema validation if provided
            if self.schema:
                data = self._apply_schema_validation(data, file_path)
            
            logger.info(f"Successfully validated JSON file: {file_path}")
            return data
            
        except Exception as e:
            if isinstance(e, DataValidationError):
                raise
            logger.error(f"Unexpected error validating JSON file {file_path}: {str(e)}")
            raise DataValidationError(f"Failed to validate JSON file {file_path}: {str(e)}")
    
    def _clean_json_data(self, data: Any) -> Any:
        """Clean JSON data by handling various edge cases."""
        if isinstance(data, dict):
            # Clean dictionary
            cleaned = {}
            for key, value in data.items():
                if value is not None and value != '':
                    cleaned[key] = self._clean_json_data(value)
            return cleaned
        elif isinstance(data, list):
            # Clean list
            return [self._clean_json_data(item) for item in data if item is not None]
        elif isinstance(data, str):
            # Clean string
            return data.strip() if data.strip() != '' else None
        else:
            return data
    
    def _apply_schema_validation(self, data: Any, file_path: str) -> Any:
        """Apply schema validation to JSON data."""
        # This is a simplified schema validation
        # In a production environment, you might want to use a library like jsonschema
        try:
            return data
        except Exception as e:
            logger.warning(f"Schema validation failed for {file_path}: {str(e)}")
            return data


class DataLoader:
    """Main data loader class with validation and caching."""
    
    def __init__(self, cache_dir: str = "cache"):
        """
        Initialize data loader with caching capability.
        
        Args:
            cache_dir: Directory for caching processed data
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.csv_validator = CSVValidator()
        self.json_validator = JSONValidator()
        
    def load_csv_with_fallback(self, 
                              primary_path: str, 
                              fallback_paths: List[str] = None, 
                              required_columns: List[str] = None,
                              default_df: pd.DataFrame = None) -> pd.DataFrame:
        """
        Load CSV file with fallback options and validation.
        
        Args:
            primary_path: Primary file path to try
            fallback_paths: List of fallback file paths
            required_columns: List of required columns
            default_df: Default DataFrame to return if all paths fail
            
        Returns:
            pd.DataFrame: Loaded and validated DataFrame
        """
        paths_to_try = [primary_path] + (fallback_paths or [])
        
        for path in paths_to_try:
            try:
                df = self.csv_validator.validate_csv_file(path, required_columns)
                return df
            except DataValidationError as e:
                logger.warning(f"Failed to load CSV from {path}: {str(e)}")
                continue
        
        # If all paths failed, return default or empty DataFrame
        if default_df is not None:
            logger.info(f"Using provided default DataFrame")
            return default_df
        
        logger.warning(f"All CSV paths failed, returning empty DataFrame")
        return pd.DataFrame()
    
    def load_json_with_fallback(self, 
                               primary_path: str, 
                               fallback_paths: List[str] = None, 
                               required_keys: List[str] = None,
                               default_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Load JSON file with fallback options and validation.
        
        Args:
            primary_path: Primary file path to try
            fallback_paths: List of fallback file paths
            required_keys: List of required keys
            default_data: Default data to return if all paths fail
            
        Returns:
            Dict[str, Any]: Loaded and validated JSON data
        """
        paths_to_try = [primary_path] + (fallback_paths or [])
        
        for path in paths_to_try:
            try:
                data = self.json_validator.validate_json_file(path, required_keys)
                return data
            except DataValidationError as e:
                logger.warning(f"Failed to load JSON from {path}: {str(e)}")
                continue
        
        # If all paths failed, return default or empty dict
        if default_data is not None:
            logger.info(f"Using provided default data")
            return default_data
        
        logger.warning(f"All JSON paths failed, returning empty dictionary")
        return {}
    
    def cache_data(self, data: Union[pd.DataFrame, Dict[str, Any]], cache_key: str) -> None:
        """
        Cache processed data for faster subsequent access.
        
        Args:
            data: Data to cache
            cache_key: Unique key for the cached data
        """
        try:
            cache_file = self.cache_dir / f"{cache_key}.json"
            
            if isinstance(data, pd.DataFrame):
                # Cache DataFrame as JSON
                data_dict = {
                    'data': data.to_dict(orient='records'),
                    'columns': list(data.columns),
                    'cached_at': datetime.now().isoformat()
                }
                with open(cache_file, 'w') as f:
                    json.dump(data_dict, f, indent=2)
            else:
                # Cache dictionary data
                cache_data = {
                    'data': data,
                    'cached_at': datetime.now().isoformat()
                }
                with open(cache_file, 'w') as f:
                    json.dump(cache_data, f, indent=2)
            
            logger.info(f"Successfully cached data with key: {cache_key}")
        except Exception as e:
            logger.error(f"Failed to cache data with key {cache_key}: {str(e)}")
    
    def load_from_cache(self, cache_key: str, max_age_hours: int = 24) -> Optional[Union[pd.DataFrame, Dict[str, Any]]]:
        """
        Load data from cache if available and not expired.
        
        Args:
            cache_key: Unique key for the cached data
            max_age_hours: Maximum age of cached data in hours
            
        Returns:
            Cached data or None if not available or expired
        """
        try:
            cache_file = self.cache_dir / f"{cache_key}.json"
            
            if not cache_file.exists():
                return None
            
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
            
            # Check cache age
            cached_at = datetime.fromisoformat(cache_data['cached_at'])
            age_hours = (datetime.now() - cached_at).total_seconds() / 3600
            
            if age_hours > max_age_hours:
                logger.info(f"Cache expired for key {cache_key} (age: {age_hours:.1f} hours)")
                return None
            
            # Return cached data
            if 'columns' in cache_data:
                # This is a DataFrame
                return pd.DataFrame(cache_data['data'])
            else:
                # This is dictionary data
                return cache_data['data']
                
        except Exception as e:
            logger.error(f"Failed to load from cache with key {cache_key}: {str(e)}")
            return None


# Convenience functions for common use cases
def validate_and_load_csv(file_path: str, required_columns: List[str] = None) -> pd.DataFrame:
    """
    Convenience function to validate and load a single CSV file.
    
    Args:
        file_path: Path to the CSV file
        required_columns: List of required columns
        
    Returns:
        pd.DataFrame: Validated DataFrame
    """
    validator = CSVValidator()
    return validator.validate_csv_file(file_path, required_columns)


def validate_and_load_json(file_path: str, required_keys: List[str] = None) -> Dict[str, Any]:
    """
    Convenience function to validate and load a single JSON file.
    
    Args:
        file_path: Path to the JSON file
        required_keys: List of required keys
        
    Returns:
        Dict[str, Any]: Validated JSON data
    """
    validator = JSONValidator()
    return validator.validate_json_file(file_path, required_keys)
