"""Test SpellCheckPipeline functionality."""

import pytest
from furlan_spellchecker.services import SpellCheckPipeline
from furlan_spellchecker.dictionary import Dictionary


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