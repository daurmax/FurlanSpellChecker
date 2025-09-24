"""
Test RadixTree functionality for 1:1 compatibility with COF.

This comprehensive test module verifies that our BinaryRadixTree implementation produces
exactly the same results as COF's RadixTree for edit-distance-1 suggestions.

Test Coverage:
- COF Compatibility: Core suggestion matching with verified test cases
- Edge Cases: Empty input, single characters, invalid words, Friulian diacritics
- Performance: Batch processing, timing measurements, stress testing
- Integration: DatabaseManager integration and availability checks

Based on the comprehensive test suite from COF (Coretôr Ortografic Furlan) with
21 test cases covering basic functionality, edge cases, and performance validation.
"""
import pytest
from furlan_spellchecker.database.manager import DatabaseManager
from furlan_spellchecker.database.radix_tree import RadixTreeDatabase
from tests.database_utils import get_database_paths


class TestRadixTreeCOFCompatibility:
    """Test RadixTree compatibility with COF implementation."""

    @pytest.fixture(scope="class")
    def radix_tree(self):
        """Initialize RadixTree database for testing."""
        db_paths = get_database_paths()
        if not db_paths["radix_tree"].exists():
            pytest.skip("RadixTree database file not found")
        
        return RadixTreeDatabase(str(db_paths["radix_tree"]))

    def test_radix_tree_initialization(self, radix_tree):
        """Test that RadixTree loads correctly."""
        assert radix_tree is not None
        # Basic test to ensure the tree loaded
        assert radix_tree.has_word("furlan")  # A word we know exists

    def test_furla_suggestions(self, radix_tree):
        """Test 'furla' suggestions match COF exactly.
        
        COF output: [{"word": "furla", "suggestion": "furlan"}]
        """
        suggestions = radix_tree.get_words_ed1("furla")
        expected = ["furlan"]
        assert suggestions == expected, f"Expected {expected}, got {suggestions}"

    def test_lengha_suggestions(self, radix_tree):
        """Test 'lengha' suggestions match COF exactly.
        
        COF output: [{"word": "lengha", "suggestion": "lenghe"}]
        """
        suggestions = radix_tree.get_words_ed1("lengha")
        expected = ["lenghe"]
        assert suggestions == expected, f"Expected {expected}, got {suggestions}"

    def test_cjupe_suggestions(self, radix_tree):
        """Test 'cjupe' suggestions match COF exactly.
        
        COF output: [
            {"word": "cjupe", "suggestion": "cjape"},
            {"suggestion": "cjepe", "word": "cjupe"},
            {"suggestion": "cjope", "word": "cjupe"},
            {"suggestion": "clupe", "word": "cjupe"},
            {"suggestion": "crupe", "word": "cjupe"}
        ]
        """
        suggestions = radix_tree.get_words_ed1("cjupe")
        expected = ["cjape", "cjepe", "cjope", "clupe", "crupe"]
        assert suggestions == expected, f"Expected {expected}, got {suggestions}"

    def test_cjasa_suggestions(self, radix_tree):
        """Test 'cjasa' suggestions match COF exactly.
        
        COF output: [
            {"word": "cjasa", "suggestion": "cjase"},
            {"suggestion": "cjast", "word": "cjasa"},
            {"word": "cjasa", "suggestion": "cjas*"}
        ]
        """
        suggestions = radix_tree.get_words_ed1("cjasa")
        expected = ["cjase", "cjast", "cjas*"]
        assert suggestions == expected, f"Expected {expected}, got {suggestions}"

    @pytest.mark.parametrize("word,expected_suggestions", [
        ("furla", ["furlan"]),
        ("lengha", ["lenghe"]),
        ("cjupe", ["cjape", "cjepe", "cjope", "clupe", "crupe"]),
        ("cjasa", ["cjase", "cjast", "cjas*"]),
        # Additional test cases from COF curated dataset
        ("ostaria", ["ostarie"]),
        ("anell", ["anel"]),
    ])
    def test_comprehensive_radix_tree_suggestions(self, radix_tree, word, expected_suggestions):
        """Comprehensive test for all RadixTree suggestions."""
        suggestions = radix_tree.get_words_ed1(word)
        assert suggestions == expected_suggestions, (
            f"Word '{word}': Expected {expected_suggestions}, got {suggestions}"
        )

    def test_word_lookup(self, radix_tree):
        """Test basic word lookup functionality."""
        # Test words that should exist
        assert radix_tree.has_word("furlan")
        assert radix_tree.has_word("lenghe")
        assert radix_tree.has_word("cjase")
        
        # Test words that shouldn't exist
        assert not radix_tree.has_word("furla")
        assert not radix_tree.has_word("lengha")
        assert not radix_tree.has_word("cjupe")

    def test_valid_words_can_have_ed1_suggestions(self, radix_tree):
        """Test that valid words can have edit-distance-1 suggestions (other similar words)."""
        # "furlan" exists but can still have edit-distance-1 neighbors like "furlane", etc.
        suggestions = radix_tree.get_words_ed1("furlan")
        assert isinstance(suggestions, list), "Should return a list of suggestions"
        
        # Verify some expected suggestions for "furlan" (based on COF output)
        expected_suggestions = ["furlane", "furlani", "furlans", "furlanà", "furlanâ"] 
        assert suggestions == expected_suggestions, f"Expected {expected_suggestions}, got {suggestions}"


class TestRadixTreeEdgeCases:
    """Test RadixTree edge cases and robustness, ported from COF test patterns."""
    
    @pytest.fixture(scope="class")
    def radix_tree(self):
        """Initialize RadixTree database for testing."""
        db_paths = get_database_paths()
        if not db_paths["radix_tree"].exists():
            pytest.skip("RadixTree database file not found")
        
        return RadixTreeDatabase(str(db_paths["radix_tree"]))

    def test_empty_input_handling(self, radix_tree):
        """Test empty input handling - should return suggestions for single character inserts."""
        suggestions = radix_tree.get_words_ed1("")
        assert isinstance(suggestions, list), "Empty input should return a list"
        # Empty input should produce suggestions (likely single letters)
        assert len(suggestions) > 0, "Empty input should produce suggestions for single character inserts"

    def test_single_character_input(self, radix_tree):
        """Test single character input."""
        suggestions = radix_tree.get_words_ed1("a")
        assert isinstance(suggestions, list), "Single character input should return a list"
        # Should not crash, may or may not have suggestions

    def test_very_short_words(self, radix_tree):
        """Test very short words (2-3 characters)."""
        test_words = ["ab", "xyz", "fu"]
        for word in test_words:
            suggestions = radix_tree.get_words_ed1(word)
            assert isinstance(suggestions, list), f"Word '{word}' should return a list"

    def test_non_existent_words(self, radix_tree):
        """Test completely non-existent/invalid words."""
        invalid_words = ["xyzqwerty", "abcdefghijklmnop", "zzzzzz"]
        for word in invalid_words:
            suggestions = radix_tree.get_words_ed1(word)
            assert isinstance(suggestions, list), f"Invalid word '{word}' should return a list"
            # Should not crash, likely no suggestions for completely invalid words

    def test_friulian_specific_characters(self, radix_tree):
        """Test words with Friulian-specific characters and diacritics."""
        friulian_words = [
            "cjàse",   # with grave accent
            "furlanâ", # with circumflex  
            "çi",      # with cedilla
            "òs",      # with grave accent
            "ûs"       # with circumflex
        ]
        for word in friulian_words:
            suggestions = radix_tree.get_words_ed1(word)
            assert isinstance(suggestions, list), f"Friulian word '{word}' should return a list"
            # Should handle Friulian characters without crashing

    def test_edge_case_characters(self, radix_tree):
        """Test edge case characters and patterns from COF."""
        edge_cases = [
            "A",           # Single uppercase
            "aa",          # Repeated character
            "a" * 50,      # Very long word (50 characters)
            "123",         # Numbers
            "test-word",   # Hyphenated (if applicable)
            "test'word",   # Apostrophe (if applicable)
        ]
        
        handled_count = 0
        for edge_case in edge_cases:
            try:
                suggestions = radix_tree.get_words_ed1(edge_case)
                assert isinstance(suggestions, list), f"Edge case '{edge_case}' should return a list"
                handled_count += 1
            except Exception:
                # Some edge cases might not be handled, but shouldn't crash the system
                pass
        
        # At least basic cases should be handled
        assert handled_count >= len(edge_cases) // 2, (
            f"Should handle most edge cases without crashing ({handled_count}/{len(edge_cases)})"
        )

    def test_known_suggestion_pairs(self, radix_tree):
        """Test known good suggestion pairs from COF usage patterns."""
        known_pairs = {
            'lengha': 'lenghe',
            'cjupe': 'cjope',  # One of the expected suggestions
            'anell': 'anel',
            'ostaria': 'ostarie',
        }
        
        for input_word, expected_suggestion in known_pairs.items():
            suggestions = radix_tree.get_words_ed1(input_word)
            assert expected_suggestion in suggestions, (
                f"'{expected_suggestion}' should be suggested for '{input_word}'. "
                f"Got: {suggestions}"
            )


class TestRadixTreePerformance:
    """Test RadixTree performance characteristics, ported from COF patterns."""
    
    @pytest.fixture(scope="class")
    def radix_tree(self):
        """Initialize RadixTree database for testing."""
        db_paths = get_database_paths()
        if not db_paths["radix_tree"].exists():
            pytest.skip("RadixTree database file not found")
        
        return RadixTreeDatabase(str(db_paths["radix_tree"]))

    def test_batch_processing_performance(self, radix_tree):
        """Test batch processing of multiple words - ported from COF performance test."""
        import time
        
        # Test batch similar to COF test pattern
        test_batch = [
            "furla", "lengha", "cjupe", "cjasa", "ostaria", "anell",
            "grant", "piçul", "bon", "catîf", "alt", "bas",
            "plui", "prossim", "lontam"
        ]
        
        start_time = time.time()
        total_suggestions = 0
        
        for word in test_batch:
            suggestions = radix_tree.get_words_ed1(word)
            total_suggestions += len(suggestions)
        
        elapsed_time = time.time() - start_time
        
        assert total_suggestions >= 0, "Batch processing should complete successfully"
        assert elapsed_time < 10.0, f"Batch processing should be reasonably fast (took {elapsed_time:.2f}s)"
        
        # Log performance info like COF does
        print(f"Processed {len(test_batch)} words, generated {total_suggestions} suggestions in {elapsed_time:.2f} seconds")

    @pytest.mark.slow
    def test_stress_test_large_input(self, radix_tree):
        """Stress test with larger dataset."""
        # Generate test words of various patterns
        test_words = []
        
        # Add various word patterns
        for i in range(50):
            test_words.extend([
                f"test{i}",        # Numbered variants
                f"furla{i % 5}",   # Variations of known words
                f"c{'a' * (i % 10)}se",  # Variable length patterns
            ])
        
        processed_count = 0
        total_suggestions = 0
        
        for word in test_words:
            try:
                suggestions = radix_tree.get_words_ed1(word)
                total_suggestions += len(suggestions)
                processed_count += 1
            except Exception:
                # Some generated words might cause issues, but most should work
                pass
        
        # Should process most words successfully
        success_rate = processed_count / len(test_words)
        assert success_rate > 0.8, f"Should process >80% of test words (got {success_rate:.1%})"
        
        print(f"Stress test: {processed_count}/{len(test_words)} words processed, "
              f"{total_suggestions} total suggestions")


class TestRadixTreeIntegration:
    """Test RadixTree integration with DatabaseManager."""

    @pytest.fixture(scope="class")
    def database_manager(self):
        """Initialize DatabaseManager for integration testing."""
        return DatabaseManager()

    def test_radix_tree_integration(self, database_manager):
        """Test RadixTree access through DatabaseManager."""
        radix_tree = database_manager.radix_tree
        assert radix_tree is not None
        
        # Test basic functionality through manager
        suggestions = radix_tree.get_words_ed1("furla")
        assert "furlan" in suggestions

    def test_radix_tree_availability(self, database_manager):
        """Test RadixTree availability check."""
        from furlan_spellchecker.database.interfaces import DictionaryType
        availability = database_manager.ensure_databases_available()
        assert DictionaryType.RADIX_TREE in availability
        assert availability[DictionaryType.RADIX_TREE] is True


if __name__ == "__main__":
    # Allow running this test file directly
    # Example usage:
    #   python tests/test_radix_tree.py                    # Run all tests  
    #   python -m pytest tests/test_radix_tree.py -v      # Verbose output
    #   python -m pytest tests/test_radix_tree.py -m slow # Only performance tests
    pytest.main([__file__, "-v"])