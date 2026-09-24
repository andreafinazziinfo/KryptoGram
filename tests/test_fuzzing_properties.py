"""Property-Based Testing & Chaos Fuzzing Suite per KryptoGram.

Implementa test invarianti su proprietà matematiche e fuzzing su input estremi
conforme ai requisiti di certificazione del Framework Operativo (Pilastro 6 1_DESIGN).
"""

from __future__ import annotations
import os
import random
import string
import pytest
from nexa_lib import italian_to_nexa, nexa_to_italian, validate_nexa
from nexa_crypto_v2 import (
    pack_nxs2_envelope,
    unpack_nxs2_envelope,
    KDFProfile,
)


def generate_natural_text(length: int) -> str:
    """Genera testo naturale casuale con lettere latine, numeri, punteggiatura ed emoji (senza delimitatori raw)."""
    charset = (
        string.ascii_letters
        + string.digits
        + " ,.;:!?'-"
        + "àèéìòùÀÈÉÌÒÙ"
        + "🚀📈💡🛡️"
        + "\t\n"
    )
    return "".join(random.choice(charset) for _ in range(length))


def generate_wild_unicode(length: int) -> str:
    """Genera caratteri arbitrari inclusi simboli matematici e delimitatori grezzi per test di robustezza a crash."""
    charset = (
        string.ascii_letters
        + string.digits
        + string.punctuation
        + " "
        + "àèéìòù"
        + "⟦⟧⟪⟫∴⇒≥≤%⊕≋∿⊙∪⊓⌁∆ƒ⅁⊥⌯⋔⋒⌐⌿≈↑"
        + "🚀🔥📈💡🛡️"
    )
    return "".join(random.choice(charset) for _ in range(length))


# ------------------------------------------------------------------------------
# Invariante 1: Robustezza del Motore Fonetico contro Crash (Zero-Exception)
# ------------------------------------------------------------------------------
@pytest.mark.parametrize("iteration", range(10))
def test_property_phonetic_fuzzing_no_crash(iteration: int) -> None:
    """Qualsiasi stringa arbitraria non deve mai causare eccezioni non gestite nel parser."""
    rnd_len = random.randint(0, 300)
    sample_text = generate_wild_unicode(rnd_len)

    glyphs = italian_to_nexa(sample_text, wrap_blocks=True)
    assert isinstance(glyphs, str)

    # Validatore a stack non deve mai andare in crash
    is_valid, errors = validate_nexa(glyphs)
    assert isinstance(is_valid, bool)
    assert isinstance(errors, list)

    reversed_text = nexa_to_italian(glyphs)
    assert isinstance(reversed_text, str)


# ------------------------------------------------------------------------------
# Invariante 2: Bilanciamento Sintattico Garantito su Testo Naturale
# ------------------------------------------------------------------------------
@pytest.mark.parametrize("iteration", range(10))
def test_property_natural_text_always_valid_syntax(iteration: int) -> None:
    """Il testo naturale traslitterato dal motore produce sempre sintassi valida con blocchi bilanciati."""
    sample = generate_natural_text(random.randint(1, 200))
    glyphs = italian_to_nexa(sample, wrap_blocks=True)

    is_valid, errors = validate_nexa(glyphs)
    assert is_valid is True, f"Sintassi non bilanciata su: {glyphs} (Errori: {errors})"


# ------------------------------------------------------------------------------
# Invariante 3: Integrità Roundtrip Lossless su Dati Arbitrari
# ------------------------------------------------------------------------------
@pytest.mark.parametrize("profile", [KDFProfile.DESKTOP_VAULT, KDFProfile.MOBILE_TERMINAL])
def test_property_lossless_roundtrip_invariant(profile: KDFProfile) -> None:
    """Qualsiasi testo in chiaro cifrato con lossless metadata deve essere ripristinato in modo identico al bit."""
    for _ in range(3):
        sample = generate_natural_text(random.randint(10, 150))
        passphrase = "".join(random.choices(string.ascii_letters + string.digits, k=14))

        envelope = pack_nxs2_envelope(
            payload_data=sample.encode("utf-8"),
            passphrase=passphrase,
            target_pad=1024,
            lossless_orig_text=sample,
            profile=profile,
        )

        dec_bytes, metadata = unpack_nxs2_envelope(envelope, passphrase)
        assert dec_bytes == sample.encode("utf-8")
        assert metadata.get("orig") == sample


# ------------------------------------------------------------------------------
# Invariante 4: Chaos Testing (Zero-Tolerance Tampering con Bit-Flip)
# ------------------------------------------------------------------------------
def test_property_chaos_bit_flips() -> None:
    """Qualsiasi mutazione di un bit nel ciphertext deve causare rifiuto categorico AEAD."""
    original_payload = b"CycleLab Confidential Trading Parameters"
    passphrase = "ChaosVerificationPassphrase2026!"
    envelope = bytearray(pack_nxs2_envelope(original_payload, passphrase, target_pad=1024))

    ciphertext_start = 46
    for _ in range(10):
        tampered = bytearray(envelope)
        flip_pos = random.randint(ciphertext_start, len(tampered) - 1)
        bit_pos = random.randint(0, 7)
        tampered[flip_pos] ^= (1 << bit_pos)

        with pytest.raises(Exception):
            unpack_nxs2_envelope(bytes(tampered), passphrase)


# ------------------------------------------------------------------------------
# Invariante 5: Idempotenza della Decifratura (Pilastro 5 1_DESIGN)
# ------------------------------------------------------------------------------
def test_property_idempotency_zero_side_effect() -> None:
    """Invocazioni ripetute sulla stessa busta devono restituire esattamente lo stesso output."""
    sample = b"DatiIdempotentiCycleLab"
    passphrase = "IdempotentPassphrase2026!"
    envelope = pack_nxs2_envelope(sample, passphrase, target_pad=1024)

    first_res, first_meta = unpack_nxs2_envelope(envelope, passphrase)
    for _ in range(5):
        res, meta = unpack_nxs2_envelope(envelope, passphrase)
        assert res == first_res
        assert meta["h"] == first_meta["h"]
