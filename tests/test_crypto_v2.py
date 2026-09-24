"""Unit test suite per il modulo crittografico KryptoGram."""

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
    generate_system_enclave_code,
    derive_dual_part_credential,
)


def test_kdf_dual_profiles() -> None:
    """Verifica che sia il profilo Desktop che quello Mobile derivino chiavi a 32 byte."""
    salt = os.urandom(16)
    passphrase = "UltraSecureKey123!"

    key_desktop = derive_key_argon2id(passphrase, salt, profile=KDFProfile.DESKTOP_VAULT)
    key_mobile = derive_key_argon2id(passphrase, salt, profile=KDFProfile.MOBILE_TERMINAL)

    assert len(key_desktop) == 32
    assert len(key_mobile) == 32


def test_aead_roundtrip() -> None:
    """Verifica cifratura e decifratura autenticata AEAD."""
    key = os.urandom(32)
    nonce = os.urandom(24)
    plaintext = b"Messaggio riservato per il nodo quantitativo CycleLab"
    aad = b"CYCLELAB-AUTH"

    ciphertext = encrypt_xchacha20(plaintext, key, nonce, aad=aad)
    decrypted = decrypt_xchacha20(ciphertext, key, nonce, aad=aad)

    assert decrypted == plaintext


def test_aead_chaos_bit_flip_tampering() -> None:
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


def test_ed25519_signatures() -> None:
    """Verifica generazione, firma e verifica con Ed25519."""
    verify_key, signing_key = generate_ed25519_keypair()
    payload = b"Trade Signal: BUY BTC 65000 @ Pivot S1"

    signed_msg = sign_data(signing_key, payload)
    verified = verify_signature(verify_key, signed_msg)

    assert verified == payload


def test_x25519_keypair() -> None:
    """Verifica generazione chiavi asimmetriche X25519."""
    pub, priv = generate_x25519_keypair()
    assert len(pub) == 32
    assert len(priv) >= 32


def test_secure_zero() -> None:
    """Verifica la bonifica di sicurezza dei buffer di memoria sensibili."""
    buf = bytearray(b"ChiaveSegretissimaInMemoriaRAM")
    secure_zero(buf)
    assert all(b == 0 for b in buf)


def test_kdf_pepper_defense() -> None:
    """Verifica che l'aggiunta del Pepper alteri crittograficamente la chiave derivata."""
    salt = os.urandom(16)
    passphrase = "UserMasterPassword2026!"
    pepper1 = b"HSM_PEPPER_KEY_A_32_BYTES_SECRET"
    pepper2 = b"HSM_PEPPER_KEY_B_32_BYTES_SECRET"

    key_no_pep = derive_key_argon2id(passphrase, salt, pepper=None)
    key_pep1 = derive_key_argon2id(passphrase, salt, pepper=pepper1)
    key_pep2 = derive_key_argon2id(passphrase, salt, pepper=pepper2)

    # Il Pepper altera completamente l'output
    assert key_no_pep != key_pep1
    assert key_pep1 != key_pep2

    # Ripetibilità deterministica con lo stesso Pepper
    assert key_pep1 == derive_key_argon2id(passphrase, salt, pepper=pepper1)


def test_system_enclave_code_format_and_entropy() -> None:
    """Verifica il generatore di token di sistema ad alta entropia (stile 1Password Secret Key)."""
    code1 = generate_system_enclave_code()
    code2 = generate_system_enclave_code()

    assert code1.startswith("NXS-")
    assert len(code1.split("-")) == 9  # NXS + 8 blocchi esadecimali da 4 caratteri
    assert code1 != code2


def test_dual_part_credential_derivation() -> None:
    """Verifica la derivazione ibrida (User Passphrase + Algorithmic System Code + Salt + Pepper)."""
    user_pass = "MySecretPassphrase"
    system_code = generate_system_enclave_code()
    salt = os.urandom(16)
    pepper = b"SERVER_ENCLAVE_PEPPER_32B_HSM!!"

    derived_key = derive_dual_part_credential(user_pass, system_code, salt, pepper=pepper)
    assert len(derived_key) == 32

    # Stessi parametri -> stessa chiave
    rederived = derive_dual_part_credential(user_pass, system_code, salt, pepper=pepper)
    assert rederived == derived_key

    # Se un attaccante conosce solo la password utente ma NON il system_code, fallisce
    attacker_key = derive_dual_part_credential(user_pass, "NXS-0000-0000-0000-0000", salt, pepper=pepper)
    assert attacker_key != derived_key
