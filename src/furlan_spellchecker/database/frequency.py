"""
Frequency database for Friulian word frequency-based suggestion ranking.

This module implements frequency database functionality from COF,
which contains ~69,000 word frequency entries for prioritizing 
spelling suggestions based on word usage frequency.
"""

from __future__ import annotations
from typing import Dict, Optional, List, Tuple
from pathlib import Path
import sqlite3


class FrequencyDatabase:
    """Database for Friulian word frequencies."""
    
    def __init__(self, db_path: str | Path) -> None:
        """
        Initialize frequency database.
        
        Args:
            db_path: Path to SQLite database containing frequency data
        """
        self.db_path = Path(db_path) if isinstance(db_path, str) else db_path
        self._connection: Optional[sqlite3.Connection] = None
        self._freq_cache: Dict[str, int] = {}
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection (lazy initialization)."""
        if self._connection is None:
            if not self.db_path.exists():
                raise FileNotFoundError(f"Frequency database not found: {self.db_path}")
            
            self._connection = sqlite3.connect(str(self.db_path))
            self._connection.row_factory = sqlite3.Row
        
        return self._connection
    
    def get_frequency(self, word: str) -> int:
        """
        Get frequency score for word.
        
        Equivalent to COF's $self->data->get_freq->{$word} || 0
        
        Args:
            word: Friulian word to lookup
            
        Returns:
            Frequency score (0 if word not found)
            Higher numbers = more frequent words
            
        Examples:
            >>> db.get_frequency("di")     # Most common word
            255
            >>> db.get_frequency("furlan") # Common word  
            192
            >>> db.get_frequency("blablabla") # Unknown
            0
        """
        if not word:
            return 0
            
        # Check cache first
        if word in self._freq_cache:
            return self._freq_cache[word]
        
        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT Value FROM Data WHERE Key = ? LIMIT 1",
            (word,)
        )
        
        result = cursor.fetchone()
        frequency = result["Value"] if result else 0
        
        # Cache result
        self._freq_cache[word] = frequency
        
        return frequency
    
    def get_frequency_rank(self, word: str) -> float:
        """
        Get normalized frequency rank for word (0.0 - 1.0).
        
        Args:
            word: Word to get rank for
            
        Returns:
            Normalized rank where 1.0 = most frequent, 0.0 = not found
        """
        frequency = self.get_frequency(word)
        if frequency == 0:
            return 0.0
        
        # Get max frequency for normalization (cached)
        if not hasattr(self, '_max_frequency'):
            conn = self._get_connection()
            cursor = conn.execute("SELECT MAX(value) as max_freq FROM frequencies")
            result = cursor.fetchone()
            self._max_frequency = result["max_freq"] if result else 255
        
        return frequency / self._max_frequency
    
    def rank_suggestions(self, suggestions: List[str]) -> List[Tuple[str, int]]:
        """
        Rank suggestions by frequency score.
        
        Args:
            suggestions: List of word suggestions
            
        Returns:
            List of (word, frequency) tuples sorted by frequency (high to low)
        """
        ranked = []
        for suggestion in suggestions:
            frequency = self.get_frequency(suggestion)
            ranked.append((suggestion, frequency))
        
        # Sort by frequency (descending) then alphabetically
        ranked.sort(key=lambda x: (-x[1], x[0]))
        
        return ranked
    
    def get_most_frequent(self, limit: int = 10) -> List[Tuple[str, int]]:
        """
        Get most frequent words from database.
        
        Args:
            limit: Maximum number of words to return
            
        Returns:
            List of (word, frequency) tuples
        """
        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT key, value FROM frequencies ORDER BY value DESC LIMIT ?",
            (limit,)
        )
        
        return [(row["key"], row["value"]) for row in cursor]
    
    def get_frequency_distribution(self) -> Dict[str, int]:
        """Get frequency distribution statistics."""
        conn = self._get_connection()
        cursor = conn.execute(
            """
            SELECT 
                CASE 
                    WHEN value >= 200 THEN 'very_high'
                    WHEN value >= 100 THEN 'high' 
                    WHEN value >= 50 THEN 'medium'
                    WHEN value >= 10 THEN 'low'
                    ELSE 'very_low'
                END as freq_range,
                COUNT(*) as count
            FROM frequencies 
            GROUP BY freq_range
            """
        )
        
        distribution = {}
        for row in cursor:
            distribution[row["freq_range"]] = row["count"]
        
        return distribution
    
    def get_stats(self) -> Dict[str, int]:
        """Get database statistics."""
        conn = self._get_connection()
        
        # Total entries
        cursor = conn.execute("SELECT COUNT(*) as total FROM frequencies")
        total_result = cursor.fetchone()
        
        # Max frequency
        cursor = conn.execute("SELECT MAX(value) as max_freq FROM frequencies")
        max_result = cursor.fetchone()
        
        # Average frequency
        cursor = conn.execute("SELECT AVG(value) as avg_freq FROM frequencies")
        avg_result = cursor.fetchone()
        
        return {
            "total_words": total_result["total"] if total_result else 0,
            "max_frequency": max_result["max_freq"] if max_result else 0,
            "avg_frequency": int(avg_result["avg_freq"]) if avg_result else 0,
            "cache_size": len(self._freq_cache)
        }
    
    def close(self) -> None:
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
        self._freq_cache.clear()
    
    def __del__(self) -> None:
        """Cleanup database connection."""
        self.close()