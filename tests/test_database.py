"""Tests for database functionality."""
import os
import pytest
import tempfile
import time
import shutil
import sqlite3
from pathlib import Path

from furlan_spellchecker.database import (
    SQLiteKeyValueDatabase,
    DatabaseManager,
    DictionaryType,
    AddWordResult
)
from furlan_spellchecker.config.schemas import FurlanSpellCheckerConfig, DictionaryConfig


@pytest.fixture
def temp_config():
    """Create a temporary configuration for testing with robust Windows cleanup.

    Using TemporaryDirectory context directly sometimes triggers PermissionError on Windows
    because SQLite may keep the file handle a fraction of a second after context exit.
    We implement manual cleanup with retries.
    """
    temp_dir = tempfile.mkdtemp()
    config = FurlanSpellCheckerConfig(dictionary=DictionaryConfig(cache_directory=temp_dir))
    try:
        yield config
    finally:
        # Retry deletion a few times if locked
        for attempt in range(5):
            try:
                # Attempt rename of sqlite files to break lingering handles (Windows quirk)
                for root, _dirs, files in os.walk(temp_dir):
                    for f in files:
                        if f.endswith('.sqlite'):
                            p = os.path.join(root, f)
                            try:
                                os.replace(p, p + f".tmp{attempt}")
                            except OSError:
                                pass
                shutil.rmtree(temp_dir)
                break
            except PermissionError:
                if attempt == 4:
                    # Give up and leak temp dir rather than failing test on Windows
                    break
                time.sleep(0.2)


@pytest.fixture
def sqlite_db(temp_config):
    """Create SQLiteKeyValueDatabase instance for testing."""
    return SQLiteKeyValueDatabase(temp_config)


@pytest.fixture
def sample_system_db(temp_config):
    """Create a sample system database for testing."""
    cache_dir = Path(temp_config.dictionary.cache_directory)
    words_dir = cache_dir / "words_database"
    words_dir.mkdir(parents=True, exist_ok=True)
    
    db_path = words_dir / "words.db"
    
    # Create and populate sample database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create table structure similar to C# version
    cursor.execute("""
        CREATE TABLE Words (
            Key TEXT PRIMARY KEY,
            Value TEXT NOT NULL
        )
    """)
    
    # Add some sample data (phonetic hash -> word mappings)
    sample_data = [
        ("KS", "cjase"),  # house
        ("FRD", "fradi"),  # brother
        ("MR", "mari"),   # mother
    ]
    
    cursor.executemany("INSERT INTO Words (Key, Value) VALUES (?, ?)", sample_data)
    conn.commit()
    conn.close()
    
    return db_path


class TestSQLiteKeyValueDatabase:
    """Test SQLite database operations."""
    
    def test_user_database_creation(self, sqlite_db):
        """Test that user database is created when accessed."""
        # Database should be created when first accessed
        result = sqlite_db.add_to_user_database("test_word")
        
        # Should succeed in creating and adding
        assert result in [AddWordResult.SUCCESS, AddWordResult.ALREADY_PRESENT]
    
    def test_find_in_system_database(self, sqlite_db, sample_system_db):
        """Test finding words in system database."""
        # Should find existing phonetic hash
        result = sqlite_db.find_in_system_database("KS")
        assert result == "cjase"
        
        # Should return None for non-existent hash
        result = sqlite_db.find_in_system_database("NONEXISTENT")
        assert result is None
    
    def test_add_to_user_database(self, sqlite_db):
        """Test adding words to user database."""
        # Add a word
        result = sqlite_db.add_to_user_database("test_word")
        assert result == AddWordResult.SUCCESS
        
        # Adding the same word should return ALREADY_PRESENT
        result = sqlite_db.add_to_user_database("test_word")
        assert result == AddWordResult.ALREADY_PRESENT
    
    def test_unicode_replacement(self, sqlite_db):
        """Test Unicode code replacement functionality."""
        # This tests the internal method
        result = sqlite_db._replace_unicode_codes_with_special_chars("test\\e7word")
        assert result == "testçword"
        
        result = sqlite_db._replace_unicode_codes_with_special_chars("norm\\e2l")
        assert result == "normâl"


class TestDatabaseManager:
    """Test database manager functionality."""
    
    def test_database_availability_check(self, temp_config):
        """Test checking database availability."""
        manager = DatabaseManager(temp_config)
        availability = manager.ensure_databases_available()
        
        # Should return status for all database types
        assert DictionaryType.USER_DICTIONARY in availability
        assert DictionaryType.SYSTEM_DICTIONARY in availability
        assert DictionaryType.RADIX_TREE in availability
        
        # User database should be available (can be created)
        assert availability[DictionaryType.USER_DICTIONARY] is True
    
    def test_missing_databases(self, temp_config):
        """Test getting list of missing databases."""
        manager = DatabaseManager(temp_config)
        missing = manager.get_missing_databases()
        
        # Should include missing required databases
        assert DictionaryType.SYSTEM_DICTIONARY in missing
        assert DictionaryType.FREQUENCIES in missing
        assert DictionaryType.ELISIONS in missing
        
        # Each missing database should have a path
        for db_type, path in missing.items():
            assert isinstance(path, Path)


@pytest.mark.integration
class TestDatabaseIntegration:
    """Integration tests for database functionality."""
    
    @pytest.mark.skipif(
        os.environ.get("GITHUB_ACTIONS") == "true",
        reason="Skip integration tests in CI"
    )
    def test_database_with_extracted_files(self, temp_config):
        """Test database operations with actual extracted files."""
        # This test would work with files extracted by DictionaryManager
        manager = DatabaseManager(temp_config)
        
        # Check initial state
        availability = manager.ensure_databases_available()
        missing = manager.get_missing_databases()
        
        # Should have some missing databases initially
        assert len(missing) > 0
        
        # After extracting files (would be done by DictionaryManager),
        # availability should improve
        # This is a placeholder for future integration with actual files