"""Pipeline service for orchestrating spell checking operations."""

from __future__ import annotations

from ..core.interfaces import ISpellChecker, IDictionary
from ..spellchecker import FurlanSpellChecker, TextProcessor
from ..dictionary import Dictionary
from ..phonetic import FurlanPhoneticAlgorithm
from ..entities import ProcessedWord


class SpellCheckPipeline:
    """Service for orchestrating the complete spell checking pipeline."""

    def __init__(
        self,
        dictionary: IDictionary | None = None,
        spell_checker: ISpellChecker | None = None,
    ) -> None:
        """Initialize the spell check pipeline."""
        self._dictionary = dictionary or Dictionary()
        self._text_processor = TextProcessor()
        self._phonetic_algorithm = FurlanPhoneticAlgorithm()
        self._spell_checker = spell_checker or FurlanSpellChecker(
            self._dictionary, 
            self._text_processor
        )

    def check_text(self, text: str) -> dict:
        """Check text and return results."""
        # Execute spell check
        self._spell_checker.execute_spell_check(text)
        
        # Get results
        incorrect_words = self._spell_checker.get_all_incorrect_words()
        processed_text = self._spell_checker.get_processed_text()
        
        return {
            "original_text": text,
            "processed_text": processed_text,
            "incorrect_words": [
                {
                    "original": word.original,
                    "current": word.current,
                    "suggestions": [], # TODO: Get suggestions
                    "case": word.case.value,
                }
                for word in incorrect_words
            ],
            "total_words": len(self._spell_checker.processed_words),
            "incorrect_count": len(incorrect_words),
        }

    async def check_word(self, word: str) -> dict:
        """Check a single word and return results."""
        processed_word = ProcessedWord(word)
        is_correct = await self._spell_checker.check_word(processed_word)
        
        result = {
            "word": word,
            "is_correct": is_correct,
            "case": processed_word.case.value,
            "suggestions": [],
        }
        
        if not is_correct:
            suggestions = await self._spell_checker.get_word_suggestions(processed_word)
            result["suggestions"] = suggestions
            
        return result

    async def get_suggestions(self, word: str, max_suggestions: int = 10) -> list[str]:
        """Get spelling suggestions for a word."""
        processed_word = ProcessedWord(word)
        suggestions = await self._spell_checker.get_word_suggestions(processed_word)
        return suggestions[:max_suggestions]

    def add_word_to_dictionary(self, word: str) -> bool:
        """Add a word to the dictionary."""
        return self._dictionary.add_word(word)

    def load_dictionary(self, dictionary_path: str) -> None:
        """Load dictionary from file."""
        self._dictionary.load_dictionary(dictionary_path)

    def clean(self) -> None:
        """Clean the pipeline state."""
        self._spell_checker.clean_spell_checker()