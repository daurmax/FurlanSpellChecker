"""Tests with reference values from original Perl phalg_furlan logic."""
from furlan_spellchecker.phonetic import FurlanPhoneticAlgorithm

cases = [
    # Original test cases - values from REAL Perl phalg_furlan execution
    ("cjatâ", ("A696", "c7696")),  # Note: accented chars may show as ├ó in terminal but work correctly
    ("'savote", ("A6v897", "E6v897")),
    ("çavatis", ("ç6v6AA", "ç6v697E")),  # ç preserved, not converted to A
    ("diretamentri", ("I7r79O", "Er79O")),
    ("sdrumâ", ("A9r856", "E9r856")),
    ("rinfuarçadis", ("r75fYç697A", "r75fYç6EE")),  # ç preserved
    ("marilenghe", ("527X7", "527X7")),
    ("mandi", ("56597", "56597")),
    ("dindi", ("I7597", "E597")),
    
    # Additional comprehensive test cases from Perl reference
    ("gjat", ("g769", "E69")),
    ("fuee", ("f87", "f87")),
    ("ai", ("6", "6")),
    ("ei", ("7", "7")),
    ("ou", ("8", "8")),
    ("oi", ("8", "8")),
    ("vu", ("8", "8")),
    ("tane", ("H657", "H657")),
    ("dane", ("I657", "I657")),
    ("bat", ("b69", "b69")),
    ("bad", ("b69", "b69")),
    ("cjjar", ("A2", "c72")),
    ("fuje", ("f877", "f877")),
    ("che", ("A", "c7")),
    ("sciençe", ("A75ç7", "E775ç7")),  # ç preserved in output - KEY DIFFERENCE
    ("leng", ("X", "X")),
    ("lingu", ("X", "X")),
    ("amentri", ("O", "O")),
    ("ementi", ("O", "O")),
    ("uintri", ("W", "W")),
    ("ontra", ("W", "W")),
    ("ur", ("Y", "Y")),
    ("uar", ("Y", "Y")),
    ("or", ("Y", "Y")),
    ("'s", ("A", "E")),
    ("'n", ("5", "5")),
    ("ins", ("1", "1")),
    ("in", ("1", "1")),
    ("mn", ("5", "5")),
    ("nm", ("5", "5")),
    ("m", ("5", "5")),
    ("n", ("5", "5")),
    ("er", ("2", "2")),
    ("ar", ("2", "2")),
    ("colegb", ("A8l7g3", "c8l7E3")),
    ("stopp", ("A983", "E983")),
    ("altrev", ("6l9r74", "6l9r74")),
    ("altref", ("6l9r74", "6l9r74")),
]

def test_phonetic_hashes_ported():
    algo = FurlanPhoneticAlgorithm()
    for word, expected in cases:
        calculated = algo.get_phonetic_hashes_by_word(word)
        assert calculated == expected, f"Mismatch for {word}: expected {expected}, got {calculated}"