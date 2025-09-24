"""SQLite database implementation for Friulian spell checker."""
import re
import sqlite3
from pathlib import Path
from typing import Optional, List, Tuple, Dict

from .interfaces import IKeyValueDatabase, DictionaryType, AddWordResult
from ..config.schemas import FurlanSpellCheckerConfig


class SQLiteKeyValueDatabase(IKeyValueDatabase):
    """SQLite implementation of key-value database operations."""
    
    def __init__(self, config: Optional[FurlanSpellCheckerConfig] = None):
        """Initialize with configuration for database paths."""
        self.config = config or FurlanSpellCheckerConfig()
        self._db_paths = self._get_database_paths()
    
    def _get_database_paths(self) -> Dict[DictionaryType, Path]:
        """Get paths for each database type based on configuration."""
        cache_directory = self.config.dictionary.cache_directory
        if cache_directory is None:
            # Use same logic as DatabaseManager for default cache directory  
            import platform
            system = platform.system()
            if system == "Windows":
                cache_dir = Path.home() / "AppData" / "Local" / "FurlanSpellChecker"
            elif system == "Darwin":  # macOS
                cache_dir = Path.home() / "Library" / "Caches" / "FurlanSpellChecker"
            else:  # Linux and other Unix-like
                cache_dir = Path.home() / ".cache" / "FurlanSpellChecker"
        else:
            cache_dir = Path(cache_directory)
        
        return {
            DictionaryType.SYSTEM_DICTIONARY: cache_dir / "words_database" / "words.db",
            DictionaryType.USER_DICTIONARY: cache_dir / "UserDictionary" / "user_dictionary.sqlite",
            DictionaryType.SYSTEM_ERRORS: cache_dir / "errors" / "errors.sqlite", 
            DictionaryType.USER_ERRORS: cache_dir / "UserErrors" / "user_errors.sqlite",
            DictionaryType.FREQUENCIES: cache_dir / "frequencies" / "frequencies.sqlite",
            DictionaryType.ELISIONS: cache_dir / "elisions" / "elisions.sqlite",
        }
    
    def find_in_user_database(self, phonetic_hash: str) -> Optional[str]:
        """Find value in user dictionary by phonetic hash."""
        db_path = self._db_paths[DictionaryType.USER_DICTIONARY]
        if not db_path.exists():
            self._create_user_database()
        
        return self._find_in_database(
            db_path, DictionaryType.USER_DICTIONARY, phonetic_hash, search_for_errors=False
        )
    
    def find_in_user_errors_database(self, word: str) -> Optional[str]:
        """Find correction in user errors database."""
        db_path = self._db_paths[DictionaryType.USER_ERRORS]
        # User errors DB is optional; if missing just return None
        if not db_path.exists():
            return None
        return self._find_in_database(db_path, DictionaryType.USER_ERRORS, word, search_for_errors=True)
    
    def find_in_system_database(self, phonetic_hash: str) -> Optional[str]:
        """Find value in system dictionary by phonetic hash."""
        db_path = self._db_paths[DictionaryType.SYSTEM_DICTIONARY]
        return self._find_in_database(
            db_path, DictionaryType.SYSTEM_DICTIONARY, phonetic_hash, search_for_errors=False
        )
    
    def find_in_system_errors_database(self, word: str) -> Optional[str]:
        """Find correction in system errors database."""
        db_path = self._db_paths[DictionaryType.SYSTEM_ERRORS]
        return self._find_in_database(
            db_path, DictionaryType.SYSTEM_ERRORS, word, search_for_errors=True
        )
    
    def find_in_frequencies_database(self, word: str) -> Optional[int]:
        """Find frequency value for a word."""
        if not word:
            raise ValueError("Word cannot be null or empty")
        
        db_path = self._db_paths[DictionaryType.FREQUENCIES]
        if not db_path.exists():
            raise FileNotFoundError(f"Frequencies database not found at '{db_path}'")
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM Data WHERE Key = ?", (word,))
            results = cursor.fetchall()
            
            if len(results) == 1:
                return results[0][1] if results[0][1] is not None else None
            elif len(results) == 0:
                return None
            else:
                raise ValueError(f"Key '{word}' returned more than one result")
    
    def has_elisions(self, word: str) -> bool:
        """Check if word exists in elisions database."""
        if not word:
            raise ValueError("Word cannot be null or empty")
        
        db_path = self._db_paths[DictionaryType.ELISIONS]
        if not db_path.exists():
            raise FileNotFoundError(f"Elisions database not found at '{db_path}'")
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM Data WHERE Key = ?", (word,))
            return cursor.fetchone() is not None
    
    def add_to_user_database(self, word: str) -> AddWordResult:
        """Add word to user dictionary."""
        if not word:
            return AddWordResult.DATABASE_NOT_EXISTS
        
        # Import here to avoid circular dependency
        from ..phonetic.furlan_phonetic import FurlanPhoneticAlgorithm
        
        db_path = self._db_paths[DictionaryType.USER_DICTIONARY]
        if not db_path.exists():
            self._create_user_database()
        
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                phonetic_algo = FurlanPhoneticAlgorithm()
                hash_a, hash_b = phonetic_algo.get_phonetic_hashes_by_word(word)
                hashes_to_process = [hash_a] if hash_a == hash_b else [hash_a, hash_b]

                for phonetic_hash in hashes_to_process:
                    # Query within the same connection to avoid nested connection handles on Windows
                    cursor.execute("SELECT Value FROM Data WHERE Key = ?", (phonetic_hash,))
                    row = cursor.fetchone()
                    existing_word = row[0] if row else None

                    if existing_word is None:
                        cursor.execute("INSERT INTO Data (Key, Value) VALUES (?, ?)", (phonetic_hash, word))
                    elif existing_word != word:
                        new_word_list = f"{existing_word},{word}"
                        cursor.execute("UPDATE Data SET Value = ? WHERE Key = ?", (new_word_list, phonetic_hash))
                    else:
                        return AddWordResult.ALREADY_PRESENT

                conn.commit()
                return AddWordResult.SUCCESS
        except Exception:
            return AddWordResult.ERROR
    
    def _find_in_database(
        self, 
        db_path: Path, 
        dictionary_type: DictionaryType, 
        key: str, 
        search_for_errors: bool
    ) -> Optional[str]:
        """Find value in specified database."""
        if not key:
            raise ValueError("Key cannot be null or empty")
        
        if not db_path.exists():
            # Optional user errors DB handled earlier; others must exist
            if dictionary_type == DictionaryType.USER_ERRORS:
                return None
            raise FileNotFoundError(f"{dictionary_type.value} database not found at '{db_path}'")
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Choose table name based on dictionary type
            table_name = "Words" if dictionary_type == DictionaryType.SYSTEM_DICTIONARY else "Data"
            cursor.execute(f"SELECT * FROM {table_name} WHERE Key = ?", (key,))
            results = cursor.fetchall()
            
            if len(results) == 1:
                return self._replace_unicode_codes_with_special_chars(results[0][1])
            elif len(results) == 0:
                return None
            else:
                error_msg = (
                    f"Key '{key}' returned more than one result in errors database"
                    if search_for_errors
                    else f"Key '{key}' returned more than one result"
                )
                raise ValueError(error_msg)
    
    def _create_user_database(self) -> None:
        """Create user database if it doesn't exist."""
        db_path = self._db_paths[DictionaryType.USER_DICTIONARY]
        
        # Ensure directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Data (
                    Key TEXT NOT NULL,
                    Value TEXT NOT NULL,
                    PRIMARY KEY (Key, Value)
                )
            """)
            conn.commit()
    
    def _replace_unicode_codes_with_special_chars(self, word: str) -> str:
        """Replace Unicode codes with special Friulian characters."""
        if not word:
            return word
        
        replacements = {
            r'\\e7': 'ç',
            r'\\e2': 'â', 
            r'\\ea': 'ê',
            r'\\ee': 'î',
            r'\\f4': 'ô',
            r'\\fb': 'û',
            r'\\e0': 'à',
            r'\\e8': 'è', 
            r'\\ec': 'ì',
            r'\\f2': 'ò',
            r'\\f9': 'ù'
        }
        
        result = word
        for pattern, replacement in replacements.items():
            result = re.sub(pattern, replacement, result)
        
        return result