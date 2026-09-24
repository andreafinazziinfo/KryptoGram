# NEXA-S — Piano Completo Definitivo (Roadmap 2026-2027)

## Executive Summary

NEXA-S è un sistema ibrido unico: **alfabeto fonetico simbolico** + **crittografia moderna**. Per raggiungere l'eccellenza (9,5-10/10), dobbiamo trasformarlo da progetto "indie avanzato" a **piattaforma matura, auditata e adottata**.

## 1. Roadmap Strategica per Aree

### 1.1 Originalità e Coerenza Concettuale (9,3 → 9,8)

**Obiettivo:** Diventare lo standard de facto per "scritture costruite + sicurezza".

**Azioni Chiave:**
- **Fonetica v2.0**: Copertura totale di dialetti italiani e prestiti inglesi comuni.
- **Tavola Glyph Ufficiale**: Poster grafico ad alta risoluzione.
- **Showcase Lunghi**: Racconto breve (2k parole), documento tecnico finanziario, poesia.
- **Multilingua**: Tabelle fonetiche per EN/ES/DE (fase avanzata).

**Deliverable:**
- `nexa_phonetics_v2.md`
- `assets/glyph_table.png`
- `showcase/racconto_completo.md`

### 1.2 Qualità Implementazione Software (8,7 → 9,6)

**Obiettivo:** Libreria "production-grade", testata e type-checked.

**Azioni Chiave:**
- **Refactoring Pacchetto**: Struttura `nexa/` modulare (`phonetics`, `parser`, `validator`).
- **Parser Inverso Completo**: NEXA-S → Italiano con gestione ambiguità contestuale.
- **Test Avanzati**: `hypothesis` per property-based testing, fuzzing.
- **CI/CD Evoluta**: Lint (ruff), Type Check (mypy), Build wheel.
- **GUI Production**: Tkinter avanzato o WebApp locale (Flask).
- **Plugin VS Code Reale**: Comandi encrypt/decrypt funzionanti.

**Deliverable:**
- Pacchetto Python `nexa` su PyPI (o locale).
- Suite test > 80% copertura.
- GUI stabile.
- Extension VS Code pubblicabile.

### 1.3 Sicurezza Crittografica (8,8 → 9,7)

**Obiettivo:** Auditabile, robusta, integrata con standard asimmetrici.

**Azioni Chiave:**
- **Audit Interno**: Review codice crittografico documentata.
- **Integrazione Age Stabile**: Wrapper nativo per X25519 nella CLI.
- **Test Crittografici**: Verifica formale di nonce, salt, tag autenticazione.
- **Modalità High-Security**: Parametri Argon2id aggressivi, padding fisso.
- **Audit Esterno**: Coinvolgimento esperto sicurezza (report pubblico).

**Deliverable:**
- `audit_report.md`
- CLI con flag `--age-recipient`.
- Report audit esterno.

### 1.4 Documentazione e Usabilità (9,0 → 9,8)

**Obiettivo:** Accessibile a tutti, tecnica per esperti.

**Azioni Chiave:**
- **Tutorial Multilivello**: Base (utente), Dev (libreria), Security (threat model).
- **Materiale Visivo**: Screenshot GUI, video demo, hex dump commentati.
- **Specifiche Tecniche**: Formato contenitore byte-level, grammatica BNF.
- **FAQ Espansa**: Basata su casi reali.

**Deliverable:**
- `docs/tutorials/` completi.
- `docs/spec/` dettagliate.
- Media kit (img/video).

### 1.5 Adozione e Nicchia (7,5 → 9,5)

**Obiettivo:** Community attiva, casi d'uso reali.

**Azioni Chiave:**
- **Repo Pubblico**: GitHub organizzato con issue/PR template.
- **Casi d'Uso Killer**: Diario trading cifrato, appunti security, zine artistica.
- **Plugin Ecosistema**: Obsidian, Logseq, CLI per password manager.
- **Visibilità**: Articoli, demo live, community building.

**Deliverable:**
- Repo GitHub pubblico.
- 3 casi d'uso documentati.
- Plugin Obsidian.

## 2. Timeline Operativa

| Fase | Durata | Focus | Milestone |
|---|---|---|---|
| **1. Consolidamento** | 1-2 mesi | Fonetica, Libreria, Test | Pacchetto `nexa` stabile, test >80% |
| **2. Sicurezza & Tooling** | 2-3 mesi | Audit, Age, GUI | CLI con age, GUI production, audit interno |
| **3. Adozione** | 3-6 mesi | Community, Plugin, Docs | Repo pubblico, plugin Obsidian, articoli |

## 3. Criteri di Successo (9,5+)

- **Originalità**: Nessun comparabile diretto (alfabeto + crypto auditata).
- **Implementazione**: Usabile solo con docs, senza leggere codice.
- **Sicurezza**: Report audit pubblico, integrazione standard (age).
- **Docs**: Utente produttivo in <30 min.
- **Adozione**: Casi d'uso reali e replicabili.

## 4. Prossimi Passi Immediati (Fase 1)

1. Refactoring libreria `nexa/`.
2. Implementazione parser inverso completo.
3. Setup `hypothesis` per test avanzati.
4. Scrittura specifiche fonetiche v2.

---

*Questo piano trasforma NEXA-S da progetto personale a piattaforma di riferimento.*
