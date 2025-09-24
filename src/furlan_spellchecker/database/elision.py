"""
Elisions database for Friulian elision handling.

This module implements the elision database functionality from COF,
which contains ~10,600 entries of Friulian words that can be contracted
with apostrophes (e.g., "la aghe" -> "l'aghe").
"""

from __future__ import annotations
from typing import Dict, Optional
from pathlib import Path
import sqlite3


class ElisionDatabase:
    """Database for Friulian elision rules."""
    
    def __init__(self, db_path: str | Path) -> None:
        """
        Initialize elision database.
        
        Args:
            db_path: Path to SQLite database containing elision data
        """
        self.db_path = Path(db_path) if isinstance(db_path, str) else db_path
        self._connection: Optional[sqlite3.Connection] = None
        self._elision_cache: Dict[str, bool] = {}
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection (lazy initialization)."""
        if self._connection is None:
            if not self.db_path.exists():
                raise FileNotFoundError(f"Elision database not found: {self.db_path}")
            
            self._connection = sqlite3.connect(str(self.db_path))
            self._connection.row_factory = sqlite3.Row
        
        return self._connection
    
    def has_elision(self, word: str) -> bool:
        """
        Check if word can be contracted with apostrophe.
        
        Equivalent to COF's word_has_elision() method.
        
        Args:
            word: Friulian word to check
            
        Returns:
            True if word supports elision contractions
            
        Examples:
            >>> db.has_elision("ore")  # "l'ore" -> "la ore"  
            True
            >>> db.has_elision("cjase")
            False
        """
        if not word:
            return False
            
        # Check cache first for performance
        if word in self._elision_cache:
            return self._elision_cache[word]
        
        conn = self._get_connection()
        
        # Try exact match first (case-sensitive)
        cursor = conn.execute(
            "SELECT Word FROM Data WHERE Word = ? LIMIT 1",
            (word,)
        )
        result = cursor.fetchone()
        
        if result is None:
            # Try lowercase version
            word_lower = word.lower()
            cursor = conn.execute(
                "SELECT Word FROM Data WHERE Word = ? LIMIT 1", 
                (word_lower,)
            )
            result = cursor.fetchone()
        
        has_elision_rule = result is not None
        
        # Cache result
        self._elision_cache[word] = has_elision_rule
        
        return has_elision_rule
    
    def get_elision_candidates(self, apostrophe_word: str) -> list[str]:
        """
        Get elision expansion candidates for apostrophe word.
        
        Args:
            apostrophe_word: Word with apostrophe like "l'aghe"
            
        Returns:
            List of possible expansions like ["la aghe"]
        """
        if "'" not in apostrophe_word:
            return []
        
        # Split on apostrophe
        parts = apostrophe_word.split("'", 1)
        if len(parts) != 2:
            return []
        
        prefix, base_word = parts
        
        # Check if base word supports elision
        if not self.has_elision(base_word):
            return []
        
        # Generate common Friulian elision expansions
        candidates = []
        
        # Common prefix mappings for Friulian
        prefix_mappings = {
            "l": ["la", "il"],
            "un": ["une"],
            "dal": ["de la", "dal"],
            "tal": ["te la", "tal"],
            "pal": ["pe la", "pal"],
            "cul": ["cu la", "cul"],
        }
        
        if prefix.lower() in prefix_mappings:
            for expansion in prefix_mappings[prefix.lower()]:
                candidates.append(f"{expansion} {base_word}")
        
        return candidates
    
    def get_stats(self) -> Dict[str, int]:
        """Get database statistics."""
        conn = self._get_connection()
        cursor = conn.execute("SELECT COUNT(*) as total FROM elisions")
        result = cursor.fetchone()
        
        return {
            "total_elisions": result["total"] if result else 0,
            "cache_size": len(self._elision_cache)
        }
    
    def close(self) -> None:
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
        self._elision_cache.clear()
    
    def __del__(self) -> None:
        """Cleanup database connection."""
        self.close()