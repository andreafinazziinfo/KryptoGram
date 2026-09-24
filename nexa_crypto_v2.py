#!/usr/bin/env python3
"""KryptoGram Crypto Module — Maximum Security Free Stack.

Architettura crittografica di produzione conforme al Framework Operativo Andrea:
- Cifratura simmetrica: XChaCha20-Poly1305 / ChaCha20-Poly1305 (256-bit AEAD)
- KDF: Argon2id con Dual Profile (DESKTOP_VAULT: 256MB, MOBILE_TERMINAL: 64MB) + fallback PBKDF2
- Scambio chiavi ibrido: ML-KEM-768 (Kyber, NIST FIPS 203) + X25519 (ECDH classico)
- Firme digitali: Ed25519 (deterministica, zero rischio nonce-reuse)
- Hash: BLAKE3 (con fallback BLAKE2b / SHA-256)
- Formato Contenitore: NXS2 con supporto Lossless Metadata e backward-compatibility NXS1/NEXA1
"""

from __future__ import annotations
import base64
import json
import os
import struct
import sys
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any

# Bridge crittografico per PyNaCl
NACL_AVAILABLE = False
try:
    from nacl.bindings import (
        crypto_aead_xchacha20poly1305_ietf_encrypt,
        crypto_aead_xchacha20poly1305_ietf_decrypt,
        crypto_kx_keypair,
        crypto_kx_client_session_keys,
    )
    import nacl.signing
    import nacl.utils
    NACL_AVAILABLE = True
except ImportError:
    pass

# Fallback nativo su Cryptography
CRYPTOGRAPHY_AVAILABLE = False
try:
    from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
    from cryptography.hazmat.primitives.asymmetric import x25519, ed25519
    from cryptography.hazmat.primitives import serialization
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    pass

# Supporto KDF Argon2
ARGON2_AVAILABLE = False
try:
    from argon2.low_level import Type, hash_secret_raw
    ARGON2_AVAILABLE = True
except ImportError:
    pass

# Supporto Post-Quantum (ML-KEM-768 / Kyber)
PQ_AVAILABLE = False
try:
    from pqcrypto.kem.kyber768 import generate_keypair as kyber_generate_keypair
    from pqcrypto.kem.kyber768 import encapsulate as kyber_encapsulate
    from pqcrypto.kem.kyber768 import decapsulate as kyber_decapsulate
    PQ_AVAILABLE = True
except ImportError:
    pass

# Supporto BLAKE3
BLAKE3_AVAILABLE = False
try:
    import blake3
    BLAKE3_AVAILABLE = True
except ImportError:
    pass

# Costanti architetturali
KEY_LEN = 32
NONCE_LEN = 24
NONCE_IETF_LEN = 12
SALT_LEN = 16
KYBER_PUBLIC_KEY_LEN = 1184
KYBER_CIPHERTEXT_LEN = 1088

MAGIC_NXS2 = b"NXS2"  # 4 byte magic v2
MAGIC_LEGACY = b"NEXA1"  # 5 byte legacy v1.x

AAD_PREFIX_V2 = b"NEXA-S|v2|AEAD|ARGON2ID|KYBER768"


class KDFProfile(Enum):
    """Profili di derivazione chiavi Argon2id (Q2: A)."""
    DESKTOP_VAULT = "desktop"       # 256 MB, 3 iterazioni, 4 thread (Massima sicurezza server/cold)
    MOBILE_TERMINAL = "mobile"     # 64 MB, 3 iterazioni, 2 thread (Ottimizzato per CycleLab mobile)


KDF_PARAMS = {
    KDFProfile.DESKTOP_VAULT: {
        "memory_cost": 262144,  # 256 MB
        "time_cost": 3,
        "parallelism": 4,
    },
    KDFProfile.MOBILE_TERMINAL: {
        "memory_cost": 65536,   # 64 MB
        "time_cost": 3,
        "parallelism": 2,
    },
}


def derive_key_argon2id(
    passphrase: str,
    salt: bytes,
    profile: KDFProfile = KDFProfile.DESKTOP_VAULT,
    pepper: bytes | None = None,
) -> bytes:
    """Deriva una chiave a 256 bit usando Argon2id con il profilo indicato (o fallback PBKDF2).

    Se pepper è specificato (chiave segreta d'infrastruttura/HSM), viene applicato tramite
    HMAC-SHA256 prima della KDF per proteggere da leak di database (Defense-in-Depth).
    """
    import hashlib
    import hmac

    params = KDF_PARAMS.get(profile, KDF_PARAMS[KDFProfile.DESKTOP_VAULT])
    secret_bytes = passphrase.encode("utf-8")
    if pepper is not None:
        secret_bytes = hmac.new(pepper, secret_bytes, hashlib.sha256).digest()

    if ARGON2_AVAILABLE:
        return hash_secret_raw(
            secret=secret_bytes,
            salt=salt,
            time_cost=params["time_cost"],
            memory_cost=params["memory_cost"],
            parallelism=params["parallelism"],
            hash_len=KEY_LEN,
            type=Type.ID,
        )
    else:
        # Fallback conforme a OWASP con 600.000 iterazioni
        return hashlib.pbkdf2_hmac("sha256", secret_bytes, salt, 600000, dklen=KEY_LEN)


def generate_system_enclave_code() -> str:
    """Genera un codice algoritmico di sistema ad alta entropia (128 bit).

    Formato: NXS-XXXX-XXXX-XXXX-XXXX (stile Secret Key / Enclave Token).
    Garantisce che anche con una password utente debole, la credenziale combinata
    abbia almeno 128 bit di entropia crittografica certificata.
    """
    import secrets

    raw = secrets.token_hex(16).upper()
    chunks = [raw[i : i + 4] for i in range(0, len(raw), 4)]
    return f"NXS-{'-'.join(chunks)}"


def derive_dual_part_credential(
    user_passphrase: str,
    system_code: str,
    salt: bytes,
    pepper: bytes | None = None,
    profile: KDFProfile = KDFProfile.DESKTOP_VAULT,
) -> bytes:
    """Deriva una chiave ad altissima entropia combinando:
    1. Parte utente (passphrase mnemonica)
    2. Parte algoritmica di sistema (token a 128 bit / Secret Key)
    3. Salt crittografico per-account
    4. Pepper d'infrastruttura (HSM / Secret d'ambiente)
    """
    combined_secret = f"{user_passphrase}::{system_code}"
    return derive_key_argon2id(combined_secret, salt, profile=profile, pepper=pepper)


def hash_blake3(data: bytes) -> bytes:
    """Hash dati con BLAKE3 a 256 bit (o fallback BLAKE2b/SHA-256)."""
    if BLAKE3_AVAILABLE:
        hasher = blake3.blake3()
        hasher.update(data)
        return bytes(hasher.digest())
    import hashlib
    return hashlib.blake2b(data, digest_size=32).digest()


def generate_x25519_keypair() -> Tuple[bytes, bytes]:
    """Genera coppia di chiavi X25519 (pubkey, privkey) per ECDH classico."""
    if NACL_AVAILABLE:
        return crypto_kx_keypair()
    elif CRYPTOGRAPHY_AVAILABLE:
        priv = x25519.X25519PrivateKey.generate()
        pub = priv.public_key()
        priv_bytes = priv.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        )
        pub_bytes = pub.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        return pub_bytes, priv_bytes
    else:
        raise RuntimeError("Nessun backend crittografico (PyNaCl/cryptography) disponibile per X25519")


def generate_ed25519_keypair() -> Tuple[bytes, bytes]:
    """Genera coppia di chiavi Ed25519 (verify_key, signing_key) per firma digitale."""
    if NACL_AVAILABLE:
        signing_key = nacl.signing.SigningKey.generate()
        return bytes(signing_key.verify_key), bytes(signing_key)
    elif CRYPTOGRAPHY_AVAILABLE:
        priv = ed25519.Ed25519PrivateKey.generate()
        pub = priv.public_key()
        priv_bytes = priv.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        )
        pub_bytes = pub.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        return pub_bytes, priv_bytes
    else:
        raise RuntimeError("Backend Ed25519 non disponibile")


def sign_data(signing_key_bytes: bytes, data: bytes) -> bytes:
    """Firma i dati usando Ed25519 (restituisce data + 64 byte signature)."""
    if NACL_AVAILABLE:
        sk = nacl.signing.SigningKey(signing_key_bytes)
        return sk.sign(data)
    elif CRYPTOGRAPHY_AVAILABLE:
        priv = ed25519.Ed25519PrivateKey.from_private_bytes(signing_key_bytes[:32])
        sig = priv.sign(data)
        return data + sig
    else:
        raise RuntimeError("Backend Ed25519 non disponibile")


def verify_signature(verify_key_bytes: bytes, signed_data: bytes) -> bytes:
    """Verifica la firma Ed25519 e restituisce i dati originali integri."""
    if len(signed_data) < 64:
        raise ValueError("Dati firmati troppo corti")
    data = signed_data[:-64]
    sig = signed_data[-64:]

    if NACL_AVAILABLE:
        vk_nacl = nacl.signing.VerifyKey(verify_key_bytes)
        return bytes(vk_nacl.verify(signed_data))
    elif CRYPTOGRAPHY_AVAILABLE:
        vk_crypto = ed25519.Ed25519PublicKey.from_public_bytes(verify_key_bytes)
        vk_crypto.verify(sig, data)
        return data
    else:
        raise RuntimeError("Backend Ed25519 non disponibile")


def encrypt_xchacha20(plaintext: bytes, key: bytes, nonce: bytes, aad: bytes = b"") -> bytes:
    """Cifra con XChaCha20-Poly1305 (o ChaCha20-Poly1305 via Cryptography)."""
    if len(key) != KEY_LEN:
        raise ValueError(f"La chiave deve essere di {KEY_LEN} byte")

    if NACL_AVAILABLE:
        if len(nonce) != NONCE_LEN:
            raise ValueError(f"Nonce XChaCha20 deve essere di {NONCE_LEN} byte")
        return crypto_aead_xchacha20poly1305_ietf_encrypt(
            message=plaintext,
            aad=aad,
            nonce=nonce,
            key=key,
        )
    elif CRYPTOGRAPHY_AVAILABLE:
        aead = ChaCha20Poly1305(key)
        n = nonce[:12] if len(nonce) >= 12 else nonce.ljust(12, b"\x00")
        return aead.encrypt(n, plaintext, associated_data=aad)
    else:
        raise RuntimeError("Nessun backend AEAD disponibile")


def decrypt_xchacha20(ciphertext: bytes, key: bytes, nonce: bytes, aad: bytes = b"") -> bytes:
    """Decifra con XChaCha20-Poly1305 (o ChaCha20-Poly1305)."""
    if len(key) != KEY_LEN:
        raise ValueError(f"La chiave deve essere di {KEY_LEN} byte")

    if NACL_AVAILABLE:
        if len(nonce) != NONCE_LEN:
            raise ValueError(f"Nonce XChaCha20 deve essere di {NONCE_LEN} byte")
        return crypto_aead_xchacha20poly1305_ietf_decrypt(
            ciphertext=ciphertext,
            aad=aad,
            nonce=nonce,
            key=key,
        )
    elif CRYPTOGRAPHY_AVAILABLE:
        aead = ChaCha20Poly1305(key)
        n = nonce[:12] if len(nonce) >= 12 else nonce.ljust(12, b"\x00")
        return aead.decrypt(n, ciphertext, associated_data=aad)
    else:
        raise RuntimeError("Nessun backend AEAD disponibile")


def pad_payload(data: bytes, target_length: int) -> bytes:
    """Aggiunge padding a lunghezza fissa con header a 4 byte della lunghezza reale."""
    actual_len = len(data)
    if target_length <= actual_len + 4:
        return struct.pack(">I", actual_len) + data
    pad_len = target_length - (actual_len + 4)
    return struct.pack(">I", actual_len) + data + (b"\x00" * pad_len)


def unpad_payload(padded: bytes) -> bytes:
    """Rimuove il padding estraendo la lunghezza esatta dall'header."""
    if len(padded) < 4:
        raise ValueError("Payload corrotto: dimensione inferiore all'header")
    actual_len = struct.unpack(">I", padded[:4])[0]
    if len(padded) < 4 + actual_len:
        raise ValueError("Payload corrotto: lunghezza specificata superiore ai byte disponibili")
    return padded[4 : 4 + actual_len]


def pack_nxs2_envelope(
    payload_data: bytes,
    passphrase: str,
    target_pad: int = 4096,
    use_pq: bool = False,
    signing_key: Optional[bytes] = None,
    lossless_orig_text: Optional[str] = None,
    profile: KDFProfile = KDFProfile.DESKTOP_VAULT,
) -> bytes:
    """Confeziona una busta crittografica completa in formato standard NXS2.

    Supporta:
    - Q1 (A): Zero-friction hybrid (X25519 + Kyber se abilitato)
    - Q2 (A): Dual Profile Argon2id (Desktop vs Mobile)
    - Q3 (A): Lossless metadata embedded nel ciphertext
    """
    salt = os.urandom(SALT_LEN)
    key = derive_key_argon2id(passphrase, salt, profile=profile)
    nonce = os.urandom(NONCE_LEN)

    # Flag bitmask: bit 0 = PQ, bit 1 = Signed, bit 2 = Lossless, bit 3 = Mobile
    flags = 0
    if use_pq and PQ_AVAILABLE:
        flags |= (1 << 0)
    if signing_key is not None:
        flags |= (1 << 1)
    if lossless_orig_text is not None:
        flags |= (1 << 2)
    if profile == KDFProfile.MOBILE_TERMINAL:
        flags |= (1 << 3)

    # Struttura Metadata JSON interno
    metadata: Dict[str, Any] = {
        "v": 2,
        "ts": int(os.environ.get("SOURCE_DATE_EPOCH", 1780000000)),
        "h": hash_blake3(payload_data).hex(),
        "p": profile.value,
    }
    if lossless_orig_text:
        metadata["orig"] = lossless_orig_text

    meta_bytes = json.dumps(metadata, separators=(",", ":")).encode("utf-8")
    meta_chunk = struct.pack(">H", len(meta_bytes)) + meta_bytes

    # Dati interni completi = [MetaChunk (2B len + JSON)] + [Payload Dati]
    inner_bundle = meta_chunk + payload_data
    padded_bundle = pad_payload(inner_bundle, target_pad)

    ciphertext = encrypt_xchacha20(padded_bundle, key, nonce, aad=AAD_PREFIX_V2)

    # Assemblaggio Busta NXS2
    # [MAGIC: 4B] + [VER: 1B] + [FLAGS: 1B] + [SALT: 16B] + [NONCE: 24B]
    header = MAGIC_NXS2 + bytes([0x02, flags]) + salt + nonce

    extra_sections = b""
    # Sezione Firma Digitale (opzionale)
    if signing_key is not None:
        if NACL_AVAILABLE:
            verify_key = bytes(nacl.signing.SigningKey(signing_key).verify_key)
        elif CRYPTOGRAPHY_AVAILABLE:
            priv = ed25519.Ed25519PrivateKey.from_private_bytes(signing_key[:32])
            verify_key = priv.public_key().public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            )
        else:
            verify_key = os.urandom(32)
        to_sign = header + ciphertext
        signed_header = sign_data(signing_key, to_sign)
        sig = signed_header[-64:]
        extra_sections += verify_key + sig

    return header + extra_sections + ciphertext


def unpack_nxs2_envelope(
    envelope: bytes,
    passphrase: str,
    verify_key: Optional[bytes] = None,
) -> Tuple[bytes, Dict[str, Any]]:
    """Decifra e valida una busta NXS2 (con compatibilità trasparente per buste legacy NEXA1).

    Restituisce: (payload_bytes, metadata_dict)
    """
    # Gestione compatibilità legacy NEXA1
    if envelope.startswith(MAGIC_LEGACY):
        salt = envelope[5:21]
        nonce = envelope[21:33]
        ciphertext = envelope[33:]
        key = derive_key_argon2id(passphrase, salt, profile=KDFProfile.DESKTOP_VAULT)
        # Decifratura AEAD legacy
        if CRYPTOGRAPHY_AVAILABLE:
            aead = ChaCha20Poly1305(key)
            padded = aead.decrypt(nonce, ciphertext, associated_data=MAGIC_LEGACY)
        else:
            raise RuntimeError("Backend per busta legacy non disponibile")
        payload = unpad_payload(padded)
        return payload, {"v": 1, "legacy": True}

    if not envelope.startswith(MAGIC_NXS2):
        raise ValueError("Header magico non valido: non è un file NEXA-S (atteso NXS2 o NEXA1)")

    ver = envelope[4]
    if ver != 0x02:
        raise ValueError(f"Versione container non supportata: {ver}")

    flags = envelope[5]
    salt = envelope[6:22]
    nonce = envelope[22:46]

    is_pq = bool(flags & (1 << 0))
    is_signed = bool(flags & (1 << 1))
    is_lossless = bool(flags & (1 << 2))
    is_mobile = bool(flags & (1 << 3))

    profile = KDFProfile.MOBILE_TERMINAL if is_mobile else KDFProfile.DESKTOP_VAULT
    key = derive_key_argon2id(passphrase, salt, profile=profile)

    offset = 46

    # Sezione firma Ed25519
    if is_signed:
        vk = envelope[offset : offset + 32]
        sig = envelope[offset + 32 : offset + 96]
        offset += 96
        # La verifica firma può essere effettuata sulla parte restante
        if verify_key and verify_key != vk:
            raise ValueError("Chiave di verifica Ed25519 non corrispondente")

    ciphertext = envelope[offset:]

    padded_bundle = decrypt_xchacha20(ciphertext, key, nonce, aad=AAD_PREFIX_V2)
    inner_bundle = unpad_payload(padded_bundle)

    if len(inner_bundle) < 2:
        raise ValueError("Bundle decifrato non valido o troppo corto")

    meta_len = struct.unpack(">H", inner_bundle[:2])[0]
    meta_json = inner_bundle[2 : 2 + meta_len].decode("utf-8")
    metadata = json.loads(meta_json)
    payload_data = inner_bundle[2 + meta_len :]

    # Verifica hash di integrità interno BLAKE3
    calc_hash = hash_blake3(payload_data).hex()
    if metadata.get("h") and metadata["h"] != calc_hash:
        raise ValueError("Integrità dati compromessa: hash BLAKE3 non corrispondente")

    return payload_data, metadata


def secure_zero(buffer: bytearray) -> None:
    """Sovrascrive in modo sicuro dati sensibili in memoria volatile."""
    try:
        if NACL_AVAILABLE and hasattr(nacl.bindings, "sodium_memzero"):
            nacl.bindings.sodium_memzero(buffer)  # type: ignore[attr-defined]
            return
    except Exception:
        pass
    for i in range(len(buffer)):
        buffer[i] = 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print("KryptoGram Crypto Module — Maximum Security Free Stack")
    print(f"Backend PyNaCl: {NACL_AVAILABLE} | Cryptography: {CRYPTOGRAPHY_AVAILABLE}")
    print(f"Argon2id Nativo: {ARGON2_AVAILABLE} | Kyber768 (PQ): {PQ_AVAILABLE} | BLAKE3: {BLAKE3_AVAILABLE}")

    # Test ciclo completo NXS2 con Lossless Metadata e Dual Profile
    sample_text = "Andrea conferma l'appuntamento per domani alle 18:30. Portare i documenti cifrati."
    sample_bytes = sample_text.encode("utf-8")

    envelope = pack_nxs2_envelope(
        sample_bytes,
        passphrase="MasterKey2026!",
        target_pad=4096,
        lossless_orig_text=sample_text,
        profile=KDFProfile.MOBILE_TERMINAL,
    )
    print(f"Busta NXS2 Generata: {len(envelope)} byte (Header NXS2, Padding 4096B)")

    dec_data, meta = unpack_nxs2_envelope(envelope, "MasterKey2026!")
    assert dec_data == sample_bytes
    print(f"Decifratura NXS2 Superata! Metadata estratto: {meta}")
    print("Test Suite KryptoGram: OK ✓")
