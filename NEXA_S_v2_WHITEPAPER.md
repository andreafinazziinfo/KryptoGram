# NEXA-S v2.0 — Whitepaper Tecnico

## Abstract

NEXA-S v2.0 è il primo sistema di scrittura simbolica + crittografia **post-quantum ready** pubblicamente disponibile e gratuito. Integra lo stack crittografico più avanzato possibile senza costi o restrizioni, posizionandosi come riferimento per dati che devono rimanere segreti per 30+ anni.

---

## 1. Introduzione

### 1.1 Contesto

L'avvento dei computer quantistici (previsto 15-30 anni) renderà obsoleti gli algoritmi asimmetrici attuali (RSA, ECC, X25519). Dati cifrati oggi e archiviati potrebbero essere decifrati in futuro con l'algoritmo di Shor.

### 1.2 Obiettivo

NEXA-S v2.0 integra **crittografia post-quantum standardizzata NIST 2024** per proteggere dati a lungo termine, mantenendo compatibilità con stack classico per utenti che non necessitano di protezione quantum.

---

## 2. Stack Crittografico

### 2.1 Cifratura Simmetrica: XChaCha20-Poly1305

**Motivazione:**
- AEAD (Authenticated Encryption with Associated Data)
- Chiave 256 bit, nonce 192 bit (XChaCha20 riduce rischio nonce misuse)
- Immune a timing attack (implementazione software pura)
- Più sicuro di AES-GCM in assenza di hardware acceleration

**Parametri:**
- Chiave: 256 bit (32 byte)
- Nonce: 192 bit (24 byte)
- Tag autenticazione: 128 bit (16 byte)

### 2.2 Derivazione Chiavi: Argon2id

**Motivazione:**
- Winner Password Hashing Competition (2015)
- Resistente a GPU, ASIC, side-channel
- Combina resistenza memory-hard (Argon2i) e data-dependent (Argon2d)

**Parametri (v2.0):**
- Memoria: 256 MB (262144 KB)
- Iterazioni: 3
- Parallelismo: 4 thread
- Output: 256 bit (32 byte)

### 2.3 Scambio Chiavi Ibrido: X25519 + ML-KEM-768

**Motivazione:**
- **X25519**: Classico ECDH, veloce, sicuro contro attacchi classici
- **ML-KEM-768 (Kyber)**: Post-quantum KEM, standard NIST FIPS 203 (2024)
- **Ibrido**: Sicurezza contro attacchi classici E quantum

**Implementazione:**
```
shared_secret = HKDF-SHA256(
    X25519(peer_public, client_secret) || 
    ML-KEM-768-Encapsulate(peer_public)
)
```

**Dimensioni:**
- X25519 pubkey: 32 byte
- ML-KEM-768 pubkey: 1184 byte
- ML-KEM-768 ciphertext: 1088 byte
- Overhead totale: ~2.3 KB per file

### 2.4 Firma Digitale: Ed25519

**Motivazione:**
- Più veloce di RSA-4096 (10x firma, 100x verifica)
- Chiavi corte (32 byte pubblica, 64 byte firma)
- Deterministica (no rischio nonce reuse)
- Parte di libsodium/PyNaCl (gratis, auditata)

**Uso in NEXA-S:**
- Firma metadata (filename, timestamp, hash BLAKE3)
- Rilevamento manomissioni prima della decifratura
- Opzionale (flag `--sign`)

### 2.5 Hash: BLAKE3

**Motivazione:**
- 3-10x più veloce di SHA-256
- Sicurezza equivalente (256 bit output)
- Supporto hashing incrementale (file grandi)
- Parte di libsodium (gratis)

**Fallback:**
- Se BLAKE3 non disponibile: hashlib.blake2b (SHA-256 compatibile)

---

## 3. Formato Contenitore v2

### 3.1 Struttura

```
┌─────────────────────────────────────────────┐
│ Header (48 byte)                            │
│ - Magic: "NXS2" (4 byte)                    │
│ - Version: 2 (1 byte)                       │
│ - Flags: PQ, Signed (1 byte)                │
│ - Salt Argon2id (16 byte)                   │
│ - Nonce XChaCha20 (24 byte)                 │
│ - Padding riservato (2 byte)                │
├─────────────────────────────────────────────┤
│ KEM Public Keys (se flag PQ)                │
│ - ML-KEM-768 pubkey (1184 byte)             │
│ - X25519 pubkey (32 byte)                   │
├─────────────────────────────────────────────┤
│ KEM Ciphertext (se flag PQ)                 │
│ - ML-KEM-768 ciphertext (1088 byte)         │
├─────────────────────────────────────────────┤
│ Firma Ed25519 (se flag Signed)              │
│ - Verify key (32 byte)                      │
│ - Signature (64 byte)                       │
├─────────────────────────────────────────────┤
│ Metadata (JSON, cifrato)                    │
│ - filename, plaintext_bytes, padding_bytes, │
│   timestamp, hash_blake3, ecc.              │
├─────────────────────────────────────────────┤
│ Ciphertext (XChaCha20-Poly1305)             │
│ - Dati cifrati + tag (16 byte)              │
└─────────────────────────────────────────────┘
```

### 3.2 Overhead

| Modalità | Overhead |
|----------|----------|
| Legacy (v1.3) | ~200 byte |
| v2.0 PQ | +2.3 KB |
| v2.0 Signed | +96 byte |
| v2.0 PQ+Signed | +2.4 KB |

---

## 4. Sicurezza e Threat Model

### 4.1 Sicurezza Stimata

| Attacco | Sicurezza (bit) | Tempo Stimato |
|---------|-----------------|---------------|
| Classico (CPU/GPU) | 256 | > 10^77 anni |
| Quantum (Grover) | 128 | > 10^38 anni |
| Quantum (Shor su X25519) | 0 | Minuti (ma protetto da Kyber) |

**Conclusione:** L'ibrido X25519+Kyber protegge contro entrambi gli scenari.

### 4.2 Vulnerabilità Residue

1. **Computer quantistici più potenti del previsto**: Se scaling di qubit supera le stime attuali (10-15 anni invece di 30), Kyber-768 potrebbe essere vulnerabile. Mitigazione: usare Kyber-1024 (non standard NIST).

2. **Attacchi side-channel**: Implementazione software pura di XChaCha20 è immune, ma Argon2id potrebbe essere vulnerabile a cache-timing. Mitigazione: usare parametri conservativi.

3. **Backdoor nelle librerie**: PyNaCl, argon2-cffi, pqcrypto sono open source e auditati. Rischio basso ma non nullo.

4. **Endpoint compromesso**: Se il PC dell'utente è infetto (keylogger, malware), nessuna crittografia protegge. Fuori scope.

---

## 5. Performance

### 5.1 Benchmark (stimati, Intel i7-12700K)

| Operazione | Tempo |
|------------|-------|
| Generazione chiave Kyber | 50 ms |
| Encapsulation Kyber | 100 ms |
| Decapsulation Kyber | 150 ms |
| Cifratura XChaCha20 (1 MB) | 50 ms |
| Argon2id (256 MB, 3 iter) | 200 ms |
| Firma Ed25519 (1 KB) | 5 ms |
| Verifica Ed25519 | 15 ms |
| Hash BLAKE3 (1 MB) | 5 ms |

### 5.2 Confronto con v1.3

| Metrica | v1.3 (Legacy) | v2.0 (PQ) | Delta |
|---------|---------------|-----------|-------|
| Cifratura 1 MB | 50 ms | 55 ms | +10% |
| Generazione chiave | 1 ms | 150 ms | +150x |
| Overhead file | 200 byte | 2.5 KB | +12x |

**Conclusione:** Overhead accettabile per sicurezza post-quantum.

---

## 6. Compatibilità e Migrazione

### 6.1 Forward Compatibility

- v2.0 legge file v1.3 (flag `--legacy`)
- v1.3 NON legge file v2.0 (header "NXS2" vs "NXS1")

### 6.2 Migrazione Consigliata

1. Decifrare tutti i file v1.3
2. Ricifrare con v2.0 `--pq --sign`
3. Archiviare chiavi Kyber in backup sicuro

---

## 7. Conclusioni

NEXA-S v2.0 rappresenta lo **stato dell'arte della crittografia gratuita e pubblicamente disponibile** (2026):

- ✅ Post-quantum ready (NIST FIPS 203)
- ✅ AEAD moderno (XChaCha20-Poly1305)
- ✅ KDF memory-hard (Argon2id)
- ✅ Firma digitale veloce (Ed25519)
- ✅ Hash ultra-veloce (BLAKE3)

**Nessun algoritmo più sicuro è disponibile senza costi o restrizioni.**

---

## 8. Riferimenti

1. NIST FIPS 203: ML-KEM (Kyber) - https://csrc.nist.gov/pubs/fips/203/final
2. RFC 8439: XChaCha20-Poly1305 - https://datatracker.ietf.org/doc/html/rfc8439
3. RFC 8032: Ed25519 - https://datatracker.ietf.org/doc/html/rfc8032
4. Argon2: https://github.com/P-H-C/phc-winner-argon2
5. BLAKE3: https://github.com/BLAKE3-team/BLAKE3

---

*Andrea Finazzi - Settembre 2026*
