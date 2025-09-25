#!/usr/bin/env python3
"""
Generate ground truth results using COF Perl script.

This script takes the test cases and runs them through the actual COF 
spell checker to get the real reference results for compatibility validation.
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import time

class SimpleColorManager:
    """Simple color output manager."""
    
    def info(self, text): return f"[INFO] {text}"
    def success(self, text): return f"[OK] {text}" 
    def error(self, text): return f"[ERROR] {text}"
    def warning(self, text): return f"[WARN] {text}"
    def header(self, text): return f"=== {text} ==="
    def accent(self, text): return text


class COFGroundTruthGenerator:
    """Generator for COF reference results."""
    
    def __init__(self, workspace_root: Path):
        """Initialize the generator.
        
        Args:
            workspace_root: Root directory of the workspace
        """
        self.workspace_root = workspace_root
        self.color_manager = SimpleColorManager()
        
        # Paths
        self.test_data_dir = workspace_root / "tests" / "data" / "generated"
        # COF is in the same workspace level
        self.cof_script_path = workspace_root / "COF" / "script" / "cof_oo_cli.pl"
        
        # Results storage
        self.results_cache = {}
        
    def load_test_cases(self, test_file: Optional[Path] = None) -> List[Dict[str, Any]]:
        """Load test cases from JSON file.
        
        Args:
            test_file: Path to test file (defaults to latest generated)
            
        Returns:
            List of test cases
        """
        if test_file is None:
            # Find the latest test file
            json_files = list(self.test_data_dir.glob("test_cases_*.json"))
            if not json_files:
                raise FileNotFoundError("No test case files found")
            
            test_file = max(json_files, key=lambda p: p.stat().st_mtime)
        
        print(self.color_manager.info(f"Loading test cases from: {test_file.name}"))
        
        with open(test_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return data['test_cases']
    
    def check_cof_availability(self) -> bool:
        """Check if COF Perl script is available.
        
        Returns:
            True if COF script exists and is accessible
        """
        if not self.cof_script_path.exists():
            print(self.color_manager.error(f"COF script not found at: {self.cof_script_path}"))
            print(self.color_manager.info("Expected path: COF/script/cof_oo_cli.pl"))
            return False
        
        # Test if perl is available
        try:
            result = subprocess.run(['perl', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                print(self.color_manager.error("Perl not found or not working"))
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print(self.color_manager.error("Perl not available in system PATH"))
            return False
        
        print(self.color_manager.success("COF script and Perl are available"))
        return True
    
    def run_cof_on_word(self, word: str) -> Tuple[bool, List[str]]:
        """Run COF spell checker on a single word using STDIN protocol.
        
        Args:
            word: Word to check
            
        Returns:
            Tuple of (is_correct, suggestions_list)
        """
        if word in self.results_cache:
            return self.results_cache[word]
        
        try:
            # COF CLI protocol via STDIN:
            # Input: "s <word>\nq\n" (suggest command + quit)
            # Output: "ok" or "no\t<suggestions>"
            
            cmd = [
                'perl', '-I', str(self.cof_script_path.parent.parent / 'lib'),
                str(self.cof_script_path)
            ]
            
            # Prepare input for COF
            cof_input = f"s {word}\nq\n"
            
            # Set up environment with proper PATH for Strawberry Perl
            env = os.environ.copy()
            strawberry_paths = [
                "C:\\Strawberry\\perl\\bin",
                "C:\\Strawberry\\c\\bin"
            ]
            for path in strawberry_paths:
                if path not in env.get('PATH', ''):
                    env['PATH'] = env.get('PATH', '') + f";{path}"
            
            result = subprocess.run(
                cmd, 
                input=cof_input,
                capture_output=True, 
                text=True, 
                timeout=10,
                encoding='utf-8',
                cwd=str(self.cof_script_path.parent.parent),
                env=env
            )
            
            if result.returncode != 0:
                print(self.color_manager.warning(f"COF error for word '{word}': {result.stderr}"))
                return (False, [])
            
            # Parse COF output
            cof_output = result.stdout.strip()
            is_correct = False
            suggestions = []
            
            if cof_output:
                lines = cof_output.split('\n')
                for line in lines:
                    line = line.strip()
                    if line == 'ok':
                        is_correct = True
                        suggestions = []
                        break
                    elif line.startswith('no') and '\t' in line:
                        is_correct = False
                        # Split by tab and get suggestions part
                        parts = line.split('\t', 1)
                        if len(parts) > 1:
                            suggestions_part = parts[1]
                            if suggestions_part:
                                suggestions = [s.strip() for s in suggestions_part.split(',') if s.strip()]
                        break
                    elif line == 'no':
                        is_correct = False
                        suggestions = []
                        break
            
            # Cache result
            self.results_cache[word] = (is_correct, suggestions)
            return (is_correct, suggestions)
            
        except subprocess.TimeoutExpired:
            print(self.color_manager.warning(f"Timeout processing word: {word}"))
            return (False, [])
        except Exception as e:
            print(self.color_manager.warning(f"Error processing word '{word}': {e}"))
            return (False, [])
    
    def generate_ground_truth_batch(self, test_cases: List[Dict[str, Any]], 
                                   batch_size: int = 50) -> Dict[str, Dict[str, Any]]:
        """Generate ground truth results for test cases in batches.
        
        Args:
            test_cases: List of test cases
            batch_size: Number of words to process per batch
            
        Returns:
            Dictionary mapping word -> {is_correct, suggestions}
        """
        print(self.color_manager.info("Generating ground truth results using COF..."))
        
        ground_truth = {}
        total_words = len(test_cases)
        processed = 0
        
        start_time = time.time()
        
        for i in range(0, total_words, batch_size):
            batch = test_cases[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_words + batch_size - 1) // batch_size
            
            print(self.color_manager.info(f"Processing batch {batch_num}/{total_batches}..."))
            
            for test_case in batch:
                word = test_case['word']
                
                # Skip empty or problematic words
                if not word or len(word.strip()) == 0:
                    processed += 1
                    continue
                
                # Get COF results
                is_correct, suggestions = self.run_cof_on_word(word)
                
                ground_truth[word] = {
                    'is_correct': is_correct,
                    'suggestions': suggestions
                }
                
                processed += 1
                
                # Progress update
                if processed % 10 == 0:
                    elapsed = time.time() - start_time
                    progress = (processed / total_words) * 100
                    print(f"Progress: {progress:.1f}% ({processed}/{total_words}) - {elapsed:.1f}s elapsed")
        
        elapsed_total = time.time() - start_time
        print(self.color_manager.success(f"Generated ground truth for {len(ground_truth)} words in {elapsed_total:.1f}s"))
        
        return ground_truth
    
    def update_test_cases_with_ground_truth(self, test_cases: List[Dict[str, Any]], 
                                          ground_truth: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Update test cases with ground truth results.
        
        Args:
            test_cases: Original test cases
            ground_truth: Ground truth results from COF
            
        Returns:
            Updated test cases with real expected results
        """
        print(self.color_manager.info("Updating test cases with ground truth results..."))
        
        updated_cases = []
        matched = 0
        
        for test_case in test_cases:
            word = test_case['word']
            
            # Create updated test case
            updated_case = test_case.copy()
            
            if word in ground_truth:
                gt = ground_truth[word]
                updated_case['expected_correct'] = gt['is_correct']
                updated_case['expected_suggestions'] = gt['suggestions']
                matched += 1
            else:
                # Keep original (likely null) values if no ground truth available
                pass
            
            updated_cases.append(updated_case)
        
        print(self.color_manager.success(f"Updated {matched} test cases with ground truth results"))
        
        return updated_cases
    
    def save_results(self, test_cases: List[Dict[str, Any]], 
                    ground_truth: Dict[str, Dict[str, Any]]) -> Path:
        """Save updated test cases with ground truth.
        
        Args:
            test_cases: Updated test cases
            ground_truth: Ground truth results
            
        Returns:
            Path to saved file
        """
        # Create output data structure
        output_data = {
            "metadata": {
                "generator": "COFGroundTruthGenerator",
                "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "total_test_cases": len(test_cases),
                "ground_truth_entries": len(ground_truth),
                "cof_script_path": str(self.cof_script_path)
            },
            "test_cases": test_cases
        }
        
        # Save updated test cases
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_path = self.test_data_dir / f"test_cases_with_ground_truth_{timestamp}.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        # Also save raw ground truth for reference
        ground_truth_path = self.test_data_dir / f"cof_ground_truth_{timestamp}.json"
        
        with open(ground_truth_path, 'w', encoding='utf-8') as f:
            json.dump(ground_truth, f, indent=2, ensure_ascii=False)
        
        print(self.color_manager.success(f"Results saved:"))
        print(f"  Test cases: {self.color_manager.accent(str(output_path))}")
        print(f"  Ground truth: {self.color_manager.accent(str(ground_truth_path))}")
        
        return output_path


async def main():
    """Main execution function."""
    workspace_root = Path(__file__).parent.parent  # Go up to c:\Progetti\Furlan
    
    # Initialize generator
    generator = COFGroundTruthGenerator(workspace_root)
    
    # Display banner
    print(generator.color_manager.header("COF Ground Truth Generator"))
    print("=" * 50)
    print()
    print(generator.color_manager.info("Generating reference results using COF Perl script"))
    print()
    
    try:
        # Check COF availability
        if not generator.check_cof_availability():
            print(generator.color_manager.error("Cannot proceed without COF script"))
            return 1
        
        # Load test cases
        test_cases = generator.load_test_cases()
        print(generator.color_manager.success(f"Loaded {len(test_cases)} test cases"))
        
        # Generate ground truth using COF
        ground_truth = generator.generate_ground_truth_batch(test_cases)
        
        # Update test cases with ground truth
        updated_test_cases = generator.update_test_cases_with_ground_truth(test_cases, ground_truth)
        
        # Save results
        output_path = generator.save_results(updated_test_cases, ground_truth)
        
        # Statistics
        correct_count = sum(1 for gt in ground_truth.values() if gt['is_correct'])
        incorrect_count = len(ground_truth) - correct_count
        
        with_suggestions = sum(1 for gt in ground_truth.values() if gt['suggestions'])
        
        print()
        print(generator.color_manager.header("Ground Truth Statistics:"))
        print(f"✅ Correct words: {generator.color_manager.success(str(correct_count))}")
        print(f"❌ Incorrect words: {generator.color_manager.error(str(incorrect_count))}")
        print(f"💭 Words with suggestions: {generator.color_manager.info(str(with_suggestions))}")
        print()
        print(generator.color_manager.success("🎉 Ground truth generation completed successfully!"))
        print()
        print(generator.color_manager.info("Next steps:"))
        print("1. Review generated ground truth results")
        print("2. Run validation suite with real COF reference data")
        print("3. Analyze compatibility and fix any issues")
        
        return 0
        
    except Exception as e:
        print(generator.color_manager.error(f"Ground truth generation failed: {e}"))
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import asyncio
    exit_code = asyncio.run(main())
    sys.exit(exit_code)