"""Friulian phonetic algorithm implementation (exact port from COF Perl)."""

from __future__ import annotations

from typing import List, Tuple

from ..core.interfaces import IPhoneticAlgorithm


class FurlanPhoneticAlgorithm(IPhoneticAlgorithm):
    """Friulian phonetic algorithm - exact port of COF::Data::phalg_furlan from Perl"""
    
    def __init__(self):
        """Initialize the phonetic algorithm"""
        pass
    
    def _phalg_furlan(self, word: str) -> tuple[str, str]:
        """
        Exact port of COF::Data::phalg_furlan from Perl (lines 274-479)
        Returns: (primo_hash, secondo_hash)
        """
        if not word or word is None:
            return "", ""
            
        original = word
        
        # Step 1: Normalize apostrophes (exact Perl equivalent)
        # FUR_APOSTROPHS = "'\\x91\\x92\\x{2018}\\x{2019}"
        import re
        original = re.sub(r"[''`´′ʼʹ\x91\x92\u2018\u2019]+", "'", original)
        
        # Step 2: e → ' (only FIRST occurrence like Perl s/e /'/ without /g)
        original = re.sub(r"e ", "'", original, count=1)
        
        # Step 3: Remove only whitespace (replicates Perl refuso with $slash_W)
        # Perl: s/\s+|\$slash_W+//g removes whitespace and literal "$slash_W+" string
        original = re.sub(r"\s+|\$slash_W+", "", original)
        
        # Step 4: Character squeeze (tr/\0-\377//s equivalent)
        # Reduces consecutive identical characters to single occurrence
        original = re.sub(r"(.)\1+", r"\1", original, flags=re.DOTALL)
        
        # Step 5: Lowercase (after normalization like Perl)
        original = original.lower()
        
        # Step 2: Handle h' -> K
        original = original.replace("h'", "K")
        
        # Step 3: Normalize accented vowels
        original = original.replace("à", "a").replace("â", "a").replace("á", "a").replace("'a", "a")
        original = original.replace("è", "e").replace("ê", "e").replace("é", "e").replace("'e", "e")
        original = original.replace("ì", "i").replace("î", "i").replace("í", "i").replace("'i", "i")
        original = original.replace("ò", "o").replace("ô", "o").replace("ó", "o").replace("'o", "o")
        original = original.replace("ù", "u").replace("û", "u").replace("ú", "u").replace("'u", "u")
        
        # Step 4: Handle çi/çe
        original = original.replace("çi", "ci").replace("çe", "ce")
        
        # Step 5: Final consonant transformations
        original = re.sub(r'ds$', 'ts', original)
        original = original.replace("sci", "ssi").replace("sce", "se")
        
        # Character squeeze again (second tr/\0-\377//s in Perl)
        original = re.sub(r"(.)\1+", r"\1", original, flags=re.DOTALL)
        
        # Step 6: Remove w, y, x
        original = original.replace("w", "").replace("y", "").replace("x", "")
        
        # Step 7: Special transformations
        original = re.sub(r'^che', 'chi', original)
        original = original.replace("h", "")
        
        # Step 8: Special sequences
        original = original.replace("leng", "X").replace("lingu", "X")
        original = original.replace("amentri", "O").replace("ementri", "O")
        original = original.replace("amenti", "O").replace("ementi", "O")
        original = original.replace("uintri", "W").replace("ontra", "W")
        
        # Step 9: Handle ur/uar/or
        original = original.replace("ur", "Y").replace("uar", "Y").replace("or", "Y")
        
        # Step 10: Handle initial contractions
        original = re.sub(r"^'s", "s", original)
        original = re.sub(r"^'n", "n", original)
        
        # Step 11: Handle endings
        original = re.sub(r'ins$', '1', original)
        original = re.sub(r'in$', '1', original)
        original = re.sub(r'ims$', '1', original)
        original = re.sub(r'im$', '1', original)
        original = re.sub(r'gns$', '1', original)
        original = re.sub(r'gn$', '1', original)
        
        # Step 12: Handle m/n sounds
        original = original.replace("mn", "5").replace("nm", "5")
        original = re.sub(r'[mn]', '5', original)
        
        # Step 13: Handle er/ar
        original = original.replace("er", "2").replace("ar", "2")
        
        # Step 14: Final consonants
        original = re.sub(r'b$', '3', original)
        original = re.sub(r'p$', '3', original)
        original = re.sub(r'v$', '4', original)
        original = re.sub(r'f$', '4', original)
        
        # Copy for primo and secondo
        primo = secondo = original
        
        # Step 15: Primo transformations
        primo = primo.replace("'c", "A")
        primo = re.sub(r'c[ji]us$', 'A', primo)
        primo = re.sub(r'c[ji]u$', 'A', primo)
        primo = primo.replace("c'", "A")
        primo = primo.replace("ti", "A").replace("ci", "A").replace("si", "A")
        primo = primo.replace("zs", "A").replace("zi", "A").replace("cj", "A")
        primo = primo.replace("çs", "A").replace("tz", "A").replace("z", "A")
        primo = primo.replace("ç", "A").replace("c", "A").replace("q", "A")
        primo = primo.replace("k", "A").replace("ts", "A").replace("s", "A")
        
        # Step 16: Secondo transformations
        secondo = re.sub(r'c$', '0', secondo)
        secondo = re.sub(r'g$', '0', secondo)
        
        secondo = re.sub(r'bs$', 's', secondo)
        secondo = re.sub(r'cs$', 's', secondo)
        secondo = re.sub(r'fs$', 's', secondo)
        secondo = re.sub(r'gs$', 's', secondo)
        secondo = re.sub(r'ps$', 's', secondo)
        secondo = re.sub(r'vs$', 's', secondo)
        
        # Handle g/gj/gi transformations for secondo
        secondo = re.sub(r'di(?=.)', 'E', secondo)
        secondo = secondo.replace("gji", "E").replace("gi", "E").replace("gj", "E")
        secondo = secondo.replace("g", "E")
        
        secondo = secondo.replace("ts", "E").replace("s", "E")
        secondo = secondo.replace("zi", "E").replace("z", "E")
        
        # Step 17: Handle j -> i for both
        primo = primo.replace("j", "i")
        secondo = secondo.replace("j", "i")
        
        # Step 18: Remove consecutive i's
        primo = re.sub(r'i+', 'i', primo)
        secondo = re.sub(r'i+', 'i', secondo)
        
        # Step 19: Vowel transformations for primo
        primo = primo.replace("ai", "6").replace("a", "6")
        primo = primo.replace("ei", "7").replace("e", "7")
        primo = primo.replace("ou", "8").replace("oi", "8").replace("o", "8")
        primo = primo.replace("vu", "8").replace("u", "8")
        primo = primo.replace("i", "7")
        
        # Step 20: Vowel transformations for secondo
        secondo = secondo.replace("ai", "6").replace("a", "6")
        secondo = secondo.replace("ei", "7").replace("e", "7")
        secondo = secondo.replace("ou", "8").replace("oi", "8").replace("o", "8")
        secondo = secondo.replace("vu", "8").replace("u", "8")
        secondo = secondo.replace("i", "7")
        
        # Step 21: Initial t/d transformations for both
        primo = re.sub(r'^t', 'H', primo)
        primo = re.sub(r'^d', 'I', primo)
        primo = primo.replace("t", "9").replace("d", "9")
        
        secondo = re.sub(r'^t', 'H', secondo)
        secondo = re.sub(r'^d', 'I', secondo)
        secondo = secondo.replace("t", "9").replace("d", "9")
        
        return primo, secondo
    
    def get_phonetic_hashes_by_word(self, word: str) -> tuple[str, str]:
        """
        Get both phonetic hashes for a word
        Returns: (first_hash, second_hash)
        """
        return self._phalg_furlan(word)
    
    def get_phonetic_code(self, word: str) -> str:
        """
        Get primary phonetic code for a word (backwards compatibility)
        Returns: first phonetic hash only
        """
        first, _ = self._phalg_furlan(word)
        return first
    
    def are_phonetically_similar(self, word1: str, word2: str) -> bool:
        """Check if two words are phonetically similar"""
        if not word1 or not word2:
            return False
            
        hash1_1, hash1_2 = self._phalg_furlan(word1)
        hash2_1, hash2_2 = self._phalg_furlan(word2)
        
        return (hash1_1 == hash2_1) or (hash1_1 == hash2_2) or (hash1_2 == hash2_1) or (hash1_2 == hash2_2)
    
    def levenshtein(self, s1: str, s2: str) -> int:
        """
        Compute Levenshtein distance with Friulian character equivalences
        Perl-compatible: vowel↔vowel substitutions have cost 0
        """
        if not s1:
            return len(s2) if s2 else 0
        if not s2:
            return len(s1)
            
        # Friulian vowels (all variations)
        vowels = set('aeiouàáâèéêìíîòóôùúû')
        
        def is_vowel(c):
            return c.lower() in vowels
        
        def normalize_vowel(c):
            """Normalize accented vowels to base form"""
            vowel_map = {
                'à': 'a', 'á': 'a', 'â': 'a',
                'è': 'e', 'é': 'e', 'ê': 'e',
                'ì': 'i', 'í': 'i', 'î': 'i', 
                'ò': 'o', 'ó': 'o', 'ô': 'o',
                'ù': 'u', 'ú': 'u', 'û': 'u'
            }
            return vowel_map.get(c.lower(), c.lower())
        
        # Standard Levenshtein with Perl-compatible vowel costs
        if len(s1) < len(s2):
            return self.levenshtein(s2, s1)
            
        if len(s2) == 0:
            return len(s1)
            
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                
                # Perl-compatible substitution cost
                if c1.lower() == c2.lower():
                    # Identical characters
                    substitution_cost = 0
                elif is_vowel(c1) and is_vowel(c2):
                    # Vowel to vowel: cost 0 (Perl behavior)
                    substitution_cost = 0
                else:
                    # All other substitutions: cost 1
                    substitution_cost = 1
                
                substitutions = previous_row[j] + substitution_cost
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
            
        return previous_row[-1]
    
    def sort_friulian(self, words: List[str]) -> List[str]:
        """
        Sort words using Friulian alphabetical order
        """
        if not words:
            return []
            
        # Friulian alphabet order (simplified)
        friulian_order = {
            'a': 1, 'à': 1, 'á': 1, 'â': 1,
            'b': 2, 'c': 3, 'ç': 4, 'd': 5,
            'e': 6, 'è': 6, 'é': 6, 'ê': 6, 'ë': 6,
            'f': 7, 'g': 8, 'h': 9,
            'i': 10, 'ì': 10, 'í': 10, 'î': 10, 'ï': 10,
            'j': 11, 'k': 12, 'l': 13, 'm': 14, 'n': 15,
            'o': 16, 'ò': 16, 'ó': 16, 'ô': 16, 'ö': 16,
            'p': 17, 'q': 18, 'r': 19, 's': 20, 't': 21,
            'u': 22, 'ù': 22, 'ú': 22, 'û': 22, 'ü': 22,
            'v': 23, 'w': 24, 'x': 25, 'y': 26, 'z': 27
        }
        
        def sort_key(word):
            return [friulian_order.get(c.lower(), 999) for c in word.lower()]
        
        return sorted(words, key=sort_key)