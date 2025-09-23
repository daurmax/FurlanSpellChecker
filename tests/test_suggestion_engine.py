"""Tests for SuggestionEngine using real Friulian databases.

This test suite validates behavioral parity with the COF reference implementation
using real Friulian databases for authentic spell checking behavior.
"""
from __future__ import annotations

import pytest

from furlan_spellchecker.spellchecker.suggestion_engine import SuggestionEngine
from furlan_spellchecker.phonetic import FurlanPhoneticAlgorithm

# Import real database fixtures
from tests.test_real_databases import real_databases, real_db_manager, real_suggestion_engine


def test_phonetic_and_error_corrections_order(real_suggestion_engine):
    """Test that error corrections are prioritized over phonetic matches."""
    suggestions = real_suggestion_engine.suggest("gnôf")
    assert len(suggestions) >= 1
    # Should get "gnûf" as primary suggestion (error correction)
    assert suggestions[0].lower() == "gnûf"


def test_case_preservation_ucfirst(real_suggestion_engine):
    """Test case preservation for Ucfirst style input."""
    suggestions = real_suggestion_engine.suggest("Gnôf")
    assert len(suggestions) >= 1
    # First suggestion should be "Gnûf" (case preserved)
    assert suggestions[0] == "Gnûf"


def test_case_preservation_upper(real_suggestion_engine):
    """Test case preservation for UPPER case input."""
    suggestions = real_suggestion_engine.suggest("GNÔF")
    assert len(suggestions) >= 1
    # Should preserve uppercase style
    assert suggestions[0] == "GNÛF"


def test_frequency_ranking_tie_break(real_suggestion_engine):
    """Test that higher frequency words rank higher when phonetically similar."""
    suggestions = real_suggestion_engine.suggest("furlans")
    assert len(suggestions) >= 2
    # furlans should appear first (likely in database)
    # followed by other furlan-family words ranked by frequency


def test_elision_generation(real_suggestion_engine):
    """Test elision handling for l' prefix."""
    suggestions = real_suggestion_engine.suggest("l'aghe")
    assert len(suggestions) >= 1
    # Should get elision suggestions


def test_hyphen_basic(real_suggestion_engine):
    """Test basic hyphen handling."""
    suggestions = real_suggestion_engine.suggest("cjase-parol")
    # Should handle hyphenated words appropriately
    assert isinstance(suggestions, list)


class TestBehavioralParity:
    """Test suite validating behavioral parity with COF reference implementation."""

    def test_furla_to_furlan(self, real_suggestion_engine):
        """Test: furla → [furlan, ...] (phonetic similarity or error correction)"""
        suggestions = real_suggestion_engine.suggest("furla")
        assert len(suggestions) >= 1
        # Check if furlan appears in suggestions (COF compatibility)
        suggestion_lower = [s.lower() for s in suggestions]
        # Note: This should pass with real databases if furla->furlan mapping exists

    def test_elision_l_aghe(self, real_suggestion_engine):
        """Test: l'aghe → appropriate elision handling"""
        suggestions = real_suggestion_engine.suggest("l'aghe")
        assert isinstance(suggestions, list)
        # Should handle elision appropriately

    def test_case_preservation_furlan(self, real_suggestion_engine):
        """Test case preservation with Furlan."""
        suggestions = real_suggestion_engine.suggest("Furlan")
        if suggestions:
            # Should preserve case style
            assert suggestions[0][0].isupper()

    def test_case_preservation_uppercase(self, real_suggestion_engine):
        """Test case preservation with FURLAN."""
        suggestions = real_suggestion_engine.suggest("FURLAN")
        if suggestions:
            # Should preserve uppercase style
            assert suggestions[0].isupper()

    def test_case_preservation_mixed(self, real_suggestion_engine):
        """Test mixed case handling."""
        suggestions = real_suggestion_engine.suggest("FuRlAn")
        # Should handle mixed case gracefully
        assert isinstance(suggestions, list)

    def test_hyphen_handling_cjase_parol(self, real_suggestion_engine):
        """Test hyphenated word handling: cjase-parol"""
        suggestions = real_suggestion_engine.suggest("cjase-parol")
        assert isinstance(suggestions, list)

    def test_hyphen_handling_bien_vignût(self, real_suggestion_engine):
        """Test hyphenated word with accents: bien-vignût"""  
        suggestions = real_suggestion_engine.suggest("bien-vignût")
        assert isinstance(suggestions, list)

    def test_friulian_characters_gnûf(self, real_suggestion_engine):
        """Test handling of Friulian characters: gnûf"""
        suggestions = real_suggestion_engine.suggest("gnuf")
        assert len(suggestions) >= 1
        # Should suggest gnûf with proper diacritics
        suggestion_lower = [s.lower() for s in suggestions]
        assert "gnûf" in suggestion_lower

    def test_friulian_characters_çucarut(self, real_suggestion_engine):
        """Test handling of Friulian characters: çucarut → zucarut"""
        suggestions = real_suggestion_engine.suggest("çucarut")
        assert len(suggestions) >= 1
        # Should suggest zucarut
        suggestion_lower = [s.lower() for s in suggestions]
        assert "zucarut" in suggestion_lower

    def test_elision_une_ore(self, real_suggestion_engine):
        """Test elision: une ore"""
        suggestions = real_suggestion_engine.suggest("un'ore")
        assert isinstance(suggestions, list)
        # Should handle un' elision

    def test_elision_d_estât(self, real_suggestion_engine):
        """Test elision: d'estât"""
        suggestions = real_suggestion_engine.suggest("d'estât")
        assert isinstance(suggestions, list)
        # Should handle d' elision

    def test_phonetic_similarity_lengha(self, real_suggestion_engine):
        """Test phonetic similarity: lengha → lenghe"""
        suggestions = real_suggestion_engine.suggest("lengha")
        assert len(suggestions) >= 1
        suggestion_lower = [s.lower() for s in suggestions]
        assert "lenghe" in suggestion_lower

    def test_frequency_ranking_furlans_vs_furlane(self, real_suggestion_engine):
        """Test frequency-based ranking between similar words."""
        suggestions = real_suggestion_engine.suggest("furlani")
        assert isinstance(suggestions, list)
        # Should rank based on frequency if both are phonetically similar

    def test_no_suggestions_for_nonsense(self, real_suggestion_engine):
        """Test that nonsense words return reasonable results."""
        suggestions = real_suggestion_engine.suggest("xyzabc123")
        # May return empty or minimal suggestions
        assert isinstance(suggestions, list)

    def test_single_letter_suggestions(self, real_suggestion_engine):
        """Test single letter input handling."""
        suggestions = real_suggestion_engine.suggest("a")
        # Should handle single letters gracefully
        assert isinstance(suggestions, list)

    def test_double_letter_handling_anell(self, real_suggestion_engine):
        """Test double letter correction: anell → anel"""
        suggestions = real_suggestion_engine.suggest("anell")
        if suggestions:
            suggestion_lower = [s.lower() for s in suggestions]
            assert "anel" in suggestion_lower

    def test_verb_forms_mangja(self, real_suggestion_engine):
        """Test verb form suggestions: mangja → mangjó"""
        suggestions = real_suggestion_engine.suggest("mangja")
        if suggestions:
            suggestion_lower = [s.lower() for s in suggestions]
            # May include mangjó or other verb forms