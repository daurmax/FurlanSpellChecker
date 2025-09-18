"""Test imports and basic functionality."""

import pytest


def test_imports():
    """Test that all main components can be imported."""
    from furlan_spellchecker import (
        FurlanSpellChecker,
        Dictionary,
        SpellCheckPipeline,
        ProcessedWord,
        ProcessedPunctuation,
        FurlanPhoneticAlgorithm,
        FurlanSpellCheckerConfig,
        version,
    )
    
    assert version is not None
    assert FurlanSpellChecker is not None
    assert Dictionary is not None
    assert SpellCheckPipeline is not None
    assert ProcessedWord is not None
    assert ProcessedPunctuation is not None
    assert FurlanPhoneticAlgorithm is not None
    assert FurlanSpellCheckerConfig is not None


def test_version_format():
    """Test that version follows semantic versioning."""
    from furlan_spellchecker import version
    
    # Should be in format X.Y.Z or X.Y.Z-suffix
    parts = version.split(".")
    assert len(parts) >= 3
    
    # First three parts should be numbers
    for i, part in enumerate(parts[:3]):
        if "-" in part and i == 2:
            # Handle pre-release versions like "1.0.0-alpha1"
            part = part.split("-")[0]
        assert part.isdigit(), f"Version part {part} is not numeric"


def test_core_interfaces_exist():
    """Test that core interfaces are properly defined."""
    from furlan_spellchecker.core.interfaces import (
        ISpellChecker,
        IDictionary,
        IPhoneticAlgorithm,
        ITextProcessor,
    )
    
    # Test that interfaces have expected methods
    assert hasattr(ISpellChecker, "execute_spell_check")
    assert hasattr(ISpellChecker, "get_word_suggestions")
    assert hasattr(IDictionary, "contains_word")
    assert hasattr(IDictionary, "add_word")
    assert hasattr(IPhoneticAlgorithm, "get_phonetic_code")
    assert hasattr(ITextProcessor, "process_text")