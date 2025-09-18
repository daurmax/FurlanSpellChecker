"""Text processor for parsing and tokenizing text."""

from __future__ import annotations

import re
from typing import List

from ..core.interfaces import ITextProcessor
from ..entities.processed_element import IProcessedElement, ProcessedWord, ProcessedPunctuation


class TextProcessor(ITextProcessor):
    """Implementation of text processing functionality."""

    def __init__(self) -> None:
        """Initialize the text processor."""
        # TODO: Define better tokenization patterns
        self._word_pattern = re.compile(r"\b\w+\b")
        self._punctuation_pattern = re.compile(r"[^\w\s]")
        self._whitespace_pattern = re.compile(r"\s+")

    def process_text(self, text: str) -> list[IProcessedElement]:
        """Process text into a list of processed elements."""
        elements: list[IProcessedElement] = []
        
        # TODO: Implement proper tokenization that preserves order and whitespace
        # This is a simplified implementation
        tokens = self.split_into_tokens(text)
        
        for token in tokens:
            if self.is_word(token):
                elements.append(ProcessedWord(token))
            elif self.is_punctuation(token):
                elements.append(ProcessedPunctuation(token))
            # Skip whitespace for now
        
        return elements

    def split_into_tokens(self, text: str) -> list[str]:
        """Split text into tokens."""
        # TODO: Implement proper tokenization that handles Friulian text
        # This is a simplified implementation using regex
        tokens = []
        
        # Find all words and punctuation
        for match in re.finditer(r"\w+|[^\w\s]|\s+", text):
            token = match.group()
            if token.strip():  # Skip pure whitespace for now
                tokens.append(token)
        
        return tokens

    def is_word(self, token: str) -> bool:
        """Check if a token is a word."""
        return bool(self._word_pattern.match(token))

    def is_punctuation(self, token: str) -> bool:
        """Check if a token is punctuation."""
        return bool(self._punctuation_pattern.match(token)) and not token.isspace()