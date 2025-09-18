# Project Architecture

FurlanSpellChecker is organized as a set of modular, typed components that compose a comprehensive spell checking pipeline for the Friulian language.

## Module Overview

| Package | Responsibility | Design Notes | Status |
| --- | --- | --- | --- |
| `core` | Abstract interfaces, exceptions, and shared types | Interface-driven design with custom error hierarchy | Complete |
| `entities` | Data structures for processed text elements | ProcessedWord and ProcessedPunctuation classes | Complete |
| `spellchecker` | Main spell checking logic and text processing | Core spell checking algorithms and text tokenization | Skeleton |
| `dictionary` | Dictionary management and data structures | RadixTree implementation for efficient lookups | Skeleton |
| `phonetic` | Friulian-specific phonetic algorithms | Custom phonetic similarity for better suggestions | Skeleton |
| `services` | High-level pipeline and I/O operations | Service layer orchestrating the complete workflow | Skeleton |
| `config` | Configuration management and schemas | Dataclass-based configuration with JSON/YAML support | Complete |
| `cli` | Command-line interface | Click-based CLI with comprehensive subcommands | Skeleton |
| `data` | Packaged dictionary data | Basic Friulian word list and resources | Basic |

## Architectural Patterns

### Interface-Driven Design
- `core.interfaces` defines abstract base classes for all major components
- `ISpellChecker`, `IDictionary`, `IPhoneticAlgorithm`, `ITextProcessor`
- Enables easy testing, mocking, and implementation swapping
- Ensures consistent APIs across different implementations

### Service Layer Pattern
- `SpellCheckPipeline` orchestrates the complete workflow
- Services provide high-level operations for CLI and API consumption
- Business logic remains in core modules, coordination in services
- Clear separation between orchestration and implementation

### Entity-Driven Processing
- Text is processed into `ProcessedElement` instances
- `ProcessedWord` and `ProcessedPunctuation` maintain state
- Supports correction tracking, case preservation, and metadata
- Enables fine-grained control over text modifications

### Configuration Management
- Dataclass-based configuration with type safety
- Hierarchical configuration structure matching module organization
- Support for JSON/YAML configuration files
- Runtime configuration validation and defaults

## Component Interactions

```
CLI/API Request
    ↓
SpellCheckPipeline (Service Layer)
    ↓
FurlanSpellChecker (Core Logic)
    ↓
TextProcessor → ProcessedElements
    ↓
Dictionary ← → PhoneticAlgorithm
    ↓
Suggestions & Corrections
    ↓
Formatted Response
```

## Key Design Decisions

### Type Safety
- Full type hints throughout codebase
- mypy strict mode compliance
- Custom type aliases for domain concepts
- Enum-based constants for type-safe values

### Error Handling
- Custom exception hierarchy rooted in `FurlanSpellCheckerError`
- Module-specific exception types with clear inheritance
- Informative error messages with context
- Graceful degradation where possible

### Performance Considerations
- RadixTree for efficient dictionary lookups
- Lazy loading of dictionary data
- Caching of phonetic computations
- Minimal object creation in hot paths

### Extensibility
- Plugin-style architecture through interfaces
- Configuration-driven behavior modification
- Support for custom dictionaries and rules
- Modular design allowing component replacement

## Implementation Status

### Phase 1: Foundation ✅
- [x] Project structure and packaging
- [x] Core interfaces and type system
- [x] Basic entity classes
- [x] Configuration framework
- [x] Test infrastructure and CI/CD

### Phase 2: Core Logic (In Progress)
- [ ] Text processing and tokenization
- [ ] Basic dictionary operations
- [ ] Simple spell checking pipeline
- [ ] CLI command implementation

### Phase 3: Advanced Features (Planned)
- [ ] Friulian phonetic algorithm
- [ ] RadixTree dictionary implementation
- [ ] Advanced suggestion algorithms
- [ ] Performance optimization

### Phase 4: Polish (Planned)
- [ ] Comprehensive documentation
- [ ] Full test coverage
- [ ] Performance benchmarking
- [ ] API service layer

## Future Enhancements

### Performance Optimizations
- Consider Cython for hot paths
- Memory-mapped dictionary files
- Parallel processing for batch operations
- Streaming API for large documents

### Language Features
- Support for Friulian dialects
- Advanced morphological analysis
- Grammar checking capabilities
- Integration with TTS/STT systems

### Integration Capabilities
- Text editor plugins
- Web service API
- Library bindings for other languages
- Cloud deployment options