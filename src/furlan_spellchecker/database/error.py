"""
Error patterns database for common Friulian spelling corrections.

This module implements error pattern database functionality from COF,
which contains ~300 entries for spacing and apostrophe corrections
(NOT phonetic corrections - those are handled by phonetic algorithm + RadixTree).
"""

from __future__ import annotations
from typing import Dict, Optional, List
from pathlib import Path
import sqlite3


class ErrorDatabase:
    """Database for common Friulian error patterns."""
    
    def __init__(self, db_path: str | Path) -> None:
        """
        Initialize error patterns database.
        
        Args:
            db_path: Path to SQLite database containing error patterns
        """
        self.db_path = Path(db_path) if isinstance(db_path, str) else db_path
        self._connection: Optional[sqlite3.Connection] = None
        self._error_cache: Dict[str, str] = {}
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection (lazy initialization)."""
        if self._connection is None:
            if not self.db_path.exists():
                raise FileNotFoundError(f"Error database not found: {self.db_path}")
            
            self._connection = sqlite3.connect(str(self.db_path))
            self._connection.row_factory = sqlite3.Row
        
        return self._connection
    
    def get_error_correction(self, word: str) -> Optional[str]:
        """
        Get error correction for word if it exists.
        
        Equivalent to COF's errors database lookup in _find_in_exc().
        
        Args:
            word: Potentially incorrect word
            
        Returns:
            Corrected word if pattern exists, None otherwise
            
        Examples:
            >>> db.get_error_correction("un'")  
            "une"
            >>> db.get_error_correction("bench├®")
            "ben che"  
            >>> db.get_error_correction("furla")  # phonetic, not in errors.db
            None
        """
        if not word:
            return None
            
        # Check cache first
        if word in self._error_cache:
            correction = self._error_cache[word]
            return correction if correction else None
        
        conn = self._get_connection()
        
        # Try exact match first
        cursor = conn.execute(
            "SELECT Value FROM Data WHERE Key = ? LIMIT 1",
            (word,)
        )
        result = cursor.fetchone()
        
        if result:
            correction = result["Value"]
            self._error_cache[word] = correction
            return correction
        
        # Try case variations (COF handles case in _find_in_exc)
        for case_variant in [word.lower(), word.capitalize(), word.upper()]:
            if case_variant != word:
                cursor = conn.execute(
                    "SELECT Value FROM Data WHERE Key = ? LIMIT 1",
                    (case_variant,)
                )
                result = cursor.fetchone()
                
                if result:
                    correction = result["Value"]
                    # Apply same case transformation to correction
                    if word.isupper():
                        correction = correction.upper()
                    elif word.istitle():
                        correction = correction.capitalize()
                    
                    self._error_cache[word] = correction
                    return correction
        
        # Cache negative result
        self._error_cache[word] = ""
        return None
    
    def get_error_candidates(self, word: str) -> List[str]:
        """
        Get all potential error corrections for word.
        
        Args:
            word: Word to find corrections for
            
        Returns:
            List of corrections (empty if none found)
        """
        correction = self.get_error_correction(word)
        return [correction] if correction else []
    
    def has_error_pattern(self, word: str) -> bool:
        """Check if word has known error pattern."""
        return self.get_error_correction(word) is not None
    
    def get_all_patterns(self) -> Dict[str, str]:
        """
        Get all error patterns from database.
        
        Returns:
            Dictionary mapping incorrect -> correct patterns
        """
        conn = self._get_connection()
        cursor = conn.execute("SELECT key, value FROM errors")
        
        patterns = {}
        for row in cursor:
            patterns[row["key"]] = row["value"]
        
        return patterns
    
    def get_stats(self) -> Dict[str, int]:
        """Get database statistics."""
        conn = self._get_connection()
        cursor = conn.execute("SELECT COUNT(*) as total FROM errors")
        result = cursor.fetchone()
        
        # Count pattern types
        patterns = self.get_all_patterns()
        apostrophe_fixes = sum(1 for k in patterns.keys() if "'" in k)
        spacing_fixes = sum(1 for v in patterns.values() if " " in v)
        
        return {
            "total_patterns": result["total"] if result else 0,
            "apostrophe_fixes": apostrophe_fixes,
            "spacing_fixes": spacing_fixes,
            "cache_size": len(self._error_cache)
        }
    
    def close(self) -> None:
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
        self._error_cache.clear()
    
    def __del__(self) -> None:
        """Cleanup database connection."""
        self.close()