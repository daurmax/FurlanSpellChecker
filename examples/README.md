# FurlanSpellChecker Examples

This directory contains example scripts demonstrating how to use FurlanSpellChecker.

## Examples

### pipeline_example.py
Comprehensive example showing:
- Single word checking
- Text processing
- Suggestion generation
- Dictionary management
- Configuration usage

To run:
```bash
cd examples
python pipeline_example.py
```

## Setting up for Examples

Make sure FurlanSpellChecker is installed:
```bash
# From the project root
pip install -e .
```

Or with development dependencies:
```bash
pip install -e ".[dev]"
```

## Example Data

The examples use the basic Friulian dictionary included with the package. For more comprehensive spell checking, you would typically load a larger dictionary file.

## Contributing Examples

When adding new examples:
1. Include comprehensive docstrings
2. Handle errors gracefully with informative messages
3. Demonstrate both successful and error cases where appropriate
4. Update this README with a description of the new example