"""Core module initialization."""

from .exceptions import (
    ConfigurationError,
    DictionaryError,
    DictionaryLoadError,
    DictionaryNotFoundError,
    FurlanSpellCheckerError,
    InvalidWordError,
    PhoneticAlgorithmError,
    SpellCheckerError,
    TextProcessingError,
)
from .interfaces import (
    IDictionary,
    IPhoneticAlgorithm,
    ISpellChecker,
    ITextProcessor,
)
from .types import (
    DictionaryType,
    PhoneticCode,
    SuggestionList,
    SuggestionOriginPriority,
    WordType,
)

__all__ = [
    # Exceptions
    "FurlanSpellCheckerError",
    "DictionaryError",
    "DictionaryNotFoundError",
    "DictionaryLoadError",
    "PhoneticAlgorithmError",
    "TextProcessingError",
    "SpellCheckerError",
    "InvalidWordError",
    "ConfigurationError",
    # Interfaces
    "ISpellChecker",
    "IDictionary",
    "IPhoneticAlgorithm",
    "ITextProcessor",
    # Types
    "WordType",
    "DictionaryType",
    "SuggestionOriginPriority",
    "SuggestionList",
    "PhoneticCode",
]