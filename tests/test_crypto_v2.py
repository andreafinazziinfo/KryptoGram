"""Unit test suite per il modulo crittografico v2.0 (nexa_crypto_v2.py)."""

import os
import pytest
from nexa_crypto_v2 import (
    derive_key_argon2id,
    encrypt_xchacha20,
    decrypt_xchacha20,
    generate_x25519_keypair,
    generate_ed25519_keypair,
    sign_data,
    verify_signature,
    hash_blake3,
    KDFProfile,
    secure_zero,
)


def test_kdf_dual_profiles():
    """Verifica che sia il profilo Desktop che quello Mobile derivino chiavi a 32 byte."""
    salt = os.urandom(16)
    passphrase = "UltraSecureKey123!"

    key_desktop = derive_key_argon2id(passphrase, salt, profile=KDFProfile.DESKTOP_VAULT)
    key_mobile = derive_key_argon2id(passphrase, salt, profile=KDFProfile.MOBILE_TERMINAL)

    assert len(key_desktop) == 32
    assert len(key_mobile) == 32


def test_aead_roundtrip():
    """Verifica cifratura e decifratura autenticata AEAD."""
    key = os.urandom(32)
    nonce = os.urandom(24)
    plaintext = b"Messaggio riservato per il nodo quantitativo CycleLab"
    aad = b"CYCLELAB-AUTH"

    ciphertext = encrypt_xchacha20(plaintext, key, nonce, aad=aad)
    decrypted = decrypt_xchacha20(ciphertext, key, nonce, aad=aad)

    assert decrypted == plaintext


def test_aead_chaos_bit_flip_tampering():
    """Test Chaos & Resilience (Pilastro 6 1_DESIGN): manomissione di 1 bit causa rifiuto immediato."""
    key = os.urandom(32)
    nonce = os.urandom(24)
    plaintext = b"Payload da verificare contro manomissioni"
    aad = b"TEST"

    ciphertext = bytearray(encrypt_xchacha20(plaintext, key, nonce, aad=aad))
    # Manometti un bit a caso
    ciphertext[len(ciphertext) // 2] ^= 0x01

    with pytest.raises(Exception):
        decrypt_xchacha20(bytes(ciphertext), key, nonce, aad=aad)


def test_ed25519_signatures():
    """Verifica generazione, firma e verifica con Ed25519."""
    verify_key, signing_key = generate_ed25519_keypair()
    payload = b"Trade Signal: BUY BTC 65000 @ Pivot S1"

    signed_msg = sign_data(signing_key, payload)
    verified = verify_signature(verify_key, signed_msg)

    assert verified == payload


def test_x25519_keypair():
    """Verifica generazione chiavi asimmetriche X25519."""
    pub, priv = generate_x25519_keypair()
    assert len(pub) == 32
    assert len(priv) >= 32


def test_secure_zero():
    """Verifica la bonifica di sicurezza dei buffer di memoria sensibili."""
    buf = bytearray(b"ChiaveSegretissimaInMemoriaRAM")
    secure_zero(buf)
    assert all(b == 0 for b in buf)
