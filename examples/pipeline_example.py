"""Example usage of FurlanSpellChecker pipeline."""

import asyncio
from pathlib import Path

from furlan_spellchecker import (
    SpellCheckPipeline,
    Dictionary,
    FurlanSpellCheckerConfig,
    DictionaryConfig,
)
from furlan_spellchecker.services import IOService


async def main() -> None:
    """Demonstrate FurlanSpellChecker usage."""
    print("FurlanSpellChecker Pipeline Example")
    print("=" * 40)

    # Initialize dictionary
    dictionary = Dictionary()
    
    # Load built-in basic dictionary
    try:
        # In a real implementation, this would load from packaged data
        basic_dict_path = Path(__file__).parent.parent / "src" / "furlan_spellchecker" / "data" / "basic_dictionary.txt"
        if basic_dict_path.exists():
            dictionary.load_dictionary(str(basic_dict_path))
            print(f"Loaded dictionary with {dictionary.word_count} words")
        else:
            print("Basic dictionary not found, using empty dictionary")
    except Exception as e:
        print(f"Error loading dictionary: {e}")

    # Initialize pipeline
    pipeline = SpellCheckPipeline(dictionary=dictionary)

    # Example 1: Check a single word
    print("\n1. Single word checking:")
    test_words = ["cjase", "furlan", "sbagliata", "bon"]
    
    for word in test_words:
        result = await pipeline.check_word(word)
        status = "✓" if result["is_correct"] else "✗"
        print(f"   {status} '{word}' - {result['case']}")
        if result["suggestions"]:
            print(f"     Suggestions: {', '.join(result['suggestions'])}")

    # Example 2: Check text
    print("\n2. Text checking:")
    test_text = "Cheste e je une frâs in furlan cun cualchi peraule sbagliade."
    print(f"   Original: {test_text}")
    
    text_result = pipeline.check_text(test_text)
    print(f"   Processed: {text_result['processed_text']}")
    print(f"   Total words: {text_result['total_words']}")
    print(f"   Incorrect: {text_result['incorrect_count']}")
    
    if text_result["incorrect_words"]:
        print("   Incorrect words found:")
        for word_info in text_result["incorrect_words"]:
            print(f"     - '{word_info['original']}' (case: {word_info['case']})")

    # Example 3: Get suggestions
    print("\n3. Getting suggestions:")
    misspelled_word = "cjasa"  # Should suggest "cjase"
    suggestions = await pipeline.get_suggestions(misspelled_word, max_suggestions=5)
    print(f"   Suggestions for '{misspelled_word}': {suggestions}")

    # Example 4: Add word to dictionary
    print("\n4. Adding word to dictionary:")
    new_word = "programazion"
    added = pipeline.add_word_to_dictionary(new_word)
    print(f"   Added '{new_word}' to dictionary: {added}")
    
    # Check the word again
    result_after_add = await pipeline.check_word(new_word)
    print(f"   '{new_word}' is now {'correct' if result_after_add['is_correct'] else 'incorrect'}")

    # Example 5: Configuration
    print("\n5. Using configuration:")
    config = FurlanSpellCheckerConfig(
        dictionary=DictionaryConfig(
            max_suggestions=3,
            use_phonetic_suggestions=True,
        )
    )
    print(f"   Max suggestions configured: {config.dictionary.max_suggestions}")
    print(f"   Phonetic suggestions: {config.dictionary.use_phonetic_suggestions}")

    print("\nExample completed!")


if __name__ == "__main__":
    asyncio.run(main())