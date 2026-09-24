"""Unit test suite per il motore fonetico NEXA-S (nexa_lib.py)."""

from nexa_lib import (
    italian_to_nexa,
    nexa_to_italian,
    validate_nexa,
    normalize_text,
    VOWEL_MAP,
    CONSONANT_MAP,
)


def test_vowel_transliteration():
    """Verifica che tutte le vocali vengano correttamente traslitterate."""
    for char, glyph in VOWEL_MAP.items():
        if len(char) == 1 and char.isalpha():
            res = italian_to_nexa(char, wrap_blocks=False)
            assert glyph in res


def test_consonant_transliteration():
    """Verifica la mappatura delle consonanti standard."""
    sample = "b d f l m n p r s t z"
    nexa = italian_to_nexa(sample, wrap_blocks=False)
    for c in ["⊓", "∆", "ƒ", "⌯", "⋔", "⋒", "⌐", "⌿", "≈", "⊥", "↑"]:
        assert c in nexa


def test_digraphs_priority():
    """Verifica che i digrammi italiani prioritari abbiano precedenza sui singoli grafemi."""
    assert "⌁" in italian_to_nexa("chiave", wrap_blocks=False)
    assert "⅁⋒" in italian_to_nexa("gnomo", wrap_blocks=False)
    assert "⌁∪" in italian_to_nexa("quota", wrap_blocks=False)


def test_numbers_encapsulation():
    """Verifica che le cifre numeriche vengano racchiuse tra ⟪...⟫."""
    res = italian_to_nexa("Ore 18:30 con 10%", wrap_blocks=False)
    assert "⟪18⟫" in res
    assert "⟪30⟫" in res or "⟪30.⟫" in res or "18:30" in res


def test_block_syntax_validation():
    """Verifica il validatore di delimitatori a stack."""
    valid_text = "⟦∧⋒∆⌿≋⊕⟧ ⟪42⟫ ∴"
    ok, errors = validate_nexa(valid_text)
    assert ok is True
    assert len(errors) == 0

    invalid_text = "⟦∧⋒∆⌿≋⊕ ⟪42⟫"
    ok_inv, errors_inv = validate_nexa(invalid_text)
    assert ok_inv is False
    assert len(errors_inv) > 0


def test_reverse_transliteration_phonetic():
    """Verifica la decodifica fonetica da glifi a testo approssimato."""
    original = "andrea conferma"
    nexa = italian_to_nexa(original, wrap_blocks=False)
    back = nexa_to_italian(nexa)
    assert "andrea" in back
    assert "conferma" in back
