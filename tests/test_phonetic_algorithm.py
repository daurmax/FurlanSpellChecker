"""Test suite for Friulian phonetic algorithm - exact compatibility with COF Perl implementation"""

import pytest
from furlan_spellchecker.phonetic import FurlanPhoneticAlgorithm


class TestFurlanPhoneticAlgorithm:
    """Test the Friulian phonetic algorithm for exact compatibility with COF Perl implementation"""

    @pytest.fixture
    def algorithm(self):
        """Create a phonetic algorithm instance"""
        return FurlanPhoneticAlgorithm()

    def test_core_phonetic_hashes(self, algorithm):
        """Test core words from COF - these results must match exactly"""
        
        # COMPREHENSIVE test cases with CORRECT results from COF Perl implementation
        test_cases = [
            # Core test words with verified Perl results from COF
            ("furlan", "fYl65", "fYl65"),
            ("cjase", "A6A7", "c76E7"), 
            ("çavatis", "A6v6AA", "ç6v697E"),
            ("cjatâ", "A696", "c7696"),
            ("diretamentri", "I7r79O", "Er79O"),
            ("sdrumâ", "A9r856", "E9r856"),
            ("lenghe", "X7", "X7"),
            ("aghe", "6g7", "6E7"),
            ("çucjar", "A8A2", "ç8c72"),
            ("çai", "A6", "ç6"),
            ("cafè", "A6f7", "c6f7"),
            ("cjanditi", "A6597A", "c765E97"),
            ("gjobat", "g78b69", "E8b69"),
            ("glama", "gl656", "El656"),
            ("gnûf", "g584", "E584"),
            ("savetât", "A6v7969", "E6v7969"),
            ("parol", "p28l", "p28l"),
            ("frut", "fr89", "fr89"),
            ("femine", "f75757", "f75757"),
            
            # Additional verified words
            ("arbul", "2b8l", "2b8l"),
            ("blanc", "bl65A", "bl650"),
            ("cjan", "A65", "c765"),
            ("duse", "I8A7", "I8E7"),
            ("erbe", "2b7", "2b7"),
            ("flôr", "flY", "flY"),
            ("gjat", "g769", "E69"),
            ("housî", "8A", "8E7"),
            ("insom", "75A85", "75E85"),
            ("jadis", "7697A", "76EE"),
            ("kwam", "A65", "k65"),
            ("lenç", "l75A", "l75ç"),
            ("muse", "58A7", "58E7"),
            ("nuje", "5877", "5877"),
            
            # Single character tests from verified Perl results
            ("a", "6", "6"),
            ("e", "7", "7"),
            ("i", "7", "7"),
            ("o", "8", "8"),
            ("u", "8", "8"),
            ("c", "A", "0"),
            ("g", "g", "0"),
            ("s", "A", "E"),
            ("t", "H", "H"),
            ("d", "I", "I"),
            
            # Additional words from expanded dataset
            ("scuele", "AA87l7", "Ec87l7"),
            ("erbis", "2b7A", "2b7E"),
            ("gnovis", "g58v7A", "E58v7E"),
            ("fameis", "f657A", "f657E"),
            ("storiis", "A9Y7A", "E9Y7E"),
            ("vignêt", "v7g579", "v7E579"),
            ("fûc", "f8A", "f80"),
            ("monts", "585A", "585E"),
            ("vieli", "v77l7", "v77l7"),
            ("gnove", "g58v7", "E58v7"),
            ("cont", "A859", "c859"),
            ("res", "r7A", "r7E"),
            ("lûs", "l8A", "l8E"),
            ("vôs", "v8A", "v8E"),
            ("timp", "A53", "H753"),
            ("gent", "g759", "E759"),
        ]
        
        for word, expected_first, expected_second in test_cases:
            first, second = algorithm.get_phonetic_hashes_by_word(word)
            assert first == expected_first, f"Word '{word}': expected first hash '{expected_first}', got '{first}'"
            assert second == expected_second, f"Word '{word}': expected second hash '{expected_second}', got '{second}'"

    def test_accent_normalization(self, algorithm):
        """Test that accented and unaccented versions produce same hashes"""
        
        # Test cases where accented/unaccented should produce similar but not identical results
        # NOTE: In the real algorithm, accented letters are normalized first, so results may differ
        accent_pairs = [
            # These test that the algorithm handles accented characters consistently
            ("cjatâ", "cjata"),  # â -> a normalization
        ]
        
        for accented, unaccented in accent_pairs:
            acc_first, acc_second = algorithm.get_phonetic_hashes_by_word(accented)
            un_first, un_second = algorithm.get_phonetic_hashes_by_word(unaccented)
            
            assert acc_first == un_first, f"Accented '{accented}' vs unaccented '{unaccented}': first hashes differ"
            assert acc_second == un_second, f"Accented '{accented}' vs unaccented '{unaccented}': second hashes differ"

    def test_consistency(self, algorithm):
        """Test that the algorithm produces consistent results"""
        
        test_words = ["cjase", "furlan", "lenghe", "aghe", "parol"]
        
        for word in test_words:
            # Multiple calls should return identical results
            first1, second1 = algorithm.get_phonetic_hashes_by_word(word)
            first2, second2 = algorithm.get_phonetic_hashes_by_word(word)
            
            assert first1 == first2, f"Inconsistent first hash for '{word}'"
            assert second1 == second2, f"Inconsistent second hash for '{word}'"

    def test_empty_and_edge_cases(self, algorithm):
        """Test edge cases like empty strings and None inputs"""
        
        # Empty string
        first, second = algorithm.get_phonetic_hashes_by_word("")
        assert first == "", "Empty string should return empty first hash"
        assert second == "", "Empty string should return empty second hash"
        
        # None input
        first, second = algorithm.get_phonetic_hashes_by_word(None)
        assert first == "", "None input should return empty first hash"
        assert second == "", "None input should return empty second hash"

    def test_backwards_compatibility(self, algorithm):
        """Test backwards compatibility method"""
        
        # get_phonetic_code should return first hash only
        first_only = algorithm.get_phonetic_code("cjase")
        first, _ = algorithm.get_phonetic_hashes_by_word("cjase")
        
        assert first_only == first, "get_phonetic_code should return first hash"

    def test_phonetic_similarity(self, algorithm):
        """Test phonetic similarity detection"""
        
        # Same word should be similar
        assert algorithm.are_phonetically_similar("cjase", "cjase")
        
        # Different words with same hashes should be similar
        # (We'd need to find actual examples from the dictionary)
        
        # Completely different words should not be similar
        word1_first, word1_second = algorithm.get_phonetic_hashes_by_word("cjase")
        word2_first, word2_second = algorithm.get_phonetic_hashes_by_word("parol")
        
        # If none of the hashes match, they should not be similar
        if (word1_first != word2_first and word1_first != word2_second and
            word1_second != word2_first and word1_second != word2_second):
            assert not algorithm.are_phonetically_similar("cjase", "parol")

    def test_levenshtein_friulian(self, algorithm):
        """Test Friulian-aware Levenshtein distance"""
        
        # Identical words
        assert algorithm.levenshtein("cjase", "cjase") == 0
        
        # Friulian vowel equivalences should have distance 0
        assert algorithm.levenshtein("à", "a") == 0
        assert algorithm.levenshtein("è", "e") == 0
        assert algorithm.levenshtein("café", "cafe") == 0
        
        # Different letters should have distance > 0
        assert algorithm.levenshtein("a", "b") == 1
        assert algorithm.levenshtein("cjase", "gjase") == 1
        
        # Empty strings
        assert algorithm.levenshtein("", "") == 0
        assert algorithm.levenshtein("a", "") == 1
        assert algorithm.levenshtein("", "a") == 1

    def test_friulian_sorting(self, algorithm):
        """Test Friulian-specific sorting"""
        
        # Basic sorting test
        words = ["zeta", "beta", "alfa", "gamma"]
        sorted_words = algorithm.sort_friulian(words)
        
        # Should preserve all words
        assert len(sorted_words) == len(words)
        assert set(sorted_words) == set(words)
        
        # Should be in alphabetical order (basic check)
        assert sorted_words[0] == "alfa"  # alfa should come first
        
        # Test with Friulian characters
        friulian_words = ["çà", "ca", "cè"]
        sorted_friulian = algorithm.sort_friulian(friulian_words)
        assert len(sorted_friulian) == len(friulian_words)

    def test_error_handling(self, algorithm):
        """Test error handling for invalid inputs"""
        
        # None input should be handled gracefully
        first, second = algorithm.get_phonetic_hashes_by_word(None)
        assert first == ""
        assert second == ""
        
        # Very long strings should not crash
        long_word = "a" * 1000
        first, second = algorithm.get_phonetic_hashes_by_word(long_word)
        assert isinstance(first, str)
        assert isinstance(second, str)