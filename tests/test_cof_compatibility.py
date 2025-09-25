#!/usr/bin/env python3
"""
Test FurlanSpellChecker compatibility with COF reference results.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Any

class CompatibilityTester:
    def __init__(self):
        self.results = []
        
    def test_word_check(self, word: str) -> Dict[str, Any]:
        """Test word checking."""
        try:
            import os
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            
            result = subprocess.run([
                sys.executable, "-m", "furlan_spellchecker", "lookup", word
            ], capture_output=True, text=True, encoding='utf-8', 
               env=env, cwd=Path.cwd())
            
            # Parse the output to determine if word is correct
            is_correct = "✓" in result.stdout or "found in dictionary" in result.stdout.lower()
            
            return {
                "word": word,
                "is_correct": is_correct,
                "output": result.stdout.strip(),
                "error": result.stderr.strip() if result.stderr else None
            }
        except Exception as e:
            return {
                "word": word,
                "is_correct": False,
                "output": "",
                "error": str(e)
            }
    
    def test_word_suggestions(self, word: str) -> List[str]:
        """Test word suggestions."""
        try:
            import os
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            
            result = subprocess.run([
                sys.executable, "-m", "furlan_spellchecker", "suggest", word
            ], capture_output=True, text=True, encoding='utf-8',
               env=env, cwd=Path.cwd())
            
            # Parse suggestions from output
            suggestions = []
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if line.strip().startswith('- '):
                    suggestions.append(line.strip()[2:])
                elif line.strip() and not any(x in line.lower() for x in ['suggestions', 'for', ':']):
                    suggestions.append(line.strip())
            
            return suggestions
        except Exception as e:
            return []
    
    def test_words_from_file(self, word_file: Path) -> List[Dict[str, Any]]:
        """Test all words from a file."""
        results = []
        
        with open(word_file, 'r', encoding='utf-8') as f:
            words = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
        
        print(f"🔍 Testing {len(words)} words with FurlanSpellChecker...")
        
        for i, word in enumerate(words):
            print(f"Progress: {(i+1)/len(words)*100:.1f}% ({i+1}/{len(words)}) - Testing: {word}")
            
            # Test word checking
            check_result = self.test_word_check(word)
            
            # Test suggestions if word is incorrect
            suggestions = []
            if not check_result["is_correct"]:
                suggestions = self.test_word_suggestions(word)
            
            result = {
                "word": word,
                "is_correct": check_result["is_correct"],
                "suggestions": suggestions,
                "check_output": check_result["output"],
                "check_error": check_result["error"]
            }
            
            results.append(result)
        
        return results
    
    def save_results(self, results: List[Dict[str, Any]], output_file: Path):
        """Save test results."""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "metadata": {
                    "total_words": len(results),
                    "correct_words": sum(1 for r in results if r["is_correct"]),
                    "words_with_suggestions": sum(1 for r in results if r["suggestions"])
                },
                "results": results
            }, f, indent=2, ensure_ascii=False)
    
    def compare_with_reference(self, results: List[Dict[str, Any]], reference_file: Path):
        """Compare with COF reference results."""
        with open(reference_file, 'r', encoding='utf-8') as f:
            reference_data = json.load(f)
        
        # Handle COF ground truth format: {word: {is_correct: bool, suggestions: []}, ...}
        if isinstance(reference_data, dict):
            reference_results = reference_data
        else:
            reference_results = {r["word"]: r for r in reference_data["results"]}
        
        matches = 0
        mismatches = []
        
        for result in results:
            word = result["word"]
            if word in reference_results:
                ref_result = reference_results[word]
                
                # Compare correctness
                if result["is_correct"] == ref_result["is_correct"]:
                    matches += 1
                else:
                    mismatches.append({
                        "word": word,
                        "furlan_correct": result["is_correct"],
                        "cof_correct": ref_result["is_correct"],
                        "furlan_suggestions": result["suggestions"],
                        "cof_suggestions": ref_result["suggestions"]
                    })
        
        print(f"\n🎯 Compatibility Results:")
        print(f"✅ Matches: {matches}/{len(results)} ({matches/len(results)*100:.1f}%)")
        print(f"❌ Mismatches: {len(mismatches)}")
        
        if mismatches:
            print(f"\n🔍 First 5 mismatches:")
            for mismatch in mismatches[:5]:
                print(f"  📝 {mismatch['word']}:")
                print(f"    FurlanSpellChecker: {mismatch['furlan_correct']}")
                print(f"    COF Reference: {mismatch['cof_correct']}")
        
        return matches, mismatches

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_compatibility.py <word_file>")
        sys.exit(1)
    
    word_file = Path(sys.argv[1])
    tester = CompatibilityTester()
    
    # Test words
    results = tester.test_words_from_file(word_file)
    
    # Save results
    output_file = Path("tests/results/furlan_spellchecker_results.json")
    tester.save_results(results, output_file)
    print(f"\n💾 Results saved to: {output_file}")
    
    # Compare with reference if available
    reference_file = Path("tests/results/cof_reference_results.json")
    if reference_file.exists():
        matches, mismatches = tester.compare_with_reference(results, reference_file)
        
        # Save comparison
        comparison_file = Path("tests/results/compatibility_comparison.json")
        with open(comparison_file, 'w', encoding='utf-8') as f:
            json.dump({
                "summary": {
                    "total_words": len(results),
                    "matches": matches,
                    "mismatches": len(mismatches),
                    "compatibility_rate": matches / len(results) * 100
                },
                "mismatches": mismatches
            }, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Comparison saved to: {comparison_file}")
    
    print("\n🎉 Compatibility testing completed!")