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
        """Test comprehensive phonetic algorithm - exact compatibility with COF::DataCompat Perl implementation"""
        
        # UNIFIED test cases with CORRECT results from COF::DataCompat Perl implementation
        # These match exactly the test_phonetic_algorithm.pl test suite
        test_cases = [
            # Existing regression tests from COF
            ("furlan", "fYl65", "fYl65"),
            ("cjase", "A6A7", "c76E7"),
            ("lenghe", "X7", "X7"),
            ("scuele", "AA87l7", "Ec87l7"),
            ("mandrie", "5659r77", "5659r77"),
            ("barcon", "b2A85", "b2c85"),
            ("nade", "5697", "5697"),
            ("nuie", "587", "587"),
            ("specifiche", "Ap7Af7A7", "Ep7c7f7c7"),
            
            # From test_phonetic_perl.pl (consolidated duplications)
            ("çavatis", "A6v6AA", "ç6v697E"),
            ("cjatâ", "A696", "c7696"),
            ("diretamentri", "I7r79O", "Er79O"),
            ("sdrumâ", "A9r856", "E9r856"),
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
            
            # Single character tests
            ("a", "6", "6"),
            ("e", "7", "7"),
            ("i", "7", "7"),
            ("o", "8", "8"),
            ("u", "8", "8"),
            
            # Feature tests with ç in different positions
            ("çarve", "A2v7", "ç2v7"),
            ("braç", "br6A", "br6ç"),
            ("piçul", "p7A8l", "p7ç8l"),
            
            # Words with gj/gi patterns
            ("gjat", "g769", "E69"),
            ("bragje", "br6g77", "br6E7"),
            ("gjaldi", "g76l97", "E6l97"),
            
            # Words with cj patterns
            ("cjalç", "A6lA", "c76lç"),
            ("ancje", "65A7", "65c77"),
            ("vecje", "v7A7", "v7c77"),
            
            # Consonant sequences
            ("struc", "A9r8A", "E9r80"),
            ("spès", "Ap7A", "Ep7E"),
            ("blanc", "bl65A", "bl650"),
            ("spirt", "Ap7r9", "Ep7r9"),
            
            # Words with h
            ("ghe", "g7", "E7"),
            ("ghi", "g7", "E"),
            ("chê", "A", "c7"),
            ("schei", "AA7", "Ec7"),
            
            # Words with apostrophes
            ("l'aghe", "l6g7", "l6E7"),
            ("d'àcue", "I6A87", "I6c87"),
            ("n'omp", "5853", "5853"),
            
            # Accented vowels
            ("gòs", "g8A", "E8E"),
            ("pôc", "p8A", "p80"),
            ("crês", "Ar7A", "cr7E"),
            ("fûc", "f8A", "f80"),
            ("çûç", "A8A", "ç8ç"),
            
            # Special combinations
            ("sdrume", "A9r857", "E9r857"),
            ("strucâ", "A9r8A6", "E9r8c6"),
            ("blave", "bl6v7", "bl6v7"),
            
            # Double consonants
            ("mame", "5657", "5657"),
            ("sasse", "A6A7", "E6E7"),
            ("puarte", "pY97", "pY97"),
            
            # Special endings
            ("prins", "pr1", "pr1"),
            ("gjenç", "g775A", "E75ç"),
            ("mont", "5859", "5859"),
            ("viert", "v729", "v729"),
            
            # Short words
            ("me", "57", "57"),
            ("no", "58", "58"),
            ("sì", "A", "E7"),
            ("là", "l6", "l6"),
            
            # Long words
            ("diretament", "I7r7965759", "Er7965759"),
            ("incjamarade", "75A652697", "75c7652697"),
            ("straçonarie", "A9r6A85277", "E9r6ç85277"),
            
            # Additional test cases from legacy Friulian word files
            # Selected for diverse phonetic patterns and comprehensive coverage
            ("mote", "5897", "5897"),
            ("nobèl", "58b7l", "58b7l"),
            ("nissun", "57A85", "57E85"),
            ("babèl", "b6b7l", "b6b7l"),
            ("bertòs", "b298A", "b298E"),
            ("cjandùs", "A6598A", "c76598E"),
            ("cnît", "A579", "c579"),
            ("corfù", "AYf8", "cYf8"),
            ("epicûr", "7p7AY", "7p7cY"),
            ("maiôr", "56Y", "56Y"),
            ("gjalde", "g76l97", "E6l97"),
            ("gjenar", "g7752", "E752"),
            ("gjessis", "g77AA", "E7E7E"),
            ("gjetâ", "g7796", "E796"),
            ("gjoc", "g78A", "E80"),
            ("çucule", "A8A8l7", "ç8c8l7"),
            ("çuple", "A8pl7", "ç8pl7"),
            ("çurì", "AY7", "çY7"),
            ("çuse", "A8A7", "ç8E7"),
            ("çusse", "A8A7", "ç8E7"),
            ("nîf", "574", "574"),
            ("nîl", "57l", "57l"),
            ("nît", "579", "579"),
            ("mûf", "584", "584"),
            ("mûr", "5Y", "5Y"),
            ("mûs", "58A", "58E"),
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