"""SQLite database implementation for Friulian spell checker."""
import re
import sqlite3
from pathlib import Path
from typing import Optional, List, Tuple, Dict

from .interfaces import (
    IKeyValueDatabase, DictionaryType, AddWordResult, RemoveWordResult, AddExceptionResult
)
from .user_dictionary import UserDictionaryDatabase
from .user_exceptions import UserExceptionsDatabase
from ..config.schemas import FurlanSpellCheckerConfig


class SQLiteKeyValueDatabase(IKeyValueDatabase):
    """SQLite implementation of key-value database operations."""
    
    def __init__(self, config: Optional[FurlanSpellCheckerConfig] = None):
        """Initialize with configuration for database paths."""
        self.config = config or FurlanSpellCheckerConfig()
        self._db_paths = self._get_database_paths()
        
        # Initialize user databases
        self._user_dictionary = UserDictionaryDatabase(
            self._db_paths[DictionaryType.USER_DICTIONARY]
        )
        self._user_exceptions = UserExceptionsDatabase(
            self._db_paths[DictionaryType.USER_ERRORS]
        )
    
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
        words = self._user_dictionary.get_words_by_phonetic_code(phonetic_hash)
        return ','.join(words) if words else None
    
    def find_in_user_errors_database(self, word: str) -> Optional[str]:
        """Find correction in user errors database."""
        return self._user_exceptions.get_correction(word)
    
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
            cursor.execute("SELECT * FROM Data WHERE Word = ?", (word,))
            return cursor.fetchone() is not None
    
    def add_to_user_database(self, word: str) -> AddWordResult:
        """Add word to user dictionary."""
        if not word:
            return AddWordResult.ERROR
        
        try:
            success = self._user_dictionary.add_word(word)
            return AddWordResult.SUCCESS if success else AddWordResult.ALREADY_PRESENT
        except Exception:
            return AddWordResult.ERROR
    
    def remove_from_user_database(self, word: str) -> RemoveWordResult:
        """Remove word from user dictionary."""
        if not word:
            return RemoveWordResult.ERROR
        
        try:
            success = self._user_dictionary.remove_word(word)
            return RemoveWordResult.SUCCESS if success else RemoveWordResult.NOT_FOUND
        except Exception:
            return RemoveWordResult.ERROR
    
    def add_user_exception(self, error_word: str, correction: str) -> AddExceptionResult:
        """Add error -> correction pair to user exceptions."""
        if not error_word or not correction:
            return AddExceptionResult.INVALID_INPUT
        
        try:
            # Check if exception already exists
            existing = self._user_exceptions.get_correction(error_word)
            success = self._user_exceptions.add_exception(error_word, correction)
            
            if success:
                return AddExceptionResult.UPDATED if existing else AddExceptionResult.SUCCESS
            else:
                return AddExceptionResult.INVALID_INPUT
        except Exception:
            return AddExceptionResult.ERROR
    
    def remove_user_exception(self, error_word: str) -> RemoveWordResult:
        """Remove exception from user exceptions."""
        if not error_word:
            return RemoveWordResult.ERROR
        
        try:
            success = self._user_exceptions.remove_exception(error_word)
            return RemoveWordResult.SUCCESS if success else RemoveWordResult.NOT_FOUND
        except Exception:
            return RemoveWordResult.ERROR
    
    def get_user_dictionary_suggestions(self, word: str, max_suggestions: int = 10) -> List[str]:
        """Get phonetic suggestions from user dictionary."""
        if not word:
            return []
        
        try:
            return self._user_dictionary.get_phonetic_suggestions(word, max_suggestions)
        except Exception:
            return []
    
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