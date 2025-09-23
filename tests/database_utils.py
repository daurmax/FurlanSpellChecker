"""Database utilities for testing with real Friulian databases."""

import zipfile
from pathlib import Path
import sqlite3


def get_database_paths():
    """Get paths to extracted database files."""
    base_dir = Path(__file__).parent.parent / "data" / "databases"
    return {
        "words": base_dir / "words.db",
        "frequencies": base_dir / "frequencies.sqlite", 
        "errors": base_dir / "errors.sqlite",
        "elisions": base_dir / "elisions.sqlite",
        "radix_tree": base_dir / "words.rt",
    }


def ensure_databases_extracted():
    """Ensure all database ZIP files are extracted."""
    base_dir = Path(__file__).parent.parent / "data" / "databases"
    
    # Extract ZIP files if database files don't exist
    zip_files = {
        "words_database.zip": "words.db",
        "frequencies.zip": "frequencies.sqlite",
        "errors.zip": "errors.sqlite", 
        "elisions.zip": "elisions.sqlite",
        "words_radix_tree.zip": "words.rt",
    }
    
    for zip_name, db_file in zip_files.items():
        zip_path = base_dir / zip_name
        db_path = base_dir / db_file
        
        if zip_path.exists() and not db_path.exists():
            print(f"Extracting {zip_name}...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(base_dir)
    
    return base_dir


def verify_database_files():
    """Verify all database files are present and accessible."""
    paths = get_database_paths()
    
    # Check files exist
    for name, path in paths.items():
        if not path.exists():
            print(f"Missing database file: {path}")
            return False
            
        # Quick validation for SQLite files
        if path.suffix == ".sqlite":
            try:
                conn = sqlite3.connect(str(path))
                conn.close()
            except Exception as e:
                print(f"Invalid SQLite database {path}: {e}")
                return False
    
    return True