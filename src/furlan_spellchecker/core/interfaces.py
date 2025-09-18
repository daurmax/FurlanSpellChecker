"""Abstract base interfaces for FurlanSpellChecker components."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Any

from ..entities.processed_element import IProcessedElement, ProcessedWord


class ISpellChecker(ABC):
    """Interface for spell checking functionality."""

    @property
    @abstractmethod
    def processed_elements(self) -> list[IProcessedElement]:
        """Immutable collection of all processed elements."""
        raise NotImplementedError

    @property
    @abstractmethod
    def processed_words(self) -> list[IProcessedElement]:
        """Immutable collection containing only processed words."""
        raise NotImplementedError

    @abstractmethod
    def execute_spell_check(self, text: str) -> None:
        """Execute spell check on the given text."""
        raise NotImplementedError

    @abstractmethod
    def clean_spell_checker(self) -> None:
        """Clean the spell checker state."""
        raise NotImplementedError

    @abstractmethod
    async def check_word(self, word: ProcessedWord) -> bool:
        """Check if the given word is correct."""
        raise NotImplementedError

    @abstractmethod
    async def get_word_suggestions(self, word: ProcessedWord) -> list[str]:
        """Get suggestions for the given word."""
        raise NotImplementedError

    @abstractmethod
    def swap_word_with_suggested(self, original_word: ProcessedWord, suggested_word: str) -> None:
        """Replace the original word with the suggested one."""
        raise NotImplementedError

    @abstractmethod
    def ignore_word(self, word: ProcessedWord) -> None:
        """Ignore the given word during spell checking."""
        raise NotImplementedError

    @abstractmethod
    def add_word(self, word: ProcessedWord) -> None:
        """Add the given word to the dictionary."""
        raise NotImplementedError

    @abstractmethod
    def get_processed_text(self) -> str:
        """Return the corrected text."""
        raise NotImplementedError

    @abstractmethod
    def get_all_incorrect_words(self) -> list[ProcessedWord]:
        """Retrieve all incorrect words."""
        raise NotImplementedError


class IDictionary(ABC):
    """Interface for dictionary operations."""

    @abstractmethod
    def contains_word(self, word: str) -> bool:
        """Check if the dictionary contains the given word."""
        raise NotImplementedError

    @abstractmethod
    def add_word(self, word: str) -> bool:
        """Add a word to the dictionary."""
        raise NotImplementedError

    @abstractmethod
    def get_suggestions(self, word: str, max_suggestions: int = 10) -> list[str]:
        """Get spelling suggestions for the given word."""
        raise NotImplementedError

    @abstractmethod
    def load_dictionary(self, dictionary_path: str) -> None:
        """Load dictionary from file."""
        raise NotImplementedError


class IPhoneticAlgorithm(ABC):
    """Interface for phonetic algorithms."""

    @abstractmethod
    def get_phonetic_code(self, word: str) -> str:
        """Get the phonetic code for the given word."""
        raise NotImplementedError

    @abstractmethod
    def are_phonetically_similar(self, word1: str, word2: str) -> bool:
        """Check if two words are phonetically similar."""
        raise NotImplementedError


class ITextProcessor(ABC):
    """Interface for text processing operations."""

    @abstractmethod
    def process_text(self, text: str) -> list[IProcessedElement]:
        """Process text into a list of processed elements."""
        raise NotImplementedError

    @abstractmethod
    def split_into_tokens(self, text: str) -> list[str]:
        """Split text into tokens."""
        raise NotImplementedError

    @abstractmethod
    def is_word(self, token: str) -> bool:
        """Check if a token is a word."""
        raise NotImplementedError

    @abstractmethod
    def is_punctuation(self, token: str) -> bool:
        """Check if a token is punctuation."""
        raise NotImplementedError