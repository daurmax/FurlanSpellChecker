import pytest
from pathlib import Path

# These tests mirror CoretorOrtografic.Tests.Infrastructure.KeyValueDatabase.KeyValueDatabaseFixture
# They assume the same keys and expected values as the C# tests. Some functions may be unimplemented
# in the Python code, but the tests call the same methods and assert identical outcomes.

from furlan_spellchecker.database import SQLiteKeyValueDatabase
from furlan_spellchecker.config.schemas import FurlanSpellCheckerConfig


@pytest.fixture(scope="module")
def db():
    # Use default config which points to the extracted databases in the user's cache
    config = FurlanSpellCheckerConfig()
    db = SQLiteKeyValueDatabase(config)
    return db


def test_find_in_system_database_with_existing_key(db):
    key = "65g8A6597Y7"
    value = db.find_in_system_database(key)
    expected = "angossantjure"

    print(f"Key is: [{key}]")
    print(f"Value is: [{value}]")

    assert value is not None
    assert value == expected


def test_find_in_system_errors_database_with_existing_key(db):
    key = "adincuatri"
    value = db.find_in_system_errors_database(key)
    expected = "ad in cuatri"

    print(f"Key is: [{key}]")
    print(f"Value is: [{value}]")

    assert value is not None
    assert value == expected


def test_find_in_frequencies_database_with_existing_key(db):
    key = "cognossi"
    value = db.find_in_frequencies_database(key)
    expected = 140

    print(f"Key is: [{key}]")
    print(f"Value is: [{value}]")

    assert value is not None
    assert value == expected


def test_has_elisions_with_existing_key(db):
    key = "analfabetementri"
    value = db.has_elisions(key)
    expected = True

    print(f"Key is: [{key}]")
    print(f"Value is: [{value}]")

    assert value == expected


def test_find_in_system_database_with_nonexistent_key(db):
    key = "nonExistentKey"
    value = db.find_in_system_database(key)

    print(f"Key is: [{key}]")
    print(f"Value is: [{value}]")

    assert value is None


def test_find_in_system_errors_database_with_nonexistent_key(db):
    key = "ad in cuatri"
    value = db.find_in_system_errors_database(key)

    print(f"Key is: [{key}]")
    print(f"Value is: [{value}]")

    assert value is None


def test_find_in_frequencies_database_with_nonexistent_key(db):
    key = "nonExistentKey"
    value = db.find_in_frequencies_database(key)

    print(f"Key is: [{key}]")
    print(f"Value is: [{value}]")

    assert value is None


def test_has_elisions_with_nonexistent_key(db):
    key = "nonExistentKey"
    value = db.has_elisions(key)
    expected = False

    print(f"Key is: [{key}]")
    print(f"Value is: [{value}]")

    assert value == expected


def test_find_in_system_database_with_null_key_raises(db):
    with pytest.raises(ValueError):
        db.find_in_system_database(None)  # type: ignore


def test_find_in_system_errors_database_with_null_key_raises(db):
    with pytest.raises(ValueError):
        db.find_in_system_errors_database(None)  # type: ignore


def test_find_in_frequencies_database_with_null_key_raises(db):
    with pytest.raises(ValueError):
        db.find_in_frequencies_database(None)  # type: ignore


def test_has_elisions_with_null_key_raises(db):
    with pytest.raises(ValueError):
        db.has_elisions(None)  # type: ignore
