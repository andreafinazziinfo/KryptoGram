# NEXA-S v2.0 — Piano di Integrazione "Maximum Security Free Stack"

## Obiettivo

Portare NEXA-S al **massimo livello di sicurezza crittografica gratuita e pubblicamente disponibile** (2026), integrando:

1. **Post-Quantum Cryptography (PQC)** - Standard NIST 2024
2. **Firme Digitali Moderne** - Ed25519
3. **Hash Ultra-Veloci** - BLAKE3
4. **Hardening Operativo** - Best practice massime

**Stack Finale:**
```
┌──────────────────────────────────────────────┐
│  Cifratura: XChaCha20-Poly1305 (256 bit)     │ ← Migliore AEAD software
│  KDF: Argon2id (256 MB, 3 iter, p=4)         │ ← Migliore KDF
│  Scambio Chiavi: ML-KEM-768 (Kyber)          │ ← Post-Quantum NIST 2024
│  + X25519 (ibrido classico)                  │ ← Fallback compatibile
│  Firma: Ed25519                              │ ← Firma digitale moderna
│  Hash: BLAKE3                                │ ← Più veloce di SHA-256
│  CSPRNG: secrets / dev/urandom               │ ← Random crittografico
└──────────────────────────────────────────────┘
```

---

## 1. Roadmap di Integrazione

### **Fase 1: Fondamenta (Settimane 1-2)**
- [ ] Audit dipendenze attuali (PyNaCl, argon2-cffi)
- [ ] Integrazione libreria PQC (`liboqs-python` o `pqcrypto`)
- [ ] Integrazione BLAKE3 (`blake3` Python bindings)
- [ ] Integrazione Ed25519 (già in PyNaCl, ma esporre API)

### **Fase 2: Refactoring Crittografico (Settimane 3-4)**
- [ ] Creare `nexa/crypto.py` modulo dedicato
- [ ] Implementare **ibrido X25519 + ML-KEM-768** per scambio chiavi
- [ ] Sostituire SHA-256 con BLAKE3 per hash interni
- [ ] Aggiungere firma Ed25519 opzionale per metadata

### **Fase 3: CLI e API Aggiornate (Settimane 5-6)**
- [ ] Nuovo flag `--pq` per abilitare modalità post-quantum
- [ ] Nuovo flag `--sign` per firmare con Ed25519
- [ ] Mantenere compatibilità con formato legacy (flag `--legacy`)
- [ ] Documentare trade-off (performance vs sicurezza)

### **Fase 4: Test e Validazione (Settimane 7-8)**
- [ ] Test vettoriali NIST per ML-KEM-768
- [ ] Benchmark performance (PQC vs classico)
- [ ] Audit interno sicurezza (review codice)
- [ ] Test interoperabilità (invio file tra versioni diverse)

### **Fase 5: Documentazione e Rilascio (Settimane 9-10)**
- [ ] Aggiornare threat model con considerazioni quantum
- [ ] Scrivere whitepaper tecnico (10-15 pagine)
- [ ] Rilascio v2.0 su GitHub + PyPI
- [ ] Articolo divulgativo "NEXA-S Post-Quantum Ready"

---

## 2. Dettaglio Tecnico per Componente

### **2.1 Post-Quantum Key Encapsulation (ML-KEM-768 / Kyber)**

**Perché:**
- Standard NIST 2024 (FIPS 203)
- Resistente ad attacchi con computer quantistici
- Chiavi pubbliche ~1.2 KB, ciphertext ~1.5 KB (accettabile)

**Implementazione:**
```python
from pqcrypto.kem.kyber768 import generate_keypair, encapsulate, decapsulate

# Generazione chiave (una volta per destinatario)
public_key, secret_key = generate_keypair()

# Mittente: genera shared secret + ciphertext
shared_secret, ciphertext = encapsulate(public_key)

# Destinatario: recupera shared secret
shared_secret = decapsulate(secret_key, ciphertext)
```

**Integrazione in NEXA-S:**
- Usare shared secret (32 byte) come chiave per XChaCha20-Poly1305
- Memorizzare ciphertext nel contenitore (overhead ~1.5 KB per file)
- Modalità ibrida: `shared_secret = HKDF(X25519_output || ML-KEM_output)`

### **2.2 Firma Digitale Ed25519**

**Perché:**
- Più veloce di RSA-4096 (10x in firma, 100x in verifica)
- Chiavi più corte (32 byte pubblica, 64 byte firma)
- Deterministica (no rischio nonce reuse)

**Implementazione:**
```python
import nacl.signing

# Generazione chiave
signing_key = nacl.signing.SigningKey.generate()
verify_key = signing_key.verify_key

# Firma
signed = signing_key.sign(message)

# Verifica
verify_key.verify(signed)  # solleva eccezione se invalida
```

**Integrazione in NEXA-S:**
- Opzionale: flag `--sign` per firmare metadata (filename, timestamp, hash)
- Firma inclusa nel contenitore (overhead ~64 byte)
- Utile per rilevare manomissioni prima della decifratura

### **2.3 Hash BLAKE3**

**Perché:**
- 3-10x più veloce di SHA-256
- Sicurezza equivalente (256 bit output)
- Supporto hashing incrementale (utile per file grandi)

**Implementazione:**
```python
import blake3

hasher = blake3.blake3()
hasher.update(b"data chunk 1")
hasher.update(b"data chunk 2")
digest = hasher.digest()  # 32 byte
```

**Integrazione in NEXA-S:**
- Sostituire SHA-256 in:
  - Derivazione chiavi (affiancato ad Argon2id)
  - Hash metadata per firma Ed25519
  - Checksum integrità file

### **2.4 Hardening Operativo**

**Misure aggiuntive:**
- [ ] **Memory locking**: `mlock()` per chiavi in RAM (no swap)
- [ ] **Zeroing**: Cancellazione sicura chiavi dopo uso (`nacl.utils.sodium_memzero`)
- [ ] **Timing-safe comparisons**: Usare `hmac.compare_digest()` ovunque
- [ ] **Fail-secure**: Se qualcosa fallisce, non leak di informazioni parziali

---

## 3. Nuovo Formato Contenitore v2

```
┌─────────────────────────────────────────────────────┐
│ Header (legacy compatibile)                         │
│ - Magic: "NXS2" (4 byte)                            │
│ - Version: 2 (1 byte)                               │
│ - Flags: bit 0=PQ, bit 1=Signed (1 byte)            │
├─────────────────────────────────────────────────────┤
│ KDF Parameters                                      │
│ - Salt (16 byte)                                    │
│ - Argon2id params (mem, time, parallelism)          │
├─────────────────────────────────────────────────────┤
│ Post-Quantum Key Encapsulation (se flag PQ)         │
│ - ML-KEM-768 public key (1184 byte)                 │
│ - ML-KEM-768 ciphertext (1088 byte)                 │
│ - X25519 public key (32 byte) [ibrido]              │
├─────────────────────────────────────────────────────┤
│ Firma Ed25519 (se flag Signed)                      │
│ - Verify key (32 byte)                              │
│ - Signature su metadata (64 byte)                   │
├─────────────────────────────────────────────────────┤
│ Nonce XChaCha20 (24 byte)                           │
├─────────────────────────────────────────────────────┤
│ Metadata (JSON, cifrato)                            │
│ - filename, plaintext_bytes, padding_bytes,         │
│   timestamp, hash_blake3, ecc.                      │
├─────────────────────────────────────────────────────┤
│ Ciphertext (XChaCha20-Poly1305)                     │
│ - Dati cifrati + tag autenticazione (16 byte)       │
└─────────────────────────────────────────────────────┘
```

**Overhead totale:**
- Legacy: ~200 byte
- PQ: +2.3 KB (Kyber pubkey + ciphertext)
- Signed: +96 byte (verify key + signature)

---

## 4. Dipendenze da Aggiungere

```toml
[project.optional-dependencies]
pq = [
    "pqcrypto-kyber>=0.1.0",  # ML-KEM-768
    "blake3>=0.4.0",          # BLAKE3 hash
]
```

**Installazione:**
```bash
pip install "nexa-s[pq]"
```

---

## 5. Benchmark Stimati

| Operazione | Legacy (v1.3) | PQ (v2.0) | Delta |
|------------|---------------|-----------|-------|
| Generazione chiave | 1 ms | 50 ms (Kyber) | +50x |
| Encapsulation | - | 100 ms | Nuovo |
| Cifratura 1 MB | 50 ms | 55 ms | +10% |
| Decifratura 1 MB | 50 ms | 55 ms | +10% |
| Firma 1 KB | - | 5 ms | Nuovo |
| Verifica firma | - | 15 ms | Nuovo |

**Conclusione:** Overhead accettabile (~10% su cifratura, chiave one-time).

---

## 6. Criteri di Accettazione

- [ ] Tutti i test legacy passano in modalità `--legacy`
- [ ] Test PQC passano con vettori NIST
- [ ] Benchmark: <100 ms overhead per file <10 MB
- [ ] Documentazione aggiornata (threat model, whitepaper)
- [ ] Audit interno completato (nessuna vulnerabilità critica)

---

## 7. Timeline e Milestone

| Settimana | Milestone | Deliverable |
|-----------|-----------|-------------|
| 1-2 | Fondamenta | `liboqs`, `blake3` integrati |
| 3-4 | Refactoring | `nexa/crypto.py`, ibrido X25519+Kyber |
| 5-6 | CLI | Flag `--pq`, `--sign`, `--legacy` |
| 7-8 | Test | Vettori NIST, benchmark, audit |
| 9-10 | Rilascio | v2.0 su GitHub + PyPI, whitepaper |

---

## 8. Rischio e Mitigazione

| Rischio | Impatto | Mitigazione |
|---------|---------|-------------|
| Librerie PQC immature | Alto | Usare `pqcrypto` (maintained da OpenQuantumSafe) |
| Performance inaccettabili | Medio | Modalità `--legacy` per fallback |
| Incompatibilità forward | Alto | Header versionato, supporto legacy per 2 anni |
| Bug crittografici | Critico | Audit interno + test vettoriali NIST |

---

## 9. Conclusione

Con questo piano, **NEXA-S v2.0 diventerà uno dei pochi tool gratuiti e pubblicamente disponibili con sicurezza post-quantum**, posizionandosi come riferimento per:

- Dati che devono rimanere segreti per 30+ anni
- Utenti paranoia-compatibili che vogliono "il massimo del gratis"
- Nicchia privacy + quantum-aware

**Nessun algoritmo più sicuro è disponibile pubblicamente senza costi o restrizioni.**
