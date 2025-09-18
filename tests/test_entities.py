"""Test ProcessedWord and ProcessedPunctuation entities."""

import pytest
from furlan_spellchecker.entities import ProcessedWord, ProcessedPunctuation
from furlan_spellchecker.core.types import WordType


class TestProcessedWord:
    """Test ProcessedWord functionality."""

    def test_initialization(self):
        """Test ProcessedWord initialization."""
        word = ProcessedWord("cjase")
        
        assert word.original == "cjase"
        assert word.current == "cjase"
        assert word.checked is False
        assert word.correct is False

    def test_current_modification(self):
        """Test modifying current word."""
        word = ProcessedWord("original")
        word.current = "modified"
        
        assert word.original == "original"
        assert word.current == "modified"

    def test_case_detection(self):
        """Test case type detection."""
        # Test lowercase
        word_lower = ProcessedWord("cjase")
        assert word_lower.case == WordType.LOWERCASE
        
        # Test uppercase  
        word_upper = ProcessedWord("CJASE")
        assert word_upper.case == WordType.UPPERCASE
        
        # Test first letter uppercase
        word_title = ProcessedWord("Cjase")
        assert word_title.case == WordType.FIRST_LETTER_UPPERCASE
        
        # Test mixed case
        word_mixed = ProcessedWord("CjAsE")
        assert word_mixed.case == WordType.MIXED_CASE

    def test_checked_property(self):
        """Test checked property."""
        word = ProcessedWord("test")
        
        assert word.checked is False
        word.checked = True
        assert word.checked is True

    def test_correct_property(self):
        """Test correct property."""
        word = ProcessedWord("test")
        
        assert word.correct is False
        word.correct = True
        assert word.correct is True

    def test_string_representation(self):
        """Test string representations."""
        word = ProcessedWord("test")
        word.correct = True
        
        str_repr = str(word)
        assert "ProcessedWord" in str_repr
        assert "'test'" in str_repr
        assert "correct=True" in str_repr
        
        repr_str = repr(word)
        assert "ProcessedWord" in repr_str
        assert "original='test'" in repr_str
        assert "current='test'" in repr_str


class TestProcessedPunctuation:
    """Test ProcessedPunctuation functionality."""

    def test_initialization(self):
        """Test ProcessedPunctuation initialization."""
        punct = ProcessedPunctuation(".")
        
        assert punct.original == "."
        assert punct.current == "."

    def test_current_modification(self):
        """Test modifying current punctuation."""
        punct = ProcessedPunctuation(".")
        punct.current = "!"
        
        assert punct.original == "."
        assert punct.current == "!"

    def test_string_representation(self):
        """Test string representations."""
        punct = ProcessedPunctuation(",")
        
        str_repr = str(punct)
        assert "ProcessedPunctuation" in str_repr
        assert "','" in str_repr
        
        repr_str = repr(punct)
        assert "ProcessedPunctuation" in repr_str
        assert "original=','" in repr_str
        assert "current=','" in repr_str