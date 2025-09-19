"""Database interfaces for Friulian spell checker.

This module defines interfaces for accessing different types of databases:
- SQLite databases for words, errors, frequencies, elisions
- Binary radix tree for fast word lookups
"""

# Import enums and interfaces from interfaces module
from .interfaces import DictionaryType, AddWordResult, IKeyValueDatabase, IRadixTree

# Import implementations
from .sqlite_database import SQLiteKeyValueDatabase
from .radix_tree import BinaryRadixTree, RadixTreeDatabase
from .manager import DatabaseManager

__all__ = [
    'DictionaryType',
    'AddWordResult', 
    'IKeyValueDatabase',
    'IRadixTree',
    'SQLiteKeyValueDatabase',
    'BinaryRadixTree',
    'RadixTreeDatabase', 
    'DatabaseManager'
]