#!/usr/bin/env python3
"""NEXA-S v2.0 Unified Command Line Interface.

Fornisce comandi completi di produzione per:
- Cifratura e confezionamento buste NXS2
- Decifratura trasparente (con fallback legacy NXS1)
- Traslitterazione fonetica e ripristino Lossless
- Selezione profilo KDF (desktop vault vs mobile terminal)
"""

from __future__ import annotations
import argparse
import base64
import getpass
import sys
from pathlib import Path
from typing import Optional

from nexa_lib import italian_to_nexa, nexa_to_italian
from nexa_crypto_v2 import (
    KDFProfile,
    pack_nxs2_envelope,
    unpack_nxs2_envelope,
    PQ_AVAILABLE,
)


def read_passphrase(confirm: bool = False) -> str:
    """Legge la passphrase in modo sicuro da terminale o stdin."""
    if not sys.stdin.isatty():
        p1 = sys.stdin.readline().rstrip("\r\n")
        if confirm:
            p2 = sys.stdin.readline().rstrip("\r\n")
            if p1 != p2:
                raise ValueError("Le due passphrase inserite non coincidono")
        return p1
    else:
        p1 = getpass.getpass("Inserisci passphrase NEXA-S: ")
        if confirm:
            p2 = getpass.getpass("Conferma passphrase: ")
            if p1 != p2:
                raise ValueError("Le due passphrase inserite non coincidono")
        return p1


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(
        prog="nexa-s",
        description="NEXA-S v2.0 — Post-Quantum Symbolic Cryptography Engine",
    )
    subparsers = parser.add_subparsers(dest="cmd", required=True)

    # Subcommand: Encrypt
    enc = subparsers.add_parser("encrypt", help="Cifra un file o documento in busta NXS2")
    enc.add_argument("--in", dest="inp", required=True, help="File sorgente in chiaro")
    enc.add_argument("--out", dest="outp", required=True, help="Percorso file busta .nexa generato")
    enc.add_argument("--pad", type=int, default=4096, help="Target padding fisso in byte (default: 4096)")
    enc.add_argument("--profile", choices=["desktop", "mobile"], default="desktop", help="Profilo KDF Argon2id")
    enc.add_argument("--nexa", action="store_true", help="Traslittera il testo in glifi NEXA-S prima di cifrare")
    enc.add_argument("--lossless", action="store_true", default=True, help="Include metadata per decodifica ortografica identica al 100%")
    enc.add_argument("--pq", action="store_true", help="Abilita incapsulamento ibrido Post-Quantum ML-KEM-768")
    enc.add_argument("--new-passphrase", action="store_true", help="Richiedi conferma della passphrase")
    enc.add_argument("--raw-binary", action="store_true", help="Salva file binario raw anziché Base64url")

    # Subcommand: Decrypt
    dec = subparsers.add_parser("decrypt", help="Decifra e valida una busta NXS2 (o legacy)")
    dec.add_argument("--in", dest="inp", required=True, help="File busta .nexa cifrato")
    dec.add_argument("--out", dest="outp", required=True, help="File destinazione decifrato")
    dec.add_argument("--nexa", action="store_true", help="Ritraslittera da glifi fonetici a testo")

    # Subcommand: Transliterate
    trans = subparsers.add_parser("transliterate", help="Traslittera direttamente testo ⇄ glifi senza cifrare")
    trans.add_argument("--text", type=str, help="Stringa di testo o glifi da traslitterare")
    trans.add_argument("--reverse", action="store_true", help="Inverti direzione (NEXA-S -> Italiano)")

    args = parser.parse_args()

    if args.cmd == "transliterate":
        if not args.text:
            print("Specificare --text per la traslitterazione", file=sys.stderr)
            sys.exit(1)
        if args.reverse:
            res = nexa_to_italian(args.text)
        else:
            res = italian_to_nexa(args.text)
        print(res)
        return

    in_path = Path(args.inp)
    out_path = Path(args.outp)

    if not in_path.exists():
        print(f"Errore: il file di input '{in_path}' non esiste.", file=sys.stderr)
        sys.exit(1)

    passphrase = read_passphrase(confirm=getattr(args, "new_passphrase", False))

    if args.cmd == "encrypt":
        raw_data = in_path.read_bytes()
        orig_text: Optional[str] = None
        data_to_encrypt = raw_data

        try:
            text_candidate = raw_data.decode("utf-8")
            if args.lossless:
                orig_text = text_candidate
            if args.nexa:
                glyphs = italian_to_nexa(text_candidate)
                data_to_encrypt = glyphs.encode("utf-8")
        except UnicodeDecodeError:
            # File binario, procedi senza traslitterazione
            pass

        kdf_profile = KDFProfile.MOBILE_TERMINAL if args.profile == "mobile" else KDFProfile.DESKTOP_VAULT

        envelope = pack_nxs2_envelope(
            payload_data=data_to_encrypt,
            passphrase=passphrase,
            target_pad=args.pad,
            use_pq=args.pq,
            lossless_orig_text=orig_text,
            profile=kdf_profile,
        )

        if args.raw_binary:
            out_path.write_bytes(envelope)
        else:
            b64_str = base64.urlsafe_b64encode(envelope).decode("ascii")
            out_path.write_text(b64_str, encoding="utf-8")

        print(f"✓ Busta NXS2 creata con successo: {out_path} ({len(envelope)} byte)")

    elif args.cmd == "decrypt":
        content = in_path.read_text(encoding="utf-8").strip()
        try:
            envelope_bytes = base64.urlsafe_b64decode(content.encode("ascii"))
        except Exception:
            envelope_bytes = in_path.read_bytes()

        decrypted_payload, metadata = unpack_nxs2_envelope(envelope_bytes, passphrase)

        # Se era abilitato il salvataggio lossless, usa l'ortografia originale
        if metadata.get("orig"):
            final_output = metadata["orig"].encode("utf-8")
        elif args.nexa:
            try:
                glyphs = decrypted_payload.decode("utf-8")
                final_output = nexa_to_italian(glyphs).encode("utf-8")
            except UnicodeDecodeError:
                final_output = decrypted_payload
        else:
            final_output = decrypted_payload

        out_path.write_bytes(final_output)
        print(f"✓ File decifrato con successo: {out_path} ({len(final_output)} byte, Metadata: {metadata})")


if __name__ == "__main__":
    main()
