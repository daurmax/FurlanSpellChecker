# FurlanSpellChecker

A comprehensive spell checker for the Friulian language with CLI and pipeline service.

## Overview

FurlanSpellChecker is a Python library and command-line tool for spell checking text in the Friulian (Furlan) language. It provides a complete spell checking pipeline with dictionary management, phonetic algorithms, and text processing capabilities specifically designed for Friulian linguistic features.

## Features

- **Complete spell checking pipeline** - Tokenization, spell checking, and correction suggestions
- **Friulian-specific phonetic algorithm** - Custom phonetic similarity for better suggestions
- **Flexible dictionary system** - Support for multiple dictionaries with RadixTree optimization
- **Command-line interface** - Easy-to-use CLI for batch processing and interactive use
- **Configurable processing** - Extensive configuration options for different use cases
- **Python API** - Full programmatic access to all functionality

## Installation

### From PyPI (when available)

```bash
pip install furlanspellchecker
```

### From source

```bash
git clone https://github.com/daurmax/FurlanSpellChecker.git
cd FurlanSpellChecker
pip install -e .
```

### Development installation

```bash
git clone https://github.com/daurmax/FurlanSpellChecker.git
cd FurlanSpellChecker
pip install -e ".[dev]"
```

## Quick Start

### Command Line Usage

Check a single word:
```bash
furlanspellchecker lookup "cjase"
```

Get suggestions for a misspelled word:
```bash
furlanspellchecker suggest "cjasa"
```

Check text from a file:
```bash
furlanspellchecker file input.txt -o corrected.txt
```

### Python API Usage

```python
import asyncio
from furlan_spellchecker import SpellCheckPipeline

# Initialize the spell checker
pipeline = SpellCheckPipeline()

# Check text
result = pipeline.check_text("Cheste e je une frâs in furlan.")
print(f"Incorrect words: {result['incorrect_count']}")

# Check a single word
async def check_word():
    word_result = await pipeline.check_word("furlan")
    print(f"'{word_result['word']}' is {'correct' if word_result['is_correct'] else 'incorrect'}")

asyncio.run(check_word())
```

## Architecture

FurlanSpellChecker is organized as a set of modular components:

| Module | Responsibility |
|--------|----------------|
| `core` | Abstract interfaces, exceptions, and type definitions |
| `entities` | Data structures for processed text elements |
| `spellchecker` | Main spell checking logic and text processing |
| `dictionary` | Dictionary management and RadixTree implementation |
| `phonetic` | Friulian-specific phonetic algorithm |
| `services` | High-level pipeline and I/O services |
| `config` | Configuration schemas and management |
| `cli` | Command-line interface |
| `data` | Packaged dictionary data |

## Configuration

The spell checker can be configured through configuration files or programmatically:

```python
from furlan_spellchecker import FurlanSpellCheckerConfig, DictionaryConfig

config = FurlanSpellCheckerConfig(
    dictionary=DictionaryConfig(
        max_suggestions=5,
        use_phonetic_suggestions=True
    )
)
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

### Development Setup

1. Clone the repository
2. Install development dependencies: `pip install -e ".[dev]"`
3. Run tests: `pytest`
4. Run linting: `ruff check src tests`
5. Run type checking: `mypy src`

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Based on the original C# implementation in CoretorOrtograficFurlan-Core
- Inspired by the architecture of FurlanG2P
- Dictionary data sourced from Friulian linguistic resources

## Related Projects

- [CoretorOrtograficFurlan-Core](https://github.com/daurmax/CoretorOrtograficFurlan-Core) - Original C# implementation
- [FurlanG2P](https://github.com/daurmax/FurlanG2P) - Friulian grapheme-to-phoneme conversion