"""Central Suggestion Engine for FurlanSpellChecker.

Phase 1 scope:
- Phonetic cluster retrieval (system dictionary only)
- System error corrections integration
- Frequency weighting
- Elision / apostrophe prefixed variants (l'/la, d'/di, un'/une)
- Case classification & normalization
- Hyphen handling (basic split & recombination)
- Ranking: weight constants / frequency > edit distance > Friulian sort

Deferred (placeholders):
- User dictionary integration
- User errors integration
- Radix tree edit-distance-1 suggestions

Design notes:
- Weight constants reflect an internal priority ladder; future tiers (user dict, radix) can be inserted without renumbering existing ones.
- Dependencies are injected (database manager, phonetic algorithm) to simplify testing.
- Returned list is already ranked, unique and truncated to *max_suggestions*.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, List, Dict, Set, Tuple, Optional

from ..phonetic.furlan_phonetic import FurlanPhoneticAlgorithm
from ..database import DatabaseManager, DictionaryType

# -----------------------------
# Weight Constants
# -----------------------------
# Priority ladder (current + future placeholders):
# 1. User exception (1000)      [deferred]
# 2. Exact same lowercase (400)
# 3. User dictionary (350)      [deferred]
# 4. System errors (300)
# 5. Radix edit distance (freq) [deferred]
# 6. System phonetic (freq)
# Numeric values chosen to leave gaps for future insertion without rewrites.

F_USER_EXC = 1000  # placeholder for future
F_SAME = 400
F_USER_DICT = 350   # placeholder for future
F_ERRS = 300
# Radix suggestions will use frequency directly in future.

@dataclass
class Candidate:
    word: str
    base_weight: int
    distance: int
    original_freq: int

class CaseClass(Enum):
    LOWER = 1
    UCFIRST = 2
    UPPER = 3

class SuggestionEngine:
    def __init__(
        self,
        db_manager: DatabaseManager,
        phonetic: Optional[FurlanPhoneticAlgorithm] = None,
        max_suggestions: int = 10,
    ) -> None:
        self.db = db_manager
        self.phonetic = phonetic or FurlanPhoneticAlgorithm()
        self.max_suggestions = max_suggestions
        # Simple cache for frequency lookups
        self._freq_cache: Dict[str, int] = {}

    # -------- Public API --------
    def suggest(self, word: str) -> List[str]:
        """
        Generate spelling suggestions following COF's exact algorithm.
        
        COF Priority Order (from SpellChecker.pm _basic_suggestions):
        5. Phonetic suggestions (system dict) + frequency
        4. Phonetic suggestions (user dict) + frequency  
        3. RadixTree suggestions + frequency
        2. System error corrections (no frequency)
        1. User error corrections (no frequency)
        
        Special handling for apostrophes (d', un', l') and hyphens.
        """
        if not word:
            return []

        case_class = self._classify_case(word)
        lower_word = word.lower()
        
        # Build suggestions dictionary following COF logic
        suggestions = self._cof_basic_suggestions(word, lower_word, case_class)
        
        # Handle special cases like COF's _build_suggestions
        suggestions = self._cof_handle_apostrophes(word, lower_word, case_class, suggestions)
        suggestions = self._cof_handle_hyphens(word, suggestions)
        
        # Rank and return like COF's suggest method
        return self._cof_rank_suggestions(suggestions, case_class)

    # -------- COF Algorithm Implementation --------
    def _cof_basic_suggestions(self, word: str, lower_word: str, case_class: CaseClass) -> Dict[str, List]:
        """
        Implement COF's _basic_suggestions method exactly.
        
        Returns dictionary: {suggestion_word: [frequency_or_weight, distance]}
        """
        suggestions = {}
        temp_candidates = {}  # COF's %sugg hash
        
        # Get phonetic codes
        code_a, code_b = self.phonetic.get_phonetic_hashes_by_word(lower_word)
        
        # 1. Phonetic suggestions (system dict) - priority 5
        phonetic_sys = self._get_phonetic_candidates(lower_word)
        for word_candidate in phonetic_sys:
            temp_candidates[word_candidate] = 5
            
        # 2. Phonetic suggestions (user dict) - priority 4 
        try:
            user_phonetic = self.db.key_value_db.get_user_dictionary_suggestions(lower_word, max_suggestions=50)
            for word_candidate in user_phonetic:
                if word_candidate and word_candidate not in temp_candidates:
                    temp_candidates[word_candidate] = 4
        except Exception:
            pass
        
        # 3. RadixTree suggestions - priority 3  
        try:
            radix_suggestions = self.db.radix_tree.get_suggestions(lower_word, max_suggestions=50)
            for word_candidate in radix_suggestions:
                if word_candidate and word_candidate not in temp_candidates:
                    temp_candidates[word_candidate] = 3
        except Exception:
            pass
            
        # 4. System error corrections - priority 2
        try:
            error_correction = self.db.error_db.get_error_correction(word)
            if error_correction:
                temp_candidates[error_correction] = 2
        except (FileNotFoundError, AttributeError):
            # Fallback to old method
            error_corrections = self._get_error_corrections(word)
            for correction in error_corrections:
                temp_candidates[correction] = 2
        
        # 5. User error corrections - priority 1 (highest priority)
        try:
            user_correction = self.db.key_value_db.find_in_user_errors_database(word)
            if user_correction:
                temp_candidates[user_correction] = 1
        except Exception:
            pass
        
        # Convert to COF's final format: {word: [frequency_or_weight, distance]}
        for candidate, priority in temp_candidates.items():
            fixed_candidate = self._apply_case(case_class, candidate)
            
            if fixed_candidate not in suggestions:
                candidate_lower = candidate.lower()
                
                # Calculate values like COF
                if lower_word == candidate_lower:
                    # Exact match gets F_SAME weight
                    vals = [F_SAME, 1]
                elif priority == 1:
                    # User exceptions
                    vals = [F_USER_EXC, 0] 
                elif priority == 2:
                    # System errors
                    vals = [F_ERRS, 0]
                elif priority == 3:
                    # RadixTree - use frequency + edit distance 1
                    frequency = self._get_frequency(candidate)
                    vals = [frequency, 1]
                elif priority == 4:
                    # User dict - use F_USER_DICT + levenshtein
                    distance = self._levenshtein(lower_word, candidate_lower)
                    vals = [F_USER_DICT, distance]
                else:  # priority == 5
                    # System phonetic - use frequency + levenshtein
                    frequency = self._get_frequency(candidate)
                    distance = self._levenshtein(lower_word, candidate_lower)
                    vals = [frequency, distance]
                
                suggestions[fixed_candidate] = vals
                
        return suggestions
    
    def _cof_handle_apostrophes(self, word: str, lower_word: str, case_class: CaseClass, 
                               base_suggestions: Dict[str, List]) -> Dict[str, List]:
        """
        Handle apostrophe contractions like COF's _build_suggestions.
        
        Handles d', un', l' patterns exactly like COF.
        """
        suggestions = base_suggestions.copy()
        
        # Handle d' prefix (pos=2)
        if len(lower_word) > 2 and lower_word.startswith("d'"):
            suffix_word = word[2:]
            suffix_lower = lower_word[2:]
            
            # Create answer object for suffix
            suffix_suggestions = self._cof_basic_suggestions(suffix_word, suffix_lower, self._classify_case(suffix_word))
            
            # Determine case for 'di'
            if case_class == CaseClass.UPPER:
                prefix = 'DI '
            elif case_class == CaseClass.UCFIRST or (len(word) > 0 and word[0].isupper()):
                prefix = 'Di '
            else:
                prefix = 'di '
                
            # Add combined suggestions
            for suffix_candidate, vals in suffix_suggestions.items():
                combined = prefix + suffix_candidate
                # Increment distance by 1 as per COF
                suggestions[combined] = [vals[0], vals[1] + 1]
        
        # Handle un' prefix (pos=3) 
        elif len(lower_word) > 3 and lower_word.startswith("un'"):
            suffix_word = word[3:]
            suffix_lower = lower_word[3:]
            
            suffix_suggestions = self._cof_basic_suggestions(suffix_word, suffix_lower, self._classify_case(suffix_word))
            
            # Determine case for 'une'
            if case_class == CaseClass.UPPER:
                prefix = 'UNE '
            elif case_class == CaseClass.UCFIRST or (len(word) > 0 and word[0].isupper()):
                prefix = 'Une '
            else:
                prefix = 'une '
                
            for suffix_candidate, vals in suffix_suggestions.items():
                combined = prefix + suffix_candidate
                suggestions[combined] = [vals[0], vals[1] + 1]
        
        # Handle l' prefix (pos=2) - MOST COMPLEX CASE
        elif len(lower_word) > 2 and lower_word.startswith("l'"):
            suffix_word = word[2:]
            suffix_lower = lower_word[2:]
            
            suffix_suggestions = self._cof_basic_suggestions(suffix_word, suffix_lower, self._classify_case(suffix_word))
            
            # Determine case for prefixes
            if case_class == CaseClass.UPPER:
                prefix_ap = "L'"     # l' apostrophe form
                prefix_no_ap = 'LA ' # la non-apostrophe form
            elif case_class == CaseClass.UCFIRST or (len(word) > 0 and word[0].isupper()):
                prefix_ap = "L'"
                prefix_no_ap = 'La '
            else:
                prefix_ap = "l'"
                prefix_no_ap = 'la '
            
            # For each suffix candidate, decide l' vs la based on elision
            for suffix_candidate, vals in suffix_suggestions.items():
                frequency, distance = vals
                
                # Get the dictionary form for elision check (3rd element in COF)
                dict_form = suffix_candidate.lower()
                
                # Check if word supports elision using ElisionDatabase
                try:
                    has_elision = self.db.elision_db.has_elision(dict_form)
                except (FileNotFoundError, AttributeError):
                    # Fallback: assume no elision if database not available
                    has_elision = False
                
                # Choose prefix based on elision rule
                prefix = prefix_ap if has_elision else prefix_no_ap
                combined = prefix + suffix_candidate
                
                # Distance increases by 1 as per COF
                suggestions[combined] = [frequency, distance + 1]
        
        return suggestions

    def _add_radix_edit_distance_candidates(self, lower_word: str, candidates: Dict[str, Candidate]):
        """Add edit-distance-1 suggestions using RadixTree, matching COF's get_rt_sugg method.
        
        Uses the binary RadixTree to find all words within edit distance 1 of the input word.
        This directly matches COF's RadixTree implementation for maximum compatibility.
        """
        if not lower_word:
            return
        
        try:
            # Get suggestions from the RadixTree database
            radix_suggestions = self.db.radix_tree.get_suggestions(lower_word, max_suggestions=50)
            
            for suggestion in radix_suggestions:
                if suggestion and suggestion not in candidates:
                    # COF uses base_weight=3 for RadixTree suggestions  
                    candidates[suggestion] = Candidate(
                        word=suggestion,
                        base_weight=3,  # COF RadixTree priority level
                        distance=1,     # Edit distance is always 1
                        original_freq=self._get_frequency(suggestion),
                    )
                    
        except Exception:
            # If RadixTree fails, fall back to basic edit-distance algorithm
            # This ensures the system remains functional even with RadixTree issues
            pass

    # -------- Core Steps --------
    def _get_phonetic_candidates(self, lower_word: str) -> Set[str]:
        h1, h2 = self.phonetic.get_phonetic_hashes_by_word(lower_word)
        words: Set[str] = set()
        
        # Original logic: search in system database (words.db)
        sys_a = self.db.sqlite_db.find_in_system_database(h1)
        if sys_a:
            words.update(sys_a.split(","))
        if h2 != h1:
            sys_b = self.db.sqlite_db.find_in_system_database(h2)
            if sys_b:
                words.update(sys_b.split(","))
        
        # COF-compatible logic: also search in frequency database for phonetically similar words
        frequency_words = self._get_frequency_phonetic_candidates(lower_word, h1, h2)
        words.update(frequency_words)
        
        return {w for w in words if w}

    def _get_frequency_phonetic_candidates(self, lower_word: str, h1: str, h2: str) -> Set[str]:
        """Find phonetically similar words in frequency database (COF-compatible behavior)."""
        words: Set[str] = set()
        
        try:
            # Get all words from frequency database and check phonetic compatibility
            import sqlite3
            from pathlib import Path
            
            # Get frequency database path from database manager
            cache_dir = self.db._cache_dir
            freq_db_path = cache_dir / "frequencies" / "frequencies.sqlite"
            
            if not freq_db_path.exists():
                return words
            
            with sqlite3.connect(freq_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT Key FROM Data WHERE Value IS NOT NULL AND Key != ''")
                all_words = [row[0] for row in cursor.fetchall()]
            
            # Check each word for phonetic compatibility
            for word in all_words:
                if not word or len(word) < 2:
                    continue
                    
                try:
                    word_h1, word_h2 = self.phonetic.get_phonetic_hashes_by_word(word)
                    
                    # COF-style compatibility: exact match or prefix match
                    if (h1 == word_h1 or h1 == word_h2 or h2 == word_h1 or h2 == word_h2 or
                        # Prefix compatibility (like fYl6 matches fYl65, fYl657, etc.)
                        (len(h1) >= 3 and len(word_h1) >= 3 and 
                         (h1.startswith(word_h1) or word_h1.startswith(h1))) or
                        (len(h1) >= 3 and len(word_h2) >= 3 and 
                         (h1.startswith(word_h2) or word_h2.startswith(h1))) or
                        (len(h2) >= 3 and len(word_h1) >= 3 and 
                         (h2.startswith(word_h1) or word_h1.startswith(h2))) or
                        (len(h2) >= 3 and len(word_h2) >= 3 and 
                         (h2.startswith(word_h2) or word_h2.startswith(h2)))):
                        
                        words.add(word)
                        
                except Exception:
                    continue
                    
        except Exception as e:
            # If frequency database access fails, return empty set
            pass
            
        return words

    def _get_error_corrections(self, word: str) -> List[str]:
        """Get error corrections using the new ErrorDatabase."""
        results: List[str] = []
        try:
            # Use the new ErrorDatabase class for corrections
            correction = self.db.error_db.get_error_correction(word)
            if correction and correction != word:
                results.append(correction)
        except (FileNotFoundError, AttributeError):
            # Fall back to old method if new database isn't available
            variations = [word, word.lower(), word.capitalize(), word.upper()]
            seen = set()
            for v in variations:
                if v in seen:
                    continue
                seen.add(v)
                cor = self.db.sqlite_db.find_in_system_errors_database(v)
                if cor:
                    results.append(cor)
        return results

    def _get_frequency(self, word: str) -> int:
        if word in self._freq_cache:
            return self._freq_cache[word]
        try:
            # Use the new FrequencyDatabase class
            freq = self.db.frequency_db.get_frequency(word)
            if freq is None:
                freq = 0
        except (FileNotFoundError, AttributeError):
            # Fall back to old method if new database isn't available
            try:
                freq = self.db.sqlite_db.find_in_frequencies_database(word)
                if freq is None:
                    freq = 0
            except FileNotFoundError:
                freq = 0
        self._freq_cache[word] = int(freq)
        return self._freq_cache[word]

    # -------- Case Handling --------
    def _classify_case(self, word: str) -> CaseClass:
        if word.isupper():
            return CaseClass.UPPER
        if len(word) > 1 and word[0].isupper() and word[1:].islower():
            return CaseClass.UCFIRST
        return CaseClass.LOWER

    def _apply_case(self, case_class: CaseClass, word: str) -> str:
        if case_class == CaseClass.LOWER:
            return word.lower()
        if case_class == CaseClass.UCFIRST:
            return word[:1].upper() + word[1:].lower()
        return word.upper()

    # -------- Apostrophes / Elisions --------
    def _expand_apostrophe_variants(
        self,
        original: str,
        case_class: CaseClass,
        candidates: Dict[str, Candidate],
    ) -> None:
        lower_original = original.lower()
        # Patterns similar to COF: d' / un' / l'
        prefix_map = {
            "d'": "di ",
            "un'": "une ",
            "l'": "la ",
        }
        for ap, expanded in prefix_map.items():
            if lower_original.startswith(ap) and len(lower_original) > len(ap):
                suffix = lower_original[len(ap):]
                # If suffix is a candidate base word, build two variants depending on elision rule
                # Check elision DB: if suffix is elidable keep l' variant else expanded form
                if ap == "l'":
                    try:
                        elidable = self.db.elision_db.has_elision(suffix)
                    except (FileNotFoundError, AttributeError):
                        # If elision database isn't available, assume not elidable
                        elidable = False
                    if elidable:
                        # ensure original elided form ranks properly (prefer elided if exists)
                        norm = lower_original
                        if norm not in candidates:
                            candidates[norm] = Candidate(
                                word=self._apply_case(case_class, lower_original),
                                base_weight=F_SAME,
                                distance=0,
                                original_freq=self._get_frequency(suffix),
                            )
                        # also add expanded variant (slightly lower base weight)
                        expanded_form = expanded + suffix
                        norm_exp = expanded_form.lower()
                        if norm_exp not in candidates:
                            candidates[norm_exp] = Candidate(
                                word=self._apply_case(case_class, expanded_form),
                                base_weight=0,
                                distance=1,
                                original_freq=self._get_frequency(suffix),
                            )
                    else:
                        # Only expanded form credible
                        expanded_form = expanded + suffix
                        norm_exp = expanded_form.lower()
                        if norm_exp not in candidates:
                            candidates[norm_exp] = Candidate(
                                word=self._apply_case(case_class, expanded_form),
                                base_weight=0,
                                distance=1,
                                original_freq=self._get_frequency(suffix),
                            )
                else:
                    expanded_form = expanded + suffix
                    norm_exp = expanded_form.lower()
                    if norm_exp not in candidates:
                        candidates[norm_exp] = Candidate(
                            word=self._apply_case(case_class, expanded_form),
                            base_weight=0,
                            distance=1,
                            original_freq=self._get_frequency(suffix),
                        )

    # -------- Hyphen Handling (basic) --------
    def _expand_hyphen_variants(self, original: str, candidates: Dict[str, Candidate]) -> None:
        if '-' not in original:
            return
        parts = [p for p in original.split('-') if p]
        if len(parts) != 2:
            return  # basic phase only handles bi-part
        left, right = parts
        # Fetch phonetic candidates separately
        left_cands = self._get_phonetic_candidates(left.lower())
        right_cands = self._get_phonetic_candidates(right.lower())
        for lc in left_cands:
            for rc in right_cands:
                combo = f"{lc} {rc}"  # mimic COF space suggestion style
                norm = combo.lower()
                if norm not in candidates:
                    distance = self._levenshtein(original.lower().replace('-', ''), norm.replace(' ', ''))
                    candidates[norm] = Candidate(
                        word=combo,
                        base_weight=0,
                        distance=distance,
                        original_freq=min(self._get_frequency(lc), self._get_frequency(rc)),
                    )

    # -------- Ranking --------
    def _rank_candidates(
        self,
        lower_word: str,
        case_class: CaseClass,
        candidates: Dict[str, Candidate],
    ) -> List[str]:
        # Adjust words to correct case
        adjusted: List[Tuple[str, Candidate]] = []
        for norm, cand in candidates.items():
            adjusted.append((norm, cand))

        # Compose final score: base_weight primary, then original_freq, then negative distance
        # Sorting: base_weight desc, original_freq desc, distance asc, friulian sort
        def friulian_key(w: str) -> str:
            # Lightweight normalization similar to COF::sort_friulian
            trans_table = str.maketrans({
                'à': 'a', 'á': 'a', 'â': 'a',
                'è': 'e', 'é': 'e', 'ê': 'e',
                'ì': 'i', 'í': 'i', 'î': 'i',
                'ò': 'o', 'ó': 'o', 'ô': 'o',
                'ù': 'u', 'ú': 'u', 'û': 'u',
                'ç': 'c'
            })
            w2 = w.translate(trans_table)
            if w2.startswith("'s"):
                w2 = 's' + w2[2:]
            return w2

        # COF-compatible sorting: 
        # - base_weight (error corrections) has absolute priority
        # - when base_weight is equal, distance has priority over frequency
        # - exact matches (distance=0) should come first regardless of frequency
        adjusted.sort(
            key=lambda kv: (
                -kv[1].base_weight,     # Error corrections first
                kv[1].distance,         # Then by edit distance (0 = exact match)
                -kv[1].original_freq,   # Then by frequency (higher first)
                friulian_key(kv[0]),    # Finally friulian alphabetical sort
            )
        )
        # Apply case after ordering
        out: List[str] = []
        seen_out = set()
        for norm, cand in adjusted:
            cased = self._apply_case(case_class, cand.word)
            if cased not in seen_out:
                out.append(cased)
                seen_out.add(cased)
        return out

    # -------- Levenshtein (reuse phonetic component) --------
    def _levenshtein(self, a: str, b: str) -> int:
        return self.phonetic.levenshtein(a, b)

    # -------- Word validation --------
    def _is_valid_word(self, word: str) -> bool:
        """Check if a word exists in any of the databases."""
        if not word:
            return False
        
        # Check in system database via phonetic hash (fastest check)
        try:
            h1, h2 = self.phonetic.get_phonetic_hashes_by_word(word)
            sys_words = self.db.sqlite_db.find_in_system_database(h1)
            if sys_words and word in sys_words.split(","):
                return True
            if h2 != h1:
                sys_words = self.db.sqlite_db.find_in_system_database(h2)
                if sys_words and word in sys_words.split(","):
                    return True
        except Exception:
            pass
        
        # Check in frequency database (using new FrequencyDatabase)
        try:
            freq = self.db.frequency_db.get_frequency(word)
            if freq > 0:
                return True
        except (FileNotFoundError, AttributeError):
            # Fall back to old method
            try:
                freq = self.db.sqlite_db.find_word_frequency(word)
                if freq is not None and freq > 0:
                    return True
            except Exception:
                pass
        
        return False

    # -------- Enhanced Database Methods (COF Integration) --------
    def _add_elision_candidates(self, word: str, candidates: Dict[str, Candidate]) -> None:
        """Add elision-based candidates using ElisionDatabase.
        
        Adds variants like l'/la, d'/di, un'/une based on elision rules.
        Equivalent to COF's elision handling logic.
        """
        lower_word = word.lower()
        
        try:
            # Get elision candidates from the database
            elision_candidates = self.db.elision_db.get_elision_candidates(lower_word)
            
            for candidate in elision_candidates:
                if candidate and candidate not in candidates:
                    # Calculate edit distance
                    distance = self._levenshtein(lower_word, candidate.lower())
                    
                    # Elision variants get moderate priority (between errors and phonetic)
                    base_weight = 250 if candidate.lower() != lower_word else F_SAME
                    
                    candidates[candidate.lower()] = Candidate(
                        word=candidate,
                        base_weight=base_weight,
                        distance=distance,
                        original_freq=self._get_frequency(candidate),
                    )
                    
        except (FileNotFoundError, AttributeError):
            # If ElisionDatabase not available, fall back to basic logic
            pass

    def _add_error_pattern_candidates(self, word: str, candidates: Dict[str, Candidate]) -> None:
        """Add error pattern correction candidates using ErrorDatabase.
        
        Finds corrections for common Friulian spelling errors.
        Equivalent to COF's error pattern matching.
        """
        try:
            # Get error correction from the database
            correction = self.db.error_db.get_error_correction(word)
            
            if correction and correction != word:
                lower_correction = correction.lower()
                lower_word = word.lower()
                
                if lower_correction not in candidates:
                    distance = self._levenshtein(lower_word, lower_correction)
                    
                    # Error corrections get high priority
                    base_weight = F_ERRS if lower_correction != lower_word else F_SAME
                    
                    candidates[lower_correction] = Candidate(
                        word=correction,
                        base_weight=base_weight,
                        distance=distance,
                        original_freq=self._get_frequency(correction),
                    )
                    
        except (FileNotFoundError, AttributeError):
            # If ErrorDatabase not available, fall back to existing logic
            pass

    def rank_suggestions_by_frequency(self, suggestions: List[str]) -> List[Tuple[str, int]]:
        """Rank suggestions by frequency score using FrequencyDatabase.
        
        Args:
            suggestions: List of word suggestions
            
        Returns:
            List of (word, frequency) tuples sorted by frequency
        """
        try:
            return self.db.frequency_db.rank_suggestions(suggestions)
        except (FileNotFoundError, AttributeError):
            # Fall back to basic frequency lookup
            ranked = []
            for suggestion in suggestions:
                frequency = self._get_frequency(suggestion)
                ranked.append((suggestion, frequency))
            
            # Sort by frequency (descending) then alphabetically
            ranked.sort(key=lambda x: (-x[1], x[0]))
            return ranked
    
    def _cof_handle_hyphens(self, word: str, suggestions: Dict[str, List]) -> Dict[str, List]:
        """
        Handle hyphenated words like COF's hyphen logic.
        """
        if "-" not in word:
            return suggestions
            
        # Split on first hyphen only
        parts = word.split("-", 1)
        if len(parts) != 2:
            return suggestions
            
        left_word, right_word = parts
        
        # Get suggestions for both parts
        left_lower = left_word.lower()
        right_lower = right_word.lower()
        
        left_suggestions = self._cof_basic_suggestions(left_word, left_lower, self._classify_case(left_word))
        right_suggestions = self._cof_basic_suggestions(right_word, right_lower, self._classify_case(right_word))
        
        # Combine all possibilities
        for left_candidate, left_vals in left_suggestions.items():
            for right_candidate, right_vals in right_suggestions.items():
                combined = f"{left_candidate} {right_candidate}"
                # Add frequencies and distances
                combined_vals = [
                    left_vals[0] + right_vals[0],  # frequency sum
                    left_vals[1] + right_vals[1]   # distance sum
                ]
                suggestions[combined] = combined_vals
        
        return suggestions
    
    def _cof_rank_suggestions(self, suggestions: Dict[str, List], case_class: CaseClass) -> List[str]:
        """
        Rank suggestions exactly like COF's suggest method.
        
        COF ranking: distance=0 matches first (phonetic equivalence), then by frequency desc, 
        then by distance asc, then friulian sort.
        """
        if not suggestions:
            return []
            
        # Convert to COF's format for sorting
        words_list = list(suggestions.keys())
        
        # Sort using COF's friulian sort (basic for now)
        words_list = self._friulian_sort(words_list)
        
        # Build COF's peso structure: {distance: {frequency: [indices]}}
        # COF prioritizes distance=0 matches (phonetic equivalence) above all else
        peso = {}
        
        for idx, word in enumerate(words_list):
            frequency, distance = suggestions[word]
            
            if distance not in peso:
                peso[distance] = {}
            if frequency not in peso[distance]:
                peso[distance][frequency] = []
                
            peso[distance][frequency].append(idx)
        
        # Sort exactly like COF: distance asc (phonetic matches first), then frequency desc
        ranked_words = []
        
        for dist in sorted(peso.keys()):              # distance ascending (0 first)
            for freq in sorted(peso[dist].keys(), reverse=True):  # frequency descending
                for idx in peso[dist][freq]:
                    ranked_words.append(words_list[idx])
        
        return ranked_words[:self.max_suggestions]
    
    def _friulian_sort(self, words: List[str]) -> List[str]:
        """
        Basic Friulian sort (placeholder - COF has more complex logic).
        """
        # For now, just use standard sort - can enhance later with COF's sort_friulian
        return sorted(words, key=str.lower)
