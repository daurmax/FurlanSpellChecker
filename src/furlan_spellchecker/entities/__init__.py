"""Entities module initialization."""

from .processed_element import (
    IProcessedElement,
    ProcessedPunctuation,
    ProcessedWord,
)

__all__ = [
    "IProcessedElement",
    "ProcessedWord", 
    "ProcessedPunctuation",
]