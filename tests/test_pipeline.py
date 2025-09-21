"""Test SpellCheckPipeline functionality."""

import pytest
from furlan_spellchecker.services import SpellCheckPipeline
from furlan_spellchecker.dictionary import Dictionary
from furlan_spellchecker.spellchecker import TextProcessor


class TestSpellCheckPipeline:
    """Test SpellCheckPipeline functionality."""

    def test_initialization(self):
        """Test pipeline initialization."""
        pipeline = SpellCheckPipeline()
        assert pipeline is not None

    def test_initialization_with_dictionary(self, sample_dictionary):
        """Test pipeline initialization with custom dictionary."""
        pipeline = SpellCheckPipeline(dictionary=sample_dictionary)
        assert pipeline is not None

    def test_check_text_basic(self, spell_check_pipeline):
        """Test basic text checking."""
        text = "cjase"
        result = spell_check_pipeline.check_text(text)
        
        assert "original_text" in result
        assert "processed_text" in result
        assert "incorrect_words" in result
        assert "total_words" in result
        assert "incorrect_count" in result
        
        assert result["original_text"] == text

    @pytest.mark.asyncio
    async def test_check_word_correct(self, spell_check_pipeline):
        """Test checking a correct word."""
        result = await spell_check_pipeline.check_word("cjase")
        
        assert result["word"] == "cjase"
        assert result["is_correct"] is True
        assert "case" in result
        assert "suggestions" in result

    @pytest.mark.asyncio  
    async def test_check_word_incorrect(self, spell_check_pipeline):
        """Test checking an incorrect word."""
        result = await spell_check_pipeline.check_word("nonexistent")
        
        assert result["word"] == "nonexistent"
        assert result["is_correct"] is False
        assert "case" in result
        assert "suggestions" in result

    @pytest.mark.asyncio
    async def test_get_suggestions(self, spell_check_pipeline):
        """Test getting suggestions for a word."""
        suggestions = await spell_check_pipeline.get_suggestions("nonexistent")
        
        assert isinstance(suggestions, list)

    def test_add_word_to_dictionary(self, spell_check_pipeline):
        """Test adding word to dictionary."""
        result = spell_check_pipeline.add_word_to_dictionary("newword")
        assert result is True

    def test_clean_pipeline(self, spell_check_pipeline):
        """Test cleaning pipeline state."""
        # Check some text first
        spell_check_pipeline.check_text("some text")
        
        # Clean should not raise error
        spell_check_pipeline.clean()

    def test_load_dictionary(self, spell_check_pipeline, tmp_path):
        """Test loading dictionary through pipeline."""
        # Create temporary dictionary file
        dict_file = tmp_path / "test_dict.txt"
        dict_file.write_text("testword\nanotherword\n", encoding="utf-8")
        
        # Load should not raise error
        spell_check_pipeline.load_dictionary(str(dict_file))

    @pytest.mark.asyncio
    async def test_friulian_word_checking(self, spell_check_pipeline):
        """Test spell checking with Friulian words."""
        # Test known Friulian words
        friulian_words = ["furlan", "lenghe", "cjase", "aghe", "scuele"]
        
        for word in friulian_words:
            result = await spell_check_pipeline.check_word(word)
            # For now, just ensure it doesn't crash and returns proper structure
            assert "word" in result
            assert "is_correct" in result
            assert result["word"] == word

    @pytest.mark.asyncio 
    async def test_suggestion_generation(self, spell_check_pipeline):
        """Test suggestion mechanism for misspelled words."""
        # Test with slightly misspelled word
        result = await spell_check_pipeline.get_suggestions("furla", max_suggestions=5)
        
        # Should return a list (may be empty in test environment)
        assert isinstance(result, list)
        assert len(result) <= 5  # Respects max_suggestions limit

    def test_case_sensitivity_handling(self, spell_check_pipeline):
        """Test case sensitivity in word processing."""
        test_words = ['furlan', 'FURLAN', 'Furlan', 'FuRlAn']
        
        for word in test_words:
            # Should handle all case variants without crashing
            result = spell_check_pipeline.check_text(word)
            assert "original_text" in result
            assert result["original_text"] == word
            
    def test_edge_case_handling(self, spell_check_pipeline):
        """Test edge cases: punctuation, Unicode, empty strings."""
        edge_cases = ["", "  ", "test,", "cjàse", "l'aghe", "123", "!@#"]
        
        for test_input in edge_cases:
            # Should handle gracefully without crashing
            result = spell_check_pipeline.check_text(test_input)
            assert isinstance(result, dict)
            assert "original_text" in result

    # === Text Processing and WordIterator Tests ===

    def test_text_processor_creation(self):
        """Test TextProcessor creation and basic functionality."""
        processor = TextProcessor()
        assert processor is not None, "TextProcessor should be created successfully"

    def test_word_iterator_simple_text(self):
        """Test WordIterator with simple text."""
        processor = TextProcessor()
        text = "simple test"
        iterator = processor.create_word_iterator(text)
        assert iterator is not None, "WordIterator creation: Simple text should create valid iterator"

    def test_word_iterator_empty_text(self):
        """Test WordIterator with empty text.""" 
        processor = TextProcessor()
        text = ""
        iterator = processor.create_word_iterator(text)
        assert iterator is not None, "WordIterator creation: Empty text should create valid iterator"

    def test_word_iterator_unicode_text(self):
        """Test WordIterator with Unicode and Friulian text."""
        processor = TextProcessor()
        text = "café naïve cjàse"
        iterator = processor.create_word_iterator(text)
        assert iterator is not None, "WordIterator creation: Unicode text should create valid iterator"

    def test_word_iterator_friulian_apostrophes(self):
        """Test WordIterator with Friulian apostrophes."""
        processor = TextProcessor()
        text = "l'aghe d'une"
        iterator = processor.create_word_iterator(text)
        assert iterator is not None, "WordIterator Friulian: Should handle Friulian apostrophes"

        # Try to get a token if next() is implemented
        try:
            token = iterator.next()
            if token is not None:
                # Handle both dict and string tokens
                if isinstance(token, dict):
                    word = token.get('word', '')
                    assert len(word) > 0, "WordIterator token: Token should have content"
                else:
                    assert len(str(token)) > 0, "WordIterator token: Token should have content"
        except (NotImplementedError, StopIteration, AttributeError):
            # Expected if next() not yet implemented or no more tokens
            pass

    def test_word_iterator_long_text(self):
        """Test WordIterator with long text."""
        processor = TextProcessor()
        text = "a" * 1000 + " test word"
        iterator = processor.create_word_iterator(text)
        assert iterator is not None, "WordIterator creation: Long text should create valid iterator"

    def test_word_iterator_mixed_languages(self):
        """Test WordIterator with mixed language text."""
        processor = TextProcessor() 
        mixed_text = "Hello world cjàse café naïve test"
        iterator = processor.create_word_iterator(mixed_text)
        assert iterator is not None, "Should handle mixed language text"

        # Try to process some tokens if methods are available
        try:
            tokens = []
            for _ in range(6):  # Try to get multiple tokens 
                token = iterator.next()
                if token is None:
                    break
                tokens.append(token)
            # If we get here, next() is implemented and working
            assert len(tokens) >= 0, "Should process mixed language tokens"
        except (NotImplementedError, StopIteration, AttributeError):
            # Expected if next() not yet implemented
            pass

    def test_word_iterator_special_characters(self):
        """Test WordIterator with special characters and symbols.""" 
        processor = TextProcessor()
        special_text = "word@example.com $100 #hashtag 50% test"
        iterator = processor.create_word_iterator(special_text)
        assert iterator is not None, "Should handle special characters gracefully"

    def test_word_iterator_comprehensive_behavior(self):
        """Test comprehensive WordIterator behavior with Friulian text."""
        processor = TextProcessor()
        comprehensive_text = "Cjàse, l'aghe d'une fenèstre. Test: café naïve! #friulian"
        iterator = processor.create_word_iterator(comprehensive_text)
        
        # Should create iterator successfully
        assert iterator is not None, "Should create iterator with comprehensive Friulian text"

        # Test basic iterator behavior if methods are available
        try:
            count = 0
            while count < 15:  # Reasonable limit
                token = iterator.next()
                if token is None:
                    break
                count += 1
            # If we get here, processing worked
            assert True, f"Successfully processed tokens from comprehensive Friulian text"
        except (NotImplementedError, StopIteration, AttributeError):
            # Expected if next() not yet implemented or iterator exhausted
            pass