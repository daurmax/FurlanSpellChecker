"""Main spell checker implementation."""

from __future__ import annotations
from typing import Optional

from ..core.interfaces import ISpellChecker, IDictionary, ITextProcessor
from ..entities.processed_element import IProcessedElement, ProcessedWord
from ..database import DatabaseManager, DictionaryType
from ..phonetic.furlan_phonetic import FurlanPhoneticAlgorithm
from ..config.schemas import FurlanSpellCheckerConfig


class FurlanSpellChecker(ISpellChecker):
    """Main implementation of Friulian spell checker."""

    def __init__(
        self,
        dictionary: IDictionary,
        text_processor: ITextProcessor,
        config: Optional[FurlanSpellCheckerConfig] = None,
    ) -> None:
        """Initialize the spell checker."""
        self._dictionary = dictionary
        self._text_processor = text_processor
        self._processed_elements: list[IProcessedElement] = []
        self._config = config or FurlanSpellCheckerConfig()
        self._db_manager = DatabaseManager(self._config)
        self._phonetic_algo = FurlanPhoneticAlgorithm()

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
        word_str = word.current
        
        # Check system dictionary using phonetic hashes
        hash_a, hash_b = self._phonetic_algo.get_phonetic_hashes_by_word(word_str)
        
        # Check system dictionary
        system_result_a = self._db_manager.sqlite_db.find_in_system_database(hash_a)
        system_result_b = self._db_manager.sqlite_db.find_in_system_database(hash_b) if hash_a != hash_b else None
        
        if system_result_a is not None or system_result_b is not None:
            word.checked = True
            word.correct = True
            return True
        
        # Check user dictionary  
        user_result_a = self._db_manager.sqlite_db.find_in_user_database(hash_a)
        user_result_b = self._db_manager.sqlite_db.find_in_user_database(hash_b) if hash_a != hash_b else None
        
        if user_result_a is not None or user_result_b is not None:
            word.checked = True
            word.correct = True
            return True
        
        # Check radix tree
        try:
            if self._db_manager.radix_tree.contains_word(word_str.lower()):
                word.checked = True
                word.correct = True
                return True
        except FileNotFoundError:
            # Radix tree not available, continue with other checks
            pass
        
        # Check for corrections in error databases
        system_correction = self._db_manager.sqlite_db.find_in_system_errors_database(word_str)
        if system_correction:
            word.checked = True
            word.correct = False
            return False
        
        # Word not found in any database
        word.checked = True
        word.correct = False
        return False

    async def get_word_suggestions(self, word: ProcessedWord) -> list[str]:
        """Get suggestions for the given word."""
        if word.correct:
            return []
        
        suggestions = []
        word_str = word.current
        
        # Check for direct corrections in error databases
        system_correction = self._db_manager.sqlite_db.find_in_system_errors_database(word_str)
        if system_correction:
            suggestions.append(system_correction)
        
        user_correction = self._db_manager.sqlite_db.find_in_user_errors_database(word_str)
        if user_correction:
            suggestions.append(user_correction)
        
        # Try variations (case changes) for error database lookup
        variations = [
            word_str.lower(),
            word_str.capitalize(),
            word_str.upper()
        ]
        
        for variation in variations:
            if variation != word_str:
                system_var_correction = self._db_manager.sqlite_db.find_in_system_errors_database(variation)
                if system_var_correction and system_var_correction not in suggestions:
                    suggestions.append(system_var_correction)
        
        # Get radix tree suggestions
        try:
            radix_suggestions = self._db_manager.radix_tree.get_suggestions(
                word_str, 
                max_suggestions=self._config.dictionary.max_suggestions
            )
            for suggestion in radix_suggestions:
                if suggestion not in suggestions:
                    suggestions.append(suggestion)
        except FileNotFoundError:
            # Radix tree not available
            pass
        
        # Fallback to dictionary suggestions if available
        if not suggestions:
            suggestions = self._dictionary.get_suggestions(word_str)
        
        # Limit suggestions based on config
        return suggestions[:self._config.dictionary.max_suggestions]

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
        # Add to user database
        result = self._db_manager.sqlite_db.add_to_user_database(word.current)
        
        # Also add to in-memory dictionary if available
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