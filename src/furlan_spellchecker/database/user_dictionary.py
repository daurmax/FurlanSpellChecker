"""User dictionary database implementation for FurlanSpellChecker.

This module implements user dictionary functionality compatible with COF's user_dict,
using SQLite as the backend storage instead of Berkeley DB.
"""
import sqlite3
from pathlib import Path
from typing import Optional, List, Set
from ..phonetic.furlan_phonetic import FurlanPhoneticAlgorithm


class UserDictionaryDatabase:
    """
    User dictionary database using SQLite backend.
    
    Implements COF's user_dict functionality:
    - Stores user-added words indexed by phonetic codes
    - Uses phonetic algorithm to generate lookup keys
    - Supports add, delete, and lookup operations
    - Maintains COF-compatible comma-separated value format
    """
    
    def __init__(self, db_path: Path):
        """Initialize user dictionary database.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.phonetic = FurlanPhoneticAlgorithm()
        self._ensure_database_exists()
    
    def _ensure_database_exists(self) -> None:
        """Create database and table if they don't exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # COF-compatible schema: phonetic_code -> comma-separated words
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_dictionary (
                    phonetic_code TEXT PRIMARY KEY,
                    words TEXT NOT NULL
                )
            """)
            conn.commit()
    
    def add_word(self, word: str) -> bool:
        """
        Add word to user dictionary.
        
        Implements COF's change_user_dict logic:
        1. Calculate phonetic codes for the word
        2. For each code, check if word already exists
        3. If not exists, add to comma-separated list
        4. Store under both codes (if different)
        
        Args:
            word: Word to add
            
        Returns:
            True if word was added, False if already present
        """
        if not word:
            return False
        
        word = word.strip()
        code1, code2 = self.phonetic.get_phonetic_hashes_by_word(word)
        
        # Get unique codes
        codes = [code1] if code1 == code2 else [code1, code2]
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if word already exists under any code
            for code in codes:
                cursor.execute("SELECT words FROM user_dictionary WHERE phonetic_code = ?", (code,))
                result = cursor.fetchone()
                
                if result:
                    existing_words = result[0].split(',')
                    if word in existing_words:
                        return False  # Word already exists
            
            # Add word to all relevant codes
            for code in codes:
                cursor.execute("SELECT words FROM user_dictionary WHERE phonetic_code = ?", (code,))
                result = cursor.fetchone()
                
                if result:
                    # Add to existing list
                    existing_words = result[0].split(',')
                    existing_words.append(word)
                    new_words = ','.join(existing_words)
                    cursor.execute(
                        "UPDATE user_dictionary SET words = ? WHERE phonetic_code = ?", 
                        (new_words, code)
                    )
                else:
                    # Create new entry
                    cursor.execute(
                        "INSERT INTO user_dictionary (phonetic_code, words) VALUES (?, ?)", 
                        (code, word)
                    )
            
            conn.commit()
        
        return True
    
    def remove_word(self, word: str) -> bool:
        """
        Remove word from user dictionary.
        
        Implements COF's delete_user_dict logic:
        1. Calculate phonetic codes for the word
        2. For each code, remove word from comma-separated list
        3. Delete entry if no words remain
        
        Args:
            word: Word to remove
            
        Returns:
            True if word was removed, False if not found
        """
        if not word:
            return False
        
        word = word.strip()
        code1, code2 = self.phonetic.get_phonetic_hashes_by_word(word)
        
        # Get unique codes
        codes = [code1] if code1 == code2 else [code1, code2]
        
        removed = False
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for code in codes:
                cursor.execute("SELECT words FROM user_dictionary WHERE phonetic_code = ?", (code,))
                result = cursor.fetchone()
                
                if result:
                    existing_words = [w for w in result[0].split(',') if w != word]
                    
                    if len(existing_words) < len(result[0].split(',')):
                        removed = True
                        
                        if existing_words:
                            # Update with remaining words
                            new_words = ','.join(existing_words)
                            cursor.execute(
                                "UPDATE user_dictionary SET words = ? WHERE phonetic_code = ?", 
                                (new_words, code)
                            )
                        else:
                            # Delete empty entry
                            cursor.execute(
                                "DELETE FROM user_dictionary WHERE phonetic_code = ?", 
                                (code,)
                            )
            
            conn.commit()
        
        return removed
    
    def find_by_phonetic_code(self, phonetic_code: str) -> Optional[str]:
        """
        Find words by phonetic code.
        
        Args:
            phonetic_code: Phonetic hash code
            
        Returns:
            Comma-separated string of words, or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT words FROM user_dictionary WHERE phonetic_code = ?", (phonetic_code,))
            result = cursor.fetchone()
            return result[0] if result else None
    
    def get_phonetic_suggestions(self, word: str) -> List[str]:
        """
        Get phonetic suggestions for a word from user dictionary.
        
        Compatible with COF's get_phonetic_sugg('user', ...) method.
        
        Args:
            word: Input word
            
        Returns:
            List of phonetically similar words from user dictionary
        """
        code1, code2 = self.phonetic.get_phonetic_hashes_by_word(word)
        
        suggestions = set()
        
        # Look up both codes
        for code in ([code1] if code1 == code2 else [code1, code2]):
            words_str = self.find_by_phonetic_code(code)
            if words_str:
                suggestions.update(words_str.split(','))
        
        return list(suggestions)
    
    def contains_word(self, word: str) -> bool:
        """
        Check if word exists in user dictionary.
        
        Args:
            word: Word to check
            
        Returns:
            True if word exists in user dictionary
        """
        suggestions = self.get_phonetic_suggestions(word)
        return word in suggestions
    
    def get_all_words(self) -> List[str]:
        """
        Get all words in user dictionary.
        
        Returns:
            List of all words in user dictionary
        """
        words = set()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT words FROM user_dictionary")
            
            for row in cursor.fetchall():
                words.update(row[0].split(','))
        
        return sorted(words)
    
    def clear(self) -> None:
        """Clear all words from user dictionary."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user_dictionary")
            conn.commit()
    
    def get_word_count(self) -> int:
        """Get total number of words in user dictionary."""
        return len(self.get_all_words())
    
    def has_word(self, word: str) -> bool:
        """
        Check if word exists in user dictionary.
        
        Args:
            word: Word to check
            
        Returns:
            True if word exists in dictionary
        """
        if not word:
            return False
        
        return word in self.get_all_words()
    
    def get_words_by_phonetic_code(self, phonetic_code: str) -> List[str]:
        """
        Get all words stored under a specific phonetic code.
        
        Args:
            phonetic_code: The phonetic code to search for
            
        Returns:
            List of words matching the phonetic code
        """
        if not phonetic_code:
            return []
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT words FROM user_dictionary WHERE phonetic_code = ?", (phonetic_code,))
            result = cursor.fetchone()
            
            if result:
                return result[0].split(',')
            return []
    
    def get_phonetic_suggestions(self, word: str) -> List[str]:
        """
        Get phonetic suggestions for a word (without max_suggestions parameter to match test).
        
        Args:
            word: Word to find suggestions for
            
        Returns:
            List of phonetically similar words
        """
        return self._get_phonetic_suggestions_internal(word, max_suggestions=10)
    
    def _get_phonetic_suggestions_internal(self, word: str, max_suggestions: int = 10) -> List[str]:
        """Internal method for phonetic suggestions with max_suggestions parameter."""
        if not word:
            return []
        
        try:
            # Get phonetic codes for input word
            code_a, code_b = self.phonetic_algo.get_phonetic_hashes_by_word(word.lower())
            
            suggestions = []
            
            # Get words for both phonetic codes
            for code in [code_a, code_b]:
                if code:  # Skip empty codes
                    words = self.get_words_by_phonetic_code(code)
                    suggestions.extend(words)
            
            # Remove duplicates and the original word
            unique_suggestions = []
            seen = set()
            
            for suggestion in suggestions:
                if suggestion and suggestion.lower() != word.lower() and suggestion not in seen:
                    unique_suggestions.append(suggestion)
                    seen.add(suggestion)
            
            return unique_suggestions[:max_suggestions]
            
        except Exception:
            return []