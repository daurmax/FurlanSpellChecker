"""
COF::Data Python equivalent

This module provides the database connectivity and initialization
functionality equivalent to the Perl COF::Data module.
"""

from pathlib import Path
from typing import Any


class COFData:
    """Python equivalent of Perl COF::Data class."""

    def __init__(self, dict_dir: str, **kwargs):
        """Initialize COF Data with dictionary directory."""
        self.dict_dir = Path(dict_dir)
        self._validate_dict_dir()

        # Store initialization parameters for compatibility
        self.init_params = kwargs

    @classmethod
    def make_default_args(cls, dict_dir: str) -> dict[str, Any]:
        """Create default arguments for COF::Data initialization.

        This replicates the Perl COF::Data::make_default_args function
        that was used in the working CLI connection method.
        """
        if not dict_dir:
            raise NotImplementedError("get_dict_dir() must be implemented to provide dict_dir")

        return {
            'dict_dir': dict_dir,
            # Additional default arguments can be added here as needed
            'encoding': 'utf-8',
            'cache_size': 1000,
        }

    def _validate_dict_dir(self) -> None:
        """Validate that dictionary directory exists and contains required files."""
        if not self.dict_dir.exists():
            raise FileNotFoundError(f"Dictionary directory not found: {self.dict_dir}")

        if not self.dict_dir.is_dir():
            raise NotADirectoryError(f"Dictionary path is not a directory: {self.dict_dir}")

        # Check for required database files
        required_files = ["words.db", "words.rt", "elisions.db", "errors.db", "frec.db"]
        for file_name in required_files:
            file_path = self.dict_dir / file_name
            if not file_path.exists():
                raise FileNotFoundError(f"Required dictionary file not found: {file_path}")

    def get_dict_path(self, filename: str) -> Path:
        """Get full path to dictionary file."""
        return self.dict_dir / filename

    def __repr__(self):
        return f"COFData(dict_dir={self.dict_dir})"
