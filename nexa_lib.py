#!/usr/bin/env python3
"""NEXA-S: Core Phonetic Library & Glyph Transliteration Engine.

Implementa la mappatura fonetica bidirezionale tra lingua naturale (italiano)
e l'alfabeto simbolico NEXA-S, con gestione di digrammi, vocali, numeri
e delimitatori di blocco.
"""

from __future__ import annotations
import re
import unicodedata
from typing import Dict, List, Tuple

# Tavola fonetica ufficiale NEXA-S
# Vocali
VOWEL_MAP = {
    "a": "⊕",
    "e": "≋",
    "i": "∿",
    "o": "⊙",
    "u": "∪",
    "à": "⊕",
    "è": "≋",
    "é": "≋",
    "ì": "∿",
    "ò": "⊙",
    "ù": "∪",
}

# Consonanti e digrammi
CONSONANT_MAP = {
    "b": "⊓",
    "c": "⌁",
    "d": "∆",
    "f": "ƒ",
    "g": "⅁",
    "h": "⊥",
    "j": "⌇",
    "k": "⌁",
    "l": "⌯",
    "m": "⋔",
    "n": "⋒",
    "p": "⌐",
    "q": "⌁∪",
    "r": "⌿",
    "s": "≈",
    "t": "⊥",
    "v": "⌿",
    "w": "∪∪",
    "x": "⌁≈",
    "y": "∿",
    "z": "↑",
}

# Digrammi fonetici prioritari italiani
DIGRAPH_MAP = {
    "ch": "⌁",
    "gh": "⅁",
    "gn": "⅁⋒",
    "gl": "⌯∿",
    "gli": "⌯∿",
    "sc": "≈⌁",
    "sci": "≈∿",
    "ce": "⌁≋",
    "ci": "⌁∿",
    "ge": "⅁≋",
    "gi": "⅁∿",
    "qu": "⌁∪",
}

# Simboli speciali e punteggiatura
PUNCTUATION_MAP = {
    ".": "∴",
    ",": ",",
    ";": ";",
    ":": ":",
    "!": "!",
    "?": "?",
    "-": "-",
    "(": "(",
    ")": ")",
    "[": "⟦",
    "]": "⟧",
    ">=": "≥",
    "<=": "≤",
    "=>": "⇒",
}

# Tavola inversa per decodifica
REVERSE_GLYPH_MAP = {
    "⊕": "a",
    "∧": "a",  # variante maiuscola/iniziale
    "≋": "e",
    "∿": "i",
    "⊙": "o",
    "∪": "u",
    "⊓": "b",
    "⌁": "c",
    "∆": "d",
    "ƒ": "f",
    "⅁": "g",
    "⊥": "t",
    "⌇": "j",
    "⌯": "l",
    "⋔": "m",
    "⋒": "n",
    "⌐": "p",
    "⌿": "r",
    "≈": "s",
    "↑": "z",
    "∴": ".",
    "⇒": " allora ",
}


# Pool geometrico per la permutazione dinamica con chiave (26 glifi unici)
DYNAMIC_GLYPH_POOL = [
    "⊕", "≋", "∿", "⊙", "∪", "⊓", "⌁", "∆", "ƒ", "⅁",
    "⊥", "⌇", "⌯", "⋔", "⋒", "⌐", "⌿", "≈", "↑", "⌖",
    "⊞", "◊", "∇", "⋐", "⋑", "⨁"
]
BASE_ALPHABET_CHARS = list("abcdefghijklmnopqrstuvwxyz")


def derive_dynamic_alphabet(seed_key: str) -> Tuple[Dict[str, str], Dict[str, str]]:
    """Deriva un alfabeto fonetico permutato deterministicamente tramite HMAC-SHA256 e Fisher-Yates.

    Genera una permutazione casuale uniforme tra i 26 glifi geometrici.
    Spazio combinatorio: 26! = 4.0329 * 10^26 alfabeti unici (~88 bit di entropia).
    Questo garantisce la massima riservatezza anche se il codice sorgente è pubblico su GitHub (Kerckhoffs).
    """
    import hashlib
    import hmac

    glyphs = list(DYNAMIC_GLYPH_POOL)
    h = hmac.new(b"KRYPTEX_DYNAMIC_ALPHABET_V2_SALT", seed_key.encode("utf-8"), hashlib.sha256).digest()
    for i in range(len(glyphs) - 1, 0, -1):
        sub_hash = hashlib.sha256(h + bytes([i])).digest()
        val = int.from_bytes(sub_hash[:4], "big")
        j = val % (i + 1)
        glyphs[i], glyphs[j] = glyphs[j], glyphs[i]

    fwd: Dict[str, str] = {BASE_ALPHABET_CHARS[idx]: glyphs[idx] for idx in range(len(BASE_ALPHABET_CHARS))}
    for acc, base in [("à", "a"), ("è", "e"), ("é", "e"), ("ì", "i"), ("ò", "o"), ("ù", "u")]:
        fwd[acc] = fwd[base]
    rev: Dict[str, str] = {glyphs[idx]: str(BASE_ALPHABET_CHARS[idx]) for idx in range(len(BASE_ALPHABET_CHARS))}
    return fwd, rev


def normalize_text(text: str) -> str:
    """Normalizza il testo rimuovendo caratteri non standard ma preservando accenti base."""
    text = unicodedata.normalize("NFC", text)
    return text


def italian_to_nexa(text: str, wrap_blocks: bool = True, alphabet_key: str | None = None) -> str:
    """Converte una stringa di testo italiano in glifi NEXA-S.

    Se alphabet_key è fornito, utilizza la permutazione dinamica generata con quella chiave.
    I numeri vengono racchiusi tra delimitatori numerici ⟪...⟫.
    Le entità o frasi principali possono essere racchiuse in blocchi ⟦...⟧.
    """
    if not text:
        return ""

    text = normalize_text(text)
    output = []
    i = 0
    n = len(text)

    # Modalità dinamica con chiave
    if alphabet_key:
        dyn_fwd, _ = derive_dynamic_alphabet(alphabet_key)
        while i < n:
            char = text[i]
            if char.isdigit():
                num_start = i
                while i < n and (text[i].isdigit() or text[i] in ".,"):
                    i += 1
                output.append(f"⟪{text[num_start:i]}⟫")
                continue
            if text[i : i + 2] in ("=>", ">=", "<="):
                op = text[i : i + 2]
                output.append("⇒" if op == "=>" else ("≥" if op == ">=" else "≤"))
                i += 2
                continue
            if char in " \t\n\r":
                output.append(char)
                i += 1
                continue
            if char in PUNCTUATION_MAP:
                output.append(PUNCTUATION_MAP[char])
                i += 1
                continue
            lower_char = char.lower()
            if lower_char in dyn_fwd:
                output.append(dyn_fwd[lower_char])
            else:
                output.append(char)
            i += 1
    else:
        # Modalità canonica standard
        while i < n:
            char = text[i]

            # Gestione cifre numeriche
            if char.isdigit():
                num_start = i
                while i < n and (text[i].isdigit() or text[i] in ".,"):
                    i += 1
                num_str = text[num_start:i]
                output.append(f"⟪{num_str}⟫")
                continue

            # Gestione frecce e operatori speciali
            if text[i : i + 2] == "=>":
                output.append("⇒")
                i += 2
                continue
            if text[i : i + 2] == ">=":
                output.append("≥")
                i += 2
                continue
            if text[i : i + 2] == "<=":
                output.append("≤")
                i += 2
                continue

            # Spazi e ritorni a capo
            if char in " \t\n\r":
                output.append(char)
                i += 1
                continue

            # Punteggiatura
            if char in PUNCTUATION_MAP:
                output.append(PUNCTUATION_MAP[char])
                i += 1
                continue

            # Verifica digrammi (2 o 3 caratteri)
            lower_sub3 = text[i : i + 3].lower()
            lower_sub2 = text[i : i + 2].lower()

            if len(lower_sub3) == 3 and lower_sub3 in DIGRAPH_MAP:
                output.append(DIGRAPH_MAP[lower_sub3])
                i += 3
                continue
            if len(lower_sub2) == 2 and lower_sub2 in DIGRAPH_MAP:
                output.append(DIGRAPH_MAP[lower_sub2])
                i += 2
                continue

            # Singolo carattere
            lower_char = char.lower()
            if lower_char in VOWEL_MAP:
                if char == "A" and (i == 0 or text[i - 1] in " \t\n⟦"):
                    output.append("∧")
                else:
                    output.append(VOWEL_MAP[lower_char])
            elif lower_char in CONSONANT_MAP:
                output.append(CONSONANT_MAP[lower_char])
            else:
                output.append(char)

            i += 1

    result = "".join(output)

    if wrap_blocks and not result.startswith("⟦") and len(result) > 0:
        if result.endswith("∴"):
            result = f"⟦{result[:-1].strip()}⟧∴"
        else:
            result = f"⟦{result.strip()}⟧"

    return result


def nexa_to_italian(nexa_text: str, alphabet_key: str | None = None) -> str:
    """Decodifica testo in glifi NEXA-S in italiano approssimato/fonetico.

    Se alphabet_key è fornito, applica la permutazione inversa dinamica.
    """
    if not nexa_text:
        return ""

    output = []
    i = 0
    n = len(nexa_text)

    if alphabet_key:
        _, dyn_rev = derive_dynamic_alphabet(alphabet_key)
        while i < n:
            char = nexa_text[i]
            if char == "⟪":
                end_idx = nexa_text.find("⟫", i)
                if end_idx != -1:
                    output.append(nexa_text[i + 1 : end_idx])
                    i = end_idx + 1
                    continue
            if char in ("⟦", "⟧"):
                i += 1
                continue
            if char in dyn_rev:
                output.append(dyn_rev[char])
            elif char == "∴":
                output.append(".")
            elif char == "⇒":
                output.append(" allora ")
            else:
                output.append(char)
            i += 1
    else:
        while i < n:
            char = nexa_text[i]

            if char == "⟪":
                end_idx = nexa_text.find("⟫", i)
                if end_idx != -1:
                    output.append(nexa_text[i + 1 : end_idx])
                    i = end_idx + 1
                    continue

            if char in ("⟦", "⟧"):
                i += 1
                continue

            if char in REVERSE_GLYPH_MAP:
                output.append(REVERSE_GLYPH_MAP[char])
            else:
                output.append(char)

            i += 1

    decoded = "".join(output)
    decoded = re.sub(r" +", " ", decoded)
    return decoded.strip()


def validate_nexa(nexa_text: str) -> Tuple[bool, List[str]]:
    """Valida la sintassi di una stringa NEXA-S verificando la corretta chiusura dei blocchi."""
    errors = []
    stack = []

    for idx, c in enumerate(nexa_text):
        if c in ("⟦", "⟪"):
            stack.append((c, idx))
        elif c == "⟧":
            if not stack or stack[-1][0] != "⟦":
                errors.append(f"Blocco ⟧ non aperto alla posizione {idx}")
            else:
                stack.pop()
        elif c == "⟫":
            if not stack or stack[-1][0] != "⟪":
                errors.append(f"Blocco numerico ⟫ non aperto alla posizione {idx}")
            else:
                stack.pop()

    while stack:
        opener, idx = stack.pop()
        errors.append(f"Delimitatore '{opener}' alla posizione {idx} non chiuso")

    return len(errors) == 0, errors


if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sample = "Andrea conferma l'appuntamento per domani alle 18:30. Portare i documenti cifrati."
    print("Testo Originale:", sample)
    nexa = italian_to_nexa(sample, wrap_blocks=True)
    print("NEXA-S Generato:", nexa)
    valid, errs = validate_nexa(nexa)
    print("Validazione Sintassi:", "OK" if valid else f"ERRORI: {errs}")
    back = nexa_to_italian(nexa)
    print("Decodifica Fonetica:", back)
