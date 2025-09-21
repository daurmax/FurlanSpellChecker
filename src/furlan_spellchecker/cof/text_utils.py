"""
COF Text Utilities

This module provides text processing utilities equivalent to
the Perl COF text handling functions.
"""


def ucf_word(word: str) -> str:
    """Capitalize first letter of word (Upper Case First).

    Args:
        word: Input word

    Returns:
        Word with first letter capitalized
    """
    if not word:
        return word
    return word[0].upper() + word[1:]


def lc_word(word: str) -> str:
    """Convert word to lowercase.

    Args:
        word: Input word

    Returns:
        Word in lowercase
    """
    return word.lower()


def first_is_uc(word: str) -> bool:
    """Check if first character is uppercase.

    Args:
        word: Input word

    Returns:
        True if first character is uppercase, False otherwise
    """
    if not word:
        return False
    return word[0].isupper()
