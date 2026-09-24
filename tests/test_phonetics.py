"""Unit test suite per il motore fonetico NEXA-S (nexa_lib.py)."""

from nexa_lib import (
    italian_to_nexa,
    nexa_to_italian,
    validate_nexa,
    normalize_text,
    VOWEL_MAP,
    CONSONANT_MAP,
)


def test_vowel_transliteration() -> None:
    """Verifica che tutte le vocali vengano correttamente traslitterate."""
    for char, glyph in VOWEL_MAP.items():
        if len(char) == 1 and char.isalpha():
            res = italian_to_nexa(char, wrap_blocks=False)
            assert glyph in res


def test_consonant_transliteration() -> None:
    """Verifica la mappatura delle consonanti standard."""
    sample = "b d f l m n p r s t z"
    nexa = italian_to_nexa(sample, wrap_blocks=False)
    for c in ["⊓", "∆", "ƒ", "⌯", "⋔", "⋒", "⌐", "⌿", "≈", "⊥", "↑"]:
        assert c in nexa


def test_digraphs_priority() -> None:
    """Verifica che i digrammi italiani prioritari abbiano precedenza sui singoli grafemi."""
    assert "⌁" in italian_to_nexa("chiave", wrap_blocks=False)
    assert "⅁⋒" in italian_to_nexa("gnomo", wrap_blocks=False)
    assert "⌁∪" in italian_to_nexa("quota", wrap_blocks=False)


def test_numbers_encapsulation() -> None:
    """Verifica che le cifre numeriche vengano racchiuse tra ⟪...⟫."""
    res = italian_to_nexa("Ore 18:30 con 10%", wrap_blocks=False)
    assert "⟪18⟫" in res
    assert "⟪30⟫" in res or "⟪30.⟫" in res or "18:30" in res


def test_block_syntax_validation() -> None:
    """Verifica il validatore di delimitatori a stack."""
    valid_text = "⟦∧⋒∆⌿≋⊕⟧ ⟪42⟫ ∴"
    ok, errors = validate_nexa(valid_text)
    assert ok is True
    assert len(errors) == 0

    invalid_text = "⟦∧⋒∆⌿≋⊕ ⟪42⟫"
    ok_inv, errors_inv = validate_nexa(invalid_text)
    assert ok_inv is False
    assert len(errors_inv) > 0


def test_reverse_transliteration_phonetic() -> None:
    """Verifica la decodifica fonetica da glifi a testo approssimato."""
    original = "andrea conferma"
    nexa = italian_to_nexa(original, wrap_blocks=False)
    back = nexa_to_italian(nexa)
    assert "andrea" in back
    assert "conferma" in back


def test_dynamic_alphabet_deterministic_permutation() -> None:
    """Verifica che la derivazione dinamica sia deterministica e sensibile alla chiave."""
    from nexa_lib import derive_dynamic_alphabet
    fwd_a1, rev_a1 = derive_dynamic_alphabet("SecretKeyA")
    fwd_a2, rev_a2 = derive_dynamic_alphabet("SecretKeyA")
    fwd_b, rev_b = derive_dynamic_alphabet("SecretKeyB")

    # Stessa chiave -> stessa permutazione
    assert fwd_a1 == fwd_a2
    assert rev_a1 == rev_a2

    # Chiave diversa -> permutazione diversa
    assert fwd_a1 != fwd_b
    assert rev_a1 != rev_b

    # Biiezione completa (26 lettere mappate a 26 glifi distinti)
    assert len(set(rev_a1.keys())) == 26
    assert len(set(rev_a1.values())) == 26


def test_dynamic_alphabet_roundtrip_and_wrong_key_defense() -> None:
    """Verifica che la decodifica funzioni solo con la chiave corretta e fallisca con chiave errata."""
    original = "ordine buy btc a 65000"
    encoded_correct = italian_to_nexa(original, wrap_blocks=False, alphabet_key="CycleLabKey2026")
    decoded_correct = nexa_to_italian(encoded_correct, alphabet_key="CycleLabKey2026")

    # Con la chiave corretta il testo viene ripristinato
    assert "ordine" in decoded_correct
    assert "buy" in decoded_correct
    assert "btc" in decoded_correct
    assert "65000" in decoded_correct

    # Con chiave errata il risultato è incomprensibile (difesa Kerckhoffs)
    decoded_wrong = nexa_to_italian(encoded_correct, alphabet_key="AttackerKey999")
    assert decoded_wrong != decoded_correct
    assert "ordine" not in decoded_wrong

