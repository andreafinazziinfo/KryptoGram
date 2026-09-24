# PIANO 2 — Difesa Cyber Security, Protezione IP & Anti-Scraping (Framework 9P)

Questo piano definisce la strategia di **difesa attiva e protezione della proprietà intellettuale (IP)** per CycleLab Terminal e il Core Matassa. È progettato analizzando a ritroso esattamente **le tecniche di reverse engineering, scraping e decompilazione che abbiamo appena utilizzato sui competitor**, con l'obiettivo di rendere CycleLab completamente immune a questo tipo di analisi.

---

## 🛡️ VULNERABILITÀ DEI COMPETITOR (Cosa abbiamo sfruttato)

| Vettore di Attacco Utilizzato da Noi | Vulnerabilità Trovata nei Competitor | Rischio per CycleLab se Non Protetto |
|---|---|---|
| **Wget / Scrapy / Crawl4AI** | Pagine e route HTML pubbliche prive di controlli bot approfonditi. | Drenaggio completo dell'interfaccia e dei contenuti. |
| **JS De-bundling & Beautify** | Algoritmi ciclici e costanti scritti in chiaro nei chunk Webpack/Vite. | Furto delle formule proprietarie del Core Matassa. |
| **Electron ASAR Unpacking** | Pacchetti `app.asar` non crittografati contenenti sorgenti `.cjs` leggibili. | Clonazione immediata dell'applicazione desktop. |
| **Playwright Response Interception** | Chiamate API e WebSocket in formato JSON in chiaro e senza firma. | Esfiltrazione di tick, calcoli ciclici e dataset storici. |

---

## 🏛️ IL FRAMEWORK 9P APPLICATO ALLA DIFESA DI CYCLELAB

```
[ 1. Purpose ] ──────> [ 2. Problem ] ──────> [ 3. Product ]
       │                      │                      │
[ 4. Platform ] ─────> [ 5. Process ] ─────> [ 6. People ]
       │                      │                      │
[ 7. Performance ] ──> [ 8. Protection ] ──> [ 9. Phases ]
```

---

### 1. PURPOSE (Obiettivo di Sicurezza)
* **Missione**: Rendere il Core Matassa e l'ecosistema CycleLab una **scatola nera ermetica (Black Box)**.
* **Obiettivo Fondamentale**: Impedire a qualsiasi soggetto (umano o agent AI) di replicare le formule matematiche, intercettare i dati grezzi o clonare l'applicazione desktop, garantendo che anche in caso di scaricamento dei file non sia possibile estrarre la proprietà intellettuale.

---

### 2. PROBLEM (Minacce Identificate)
1. **Minaccia Algoritmica**: Tentativi di estrarre le formule del Test di Bartels, sintesi armonica e proiezioni cicliche dai file JavaScript client-side.
2. **Minaccia Automazione Headless**: Bot basati su Playwright, Puppeteer, Scrapling o Scrapy che navigano il terminale per prelevare segnali e dati.
3. **Minaccia Decompilazione Desktop**: De-packaging del file `.exe` per estrarre il codice del client.
4. **Minaccia Sniffing di Rete**: Monitoraggio delle connessioni WebSocket/REST per clonare i feed ciclici in tempo reale.

---

### 3. PRODUCT / DEFENSIVE PROPOSITION (Contromisure di Difesa)

#### A. Principio "Zero Math in Client" (Isolamento Totale delle Formule)
* **Regola Assoluta**: Il browser/client **non deve mai calcolare le formule del Core Matassa**.
* Tutto il calcolo (Bartels, Goertzel, FLD, sintesi composita) avviene **esclusivamente sul server backend protetto**.
* Il client riceve unicamente le coordinate grafiche pre-calcolate $(x, y)$ necessarie al rendering sul canvas Klinecharts. Anche de-offuscando l'intero JavaScript, un attaccante troverà solo istruzioni di disegno grafico e **zero formule matematiche o pesi armonici**.

#### B. Streaming di Dati Vettoriali Binari (Protobuf / FlatBuffers)
* Sostituzione dei payload JSON in chiaro con **Protocol Buffers (Protobuf)** o **FlatBuffers** binari e compressi.
* Lo sniffing di rete tramite Playwright o DevTools mostrerà solo sequenze di byte binari indecifrabili senza lo schema di compilazione.

---

### 4. PLATFORM & DEFENSIVE ARCHITECTURE (Infrastruttura di Protezione)

```
┌─────────────────────────────────────────────────────────────┐
│                       TRAFFICO IN ENTRATA                   │
│   (Utente Legittimo vs Bot Playwright / Scrapy / Curl)      │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│             LAYER 1: EDGE SECURITY (Cloudflare)             │
│  • Cloudflare Turnstile: Sfida invisibile anti-headless     │
│  • JA3 / JA4 TLS Fingerprinting: Blocco stack Python/Scrapy │
│  • WAF & IP Reputation Filtering                            │
└──────────────────────────────┬──────────────────────────────┘
                               │ (Richieste Validate)
┌──────────────────────────────▼──────────────────────────────┐
│           LAYER 2: API GATEWAY (Firma Crittografica)        │
│  • HMAC Request Signing: Firma con chiave rotante (30s)     │
│  • Nonce univoco anti-replay (blocca chiamate duplicate)    │
│  • Rate Limiting adattivo (Leaky Bucket per IP e Account)   │
└──────────────────────────────┬──────────────────────────────┘
                               │ (Richieste Autenticate)
┌──────────────────────────────▼──────────────────────────────┐
│           LAYER 3: CYCLELAB SECURE CORE (Backend)           │
│  • Core Matassa Engine isolato (Zero formule nel client)    │
│  • Watermarking Steganografico sui dati distribuiti         │
│  • Serializzazione Binaria Protobuf                         │
└─────────────────────────────────────────────────────────────┘
```

#### Dettagli Tecnologici:
1. **JA3 / JA4 Fingerprinting**:
   I tool di scraping (Scrapy, `requests`, `aiohttp`, `curl`) negoziano la connessione TLS con ciphersuite diverse dai veri browser Chrome/Edge. Il gateway controlla la firma JA4 e rifiuta a livello di socket qualsiasi connessione bot prima che tocchi il backend.
2. **HMAC Request Signing**:
   Ogni chiamata REST o handshake WebSocket contiene un header `X-Signature: HMAC-SHA256(timestamp + nonce + payload, secret_rotante)`. Uno script esterno non può generare chiamate valide senza eseguire il codice crittografico di sessione.
3. **Hardening Desktop Electron (Protezione dell'.exe)**:
   - **Bytenode V8 Compilation**: I file JavaScript dell'app Electron vengono compilati in **bytecode binario V8 (`.jsc`)**. Scompattare `app.asar` restituirà solo binari nativi non de-offuscabili con `js-beautify`.
   - **Native Addons Rust (Node-API)**: La gestione concorrente delle schede e le logiche critiche vengono compilate in librerie binarie C++/Rust (`.node` / `.dll`) senza simboli di debug.
   - **Anti-Debugging**: Rilevamento e blocco automatico dei flag `--remote-debugging-port` e disattivazione permanente di DevTools in produzione.

---

### 5. PROCESS / SECOPS PIPELINE (Monitoraggio & Reazione Attiva)
1. **Rilevamento Anomalie di Frequenza**: Se un utente richiede più di 15 cambi di layout o 100 richieste klines al minuto, l'account riceve un rate-limit istantaneo con richiesta di verifica biometrica o Captcha invisibile.
2. **Honeypot Endpoints**: Inserimento nel DOM di endpoint nascosti invisibili all'utente (es. link `display: none`). Se uno scraper li visita, l'IP viene inserito nella blacklist globale permanente.
3. **Rotazione Chiavi di Sessione**: Rinnovo continuo delle chiavi di sessione crittografiche ogni 10 minuti via WebSocket.

---

### 6. PEOPLE / ACCESS GOVERNANCE (Gestione Account & Sessioni)
* **Device Fingerprinting Univoco**: Associazione dell'account al canvas hash e alla scheda grafica dell'utente: impedisce l'uso simultaneo delle stesse credenziali su più macchine o script di scraping paralleli.
* **Revocabilità Istantanea**: Capacità del backend di invalidare istantaneamente il token JWT in caso di comportamento anomalo rilevato.

---

### 7. PERFORMANCE & OVERHEAD (Impatto sul Sistema)
* **Overhead Crittografico HMAC**: $< 2\text{ ms}$ per richiesta.
* **Vantaggio di Protobuf vs JSON**: I payload binari sono fino al **60% più leggeri** e del **40% più veloci da decodificare**, migliorando la reattività di CycleLab invece di rallentarla.
* **Esperienza Utente**: Trasparente al 100% per i trader umani; completamente bloccante per bot e strumenti di automazione.

---

### 8. PROTECTION & WATERMARKING (Difesa Legale e Forense)
* **Watermarking Steganografico dei Dati**: Iniezione di micro-variazioni impercettibili ($10^{-5}$) nei dati dei grafici consegnati a ciascun account. Se un competitor o un bot esfiltra i dati e li rivende/ripubblica, le micro-variazioni identificano matematicamente l'account autore della fuga per azione legale immediata.
* **Terms of Service (ToS)**: Clausole vincolanti con divieto esplicito di reverse engineering, scraping automatizzato ed esfiltrazione di codice.

---

### 9. PHASES / PACE (Roadmap di Blindatura in 3 Fasi)

| Fase di Blindatura | Interventi Chiave | Risultato di Sicurezza |
|---|---|---|
| **Fase 1: Network & Bot Shield** | Cloudflare Turnstile, filtro JA4, HMAC signing su API | Blocca Scrapy, Crawl4AI, Wget e script curl. |
| **Fase 2: Core Isolation & Protobuf** | Formule Matassa solo su backend, streaming binario Protobuf | Rende inutile il de-bundling JS (zero formule esposte). |
| **Fase 3: Desktop App Shielding** | Compilazione Bytenode V8 (`.jsc`), anti-debugging Electron | Blocca l'estrazione e l'analisi di `app.asar`. |
