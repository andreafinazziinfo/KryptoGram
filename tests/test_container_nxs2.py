"""Unit test suite per il contenitore NXS2 e lossless metadata."""

import pytest
from nexa_crypto_v2 import (
    pack_nxs2_envelope,
    unpack_nxs2_envelope,
    KDFProfile,
)


def test_nxs2_roundtrip_lossless():
    """Verifica packaging NXS2 con ripristino lossless ortografico."""
    orig_text = "Andrea conferma l'appuntamento per domani alle 18:30. Portare i documenti cifrati."
    payload = orig_text.encode("utf-8")
    passphrase = "PasswordDifficile2026!"

    envelope = pack_nxs2_envelope(
        payload_data=payload,
        passphrase=passphrase,
        target_pad=4096,
        lossless_orig_text=orig_text,
        profile=KDFProfile.MOBILE_TERMINAL,
    )

    dec_bytes, metadata = unpack_nxs2_envelope(envelope, passphrase)

    assert dec_bytes == payload
    assert metadata["orig"] == orig_text
    assert metadata["p"] == "mobile"
    assert metadata["v"] == 2


def test_nxs2_wrong_passphrase_rejection():
    """Verifica che una passphrase errata venga categoricamente respinta."""
    payload = b"Dati protetti"
    envelope = pack_nxs2_envelope(payload, "PassphraseCorretta", target_pad=1024)

    with pytest.raises(Exception):
        unpack_nxs2_envelope(envelope, "PassphraseSbagliata")


def test_legacy_nexa1_compatibility():
    """Verifica la retrocompatibilità automatica con buste NEXA1 create con v1.x."""
    from nexa_encrypt import encrypt_bytes

    payload = b"Messaggio creato con formato legacy NEXA1"
    passphrase = "LegacyKey2026"
    legacy_envelope = encrypt_bytes(payload, passphrase, target_pad=2048)

    # Il de-packager v2 deve riconoscerlo e decifrarlo senza errori
    dec_bytes, meta = unpack_nxs2_envelope(legacy_envelope, passphrase)
    assert dec_bytes == payload
    assert meta.get("legacy") is True
