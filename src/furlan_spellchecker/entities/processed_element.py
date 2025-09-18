"""Processed element interfaces and base classes."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..core.types import WordType


class IProcessedElement(ABC):
    """Interface for processed text elements."""

    @property
    @abstractmethod
    def original(self) -> str:
        """Get the original text."""
        raise NotImplementedError

    @property
    @abstractmethod
    def current(self) -> str:
        """Get the current text."""
        raise NotImplementedError

    @current.setter
    @abstractmethod
    def current(self, value: str) -> None:
        """Set the current text."""
        raise NotImplementedError


class ProcessedWord(IProcessedElement):
    """Represents a processed word element."""

    def __init__(self, word: str) -> None:
        """Initialize a processed word."""
        self._original = word
        self._current = word
        self._checked = False
        self._correct = False

    @property
    def original(self) -> str:
        """Get the original word."""
        return self._original

    @property
    def current(self) -> str:
        """Get the current word."""
        return self._current

    @current.setter
    def current(self, value: str) -> None:
        """Set the current word."""
        self._current = value

    @property
    def checked(self) -> bool:
        """Get whether the word has been checked."""
        return self._checked

    @checked.setter
    def checked(self, value: bool) -> None:
        """Set whether the word has been checked."""
        self._checked = value

    @property
    def correct(self) -> bool:
        """Get whether the word is correct."""
        return self._correct

    @correct.setter
    def correct(self, value: bool) -> None:
        """Set whether the word is correct."""
        self._correct = value

    @property
    def case(self) -> WordType:
        """Get the case type of the word."""
        word = self._original
        
        if word.islower():
            return WordType.LOWERCASE
        elif word.isupper():
            return WordType.UPPERCASE
        elif word[0].isupper() and word[1:].islower():
            return WordType.FIRST_LETTER_UPPERCASE
        else:
            return WordType.MIXED_CASE

    def __str__(self) -> str:
        """Return string representation."""
        return f"ProcessedWord('{self.current}', correct={self.correct})"

    def __repr__(self) -> str:
        """Return detailed string representation."""
        return (
            f"ProcessedWord(original='{self.original}', "
            f"current='{self.current}', "
            f"checked={self.checked}, "
            f"correct={self.correct}, "
            f"case={self.case})"
        )


class ProcessedPunctuation(IProcessedElement):
    """Represents a processed punctuation element."""

    def __init__(self, punctuation: str) -> None:
        """Initialize a processed punctuation."""
        self._original = punctuation
        self._current = punctuation

    @property
    def original(self) -> str:
        """Get the original punctuation."""
        return self._original

    @property
    def current(self) -> str:
        """Get the current punctuation."""
        return self._current

    @current.setter
    def current(self, value: str) -> None:
        """Set the current punctuation."""
        self._current = value

    def __str__(self) -> str:
        """Return string representation."""
        return f"ProcessedPunctuation('{self.current}')"

    def __repr__(self) -> str:
        """Return detailed string representation."""
        return f"ProcessedPunctuation(original='{self.original}', current='{self.current}')"