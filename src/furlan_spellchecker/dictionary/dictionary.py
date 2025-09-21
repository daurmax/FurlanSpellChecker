"""Dictionary implementation for spell checking."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Set

from ..core.exceptions import DictionaryError, DictionaryNotFoundError, DictionaryLoadError
from ..core.interfaces import IDictionary


class Dictionary(IDictionary):
    """Basic dictionary implementation."""

    def __init__(self) -> None:
        """Initialize the dictionary."""
        self._words: Set[str] = set()
        self._loaded = False

    def contains_word(self, word: str) -> bool:
        """Check if the dictionary contains the given word."""
        return word.lower() in self._words

    def add_word(self, word: str) -> bool:
        """Add a word to the dictionary."""
        if not word or not word.strip():
            return False
        
        self._words.add(word.lower().strip())
        return True

    def get_suggestions(self, word: str, max_suggestions: int = 10) -> list[str]:
        """Get spelling suggestions for the given word."""
        # TODO: Implement proper suggestion algorithm
        # This is a placeholder implementation using simple edit distance
        suggestions = []
        
        word_lower = word.lower()
        
        # Simple suggestions based on exact matches and basic edits
        for dict_word in self._words:
            if len(suggestions) >= max_suggestions:
                break
            
            # Check for simple character substitutions
            if len(word_lower) == len(dict_word):
                diff_count = sum(1 for a, b in zip(word_lower, dict_word) if a != b)
                if diff_count == 1:
                    suggestions.append(dict_word)
            
            # Check for insertions/deletions
            elif abs(len(word_lower) - len(dict_word)) == 1:
                longer, shorter = (word_lower, dict_word) if len(word_lower) > len(dict_word) else (dict_word, word_lower)
                for i in range(len(longer)):
                    if longer[:i] + longer[i+1:] == shorter:
                        suggestions.append(dict_word)
                        break
        
        return suggestions[:max_suggestions]

    def load_dictionary(self, dictionary_path: str) -> None:
        """Load dictionary from file."""
        path = Path(dictionary_path)
        
        if not path.exists():
            raise DictionaryNotFoundError(f"Dictionary file not found: {dictionary_path}")
        
        try:
            with open(path, 'r', encoding='utf-8') as file:
                for line in file:
                    word = line.strip()
                    if word and not word.startswith('#'):  # Skip comments
                        self.add_word(word)
            
            self._loaded = True
            
        except Exception as e:
            raise DictionaryLoadError(f"Failed to load dictionary from {dictionary_path}: {e}")

    @property
    def word_count(self) -> int:
        """Get the number of words in the dictionary."""
        return len(self._words)

    @property
    def is_loaded(self) -> bool:
        """Check if the dictionary has been loaded."""
        return self._loaded


    # Encoding utilities
    
    @staticmethod
    def is_utf8_encoded(text: str) -> bool:
        """
        Check if text appears to be UTF-8 encoded.
        
        Args:
            text: Text to check
            
        Returns:
            True if text appears to be UTF-8 encoded
        """
        try:
            # Try encoding/decoding as UTF-8
            text.encode('utf-8').decode('utf-8')
            return True
        except UnicodeError:
            return False
    
    @staticmethod 
    def detect_double_encoding(text: str) -> bool:
        """
        Detect if text has been double-encoded.
        
        Args:
            text: Text to check
            
        Returns:
            True if double encoding is detected
        """
        try:
            # Try to decode as latin-1 then encode as utf-8
            decoded = text.encode('latin-1').decode('utf-8')
            # If this succeeds without error, likely double-encoded
            return decoded != text
        except (UnicodeError, UnicodeDecodeError):
            return False
    
    @staticmethod
    def normalize_encoding(text: str) -> str:
        """
        Normalize text encoding for consistent processing.
        
        Args:
            text: Text to normalize
            
        Returns:
            Normalized text
        """
        if not text:
            return ""
            
        # Handle common encoding issues
        if Dictionary.detect_double_encoding(text):
            try:
                return text.encode('latin-1').decode('utf-8')
            except (UnicodeError, UnicodeDecodeError):
                pass
        
        # Ensure UTF-8
        return text.encode('utf-8', errors='replace').decode('utf-8')


class RadixTreeDictionary(Dictionary):
    """Dictionary implementation using RadixTree for efficient lookups."""

    def __init__(self) -> None:
        """Initialize the RadixTree dictionary."""
        super().__init__()
        # TODO: Implement RadixTree data structure
        # This is a placeholder that inherits from basic Dictionary

    def get_suggestions(self, word: str, max_suggestions: int = 10) -> list[str]:
        """Get spelling suggestions using RadixTree optimization."""
        # TODO: Implement RadixTree-based suggestions
        # For now, use the parent implementation
        return super().get_suggestions(word, max_suggestions)