"""FurlanSpellChecker public API."""

from __future__ import annotations

from .__about__ import __version__
from .core.interfaces import (
    IDictionary,
    IPhoneticAlgorithm,
    ISpellChecker,
    ITextProcessor,
)
from .dictionary import Dictionary, RadixTreeDictionary
from .entities import IProcessedElement, ProcessedPunctuation, ProcessedWord
from .phonetic import FurlanPhoneticAlgorithm
from .services import IOService, SpellCheckPipeline
from .services.dictionary_manager import DictionaryManager
from .spellchecker import FurlanSpellChecker, TextProcessor
from .database import (
    DatabaseManager,
    SQLiteKeyValueDatabase,
    BinaryRadixTree,
    RadixTreeDatabase,
    DictionaryType,
    AddWordResult,
)
from .config import (
    FurlanSpellCheckerConfig,
    DictionaryConfig,
    SpellCheckerConfig,
    TextProcessingConfig,
    PhoneticConfig,
)

version = __version__

__all__ = [
    "version",
    # Core interfaces
    "ISpellChecker",
    "IDictionary",
    "IPhoneticAlgorithm", 
    "ITextProcessor",
    # Main implementations
    "FurlanSpellChecker",
    "TextProcessor",
    "Dictionary",
    "RadixTreeDictionary",
    "FurlanPhoneticAlgorithm",
    # Entities
    "IProcessedElement",
    "ProcessedWord",
    "ProcessedPunctuation", 
    # Services
    "SpellCheckPipeline",
    "IOService",
    "DictionaryManager",
    # Database
    "DatabaseManager", 
    "SQLiteKeyValueDatabase",
    "BinaryRadixTree",
    "RadixTreeDatabase",
    "DictionaryType",
    "AddWordResult",
    # Configuration
    "FurlanSpellCheckerConfig",
    "DictionaryConfig",
    "SpellCheckerConfig", 
    "TextProcessingConfig",
    "PhoneticConfig",
]