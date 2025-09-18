"""Main spell checker implementation."""

from __future__ import annotations

from ..core.interfaces import ISpellChecker, IDictionary, ITextProcessor
from ..entities.processed_element import IProcessedElement, ProcessedWord


class FurlanSpellChecker(ISpellChecker):
    """Main implementation of Friulian spell checker."""

    def __init__(
        self,
        dictionary: IDictionary,
        text_processor: ITextProcessor,
    ) -> None:
        """Initialize the spell checker."""
        self._dictionary = dictionary
        self._text_processor = text_processor
        self._processed_elements: list[IProcessedElement] = []

    @property
    def processed_elements(self) -> list[IProcessedElement]:
        """Get immutable collection of all processed elements."""
        return self._processed_elements.copy()

    @property
    def processed_words(self) -> list[IProcessedElement]:
        """Get immutable collection containing only processed words."""
        return [elem for elem in self._processed_elements if isinstance(elem, ProcessedWord)]

    def execute_spell_check(self, text: str) -> None:
        """Execute spell check on the given text."""
        # TODO: Implement spell checking logic
        self._processed_elements = self._text_processor.process_text(text)
        
        # Check each word
        for element in self._processed_elements:
            if isinstance(element, ProcessedWord):
                # TODO: Implement async word checking
                pass

    def clean_spell_checker(self) -> None:
        """Clean the spell checker state."""
        self._processed_elements.clear()

    async def check_word(self, word: ProcessedWord) -> bool:
        """Check if the given word is correct."""
        # TODO: Implement word checking logic
        is_correct = self._dictionary.contains_word(word.current.lower())
        word.checked = True
        word.correct = is_correct
        return is_correct

    async def get_word_suggestions(self, word: ProcessedWord) -> list[str]:
        """Get suggestions for the given word."""
        # TODO: Implement suggestion logic
        if word.correct:
            return []
        return self._dictionary.get_suggestions(word.current)

    def swap_word_with_suggested(self, original_word: ProcessedWord, suggested_word: str) -> None:
        """Replace the original word with the suggested one."""
        # TODO: Implement case preservation logic
        original_word.current = suggested_word

    def ignore_word(self, word: ProcessedWord) -> None:
        """Ignore the given word during spell checking."""
        word.correct = True
        word.checked = True

    def add_word(self, word: ProcessedWord) -> None:
        """Add the given word to the dictionary."""
        self._dictionary.add_word(word.current)
        word.correct = True
        word.checked = True

    def get_processed_text(self) -> str:
        """Return the corrected text."""
        # TODO: Implement text reconstruction logic
        return "".join(elem.current for elem in self._processed_elements)

    def get_all_incorrect_words(self) -> list[ProcessedWord]:
        """Retrieve all incorrect words."""
        incorrect_words = []
        for element in self._processed_elements:
            if isinstance(element, ProcessedWord) and element.checked and not element.correct:
                incorrect_words.append(element)
        return incorrect_words