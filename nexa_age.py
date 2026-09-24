#!/usr/bin/env python3
"""NEXA-S + age/X25519 wrapper (bozza concettuale).

Richiede: age (CLI) installato e nel PATH.
Uso esempio:
  python nexa_age.py encrypt --recipient age1... --in testo.txt --out testo.age
  python nexa_age.py decrypt --identity key.txt --in testo.age --out testo.txt
"""
import argparse, subprocess, sys, tempfile
from pathlib import Path

def age_encrypt(recipient, in_path, out_path):
    cmd = ["age", "--encrypt", "--recipient", recipient, "--output", str(out_path), str(in_path)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("age encrypt failed:", r.stderr, file=sys.stderr)
        return False
    return True

def age_decrypt(identity, in_path, out_path):
    cmd = ["age", "--decrypt", "--identity", str(identity), "--output", str(out_path), str(in_path)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("age decrypt failed:", r.stderr, file=sys.stderr)
        return False
    return True

def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    enc = sp.add_parser("encrypt")
    enc.add_argument("--recipient", required=True)
    enc.add_argument("--in", dest="inp", required=True)
    enc.add_argument("--out", dest="outp", required=True)
    enc.set_defaults(fn=lambda a: age_encrypt(a.recipient, a.inp, a.outp))
    dec = sp.add_parser("decrypt")
    dec.add_argument("--identity", required=True)
    dec.add_argument("--in", dest="inp", required=True)
    dec.add_argument("--out", dest="outp", required=True)
    dec.set_defaults(fn=lambda a: age_decrypt(a.identity, a.inp, a.outp))
    args = ap.parse_args()
    ok = args.fn(args)
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
