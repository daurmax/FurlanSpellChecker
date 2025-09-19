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
        original = re.sub(r"çi", "ci", original)
        original = re.sub(r"çe", "ce", original)
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
        first_hash = original
        second_hash = original

        # first hash transformations (order matters)
        for pattern in [
            r"'c",
            r"c[ji]us$",
            r"c[ji]u$",
            r"c'",
            r"ti",
            r"ci",
            r"si",
            r"zs",
            r"zi",
            r"cj",
            r"çs",
            r"tz",
            r"z",
            r"ç",
            r"c",
            r"q",
            r"k",
            r"ts",
            r"s",
        ]:
            first_hash = re.sub(pattern, "A", first_hash)

        # second hash transformations
        second_hash = re.sub(r"c$", "0", second_hash)
        second_hash = re.sub(r"g$", "0", second_hash)
        for pattern, repl in [
            (r"bs$", "s"),
            (r"cs$", "s"),
            (r"fs$", "s"),
            (r"gs$", "s"),
            (r"ps$", "s"),
            (r"vs$", "s"),
        ]:
            second_hash = re.sub(pattern, repl, second_hash)
        for pattern in [
            r"di(?=.)",
            r"gji",
            r"gi",
            r"ge",
            r"de",
            r"te",
            r"ce",
            r"se",
            r"ze",
            r"je",
            r"ai",
            r"ei",
            r"oi",
            r"ui",
            r"y",
        ]:
            second_hash = re.sub(pattern, "E", second_hash)

        return first_hash, second_hash

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
