#!/usr/bin/env python3
"""KryptoGram — Sovereign Cryptography & Keyed Phonetic Conlang.
(dal greco: Kryptós = Nascosto, Grámma = Scrittura)

Entrypoint principale del pacchetto KryptoGram:
- Esporta le API crittografiche Post-Quantum NXS2 e i profili KDF Argon2id
- Esporta il motore di traslitterazione fonetica e permutazione dinamica (26!)
- Funge da interfaccia CLI unificata
"""

from __future__ import annotations
import sys

from nexa_lib import (
    italian_to_nexa,
    nexa_to_italian,
    validate_nexa,
    derive_dynamic_alphabet,
    DYNAMIC_GLYPH_POOL,
)
from nexa_crypto_v2 import (
    KDFProfile,
    derive_key_argon2id,
    encrypt_xchacha20,
    decrypt_xchacha20,
    pack_nxs2_envelope,
    unpack_nxs2_envelope,
    generate_x25519_keypair,
    generate_ed25519_keypair,
    sign_data,
    verify_signature,
    hash_blake3,
    secure_zero,
    PQ_AVAILABLE,
    ARGON2_AVAILABLE,
    NACL_AVAILABLE,
    CRYPTOGRAPHY_AVAILABLE,
    BLAKE3_AVAILABLE,
    MAGIC_NXS2,
)
from nexa_cli_v2 import main

__all__ = [
    "italian_to_nexa",
    "nexa_to_italian",
    "validate_nexa",
    "derive_dynamic_alphabet",
    "DYNAMIC_GLYPH_POOL",
    "KDFProfile",
    "derive_key_argon2id",
    "encrypt_xchacha20",
    "decrypt_xchacha20",
    "pack_nxs2_envelope",
    "unpack_nxs2_envelope",
    "generate_x25519_keypair",
    "generate_ed25519_keypair",
    "sign_data",
    "verify_signature",
    "hash_blake3",
    "secure_zero",
    "PQ_AVAILABLE",
    "ARGON2_AVAILABLE",
    "NACL_AVAILABLE",
    "CRYPTOGRAPHY_AVAILABLE",
    "BLAKE3_AVAILABLE",
    "MAGIC_NXS2",
    "main",
]

if __name__ == "__main__":
    main()
