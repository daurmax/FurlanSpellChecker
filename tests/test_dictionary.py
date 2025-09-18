"""Test Dictionary functionality."""

import pytest
from pathlib import Path
from furlan_spellchecker.dictionary import Dictionary
from furlan_spellchecker.core.exceptions import DictionaryNotFoundError, DictionaryLoadError


class TestDictionary:
    """Test Dictionary functionality."""

    def test_initialization(self):
        """Test dictionary initialization."""
        dictionary = Dictionary()
        assert dictionary.word_count == 0
        assert dictionary.is_loaded is False

    def test_add_word(self):
        """Test adding words to dictionary."""
        dictionary = Dictionary()
        
        # Add valid word
        result = dictionary.add_word("cjase")
        assert result is True
        assert dictionary.contains_word("cjase")
        assert dictionary.word_count == 1

    def test_add_word_case_insensitive(self):
        """Test that dictionary is case insensitive."""
        dictionary = Dictionary()
        
        dictionary.add_word("Cjase")
        assert dictionary.contains_word("cjase")
        assert dictionary.contains_word("CJASE")
        assert dictionary.contains_word("CjAsE")

    def test_add_invalid_words(self):
        """Test adding invalid words."""
        dictionary = Dictionary()
        
        # Empty string
        result = dictionary.add_word("")
        assert result is False
        assert dictionary.word_count == 0
        
        # Whitespace only
        result = dictionary.add_word("   ")
        assert result is False
        assert dictionary.word_count == 0
        
        # None (should not crash)
        result = dictionary.add_word(None)
        assert result is False
        assert dictionary.word_count == 0

    def test_contains_word(self):
        """Test word lookup."""
        dictionary = Dictionary()
        
        # Word not in dictionary
        assert dictionary.contains_word("nonexistent") is False
        
        # Add and check word
        dictionary.add_word("furlan")
        assert dictionary.contains_word("furlan") is True
        assert dictionary.contains_word("FURLAN") is True  # Case insensitive

    def test_basic_suggestions(self):
        """Test basic suggestion functionality."""
        dictionary = Dictionary()
        
        # Add some words
        words = ["cjase", "cjases", "cjasis", "casa", "case"]
        for word in words:
            dictionary.add_word(word)
        
        # Get suggestions for misspelled word
        suggestions = dictionary.get_suggestions("cjasa", max_suggestions=3)
        
        # Should get some suggestions (exact algorithm may vary)
        assert isinstance(suggestions, list)
        assert len(suggestions) <= 3

    def test_load_dictionary_file_not_found(self):
        """Test loading non-existent dictionary file."""
        dictionary = Dictionary()
        
        with pytest.raises(DictionaryNotFoundError):
            dictionary.load_dictionary("nonexistent_file.txt")

    def test_load_dictionary_success(self, tmp_path):
        """Test successfully loading dictionary from file."""
        dictionary = Dictionary()
        
        # Create temporary dictionary file
        dict_file = tmp_path / "test_dict.txt"
        dict_content = """# Test dictionary
cjase
fradi
sûr
mari
# This is a comment
pari
"""
        dict_file.write_text(dict_content, encoding="utf-8")
        
        # Load dictionary
        dictionary.load_dictionary(str(dict_file))
        
        assert dictionary.is_loaded is True
        assert dictionary.word_count == 5  # Should ignore comments and empty lines
        assert dictionary.contains_word("cjase")
        assert dictionary.contains_word("fradi")
        assert dictionary.contains_word("mari")

    def test_word_count_property(self):
        """Test word count property."""
        dictionary = Dictionary()
        
        assert dictionary.word_count == 0
        
        dictionary.add_word("first")
        assert dictionary.word_count == 1
        
        dictionary.add_word("second")
        assert dictionary.word_count == 2
        
        # Adding same word shouldn't increase count
        dictionary.add_word("first")
        assert dictionary.word_count == 2