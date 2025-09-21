"""
COF Core Functionality Tests - Ported from Perl test_core_functionality.pl

This module tests the core spell checking functionality including:
- Database connectivity and initialization
- SpellChecker word validation and suggestion generation
- Phonetic algorithm validation (phalg_furlan)
- Levenshtein distance calculations
- Case handling and text normalization

Original Perl tests: 46 tests
Python port: Maintaining identical test logic and expected behaviors
"""

from pathlib import Path

import pytest

# COF-equivalent imports - these will need to be implemented
try:
    from furlan_spellchecker.cof.algorithms import levenshtein_distance
    from furlan_spellchecker.cof.data import COFData
    from furlan_spellchecker.cof.phonetic import phalg_furlan
    from furlan_spellchecker.cof.spellchecker import COFSpellChecker
    from furlan_spellchecker.cof.text_utils import first_is_uc, lc_word, sort_suggestions, ucf_word
    from furlan_spellchecker.cof.utils import get_dict_dir
except ImportError:
    # Create placeholder classes during development
    class COFData:
        @classmethod
        def make_default_args(cls, dict_dir):
            raise NotImplementedError("COFData.make_default_args not implemented")

        def __init__(self, *args, **kwargs):
            raise NotImplementedError("COFData.__init__ not implemented")

    class COFSpellChecker:
        def __init__(self, data):
            raise NotImplementedError("COFSpellChecker.__init__ not implemented")

        def check_word(self, word):
            raise NotImplementedError("COFSpellChecker.check_word not implemented")

        def suggest(self, word):
            raise NotImplementedError("COFSpellChecker.suggest not implemented")

    def get_dict_dir():
        raise NotImplementedError("get_dict_dir not implemented")

    def phalg_furlan(word):
        raise NotImplementedError("phalg_furlan not implemented")

    def levenshtein_distance(word1, word2):
        raise NotImplementedError("levenshtein_distance not implemented")

    def ucf_word(word):
        raise NotImplementedError("ucf_word not implemented")

    def lc_word(word):
        raise NotImplementedError("lc_word not implemented")

    def first_is_uc(word):
        raise NotImplementedError("first_is_uc not implemented")

    def sort_suggestions(suggestions):
        raise NotImplementedError("sort_suggestions not implemented")


class TestCOFCoreFunctionality:
    """Test core COF functionality - database, spell checker, and phonetic algorithms."""

    def test_database_directory_access(self):
        """Test 1-5: Check if dictionary directory exists and is accessible."""
        # Test 1: Check if dictionary directory exists and is accessible
        dict_dir = get_dict_dir()
        assert Path(dict_dir).is_dir(), f"Dictionary directory exists: {dict_dir}"

        # Check for required database files
        required_files = ["words.db", "words.rt", "elisions.db", "errors.db", "frec.db"]
        for file_name in required_files:
            full_path = Path(dict_dir) / file_name
            assert full_path.is_file(), f"Required database file exists: {file_name}"
            assert full_path.stat().st_mode & 0o444, f"Database file is readable: {file_name}"

    def test_cof_data_creation(self):
        """Test 6-9: COF::Data object creation and validation."""
        dict_dir = get_dict_dir()

        # Test successful creation using CLI method pattern
        data_args = COFData.make_default_args(dict_dir)
        data = COFData(**data_args)

        assert data is not None, "COF::Data creation successful: no error"
        assert isinstance(data, COFData), "COF::Data object is defined"
        assert hasattr(data, '__class__'), "Data object has correct type"

    def test_spellchecker_creation(self):
        """Test 10-11: SpellChecker object creation and validation."""
        dict_dir = get_dict_dir()
        data_args = COFData.make_default_args(dict_dir)
        data = COFData(**data_args)

        speller = COFSpellChecker(data)
        assert speller is not None, "SpellChecker created successfully"
        assert isinstance(speller, COFSpellChecker), "SpellChecker has correct type"

    def test_word_checking_functionality(self):
        """Test 12-15: Word checking like CLI 'c' command."""
        dict_dir = get_dict_dir()
        data_args = COFData.make_default_args(dict_dir)
        data = COFData(**data_args)
        speller = COFSpellChecker(data)

        # Test known Friulian words
        test_words = ["furlan", "lenghe", "cjase", "aghe", "scuele", "parol", "frut", "femine", "om"]
        valid_words_found = 0

        for word in test_words:
            result = speller.check_word(word)
            if result and result.get('ok'):
                valid_words_found += 1
                assert True, f"Word '{word}' found in dictionary"
                if valid_words_found >= 3:  # Limit output like Perl version
                    break

        assert valid_words_found > 0, "Found valid words in dictionary"

    def test_suggestion_mechanism(self):
        """Test 16-17: Suggestion generation like CLI 's' command."""
        dict_dir = get_dict_dir()
        data_args = COFData.make_default_args(dict_dir)
        data = COFData(**data_args)
        speller = COFSpellChecker(data)

        # Test with misspelled 'furlan'
        suggestions = speller.suggest('furla')
        assert suggestions is not None, "suggest() returns defined result"
        assert isinstance(suggestions, list), "suggest() returns array reference"

    def test_case_sensitivity_handling(self):
        """Test 18-19: Case sensitivity handling."""
        dict_dir = get_dict_dir()
        data_args = COFData.make_default_args(dict_dir)
        data = COFData(**data_args)
        speller = COFSpellChecker(data)

        test_word = 'furlan'

        # Test uppercase word
        upper_result = speller.check_word(test_word.upper())
        assert upper_result is not None, "Uppercase word handled"

        # Test mixed case word
        mixed_result = speller.check_word(test_word.capitalize())
        assert mixed_result is not None, "Mixed case word handled"

    def test_edge_case_handling(self):
        """Test 20-23: Edge case handling for punctuation, Unicode, etc."""
        dict_dir = get_dict_dir()
        data_args = COFData.make_default_args(dict_dir)
        data = COFData(**data_args)
        speller = COFSpellChecker(data)

        # Test punctuation handling
        try:
            speller.check_word("test,")
            assert True, "Punctuation handled gracefully: no error"
        except Exception:
            pytest.fail("Punctuation should be handled gracefully")

        # Test Unicode handling
        try:
            speller.check_word("cjàse")
            assert True, "Unicode handled gracefully: no error"
        except Exception:
            pytest.fail("Unicode should be handled gracefully")

        # Test empty string
        try:
            speller.check_word("")
            assert True, "Empty string handled gracefully"
        except Exception:
            pytest.fail("Empty string should be handled gracefully")

        # Test very long word
        try:
            long_word = "a" * 1000
            speller.check_word(long_word)
            assert True, "Very long word handled gracefully"
        except Exception:
            pytest.fail("Very long word should be handled gracefully")

    def test_phonetic_algorithm_basic(self):
        """Test 24-28: Basic phonetic algorithm functionality."""
        # Test phalg_furlan returns two codes
        codes = phalg_furlan("furlan")
        assert isinstance(codes, tuple | list), "Phonetic: phalg_furlan returns two codes"
        assert len(codes) == 2, "Phonetic: phalg_furlan returns exactly two codes"

        primary_code, secondary_code = codes
        assert len(primary_code) > 0, "Phonetic: first code is non-empty"

        # Test accented/unaccented both work
        accented_codes = phalg_furlan("cjàse")
        unaccented_codes = phalg_furlan("cjase")
        # Both should work without error
        assert isinstance(accented_codes, tuple | list), "Phonetic: accented/unaccented both work"
        assert isinstance(unaccented_codes, tuple | list), "Phonetic: accented/unaccented both work"

        # Test apostrophe words
        apostrophe_codes = phalg_furlan("l'aghe")
        assert isinstance(apostrophe_codes, tuple | list), "Phonetic: apostrophe words handled"

        # Test empty string
        empty_codes = phalg_furlan("")
        assert isinstance(empty_codes, tuple | list), "Phonetic: empty string handled"

    def test_levenshtein_distance(self):
        """Test 29-33: Levenshtein distance calculations."""
        # Test identical words
        distance = levenshtein_distance("furlan", "furlan")
        assert distance == 0, "Levenshtein: identical words have distance 0"

        # Test vowel variants (should have distance 0 in COF implementation)
        distance = levenshtein_distance("cjase", "cjàse")
        assert distance == 0, "Levenshtein: vowel variants have distance 0"

        # Test different consonants
        distance = levenshtein_distance("cjase", "cjale")
        assert distance > 0, "Levenshtein: different consonants have positive distance"

        # Test empty strings
        distance = levenshtein_distance("", "")
        assert distance == 0, "Levenshtein: empty strings have distance 0"

        # Test single char vs empty
        distance = levenshtein_distance("a", "")
        assert distance == 1, "Levenshtein: single char vs empty has distance 1"

    def test_sorting_and_case_functions(self):
        """Test 34-39: Sorting and case handling functions."""
        # Test sort preserves array length
        suggestions = ["furlan", "furle", "furlane"]
        sorted_suggestions = sort_suggestions(suggestions)
        assert len(sorted_suggestions) == len(suggestions), "Sort: preserves array length"
        assert len(sorted_suggestions) > 0, "Sort: returns non-empty array for non-empty input"

        # Test case functions
        result = ucf_word("furlan")
        assert result == "Furlan", "Case: ucf_word capitalizes first letter"

        result = lc_word("FURLAN")
        assert result == "furlan", "Case: lc_word converts to lowercase"

        result = first_is_uc("Furlan")
        assert result is True, "Case: first_is_uc detects uppercase first"

        result = first_is_uc("furlan")
        assert result is False, "Case: first_is_uc detects lowercase first"

    def test_edge_case_performance(self):
        """Test 40-41: Edge cases and performance with large inputs."""
        # Test Levenshtein with very long strings
        long_word1 = "a" * 100
        long_word2 = "b" * 100

        try:
            distance = levenshtein_distance(long_word1, long_word2)
            assert distance > 0, "Edge: Levenshtein handles very long strings"
        except Exception:
            pytest.fail("Levenshtein should handle very long strings")

        # Test phalg_furlan with very long strings
        try:
            codes = phalg_furlan(long_word1)
            assert isinstance(codes, tuple | list), "Edge: phalg_furlan handles very long strings"
        except Exception:
            pytest.fail("phalg_furlan should handle very long strings")


if __name__ == "__main__":
    pytest.main([__file__])
