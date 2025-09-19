"""Database management for Friulian spell checker."""
import platform
from pathlib import Path
from typing import Optional, Dict

from .interfaces import IKeyValueDatabase, IRadixTree, DictionaryType
from .sqlite_database import SQLiteKeyValueDatabase
from .radix_tree import RadixTreeDatabase
from ..config.schemas import FurlanSpellCheckerConfig


class DatabaseManager:
    """Manages all database connections and operations."""
    
    def __init__(self, config: Optional[FurlanSpellCheckerConfig] = None):
        """Initialize database manager with configuration."""
        self.config = config or FurlanSpellCheckerConfig()
        self._sqlite_db: Optional[SQLiteKeyValueDatabase] = None
        self._radix_tree: Optional[RadixTreeDatabase] = None
        self._cache_dir = self._get_cache_directory()
    
    def _get_cache_directory(self) -> Path:
        """Get cache directory, using default if not specified."""
        if self.config.dictionary.cache_directory:
            return Path(self.config.dictionary.cache_directory)
        
        # Default cache directory based on platform
        system = platform.system()
        if system == "Windows":
            cache_dir = Path.home() / "AppData" / "Local" / "FurlanSpellChecker"
        elif system == "Darwin":  # macOS
            cache_dir = Path.home() / "Library" / "Caches" / "FurlanSpellChecker"
        else:  # Linux and other Unix-like
            cache_dir = Path.home() / ".cache" / "FurlanSpellChecker"
        
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir
    
    @property
    def sqlite_db(self) -> SQLiteKeyValueDatabase:
        """Get SQLite database instance."""
        if self._sqlite_db is None:
            self._sqlite_db = SQLiteKeyValueDatabase(self.config)
        return self._sqlite_db
    
    @property  
    def radix_tree(self) -> RadixTreeDatabase:
        """Get radix tree database instance."""
        if self._radix_tree is None:
            radix_tree_path = self._cache_dir / "words_radix_tree" / "words.rt"
            self._radix_tree = RadixTreeDatabase(radix_tree_path)
        return self._radix_tree
    
    def ensure_databases_available(self) -> Dict[DictionaryType, bool]:
        """Check which databases are available."""
        availability = {}
        
        # Check SQLite databases
        sqlite_paths = {
            DictionaryType.SYSTEM_DICTIONARY: self._cache_dir / "words_database" / "words.db",
            DictionaryType.SYSTEM_ERRORS: self._cache_dir / "errors" / "errors.sqlite",
            DictionaryType.FREQUENCIES: self._cache_dir / "frequencies" / "frequencies.sqlite", 
            DictionaryType.ELISIONS: self._cache_dir / "elisions" / "elisions.sqlite",
        }
        
        for db_type, path in sqlite_paths.items():
            availability[db_type] = path.exists()
        
        # Check radix tree
        radix_path = self._cache_dir / "words_radix_tree" / "words.rt"
        availability[DictionaryType.RADIX_TREE] = radix_path.exists()
        
        # User databases (these can be created on demand)
        user_db_path = self._cache_dir / "UserDictionary" / "user_dictionary.sqlite"
        user_errors_path = self._cache_dir / "UserErrors" / "user_errors.sqlite"
        availability[DictionaryType.USER_DICTIONARY] = True  # Can be created
        availability[DictionaryType.USER_ERRORS] = user_errors_path.exists()
        
        return availability
    
    def get_missing_databases(self) -> Dict[DictionaryType, Path]:
        """Get list of missing required databases and their expected paths."""
        availability = self.ensure_databases_available()
        missing = {}
        
        required_databases = [
            DictionaryType.SYSTEM_DICTIONARY,
            DictionaryType.SYSTEM_ERRORS, 
            DictionaryType.FREQUENCIES,
            DictionaryType.ELISIONS,
            DictionaryType.RADIX_TREE
        ]
        
        for db_type in required_databases:
            if not availability.get(db_type, False):
                if db_type == DictionaryType.RADIX_TREE:
                    missing[db_type] = self._cache_dir / "words_radix_tree" / "words.rt"
                elif db_type == DictionaryType.SYSTEM_DICTIONARY:
                    missing[db_type] = self._cache_dir / "words_database" / "words.db"
                elif db_type == DictionaryType.SYSTEM_ERRORS:
                    missing[db_type] = self._cache_dir / "errors" / "errors.sqlite"
                elif db_type == DictionaryType.FREQUENCIES:
                    missing[db_type] = self._cache_dir / "frequencies" / "frequencies.sqlite"
                elif db_type == DictionaryType.ELISIONS:
                    missing[db_type] = self._cache_dir / "elisions" / "elisions.sqlite"
        
        return missing