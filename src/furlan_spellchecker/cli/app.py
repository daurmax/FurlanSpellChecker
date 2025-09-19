"""Command-line interface for FurlanSpellChecker."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Optional

import click

from ..services import SpellCheckPipeline, IOService
from ..dictionary import Dictionary
from ..services.dictionary_manager import DictionaryManager
from ..config.manager import ConfigManager
from ..database import DatabaseManager, DictionaryType
from ..config.schemas import FurlanSpellCheckerConfig


@click.group()
@click.version_option()
@click.pass_context
def main(ctx: click.Context) -> None:
    """Friulian Spell Checker - A spell checker for the Friulian language."""
    ctx.ensure_object(dict)


@main.command()
@click.argument("text", type=str)
@click.option(
    "--dictionary", 
    "-d", 
    type=click.Path(exists=True),
    help="Path to dictionary file"
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output file for results"
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format"
)
def check(text: str, dictionary: Optional[str], output: Optional[str], format: str) -> None:
    """Check spelling of the given text."""
    # Initialize pipeline
    dict_obj = Dictionary()
    if dictionary:
        dict_obj.load_dictionary(dictionary)
    
    pipeline = SpellCheckPipeline(dictionary=dict_obj)
    
    # Check text
    result = pipeline.check_text(text)
    
    # Format output
    if format == "json":
        import json
        output_content = json.dumps(result, ensure_ascii=False, indent=2)
    else:
        output_content = _format_text_result(result)
    
    # Write output
    if output:
        IOService.write_text_file(output, output_content)
        click.echo(f"Results written to: {output}")
    else:
        click.echo(output_content)



@main.command("download-dicts")
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    default=False,
    help="Automatically accept download prompts",
)
@click.option(
    "--cache-dir",
    type=click.Path(),
    default=None,
    help="Override default cache directory to store dictionaries",
)
def download_dicts(yes: bool, cache_dir: Optional[str]) -> None:
    """Download required dictionary artifacts using DictionaryManager."""
    cfg = ConfigManager.load()
    # allow CLI override
    cache_path = cache_dir or cfg.get("dictionary_cache_dir")

    manager = DictionaryManager(cache_dir=cache_path)

    # simple prompt
    if not yes:
        click.echo("Dictionaries are required but not present. This will download ~100+ MB.")
        ok = click.confirm("Do you want to download now?", default=True)
        if not ok:
            click.echo("Aborted by user.")
            return

    try:
        manager.install_from_manifest()
        click.echo("Dictionaries installed successfully.")
        # persist chosen cache dir
        if cache_path:
            cfg["dictionary_cache_dir"] = str(cache_path)
            ConfigManager.save(cfg)
    except Exception as e:
        click.echo(f"Failed to install dictionaries: {e}", err=True)
        raise


@main.command("db-status")
@click.option(
    "--cache-dir",
    type=click.Path(),
    default=None,
    help="Override default cache directory to check",
)
def db_status(cache_dir: Optional[str]) -> None:
    """Check status of database files."""
    # Load config and override cache dir if provided
    cfg = ConfigManager.load()
    config = FurlanSpellCheckerConfig()
    
    if cache_dir:
        config.dictionary.cache_directory = cache_dir
    elif cfg.get("dictionary_cache_dir"):
        config.dictionary.cache_directory = cfg["dictionary_cache_dir"]
    
    db_manager = DatabaseManager(config)
    
    # Check availability
    availability = db_manager.ensure_databases_available()
    missing = db_manager.get_missing_databases()
    
    click.echo("Database Status:")
    click.echo("=" * 50)
    click.echo(f"Cache directory: {db_manager._cache_dir}")
    
    for db_type in DictionaryType:
        is_available = availability.get(db_type, False)
        status = "✓ Available" if is_available else "✗ Missing"
        click.echo(f"{db_type.value:20} {status}")
        
        if db_type in missing:
            click.echo(f"  Expected at: {missing[db_type]}")
    
    click.echo()
    if missing:
        click.echo(f"Missing {len(missing)} required databases.")
        click.echo("Run 'furlan-spellchecker download-dicts' to install them.")
    else:
        click.echo("All required databases are available!")


@main.command("extract-dicts")
@click.option(
    "--cache-dir",
    type=click.Path(), 
    default=None,
    help="Override default cache directory",
)
def extract_dicts(cache_dir: Optional[str]) -> None:
    """Extract dictionary ZIP files from data/databases/ to cache directory."""
    cfg = ConfigManager.load()
    cache_path = cache_dir or cfg.get("dictionary_cache_dir")
    
    manager = DictionaryManager(cache_dir=cache_path)
    
    click.echo("Checking for ZIP files in data/databases/...")
    
    # Check for local ZIP files
    repo_data_dir = Path.cwd() / "data" / "databases"
    if not repo_data_dir.exists():
        click.echo(f"Directory not found: {repo_data_dir}")
        click.echo("Make sure you're running from the repository root.")
        return
    
    zip_files = list(repo_data_dir.glob("*.zip"))
    if not zip_files:
        click.echo("No ZIP files found in data/databases/")
        return
    
    click.echo(f"Found {len(zip_files)} ZIP files:")
    for zip_file in zip_files:
        click.echo(f"  - {zip_file.name}")
    
    # Create manifest for local files
    import hashlib
    artifacts = []
    
    for zip_file in zip_files:
        name = zip_file.stem  # Remove .zip extension
        sha256 = hashlib.sha256(zip_file.read_bytes()).hexdigest()
        url = zip_file.as_uri()  # file:// URL
        
        artifacts.append({
            "name": name,
            "url": url,
            "sha256": sha256,
            "split": False
        })
    
    manifest = {"artifacts": artifacts}
    
    click.echo("\nExtracting ZIP files...")
    try:
        installed = manager.install_from_manifest(manifest)
        click.echo(f"Successfully extracted {len(installed)} archives:")
        for path in installed:
            click.echo(f"  - {path}")
        
        # Update config
        if cache_path:
            cfg["dictionary_cache_dir"] = str(cache_path)
            ConfigManager.save(cfg)
        
        # Check database status after extraction
        click.echo("\nChecking database status...")
        config = FurlanSpellCheckerConfig()
        config.dictionary.cache_directory = cache_path or config.dictionary.cache_directory
        
        db_manager = DatabaseManager(config)
        availability = db_manager.ensure_databases_available()
        
        available_count = sum(1 for available in availability.values() if available)
        total_count = len(availability)
        
        click.echo(f"Databases available: {available_count}/{total_count}")
        
    except Exception as e:
        click.echo(f"Error extracting dictionaries: {e}", err=True)
        raise


@main.command()
@click.argument("word", type=str)
@click.option(
    "--dictionary", 
    "-d", 
    type=click.Path(exists=True),
    help="Path to dictionary file"
)
@click.option(
    "--max-suggestions",
    "-n",
    type=int,
    default=10,
    help="Maximum number of suggestions to show"
)
def suggest(word: str, dictionary: Optional[str], max_suggestions: int) -> None:
    """Get spelling suggestions for a word."""
    # Initialize pipeline
    dict_obj = Dictionary()
    if dictionary:
        dict_obj.load_dictionary(dictionary)
    
    pipeline = SpellCheckPipeline(dictionary=dict_obj)
    
    # Get suggestions
    try:
        suggestions = asyncio.run(pipeline.get_suggestions(word, max_suggestions))
        
        if suggestions:
            click.echo(f"Suggestions for '{word}':")
            for i, suggestion in enumerate(suggestions, 1):
                click.echo(f"  {i}. {suggestion}")
        else:
            click.echo(f"No suggestions found for '{word}'")
            
    except Exception as e:
        click.echo(f"Error getting suggestions: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument("word", type=str)
@click.option(
    "--dictionary", 
    "-d", 
    type=click.Path(exists=True),
    help="Path to dictionary file"
)
def lookup(word: str, dictionary: Optional[str]) -> None:
    """Check if a word is in the dictionary."""
    # Load config and initialize database-integrated spell checker
    cfg = ConfigManager.load()
    config = FurlanSpellCheckerConfig()
    
    if dictionary:
        config.dictionary.main_dictionary_path = dictionary
    
    db_manager = DatabaseManager(config)
    
    # Check word
    try:
        from ..spellchecker import FurlanSpellChecker
        from ..phonetic import FurlanPhoneticAlgorithm
        from ..entities import ProcessedWord
        
        spell_checker = FurlanSpellChecker(db_manager, FurlanPhoneticAlgorithm())
        processed_word = ProcessedWord(word)
        
        result = asyncio.run(spell_checker.check_word(processed_word))
        
        if processed_word.correct:
            click.echo(f"✓ '{word}' is correct")
        else:
            click.echo(f"✗ '{word}' is not found in dictionary")
            
            # TODO: Add suggestion functionality when implemented
                    
    except Exception as e:
        click.echo(f"Error checking word: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output file for corrected text"
)
@click.option(
    "--dictionary", 
    "-d", 
    type=click.Path(exists=True),
    help="Path to dictionary file"
)
def file(input_file: str, output: Optional[str], dictionary: Optional[str]) -> None:
    """Check spelling of text from a file."""
    try:
        # Read input file
        text = IOService.read_text_file(input_file)
        
        # Initialize pipeline
        dict_obj = Dictionary()
        if dictionary:
            dict_obj.load_dictionary(dictionary)
        
        pipeline = SpellCheckPipeline(dictionary=dict_obj)
        
        # Check text
        result = pipeline.check_text(text)
        
        # Write output
        if output:
            IOService.write_text_file(output, result["processed_text"])
            click.echo(f"Corrected text written to: {output}")
        else:
            click.echo("Corrected text:")
            click.echo(result["processed_text"])
        
        # Show summary
        click.echo(f"\nSummary:")
        click.echo(f"  Total words: {result['total_words']}")
        click.echo(f"  Incorrect words: {result['incorrect_count']}")
        
        if result["incorrect_words"]:
            click.echo("  Incorrect words found:")
            for word_info in result["incorrect_words"]:
                click.echo(f"    - {word_info['original']}")
                
    except Exception as e:
        click.echo(f"Error processing file: {e}", err=True)
        sys.exit(1)


def _format_text_result(result: dict) -> str:
    """Format spell check result as text."""
    lines = [
        f"Original text: {result['original_text']}",
        f"Processed text: {result['processed_text']}",
        f"Total words: {result['total_words']}",
        f"Incorrect words: {result['incorrect_count']}",
    ]
    
    if result["incorrect_words"]:
        lines.append("\nIncorrect words:")
        for word_info in result["incorrect_words"]:
            lines.append(f"  - {word_info['original']} (case: {word_info['case']})")
            if word_info["suggestions"]:
                lines.append(f"    Suggestions: {', '.join(word_info['suggestions'])}")
    
    return "\n".join(lines)


if __name__ == "__main__":
    main()