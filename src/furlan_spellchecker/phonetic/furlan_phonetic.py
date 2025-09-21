"""Friulian phonetic algorithm implementation (ported from C#)."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import List, Tuple

from ..core.interfaces import IPhoneticAlgorithm
from ..core.exceptions import PhoneticAlgorithmError


# Minimal vowel groups equivalent to FriulianConstants for Levenshtein costing.
VOWELS_A = {c: True for c in "aàáâ"}
VOWELS_E = {c: True for c in "eèéê"}
VOWELS_I = {c: True for c in "iìíî"}
VOWELS_O = {c: True for c in "oòóô"}
VOWELS_U = {c: True for c in "uùúû"}

UNCOMMON_APOSTROPHES_PATTERN = r"[’`´]"
SMALL_A_VARIANTS = r"[âäàáÄÁÂÀ]"
SMALL_E_VARIANTS = r"[éêëèÉÊËÈ]"
SMALL_I_VARIANTS = r"[ïîìíÍÎÏÌ]"
SMALL_O_VARIANTS = r"[ôöòóÓÔÒÖ]"
SMALL_U_VARIANTS = r"[ÚÙÛÜúûùü]"


class FurlanPhoneticAlgorithm(IPhoneticAlgorithm):
    """Friulian-specific phonetic algorithm for word similarity and hashing."""

    def get_phonetic_code(self, word: str) -> str:  # Backwards compatibility single hash
        if not word:
            return ""
        h1, _ = self.get_phonetic_hashes_by_word(word)
        return h1

    # Public API required by higher layers.
    def get_phonetic_hashes_by_word(self, word: str) -> tuple[str, str]:
        if not word:
            return "", ""
        try:
            prepared = self._prepare_original_word(word)
            return self._get_phonetic_hashes_by_original(prepared)
        except Exception as exc:  # pragma: no cover - defensive
            raise PhoneticAlgorithmError(f"Failed phonetic hashing for '{word}': {exc}") from exc

    def are_phonetically_similar(self, word1: str, word2: str) -> bool:
        if not word1 or not word2:
            return False
        h1a, h1b = self.get_phonetic_hashes_by_word(word1)
        h2a, h2b = self.get_phonetic_hashes_by_word(word2)
        return h1a == h2a or h1a == h2b or h1b == h2a or h1b == h2b

    # Region: direct ports of the C# logic -------------------------------------------------
    def _prepare_original_word(self, original: str) -> str:
        # Replace uncommon apostrophes with '
        original = re.sub(UNCOMMON_APOSTROPHES_PATTERN, "'", original)
        # Replace "e " with "'"
        original = re.sub(r"e ", "'", original)
        # Remove spaces
        original = re.sub(r" ", "", original)
        # Remove double letters (compress runs)
        compressed = []
        for ch in original:
            if not compressed or compressed[-1] != ch:
                compressed.append(ch)
        original = "".join(compressed)
        original = original.lower()
        original = re.sub(r"h'", "K", original)
        original = re.sub(SMALL_A_VARIANTS, "a", original)
        original = re.sub(SMALL_E_VARIANTS, "e", original)
        original = re.sub(SMALL_I_VARIANTS, "i", original)
        original = re.sub(SMALL_O_VARIANTS, "o", original)
        original = re.sub(SMALL_U_VARIANTS, "u", original)
        original = re.sub(r"çi", "ci", original)
        original = re.sub(r"çe", "ce", original)
        original = re.sub(r"ds$", "ts", original)
        original = re.sub(r"sci", "ssi", original)
        original = re.sub(r"sce", "se", original)
        original = re.sub(r" ", "", original)
        original = re.sub(r"w", "", original)
        original = re.sub(r"y", "", original)
        original = re.sub(r"x", "", original)
        original = re.sub(r"^che", "chi", original)
        original = re.sub(r"h", "", original)
        original = re.sub(r"leng", "X", original)
        original = re.sub(r"lingu", "X", original)
        original = re.sub(r"amentri", "O", original)
        original = re.sub(r"ementri", "O", original)
        original = re.sub(r"amenti", "O", original)
        original = re.sub(r"ementi", "O", original)
        original = re.sub(r"uintri", "W", original)
        original = re.sub(r"ontra", "W", original)
        original = re.sub(r"ur", "Y", original)
        original = re.sub(r"uar", "Y", original)
        original = re.sub(r"or", "Y", original)
        original = re.sub(r"^'s", "s", original)
        original = re.sub(r"^'n", "n", original)
        original = re.sub(r"ins$", "1", original)
        original = re.sub(r"in$", "1", original)
        original = re.sub(r"ims$", "1", original)
        original = re.sub(r"im$", "1", original)
        original = re.sub(r"gns$", "1", original)
        original = re.sub(r"gn$", "1", original)
        original = re.sub(r"mn", "5", original)
        original = re.sub(r"nm", "5", original)
        original = re.sub(r"[mn]", "5", original)
        original = re.sub(r"er", "2", original)
        original = re.sub(r"ar", "2", original)
        original = re.sub(r"b$", "3", original)
        original = re.sub(r"p$", "3", original)
        original = re.sub(r"v$", "4", original)
        original = re.sub(r"f$", "4", original)
        return original

    def _get_phonetic_hashes_by_original(self, original: str) -> tuple[str, str]:
        # Split into first and second hashes early, following Perl exactly
        primo = original
        secondo = original

        # FIRST HASH transformations (primo) - exact Perl order
        primo = re.sub(r"'c", "A", primo)
        primo = re.sub(r"c[ji]us$", "A", primo)
        primo = re.sub(r"c[ji]u$", "A", primo)
        primo = re.sub(r"c'", "A", primo)
        primo = re.sub(r"ti", "A", primo)
        primo = re.sub(r"ci", "A", primo)
        primo = re.sub(r"si", "A", primo)
        primo = re.sub(r"zs", "A", primo)
        primo = re.sub(r"zi", "A", primo)
        primo = re.sub(r"cj", "A", primo)
        primo = re.sub(r"çs", "A", primo)
        primo = re.sub(r"tz", "A", primo)
        primo = re.sub(r"z", "A", primo)
        # primo = re.sub(r"ç", "A", primo)  # REMOVED - Perl doesn't actually transform ç in test cases
        primo = re.sub(r"c", "A", primo)
        primo = re.sub(r"q", "A", primo)
        primo = re.sub(r"k", "A", primo)
        primo = re.sub(r"ts", "A", primo)
        primo = re.sub(r"s", "A", primo)

        # SECOND HASH transformations (secondo) - exact Perl order (NO ç->A!)
        secondo = re.sub(r"c$", "0", secondo)
        secondo = re.sub(r"g$", "0", secondo)
        secondo = re.sub(r"bs$", "s", secondo)
        secondo = re.sub(r"cs$", "s", secondo)
        secondo = re.sub(r"fs$", "s", secondo)
        secondo = re.sub(r"gs$", "s", secondo)
        secondo = re.sub(r"ps$", "s", secondo)
        secondo = re.sub(r"vs$", "s", secondo)
        
        secondo = re.sub(r"di(?=.)", "E", secondo)  # di followed by something
        secondo = re.sub(r"gji", "E", secondo)
        secondo = re.sub(r"gi", "E", secondo)
        secondo = re.sub(r"gj", "E", secondo)
        secondo = re.sub(r"g", "E", secondo)
        secondo = re.sub(r"ts", "E", secondo)
        secondo = re.sub(r"s", "E", secondo)
        secondo = re.sub(r"zi", "E", secondo)
        secondo = re.sub(r"z", "E", secondo)

        # j -> i conversion and squeeze consecutive i (exact Perl: tr/i/i/s)
        primo = re.sub(r"j", "i", primo)
        secondo = re.sub(r"j", "i", secondo)
        primo = re.sub(r"i+", "i", primo)
        secondo = re.sub(r"i+", "i", secondo)

        # VOWEL AND DIPHTHONG MAPPING - Exact Perl order: diphthongs first, then singles
        # Primo hash vowel mapping
        primo = re.sub(r"ai", "6", primo)
        primo = re.sub(r"ei", "7", primo)
        primo = re.sub(r"ou", "8", primo)
        primo = re.sub(r"oi", "8", primo)
        primo = re.sub(r"vu", "8", primo)
        primo = re.sub(r"a", "6", primo)
        primo = re.sub(r"e", "7", primo)
        primo = re.sub(r"o", "8", primo)
        primo = re.sub(r"u", "8", primo)
        primo = re.sub(r"i", "7", primo)

        # Secondo hash vowel mapping (identical)
        secondo = re.sub(r"ai", "6", secondo)
        secondo = re.sub(r"ei", "7", secondo)
        secondo = re.sub(r"ou", "8", secondo)
        secondo = re.sub(r"oi", "8", secondo)
        secondo = re.sub(r"vu", "8", secondo)
        secondo = re.sub(r"a", "6", secondo)
        secondo = re.sub(r"e", "7", secondo)
        secondo = re.sub(r"o", "8", secondo)
        secondo = re.sub(r"u", "8", secondo)
        secondo = re.sub(r"i", "7", secondo)

        # START-OF-WORD t/d -> H/I BEFORE general t/d -> 9 (exact Perl order)
        primo = re.sub(r"^t", "H", primo)
        primo = re.sub(r"^d", "I", primo)
        secondo = re.sub(r"^t", "H", secondo)
        secondo = re.sub(r"^d", "I", secondo)

        # General t/d -> 9
        primo = re.sub(r"t", "9", primo)
        primo = re.sub(r"d", "9", primo)
        secondo = re.sub(r"t", "9", secondo)
        secondo = re.sub(r"d", "9", secondo)

        return primo, secondo

    # Additional utilities (port) ----------------------------------------------------------
    def levenshtein(self, source: str, target: str) -> int:
        if source == target:
            return 0
        if not source:
            return len(target)
        if not target:
            return len(source)
        rows = len(source) + 1
        cols = len(target) + 1
        dist = [[0] * cols for _ in range(rows)]
        for i in range(rows):
            dist[i][0] = i
        for j in range(cols):
            dist[0][j] = j
        for i, sc in enumerate(source, start=1):
            for j, tc in enumerate(target, start=1):
                if sc == tc:
                    cost = 0
                else:
                    if not (
                        (sc in VOWELS_A and tc in VOWELS_A)
                        or (sc in VOWELS_E and tc in VOWELS_E)
                        or (sc in VOWELS_I and tc in VOWELS_I)
                        or (sc in VOWELS_O and tc in VOWELS_O)
                        or (sc in VOWELS_U and tc in VOWELS_U)
                    ):
                        cost = 1
                    else:
                        cost = 0
                dist[i][j] = min(
                    dist[i - 1][j] + 1,
                    dist[i][j - 1] + 1,
                    dist[i - 1][j - 1] + cost,
                )
        return dist[-1][-1]

    def sort_friulian(self, words: List[str]) -> List[str]:
        return sorted(words, key=self._translate_word_for_sorting)

    def _translate_word_for_sorting(self, word: str) -> str:
        original_chars = "0123456789âäàáÄÁÂÀAaBCçÇDéêëèÉÊËÈEeFGHïîìíÍÎÏÌIiJKLMNôöòóÓÔÒÖOoPQRSTÚÙÛÜúûùüuUVWXYZ"
        sorted_chars = "0123456789aaaaaaaaaabcccdeeeeeeeeeefghiiiiiiiiiijklmnoooooooooopqrstuuuuuuuuuuvwxyz"
        trans = []
        for c in word:
            idx = original_chars.find(c)
            trans.append(sorted_chars[idx] if idx >= 0 else c)
        return "".join(trans).replace("^'s", "s")


