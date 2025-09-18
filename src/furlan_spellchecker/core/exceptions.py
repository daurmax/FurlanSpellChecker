"""Core exceptions for FurlanSpellChecker."""

from __future__ import annotations


class FurlanSpellCheckerError(Exception):
    """Base exception for all FurlanSpellChecker errors."""

    pass


class DictionaryError(FurlanSpellCheckerError):
    """Exception raised for dictionary-related errors."""

    pass


class DictionaryNotFoundError(DictionaryError):
    """Exception raised when a dictionary file is not found."""

    pass


class DictionaryLoadError(DictionaryError):
    """Exception raised when a dictionary fails to load."""

    pass


class PhoneticAlgorithmError(FurlanSpellCheckerError):
    """Exception raised for phonetic algorithm errors."""

    pass


class TextProcessingError(FurlanSpellCheckerError):
    """Exception raised for text processing errors."""

    pass


class SpellCheckerError(FurlanSpellCheckerError):
    """Exception raised for spell checker errors."""

    pass


class InvalidWordError(SpellCheckerError):
    """Exception raised when an invalid word is processed."""

    pass


class ConfigurationError(FurlanSpellCheckerError):
    """Exception raised for configuration errors."""

    pass