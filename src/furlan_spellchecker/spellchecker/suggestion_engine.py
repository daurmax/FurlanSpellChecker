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
        if not word:
            return []

        case_class = self._classify_case(word)
        lower_word = word.lower()

        # 1. Phonetic cluster (system only for now)
        phonetic_candidates = self._get_phonetic_candidates(lower_word)

        # 2. System error direct corrections
        error_corrections = self._get_error_corrections(word)

        # 3. Build candidate objects
        candidates: Dict[str, Candidate] = {}

        # Add error corrections (highest among implemented tiers except SAME)
        for corr in error_corrections:
            norm = corr.lower()
            distance = self._levenshtein(lower_word, norm)
            candidates[norm] = Candidate(
                word=corr,
                base_weight=F_ERRS if norm != lower_word else F_SAME,
                distance=distance,
                original_freq=self._get_frequency(corr),
            )

        # Add phonetic cluster words
        for w in phonetic_candidates:
            norm = w.lower()
            if norm not in candidates:
                base = F_SAME if norm == lower_word else 0
                distance = self._levenshtein(lower_word, norm)
                candidates[norm] = Candidate(
                    word=w,
                    base_weight=base,
                    distance=distance,
                    original_freq=self._get_frequency(w),
                )

        # 4. Apostrophe / elision handling expansions
        self._expand_apostrophe_variants(word, case_class, candidates)

        # 5. Hyphen handling
        self._expand_hyphen_variants(word, candidates)

        # 6. RadixTree edit-distance-1 suggestions (COF compatibility)
        self._add_radix_edit_distance_candidates(lower_word, candidates)

        # 6. Ranking & ordering
        ranked = self._rank_candidates(lower_word, case_class, candidates)
        return ranked[: self.max_suggestions]

    # -------- Placeholders for future integration --------
    def _add_user_dictionary_candidates(self, *args, **kwargs):  # pragma: no cover
        # To be implemented: integrate user dictionary clusters
        raise NotImplementedError("User dictionary integration not implemented yet")

    def _add_user_error_corrections(self, *args, **kwargs):  # pragma: no cover
        raise NotImplementedError("User error corrections not implemented yet")

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
        results: List[str] = []
        # Try exact + case variants similar to COF logic
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
                        elidable = self.db.sqlite_db.has_elisions(suffix)
                    except FileNotFoundError:
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
        
        # Check in frequency database
        try:
            freq = self.db.sqlite_db.find_word_frequency(word)
            if freq is not None and freq > 0:
                return True
        except Exception:
            pass
        
        return False
