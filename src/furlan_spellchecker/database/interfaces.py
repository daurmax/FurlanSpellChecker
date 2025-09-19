"""Separate interfaces module to avoid circular imports."""
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, List


class DictionaryType(Enum):
    """Types of dictionaries available."""
    SYSTEM_DICTIONARY = "system_dictionary"
    USER_DICTIONARY = "user_dictionary" 
    SYSTEM_ERRORS = "system_errors"
    USER_ERRORS = "user_errors"
    FREQUENCIES = "frequencies"
    ELISIONS = "elisions"
    RADIX_TREE = "radix_tree"


class AddWordResult(Enum):
    """Results of adding a word to user dictionary."""
    SUCCESS = "success"
    ALREADY_PRESENT = "already_present"
    DATABASE_NOT_EXISTS = "database_not_exists"
    ERROR = "error"


class IKeyValueDatabase(ABC):
    """Interface for key-value database operations."""
    
    @abstractmethod
    def find_in_user_database(self, phonetic_hash: str) -> Optional[str]:
        """Find value in user dictionary by phonetic hash."""
        pass
    
    @abstractmethod
    def find_in_user_errors_database(self, word: str) -> Optional[str]:
        """Find correction in user errors database."""
        pass
    
    @abstractmethod
    def find_in_system_database(self, phonetic_hash: str) -> Optional[str]:
        """Find value in system dictionary by phonetic hash."""
        pass
    
    @abstractmethod
    def find_in_system_errors_database(self, word: str) -> Optional[str]:
        """Find correction in system errors database."""
        pass
    
    @abstractmethod
    def find_in_frequencies_database(self, word: str) -> Optional[int]:
        """Find frequency value for a word."""
        pass
    
    @abstractmethod
    def has_elisions(self, word: str) -> bool:
        """Check if word exists in elisions database."""
        pass
    
    @abstractmethod
    def add_to_user_database(self, word: str) -> AddWordResult:
        """Add word to user dictionary."""
        pass


class IRadixTree(ABC):
    """Interface for radix tree operations."""
    
    @abstractmethod
    def contains(self, word: str) -> bool:
        """Check if word exists in radix tree."""
        pass
    
    @abstractmethod
    def find_suggestions(self, word: str, max_suggestions: int = 10) -> List[str]:
        """Find spelling suggestions for a word."""
        pass
    
    @abstractmethod
    def get_words_with_prefix(self, prefix: str, max_results: int = 100) -> List[str]:
        """Get words starting with given prefix."""
        pass