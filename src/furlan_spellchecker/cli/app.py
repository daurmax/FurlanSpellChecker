"""Command-line interface for FurlanSpellChecker."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Optional

import click

from ..services import SpellCheckPipeline, IOService
from ..dictionary import Dictionary


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
    # Initialize pipeline
    dict_obj = Dictionary()
    if dictionary:
        dict_obj.load_dictionary(dictionary)
    
    pipeline = SpellCheckPipeline(dictionary=dict_obj)
    
    # Check word
    try:
        result = asyncio.run(pipeline.check_word(word))
        
        if result["is_correct"]:
            click.echo(f"✓ '{word}' is correct")
        else:
            click.echo(f"✗ '{word}' is not found in dictionary")
            
            if result["suggestions"]:
                click.echo("Suggestions:")
                for suggestion in result["suggestions"]:
                    click.echo(f"  - {suggestion}")
                    
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