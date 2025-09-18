"""Type aliases and custom types for FurlanSpellChecker."""

from __future__ import annotations

from enum import Enum
from typing import Union


class WordType(Enum):
    """Enumeration for word case types."""

    LOWERCASE = "lowercase"
    FIRST_LETTER_UPPERCASE = "first_letter_uppercase"
    UPPERCASE = "uppercase"
    MIXED_CASE = "mixed_case"


class DictionaryType(Enum):
    """Enumeration for dictionary types."""

    MAIN = "main"
    USER = "user"
    TEMPORARY = "temporary"
    ERRORS = "errors"
    ELISIONS = "elisions"


class SuggestionOriginPriority(Enum):
    """Enumeration for suggestion origin priority values."""

    HIGH = 1
    MEDIUM = 2
    LOW = 3


# Type aliases
SuggestionList = list[str]
PhoneticCode = str