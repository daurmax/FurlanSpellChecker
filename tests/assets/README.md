# Test Assets for FurlanSpellChecker

This directory contains reference data and test assets for validating FurlanSpellChecker functionality against the original COF (Coretôr Ortografic Furlan) implementation.

## Dictionary Assets

### `friulian_lemmas.txt` 
- **Source**: Original COF lemmas database (2015)
- **Content**: Friulian lemmas with optional homograph numbers
- **Format**: `[lemma] [TAB] [number or empty]`
- **Encoding**: UTF-8 with CRLF line endings
- **Lines**: 24,266 entries

### `friulian_words.txt`
- **Source**: Original COF word forms database (2015)  
- **Content**: Friulian word forms with optional flags and frequency data
- **Format**: `[word] [TAB] [elision_flag] [TAB] [frequency]`
- **Encoding**: UTF-8 with CRLF line endings  
- **Lines**: 1,037,160 entries
- **Notes**: 
  - Elision flag ('1') indicates word can be preceded by "l'"
  - Frequency is normalized (1-255) when available

## Usage

These dictionary assets are used by the test suite to:

1. **Dictionary Validation**: Cross-check dictionary completeness and accuracy against COF reference
2. **Performance Benchmarking**: Test with realistic data volumes from authoritative sources
3. **Regression Testing**: Ensure changes don't break existing dictionary functionality

**Note**: Test data files (validation wordlists, reference results) are located in `tests/results/` 
and excluded from version control via `.gitignore`.

## Data Provenance

All dictionary data originates from the original COF (Coretôr Ortografic Furlan) project, 
developed for Friulian language spell checking. The data represents the authoritative 
reference for Friulian orthography and word forms as of 2015.