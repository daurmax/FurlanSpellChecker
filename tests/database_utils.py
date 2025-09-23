"""Database utilities for test setup.

This module handles extraction and setup of the real Friulian databases
from the zipped files in data/databases/ for use in testing.
"""
from __future__ import annotations

import os
import zipfile
from pathlib import Path
from typing import Optional

# Path constants
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATABASES_ZIP_DIR = DATA_DIR / "databases"
DATABASES_EXTRACT_DIR = DATA_DIR / "databases_extracted"


def ensure_databases_extracted() -> Path:
    """Ensure databases are extracted from ZIP files.
    
    Returns:
        Path to the extracted databases directory
        
    Raises:
        FileNotFoundError: If ZIP files are missing
        RuntimeError: If extraction fails
    """
    # Create extraction directory if it doesn't exist
    DATABASES_EXTRACT_DIR.mkdir(parents=True, exist_ok=True)
    
    # List of expected ZIP files and their extracted counterparts
    zip_files = {
        "words_database.zip": "words.db",          # words.db -> words.db
        "words_radix_tree.zip": "words.rt",        # words.rt -> words.rt
        "frequencies.zip": "frequencies.sqlite",   # frequencies.sqlite -> frequencies.sqlite  
        "errors.zip": "errors.sqlite",             # errors.sqlite -> errors.sqlite
        "elisions.zip": "elisions.sqlite"          # elisions.sqlite -> elisions.sqlite
    }
    
    # Check if all extracted files exist and are newer than ZIP files
    all_extracted = True
    for zip_name, db_name in zip_files.items():
        zip_path = DATABASES_ZIP_DIR / zip_name
        db_path = DATABASES_EXTRACT_DIR / db_name
        
        if not zip_path.exists():
            raise FileNotFoundError(f"Required ZIP file not found: {zip_path}")
            
        # Extract if DB doesn't exist or ZIP is newer
        if not db_path.exists() or (zip_path.stat().st_mtime > db_path.stat().st_mtime):
            all_extracted = False
            break
    
    # Extract if needed
    if not all_extracted:
        print("Extracting database files from ZIP archives...")
        
        for zip_name, db_name in zip_files.items():
            zip_path = DATABASES_ZIP_DIR / zip_name
            db_path = DATABASES_EXTRACT_DIR / db_name
            
            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_file:
                    # Find the database file in the ZIP (might be nested)
                    db_files = [f for f in zip_file.namelist() if f.endswith(('.db', '.rt', '.sqlite'))]
                    
                    if not db_files:
                        raise RuntimeError(f"No database file found in {zip_path}. Available files: {zip_file.namelist()}")
                    
                    # Use the first matching file
                    source_file = db_files[0]
                    
                    # Extract with original name (don't rename)
                    with zip_file.open(source_file) as source:
                        with open(db_path, 'wb') as target:
                            target.write(source.read())
                    
                    print(f"Extracted: {zip_name} -> {db_name}")
                    
            except Exception as e:
                raise RuntimeError(f"Failed to extract {zip_path}: {e}")
    
    return DATABASES_EXTRACT_DIR


def get_database_paths() -> dict[str, Path]:
    """Get paths to all extracted database files.
    
    Returns:
        Dictionary mapping database type to file path
    """
    db_dir = ensure_databases_extracted()
    
    return {
        "words": db_dir / "words.db",
        "radix_tree": db_dir / "words.rt", 
        "frequencies": db_dir / "frequencies.sqlite",
        "errors": db_dir / "errors.sqlite", 
        "elisions": db_dir / "elisions.sqlite"
    }


def verify_database_files() -> bool:
    """Verify that all database files exist and are readable.
    
    Returns:
        True if all databases are valid, False otherwise
    """
    try:
        paths = get_database_paths()
        
        for db_type, path in paths.items():
            if not path.exists():
                print(f"Missing database file: {path}")
                return False
                
            if not path.is_file():
                print(f"Database path is not a file: {path}")
                return False
                
            # Basic readability check
            try:
                with open(path, 'rb') as f:
                    f.read(1)  # Read first byte
            except Exception as e:
                print(f"Cannot read database file {path}: {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"Database verification failed: {e}")
        return False


if __name__ == "__main__":
    # CLI usage for manual extraction
    print("Extracting Friulian spell checker databases...")
    
    try:
        db_dir = ensure_databases_extracted()
        paths = get_database_paths()
        
        print(f"\nDatabases extracted to: {db_dir}")
        print("\nExtracted files:")
        for db_type, path in paths.items():
            size_mb = path.stat().st_size / (1024 * 1024)
            print(f"  {db_type}: {path.name} ({size_mb:.1f} MB)")
        
        if verify_database_files():
            print("\n✓ All databases verified successfully")
        else:
            print("\n✗ Database verification failed")
            
    except Exception as e:
        print(f"\n✗ Extraction failed: {e}")