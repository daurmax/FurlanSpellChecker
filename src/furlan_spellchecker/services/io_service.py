"""I/O service for file operations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


class IOService:
    """Service for handling file input/output operations."""

    @staticmethod
    def read_text_file(file_path: str, encoding: str = "utf-8") -> str:
        """Read text from a file."""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        return path.read_text(encoding=encoding)

    @staticmethod
    def write_text_file(file_path: str, content: str, encoding: str = "utf-8") -> None:
        """Write text to a file."""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding=encoding)

    @staticmethod
    def read_json_file(file_path: str, encoding: str = "utf-8") -> Dict[str, Any]:
        """Read JSON data from a file."""
        content = IOService.read_text_file(file_path, encoding)
        return json.loads(content)

    @staticmethod
    def write_json_file(
        file_path: str, 
        data: Dict[str, Any], 
        encoding: str = "utf-8",
        indent: int = 2
    ) -> None:
        """Write JSON data to a file."""
        content = json.dumps(data, ensure_ascii=False, indent=indent)
        IOService.write_text_file(file_path, content, encoding)

    @staticmethod
    def read_word_list(file_path: str, encoding: str = "utf-8") -> list[str]:
        """Read a list of words from a file (one word per line)."""
        content = IOService.read_text_file(file_path, encoding)
        words = []
        
        for line in content.split('\n'):
            word = line.strip()
            if word and not word.startswith('#'):  # Skip empty lines and comments
                words.append(word)
                
        return words

    @staticmethod
    def write_word_list(
        file_path: str, 
        words: list[str], 
        encoding: str = "utf-8"
    ) -> None:
        """Write a list of words to a file (one word per line)."""
        content = '\n'.join(words)
        IOService.write_text_file(file_path, content, encoding)

    @staticmethod
    def file_exists(file_path: str) -> bool:
        """Check if a file exists."""
        return Path(file_path).exists()

    @staticmethod
    def create_directory(directory_path: str) -> None:
        """Create a directory if it doesn't exist."""
        Path(directory_path).mkdir(parents=True, exist_ok=True)