"""Test configuration for pytest."""

import pytest
from pathlib import Path

from furlan_spellchecker import Dictionary, SpellCheckPipeline


@pytest.fixture
def sample_dictionary():
    """Create a dictionary with sample Friulian words."""
    dictionary = Dictionary()
    
    # Add some basic Friulian words
    words = [
        "cjase", "fradi", "sûr", "mari", "pari", "fi",
        "aghe", "pan", "vin", "lait", "cjar", "pes",
        "biel", "brut", "grant", "piçul", "bon", "catîf",
        "jessi", "vê", "fâ", "lâ", "vignî", "dî", "savê",
    ]
    
    for word in words:
        dictionary.add_word(word)
    
    return dictionary


@pytest.fixture
def spell_check_pipeline(sample_dictionary):
    """Create a spell check pipeline with sample dictionary."""
    return SpellCheckPipeline(dictionary=sample_dictionary)


@pytest.fixture
def test_data_dir():
    """Get the test data directory path."""
    return Path(__file__).parent / "data"


@pytest.fixture
def sample_friulian_text():
    """Sample Friulian text for testing."""
    return "Cheste e je une frâs in furlan cun cualchi peraule."