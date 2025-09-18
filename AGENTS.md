# FurlanSpellChecker Agent Guidelines

This document provides guidelines for AI agents working on the FurlanSpellChecker project.

## Project Overview

FurlanSpellChecker is a Python library and CLI tool for spell checking Friulian text. It's designed to replicate and improve upon the functionality of CoretorOrtograficFurlan-Core (C#) while following the architectural patterns established in FurlanG2P.

## Architecture Principles

### 1. Interface-Driven Design
- All major components implement abstract interfaces from `core.interfaces`
- This allows for easy testing, mocking, and future implementation swapping
- Keep interfaces focused and cohesive

### 2. Modular Structure
The project is organized into focused modules:
- `core/` - Base interfaces, exceptions, types
- `entities/` - Data structures (ProcessedWord, ProcessedPunctuation)
- `spellchecker/` - Main spell checking logic
- `dictionary/` - Dictionary management and data structures
- `phonetic/` - Friulian-specific phonetic algorithms
- `services/` - High-level orchestration and I/O
- `config/` - Configuration management
- `cli/` - Command-line interface
- `data/` - Packaged dictionary data

### 3. Service Layer Pattern
- `SpellCheckPipeline` orchestrates the complete workflow
- Services provide high-level operations for CLI and API consumption
- Keep business logic in the core modules, coordination in services

## Development Guidelines

### Code Style
- Use Black for formatting (100 character line length)
- Follow PEP 8 and type hints for all public APIs
- Use Ruff for linting with the configured rule set
- All code should pass mypy strict mode

### Testing Strategy
- Unit tests for all core functionality
- Integration tests for the complete pipeline
- Property-based testing with Hypothesis for complex algorithms
- Async tests for async functionality using pytest-asyncio

### Error Handling
- Use the custom exception hierarchy from `core.exceptions`
- Provide clear, actionable error messages
- Handle Friulian text encoding issues gracefully

### Documentation
- Docstrings for all public classes and methods
- Keep README.md current with examples
- Document configuration options thoroughly
- Include type information in docstrings

## Friulian Language Considerations

### Text Processing
- Handle Friulian diacritics (à, è, ì, ò, ù, â, ê, î, ô, û, ç)
- Consider word boundaries and elisions specific to Friulian
- Preserve case information for proper correction

### Phonetic Algorithm
- Implement a Friulian-specific phonetic algorithm in Python
- Focus on phonetic patterns relevant to Friulian for suggestions

### Dictionary Management
- Support for multiple dictionary types (main, user, errors, elisions)
- Efficient lookup and suggestion generation
- RadixTree implementation for performance

## Implementation Priorities

### Phase 1: Core Infrastructure
- [x] Basic project structure and configuration
- [x] Core interfaces and type definitions
- [x] Basic entity classes (ProcessedWord, ProcessedPunctuation)
- [x] Skeleton implementations for major components

### Phase 2: Core Functionality
- [ ] Implement text processing and tokenization
- [ ] Basic dictionary operations
- [ ] Simple spell checking pipeline
- [ ] CLI basic commands

### Phase 3: Advanced Features
- [ ] Friulian phonetic algorithm
- [ ] RadixTree dictionary implementation
- [ ] Advanced suggestion algorithms
- [ ] Configuration system

### Phase 4: Polish and Optimization
- [ ] Performance optimization
- [ ] Comprehensive testing
- [ ] Documentation completion
- [ ] API service layer

## Testing and Quality Assurance

### Test Categories
1. **Unit Tests** - Test individual components in isolation
2. **Integration Tests** - Test component interactions
3. **CLI Tests** - Test command-line interface
4. **Performance Tests** - Ensure acceptable performance with large texts

### Quality Checks
- All tests must pass
- Code coverage > 90%
- No mypy errors in strict mode
- No ruff linting errors
- Documentation is current and complete

## Collaboration Guidelines

### Git Workflow
- Use descriptive commit messages
- Create feature branches for new functionality
- Include tests with all new features
- Update documentation for API changes

### Code Review Focus Areas
1. Interface compliance and design
2. Error handling completeness
3. Test coverage and quality
4. Performance implications
5. Friulian language handling correctness

## Deployment and Distribution

### Package Distribution
- Use hatchling as build backend
- Ensure all dependencies are properly specified
- Include data files in the distribution
- Test installation in clean environments

### CLI Distribution
- Entry point properly configured in pyproject.toml
- CLI help messages are clear and complete
- Error messages are user-friendly

## Future Considerations

### Performance
- Consider Cython or other optimizations for hot paths
- Profile dictionary lookup operations
- Optimize memory usage for large texts

### Extensibility
- Plugin system for custom dictionaries
- Support for other Gallo-Romance languages
- Integration with text editors and IDEs

### API Service
- FastAPI-based REST service
- WebSocket support for real-time checking
- Rate limiting and authentication

## Resources

- Original C# codebase: CoretorOrtograficFurlan-Core
- Architecture reference: FurlanG2P
- Friulian language resources: [Add relevant linguistic resources]
- Python packaging: [Python Packaging User Guide](https://packaging.python.org/)