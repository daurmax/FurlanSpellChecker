"""User exceptions database implementation for FurlanSpellChecker.

This module implements user exceptions functionality compatible with COF's user_exc,
using SQLite as the backend storage instead of Berkeley DB.
"""
import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Tuple


class UserExceptionsDatabase:
    """
    User exceptions database using SQLite backend.
    
    Implements COF's user_exc functionality:
    - Stores error -> correction pairs
    - Direct key-value lookup (no phonetic indexing)
    - Highest priority in suggestion ranking (F_USER_EXC = 1000)
    - Simple add, delete, update operations
    """
    
    def __init__(self, db_path: Path):
        """Initialize user exceptions database.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._ensure_database_exists()
    
    def _ensure_database_exists(self) -> None:
        """Create database and table if they don't exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Direct error -> correction mapping
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_exceptions (
                    error_word TEXT PRIMARY KEY,
                    correction TEXT NOT NULL
                )
            """)
            conn.commit()
    
    def add_exception(self, error_word: str, correction: str) -> bool:
        """
        Add or update an error -> correction pair.
        
        Args:
            error_word: The incorrect word
            correction: The correct word
            
        Returns:
            True if exception was added/updated successfully
        """
        if not error_word or not correction:
            return False
        
        error_word = error_word.strip()
        correction = correction.strip()
        
        if error_word == correction:
            return False  # No point in mapping word to itself
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO user_exceptions (error_word, correction) VALUES (?, ?)",
                (error_word, correction)
            )
            conn.commit()
        
        return True
    
    def remove_exception(self, error_word: str) -> bool:
        """
        Remove an exception.
        
        Args:
            error_word: The error word to remove
            
        Returns:
            True if exception was removed, False if not found
        """
        if not error_word:
            return False
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user_exceptions WHERE error_word = ?", (error_word.strip(),))
            removed = cursor.rowcount > 0
            conn.commit()
        
        return removed
    
    def get_correction(self, error_word: str) -> Optional[str]:
        """
        Get correction for an error word.
        
        Args:
            error_word: The incorrect word
            
        Returns:
            Correction if found, None otherwise
        """
        if not error_word:
            return None
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT correction FROM user_exceptions WHERE error_word = ?", (error_word.strip(),))
            result = cursor.fetchone()
            return result[0] if result else None
    
    def has_exception(self, error_word: str) -> bool:
        """
        Check if an error word has a defined correction.
        
        Args:
            error_word: The error word to check
            
        Returns:
            True if exception exists
        """
        return self.get_correction(error_word) is not None
    
    def update_exception(self, error_word: str, new_correction: str) -> bool:
        """
        Update an existing exception.
        
        Args:
            error_word: The error word
            new_correction: The new correction
            
        Returns:
            True if exception was updated, False if not found
        """
        if not self.has_exception(error_word):
            return False
        
        return self.add_exception(error_word, new_correction)
    
    def get_all_exceptions(self) -> Dict[str, str]:
        """
        Get all error -> correction pairs.
        
        Returns:
            Dictionary mapping error words to corrections
        """
        exceptions = {}
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT error_word, correction FROM user_exceptions ORDER BY error_word")
            
            for error_word, correction in cursor.fetchall():
                exceptions[error_word] = correction
        
        return exceptions
    
    def get_all_exceptions_list(self) -> List[Tuple[str, str]]:
        """
        Get all error -> correction pairs as list of tuples.
        
        Returns:
            List of (error_word, correction) tuples, sorted by error_word
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT error_word, correction FROM user_exceptions ORDER BY error_word")
            return cursor.fetchall()
    
    def clear(self) -> None:
        """Clear all exceptions from database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user_exceptions")
            conn.commit()
    
    def get_exception_count(self) -> int:
        """Get total number of exceptions in database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM user_exceptions")
            return cursor.fetchone()[0]
    
    def import_from_dict(self, exceptions: Dict[str, str]) -> int:
        """
        Import exceptions from dictionary.
        
        Args:
            exceptions: Dictionary mapping error words to corrections
            
        Returns:
            Number of exceptions imported
        """
        count = 0
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for error_word, correction in exceptions.items():
                if error_word and correction and error_word != correction:
                    cursor.execute(
                        "INSERT OR REPLACE INTO user_exceptions (error_word, correction) VALUES (?, ?)",
                        (error_word.strip(), correction.strip())
                    )
                    count += 1
            
            conn.commit()
        
        return count
    
    def export_to_dict(self) -> Dict[str, str]:
        """
        Export all exceptions to dictionary.
        
        Returns:
            Dictionary mapping error words to corrections
        """
        return self.get_all_exceptions()