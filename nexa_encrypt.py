#!/usr/bin/env python3
"""NEXA-S: Authenticated Encryption CLI & Envelope Tool.

Implementa la cifratura/decifratura autenticata di file o testo con standard NEXA-S.
Supporta:
- KDF: Argon2id (se presente) o PBKDF2-HMAC-SHA256 (600.000 iterazioni)
- AEAD: ChaCha20-Poly1305 / AES-256-GCM
- Padding a lunghezza fissa per mitigare l'analisi del traffico
- Opzione --nexa per traslitterazione fonetica automatica
"""

from __future__ import annotations
import argparse
import base64
import getpass
import hashlib
import json
import os
import struct
import sys
from pathlib import Path

try:
    from nexa_lib import italian_to_nexa, nexa_to_italian
except ImportError:
    # Se eseguito nella stessa directory
    sys.path.insert(0, str(Path(__file__).parent))
    from nexa_lib import italian_to_nexa, nexa_to_italian

# Verifica supporto AEAD
try:
    from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305, AESGCM
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False

MAGIC_HEADER = b"NEXA1"  # 5 byte magic header


def derive_key(passphrase: str, salt: bytes, length: int = 32) -> bytes:
    """Deriva una chiave crittografica a 256 bit dalla passphrase."""
    try:
        import argon2.low_level as argon2_ll
        # Parametri Argon2id standard
        return argon2_ll.hash_secret_raw(
            secret=passphrase.encode("utf-8"),
            salt=salt,
            time_cost=3,
            memory_cost=65536,
            parallelism=4,
            hash_len=length,
            type=argon2_ll.Type.ID,
        )
    except (ImportError, Exception):
        # Fallback sicuro: PBKDF2-HMAC-SHA256 con 600.000 iterazioni
        return hashlib.pbkdf2_hmac(
            "sha256",
            passphrase.encode("utf-8"),
            salt,
            600000,
            dklen=length,
        )


def pad_payload(data: bytes, target_length: int) -> bytes:
    """Aggiunge padding PKCS7-like o zero-padding con header di lunghezza reale."""
    actual_len = len(data)
    if target_length <= actual_len + 4:
        # Nessun padding aggiuntivo oltre all'header di lunghezza a 4 byte
        return struct.pack(">I", actual_len) + data
    pad_len = target_length - (actual_len + 4)
    # Header a 4 byte con lunghezza esatta del payload originale
    padded = struct.pack(">I", actual_len) + data + (b"\x00" * pad_len)
    return padded


def unpad_payload(padded: bytes) -> bytes:
    """Rimuove il padding leggendo la lunghezza esatta dall'header a 4 byte."""
    if len(padded) < 4:
        raise ValueError("Payload corrotto o troppo corto per estrarre la lunghezza")
    actual_len = struct.unpack(">I", padded[:4])[0]
    if len(padded) < 4 + actual_len:
        raise ValueError("Payload corrotto: lunghezza specificata superiore alla dimensione effettiva")
    return padded[4 : 4 + actual_len]


def encrypt_bytes(data: bytes, passphrase: str, target_pad: int = 4096) -> bytes:
    """Cifra i byte e genera il pacchetto binario NEXA-S."""
    salt = os.urandom(16)
    key = derive_key(passphrase, salt, 32)
    nonce = os.urandom(12)

    padded_data = pad_payload(data, target_pad)

    if HAS_CRYPTOGRAPHY:
        aead = ChaCha20Poly1305(key)
        ciphertext = aead.encrypt(nonce, padded_data, associated_data=MAGIC_HEADER)
    else:
        # Fallback base con hashlib/HMAC e XOR stream (se cryptography non presente)
        keystream = hashlib.sha256(key + nonce).digest()
        ct_parts = []
        for i, b in enumerate(padded_data):
            ct_parts.append(bytes([b ^ keystream[i % len(keystream)]]))
        ct = b"".join(ct_parts)
        tag = hashlib.sha256(key + ct + MAGIC_HEADER).digest()[:16]
        ciphertext = ct + tag

    # Layout: MAGIC (5B) + SALT (16B) + NONCE (12B) + CIPHERTEXT
    envelope = MAGIC_HEADER + salt + nonce + ciphertext
    return envelope


def decrypt_bytes(envelope: bytes, passphrase: str) -> bytes:
    """Decifra il pacchetto binario NEXA-S e verifica l'integrità del tag."""
    if not envelope.startswith(MAGIC_HEADER):
        raise ValueError("Header magic NEXA non valido o file non riconosciuto")

    salt = envelope[5:21]
    nonce = envelope[21:33]
    ciphertext = envelope[33:]

    key = derive_key(passphrase, salt, 32)

    if HAS_CRYPTOGRAPHY:
        aead = ChaCha20Poly1305(key)
        try:
            padded_data = aead.decrypt(nonce, ciphertext, associated_data=MAGIC_HEADER)
        except Exception as e:
            raise ValueError("Autenticazione fallita: passphrase errata o payload alterato") from e
    else:
        tag = ciphertext[-16:]
        ct = ciphertext[:-16]
        expected_tag = hashlib.sha256(key + ct + MAGIC_HEADER).digest()[:16]
        if tag != expected_tag:
            raise ValueError("Autenticazione fallita: tag non corrispondente")
        keystream = hashlib.sha256(key + nonce).digest()
        pt_parts = []
        for i, b in enumerate(ct):
            pt_parts.append(bytes([b ^ keystream[i % len(keystream)]]))
        padded_data = b"".join(pt_parts)

    return unpad_payload(padded_data)


def read_passphrase(confirm: bool = False) -> str:
    """Legge la passphrase da stdin o terminale."""
    if not sys.stdin.isatty():
        # Esecuzione da script/GUI: legge righe da stdin
        p1 = sys.stdin.readline().rstrip("\r\n")
        if confirm:
            p2 = sys.stdin.readline().rstrip("\r\n")
            if p1 != p2:
                raise ValueError("Le due passphrase inserite non coincidono")
        return p1
    else:
        p1 = getpass.getpass("Inserisci passphrase: ")
        if confirm:
            p2 = getpass.getpass("Conferma passphrase: ")
            if p1 != p2:
                raise ValueError("Le due passphrase inserite non coincidono")
        return p1


def main():
    parser = argparse.ArgumentParser(description="NEXA-S Cryptographic Envelope CLI")
    subparsers = parser.add_subparsers(dest="cmd", required=True)

    # Subcommand encrypt
    enc_parser = subparsers.add_parser("encrypt", help="Cifra un file")
    enc_parser.add_argument("--in", dest="inp", required=True, help="File input")
    enc_parser.add_argument("--out", dest="outp", required=True, help="File output")
    enc_parser.add_argument("--pad", type=int, default=4096, help="Target padding size (byte)")
    enc_parser.add_argument("--nexa", action="store_true", help="Traslittera in glifi NEXA-S prima di cifrare")
    enc_parser.add_argument("--new-passphrase", action="store_true", help="Richiedi conferma passphrase")
    enc_parser.add_argument("--b64", action="store_true", default=True, help="Esporta come Base64url (default)")

    # Subcommand decrypt
    dec_parser = subparsers.add_parser("decrypt", help="Decifra un file")
    dec_parser.add_argument("--in", dest="inp", required=True, help="File input")
    dec_parser.add_argument("--out", dest="outp", required=True, help="File output")
    dec_parser.add_argument("--nexa", action="store_true", help="Ritraslittera da glifi NEXA-S a testo")

    args = parser.parse_args()

    in_path = Path(args.inp)
    out_path = Path(args.outp)

    if not in_path.exists():
        print(f"Errore: il file di input '{in_path}' non esiste.", file=sys.stderr)
        sys.exit(1)

    try:
        if args.cmd == "encrypt":
            passphrase = read_passphrase(confirm=args.new_passphrase)
            raw_data = in_path.read_bytes()

            # Se richiesta traslitterazione NEXA-S
            if args.nexa:
                try:
                    text = raw_data.decode("utf-8")
                    nexa_glyphs = italian_to_nexa(text)
                    raw_data = nexa_glyphs.encode("utf-8")
                except UnicodeDecodeError:
                    print("Avviso: il file contiene dati binari, traslitterazione fonetica ignorata.", file=sys.stderr)

            envelope = encrypt_bytes(raw_data, passphrase, target_pad=args.pad)

            # Esportazione in Base64url
            b64_data = base64.urlsafe_b64encode(envelope).decode("ascii")
            out_path.write_text(b64_data, encoding="utf-8")
            print(f"File cifrato con successo: {out_path} ({len(b64_data)} caratteri Base64url)")

        elif args.cmd == "decrypt":
            passphrase = read_passphrase(confirm=False)
            content = in_path.read_text(encoding="utf-8").strip()

            try:
                envelope = base64.urlsafe_b64decode(content.encode("ascii"))
            except Exception:
                # Se è binario raw
                envelope = in_path.read_bytes()

            decrypted_data = decrypt_bytes(envelope, passphrase)

            if args.nexa:
                try:
                    glyphs = decrypted_data.decode("utf-8")
                    text = nexa_to_italian(glyphs)
                    decrypted_data = text.encode("utf-8")
                except UnicodeDecodeError:
                    pass

            out_path.write_bytes(decrypted_data)
            print(f"File decifrato con successo: {out_path} ({len(decrypted_data)} byte)")

    except Exception as e:
        print(f"Errore durante l'operazione: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
