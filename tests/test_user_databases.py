"""Tests for user database functionality."""
import pytest
import tempfile
from pathlib import Path

from furlan_spellchecker.database.user_dictionary import UserDictionaryDatabase
from furlan_spellchecker.database.user_exceptions import UserExceptionsDatabase
from furlan_spellchecker.phonetic.furlan_phonetic import FurlanPhoneticAlgorithm


class TestUserDictionaryDatabase:
    """Tests for UserDictionaryDatabase."""
    
    def test_add_and_retrieve_word(self):
        """Test adding and retrieving a word."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_user_dict.sqlite"
            db = UserDictionaryDatabase(db_path)
            
            # Add a word
            result = db.add_word("cjase")
            assert result is True
            
            # Check if word exists
            assert db.has_word("cjase") is True
            assert db.has_word("inexistent") is False
    
    def test_phonetic_suggestions(self):
        """Test phonetic suggestions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_user_dict.sqlite"
            db = UserDictionaryDatabase(db_path)
            
            # Add words with similar phonetic codes
            db.add_word("cjase")
            db.add_word("cjasis")
            
            # Get suggestions for phonetically similar word
            suggestions = db.get_phonetic_suggestions("cjaze", max_suggestions=5)
            assert len(suggestions) >= 1
            assert "cjase" in suggestions or "cjasis" in suggestions
    
    def test_remove_word(self):
        """Test removing a word."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_user_dict.sqlite"
            db = UserDictionaryDatabase(db_path)
            
            # Add and remove word
            db.add_word("testword")
            assert db.has_word("testword") is True
            
            result = db.remove_word("testword")
            assert result is True
            assert db.has_word("testword") is False
    
    def test_get_word_count(self):
        """Test word count functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_user_dict.sqlite"
            db = UserDictionaryDatabase(db_path)
            
            assert db.get_word_count() == 0
            
            db.add_word("cjase")
            db.add_word("aga")
            
            assert db.get_word_count() == 2


class TestUserExceptionsDatabase:
    """Tests for UserExceptionsDatabase."""
    
    def test_add_and_retrieve_exception(self):
        """Test adding and retrieving exceptions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_user_exc.sqlite"
            db = UserExceptionsDatabase(db_path)
            
            # Add exception
            result = db.add_exception("sbajât", "sbagliât")
            assert result is True
            
            # Retrieve correction
            correction = db.get_correction("sbajât")
            assert correction == "sbagliât"
            
            # Check non-existent
            assert db.get_correction("inexistent") is None
    
    def test_update_exception(self):
        """Test updating an existing exception."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_user_exc.sqlite"
            db = UserExceptionsDatabase(db_path)
            
            # Add and update exception
            db.add_exception("sbajât", "sbagliât")
            db.add_exception("sbajât", "corrected")  # Update
            
            correction = db.get_correction("sbajât")
            assert correction == "corrected"
    
    def test_remove_exception(self):
        """Test removing an exception."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_user_exc.sqlite"
            db = UserExceptionsDatabase(db_path)
            
            # Add and remove exception
            db.add_exception("sbajât", "sbagliât")
            assert db.has_exception("sbajât") is True
            
            result = db.remove_exception("sbajât")
            assert result is True
            assert db.has_exception("sbajât") is False
    
    def test_get_all_exceptions(self):
        """Test retrieving all exceptions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_user_exc.sqlite"
            db = UserExceptionsDatabase(db_path)
            
            # Add multiple exceptions
            db.add_exception("sbajât", "sbagliât")
            db.add_exception("scritûr", "scriture")
            
            all_exceptions = db.get_all_exceptions()
            assert len(all_exceptions) == 2
            assert all_exceptions["sbajât"] == "sbagliât"
            assert all_exceptions["scritûr"] == "scriture"
    
    def test_exception_count(self):
        """Test exception count functionality.""" 
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_user_exc.sqlite"
            db = UserExceptionsDatabase(db_path)
            
            assert db.get_exception_count() == 0
            
            db.add_exception("error1", "correction1")
            db.add_exception("error2", "correction2")
            
            assert db.get_exception_count() == 2


class TestUserDatabaseIntegration:
    """Integration tests for both user databases."""
    
    def test_phonetic_algorithm_integration(self):
        """Test that phonetic algorithm works correctly with user dictionary."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_integration.sqlite"
            db = UserDictionaryDatabase(db_path)
            phonetic = FurlanPhoneticAlgorithm()
            
            # Test word with known phonetic pattern
            test_word = "cjase"
            db.add_word(test_word)
            
            # Get phonetic codes
            code_a, code_b = phonetic.get_phonetic_hashes_by_word(test_word)
            
            # Verify word is stored under correct phonetic codes
            words_a = db.get_words_by_phonetic_code(code_a)
            assert test_word in words_a
            
            if code_a != code_b:
                words_b = db.get_words_by_phonetic_code(code_b)
                assert test_word in words_b
    
    def test_cof_priority_simulation(self):
        """Test that user databases work with COF priority system."""
        with tempfile.TemporaryDirectory() as temp_dir:
            dict_path = Path(temp_dir) / "test_dict.sqlite"
            exc_path = Path(temp_dir) / "test_exc.sqlite"
            
            user_dict = UserDictionaryDatabase(dict_path)
            user_exc = UserExceptionsDatabase(exc_path)
            
            # Add user dictionary word (priority F_USER_DICT = 350)
            user_dict.add_word("cjase")
            
            # Add user exception (priority F_USER_EXC = 1000) 
            user_exc.add_exception("caze", "cjase")
            
            # Verify user exception has higher priority
            correction = user_exc.get_correction("caze")
            assert correction == "cjase"
            
            # Verify user dictionary contains word
            suggestions = user_dict.get_phonetic_suggestions("cjaze", max_suggestions=5)
            assert "cjase" in suggestions