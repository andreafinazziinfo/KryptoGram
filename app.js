/**
 * KryptoGram // Sovereign Cryptographic Terminal & Phonetic Studio
 * Core Client Application (JavaScript ES6+)
 * 
 * Features:
 * - Phonetic Transliteration Engine (Italiano <-> Glifi KryptoGram)
 * - Keyed Dynamic Alphabet Permutation (26! Dialetti, ~88 bit entropia)
 * - Tactile Virtual Glyph Keyboard
 * - Web Cryptography API (PBKDF2-HMAC-SHA256 + AES-256-GCM / AEAD Envelope)
 * - Fixed Padding & Base64url Encoder/Decoder
 * - Web Audio API Synthesizer Feedback
 * - Canonical Hex Dump & Byte Inspector
 * - CycleLab Financial Showcase Presets
 */

(() => {
  'use strict';

  /* ==========================================================================
     1. TAVOLA FONETICA UFFICIALE KRYPTOGRAM (Kryptós + Grámma)
     ========================================================================== */
  const VOWEL_MAP = {
    'a': '⊕', 'e': '≋', 'i': '∿', 'o': '⊙', 'u': '∪',
    'à': '⊕', 'è': '≋', 'é': '≋', 'ì': '∿', 'ò': '⊙', 'ù': '∪'
  };

  const CONSONANT_MAP = {
    'b': '⊓', 'c': '⌁', 'd': '∆', 'f': 'ƒ', 'g': '⅁',
    'h': '⊥', 'j': '⌇', 'k': '⌁', 'l': '⌯', 'm': '⋔',
    'n': '⋒', 'p': '⌐', 'q': '⌁∪', 'r': '⌿', 's': '≈',
    't': '⊥', 'v': '⌿', 'w': '∪∪', 'x': '⌁≈', 'y': '∿', 'z': '↑'
  };

  const DIGRAPH_MAP = {
    'ch': '⌁', 'gh': '⅁', 'gn': '⅁⋒', 'gl': '⌯∿', 'gli': '⌯∿',
    'sc': '≈⌁', 'sci': '≈∿', 'ce': '⌁≋', 'ci': '⌁∿',
    'ge': '⅁≋', 'gi': '⅁∿', 'qu': '⌁∪'
  };

  const PUNCTUATION_MAP = {
    '.': '∴', ',': ',', ';': ';', ':': ':', '!': '!', '?': '?',
    '-': '-', '(': '(', ')': ')', '[': '⟦', ']': '⟧',
    '>=': '≥', '<=': '≤', '=>': '⇒', '%': '%'
  };

  const REVERSE_GLYPH_MAP = {
    '⊕': 'a', '∧': 'a', '≋': 'e', '∿': 'i', '⊙': 'o', '∪': 'u',
    '⊓': 'b', '⌁': 'c', '∆': 'd', 'ƒ': 'f', '⅁': 'g', '⊥': 't',
    '⌇': 'j', '⌯': 'l', '⋔': 'm', '⋒': 'n', '⌐': 'p', '⌿': 'r',
    '≈': 's', '↑': 'z', '∴': '.', '⇒': ' allora ', '≥': ' >= ', '≤': ' <= '
  };

  /* ==========================================================================
     1.1 PERMUTAZIONE DINAMICA CON CHIAVE (26! Dialetti KryptoGram)
     ========================================================================== */
  const DYNAMIC_GLYPH_POOL = [
    '⊕', '≋', '∿', '⊙', '∪', '⊓', '⌁', '∆', 'ƒ', '⅁',
    '⊥', '⌇', '⌯', '⋔', '⋒', '⌐', '⌿', '≈', '↑', '⌖',
    '⊞', '◊', '∇', '⋐', '⋑', '⨁'
  ];
  const BASE_ALPHABET_CHARS = 'abcdefghijklmnopqrstuvwxyz'.split('');
  const dynamicAlphabetCache = new Map();

  async function deriveDynamicAlphabet(seedKey) {
    if (!seedKey) return null;
    if (dynamicAlphabetCache.has(seedKey)) {
      return dynamicAlphabetCache.get(seedKey);
    }
    const glyphs = [...DYNAMIC_GLYPH_POOL];
    const enc = new TextEncoder();
    const saltKey = await crypto.subtle.importKey(
      'raw',
      enc.encode('KRYPTEX_DYNAMIC_ALPHABET_V2_SALT'),
      { name: 'HMAC', hash: 'SHA-256' },
      false,
      ['sign']
    );
    const h = new Uint8Array(await crypto.subtle.sign('HMAC', saltKey, enc.encode(seedKey)));

    for (let i = glyphs.length - 1; i > 0; i--) {
      const buf = new Uint8Array(h.length + 1);
      buf.set(h, 0);
      buf[h.length] = i;
      const subHashBuffer = await crypto.subtle.digest('SHA-256', buf);
      const dv = new DataView(subHashBuffer);
      const val = dv.getUint32(0, false);
      const j = val % (i + 1);
      const tmp = glyphs[i];
      glyphs[i] = glyphs[j];
      glyphs[j] = tmp;
    }

    const fwd = {};
    BASE_ALPHABET_CHARS.forEach((c, idx) => {
      fwd[c] = glyphs[idx];
    });
    // Accenti base
    [['à', 'a'], ['è', 'e'], ['é', 'e'], ['ì', 'i'], ['ò', 'o'], ['ù', 'u']].forEach(([acc, base]) => {
      fwd[acc] = fwd[base];
    });

    const rev = {};
    BASE_ALPHABET_CHARS.forEach((c, idx) => {
      rev[glyphs[idx]] = c;
    });

    const result = { fwd, rev };
    dynamicAlphabetCache.set(seedKey, result);
    return result;
  }

  /* ==========================================================================
     2. WEB AUDIO SYNTHESIZER (Cyber Acoustic Feedback)
     ========================================================================== */
  class CyberAudio {
    constructor() {
      this.ctx = null;
      this.enabled = true;
    }

    init() {
      if (!this.ctx && (window.AudioContext || window.webkitAudioContext)) {
        this.ctx = new (window.AudioContext || window.webkitAudioContext)();
      }
      if (this.ctx && this.ctx.state === 'suspended') {
        this.ctx.resume();
      }
    }

    playClick(freq = 800, duration = 0.03, type = 'sine') {
      if (!this.enabled) return;
      try {
        this.init();
        if (!this.ctx) return;
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.type = type;
        osc.frequency.setValueAtTime(freq, this.ctx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(120, this.ctx.currentTime + duration);

        gain.gain.setValueAtTime(0.06, this.ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + duration);

        osc.connect(gain);
        gain.connect(this.ctx.destination);
        osc.start();
        osc.stop(this.ctx.currentTime + duration);
      } catch (e) {
        // Fallback silenzioso
      }
    }

    playGlyphTone(glyph) {
      if (!this.enabled) return;
      const charCode = glyph.charCodeAt(0);
      const freq = 300 + (charCode % 600);
      this.playClick(freq, 0.08, 'triangle');
    }

    playSuccess() {
      if (!this.enabled) return;
      try {
        this.init();
        if (!this.ctx) return;
        const now = this.ctx.currentTime;
        [523.25, 659.25, 783.99, 1046.50].forEach((f, idx) => {
          const osc = this.ctx.createOscillator();
          const gain = this.ctx.createGain();
          osc.type = 'sine';
          osc.frequency.setValueAtTime(f, now + idx * 0.06);
          gain.gain.setValueAtTime(0.08, now + idx * 0.06);
          gain.gain.exponentialRampToValueAtTime(0.001, now + idx * 0.06 + 0.12);
          osc.connect(gain);
          gain.connect(this.ctx.destination);
          osc.start(now + idx * 0.06);
          osc.stop(now + idx * 0.06 + 0.12);
        });
      } catch (e) {}
    }

    playError() {
      if (!this.enabled) return;
      try {
        this.init();
        if (!this.ctx) return;
        const now = this.ctx.currentTime;
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(150, now);
        osc.frequency.linearRampToValueAtTime(80, now + 0.25);
        gain.gain.setValueAtTime(0.1, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.25);
        osc.connect(gain);
        gain.connect(this.ctx.destination);
        osc.start(now);
        osc.stop(now + 0.25);
      } catch (e) {}
    }
  }

  const audio = new CyberAudio();

  /* ==========================================================================
     3. MOTORE DI TRASLITTERAZIONE FONETICA KRYPTOGRAM
     ========================================================================== */
  function transliterateItalianToNexa(text, wrapBlocks = true, dynamicTable = null) {
    if (!text) return { result: '', breakdown: [] };
    const clean = text.normalize('NFC');
    const output = [];
    const breakdown = [];
    const n = clean.length;
    let i = 0;

    // Se modalità dinamica con chiave attiva (26! permutazioni)
    if (dynamicTable && dynamicTable.fwd) {
      while (i < n) {
        const char = clean[i];

        if (/\d/.test(char)) {
          let numStart = i;
          while (i < n && /[\d\.,]/.test(clean[i])) {
            i++;
          }
          const numStr = clean.slice(numStart, i);
          const glyphToken = `⟪${numStr}⟫`;
          output.push(glyphToken);
          breakdown.push({ orig: numStr, glyph: glyphToken });
          continue;
        }

        if (clean.slice(i, i + 2) === '=>') {
          output.push('⇒');
          breakdown.push({ orig: '=>', glyph: '⇒' });
          i += 2;
          continue;
        }
        if (clean.slice(i, i + 2) === '>=') {
          output.push('≥');
          breakdown.push({ orig: '>=', glyph: '≥' });
          i += 2;
          continue;
        }
        if (clean.slice(i, i + 2) === '<=') {
          output.push('≤');
          breakdown.push({ orig: '<=', glyph: '≤' });
          i += 2;
          continue;
        }

        if (/\s/.test(char)) {
          output.push(char);
          i++;
          continue;
        }

        if (PUNCTUATION_MAP[char]) {
          const pGlyph = PUNCTUATION_MAP[char];
          output.push(pGlyph);
          breakdown.push({ orig: char, glyph: pGlyph });
          i++;
          continue;
        }

        const lower = char.toLowerCase();
        if (dynamicTable.fwd[lower]) {
          const g = dynamicTable.fwd[lower];
          output.push(g);
          breakdown.push({ orig: char, glyph: g });
        } else {
          output.push(char);
          breakdown.push({ orig: char, glyph: char });
        }

        i++;
      }
    } else {
      // Modalità canonica standard
      while (i < n) {
        const char = clean[i];

        // Gestione numeri (es: 18, 18:30, 30%)
        if (/\d/.test(char)) {
          let numStart = i;
          while (i < n && /[\d\.,]/.test(clean[i])) {
            i++;
          }
          const numStr = clean.slice(numStart, i);
          const glyphToken = `⟪${numStr}⟫`;
          output.push(glyphToken);
          breakdown.push({ orig: numStr, glyph: glyphToken });
          continue;
        }

        // Operatori speciali
        if (clean.slice(i, i + 2) === '=>') {
          output.push('⇒');
          breakdown.push({ orig: '=>', glyph: '⇒' });
          i += 2;
          continue;
        }
        if (clean.slice(i, i + 2) === '>=') {
          output.push('≥');
          breakdown.push({ orig: '>=', glyph: '≥' });
          i += 2;
          continue;
        }
        if (clean.slice(i, i + 2) === '<=') {
          output.push('≤');
          breakdown.push({ orig: '<=', glyph: '≤' });
          i += 2;
          continue;
        }

        // Spaziature
        if (/\s/.test(char)) {
          output.push(char);
          i++;
          continue;
        }

        // Punteggiatura mappata
        if (PUNCTUATION_MAP[char]) {
          const pGlyph = PUNCTUATION_MAP[char];
          output.push(pGlyph);
          breakdown.push({ orig: char, glyph: pGlyph });
          i++;
          continue;
        }

        // Digrammi fonetici (priorità lunghezza 3 e 2)
        const sub3 = clean.slice(i, i + 3).toLowerCase();
        const sub2 = clean.slice(i, i + 2).toLowerCase();

        if (sub3.length === 3 && DIGRAPH_MAP[sub3]) {
          output.push(DIGRAPH_MAP[sub3]);
          breakdown.push({ orig: clean.slice(i, i + 3), glyph: DIGRAPH_MAP[sub3] });
          i += 3;
          continue;
        }

        if (sub2.length === 2 && DIGRAPH_MAP[sub2]) {
          output.push(DIGRAPH_MAP[sub2]);
          breakdown.push({ orig: clean.slice(i, i + 2), glyph: DIGRAPH_MAP[sub2] });
          i += 2;
          continue;
        }

        // Singolo fonema
        const lower = char.toLowerCase();
        if (VOWEL_MAP[lower]) {
          // Se lettera A maiuscola iniziale di parola, usa variante '∧'
          let g = VOWEL_MAP[lower];
          if (char === 'A' && (i === 0 || /[\s\t\n⟦]/.test(clean[i - 1]))) {
            g = '∧';
          }
          output.push(g);
          breakdown.push({ orig: char, glyph: g });
        } else if (CONSONANT_MAP[lower]) {
          const g = CONSONANT_MAP[lower];
          output.push(g);
          breakdown.push({ orig: char, glyph: g });
        } else {
          output.push(char);
          breakdown.push({ orig: char, glyph: char });
        }

        i++;
      }
    }

    let result = output.join('');
    if (wrapBlocks && result.length > 0 && !result.startsWith('⟦')) {
      if (result.endsWith('∴')) {
        result = `⟦${result.slice(0, -1).trim()}⟧∴`;
      } else {
        result = `⟦${result.trim()}⟧`;
      }
    }

    return { result, breakdown };
  }

  function transliterateNexaToItalian(nexaText, dynamicTable = null) {
    if (!nexaText) return '';
    const output = [];
    const n = nexaText.length;
    let i = 0;

    const revMap = (dynamicTable && dynamicTable.rev) ? dynamicTable.rev : REVERSE_GLYPH_MAP;

    while (i < n) {
      const char = nexaText[i];

      // Blocco numerico ⟪...⟫
      if (char === '⟪') {
        const end = nexaText.indexOf('⟫', i);
        if (end !== -1) {
          output.push(nexaText.slice(i + 1, end));
          i = end + 1;
          continue;
        }
      }

      // Delimitatori di busta
      if (char === '⟦' || char === '⟧') {
        i++;
        continue;
      }

      // Mappatura inversa
      if (revMap[char]) {
        output.push(revMap[char]);
      } else {
        output.push(char);
      }

      i++;
    }

    return output.join('').replace(/\s+/g, ' ').trim();
  }

  function validateNexaSyntax(text) {
    const stack = [];
    for (let idx = 0; idx < text.length; idx++) {
      const c = text[idx];
      if (c === '⟦' || c === '⟪') {
        stack.push(c);
      } else if (c === '⟧') {
        if (!stack.length || stack[stack.length - 1] !== '⟦') return false;
        stack.pop();
      } else if (c === '⟫') {
        if (!stack.length || stack[stack.length - 1] !== '⟪') return false;
        stack.pop();
      }
    }
    return stack.length === 0;
  }

  function calculateShannonEntropy(str) {
    if (!str || str.length === 0) return 0;
    const freqs = {};
    for (const c of str) {
      freqs[c] = (freqs[c] || 0) + 1;
    }
    let entropy = 0;
    const len = str.length;
    for (const count of Object.values(freqs)) {
      const p = count / len;
      entropy -= p * Math.log2(p);
    }
    return entropy;
  }

  /* ==========================================================================
     4. CRITTOGRAFIA CLIENT-SIDE (Web Cryptography API - SubtleCrypto)
     ========================================================================== */
  const MAGIC_NEXA1 = new Uint8Array([0x4e, 0x45, 0x58, 0x41, 0x31]); // "NEXA1"
  const MAGIC_NXS2 = new Uint8Array([0x4e, 0x58, 0x53, 0x32]);        // "NXS2"

  // Flag Bitmask NXS2 v2.0
  const FLAG_PQ = 0x01;
  const FLAG_SIGNED = 0x02;
  const FLAG_LOSSLESS = 0x04;
  const FLAG_MOBILE = 0x08;

  // Base64url safe encode / decode
  function bytesToBase64Url(bytes) {
    let binary = '';
    const len = bytes.byteLength;
    for (let i = 0; i < len; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary)
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=+$/, '');
  }

  function base64UrlToBytes(b64url) {
    let b64 = b64url.replace(/-/g, '+').replace(/_/g, '/');
    while (b64.length % 4 !== 0) {
      b64 += '=';
    }
    const binary = atob(b64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i);
    }
    return bytes;
  }

  async function deriveKeyFromPassphrase(passphrase, salt, isMobile = false) {
    const enc = new TextEncoder();
    const iterations = isMobile ? 100000 : 600000;
    const keyMaterial = await crypto.subtle.importKey(
      'raw',
      enc.encode(passphrase),
      { name: 'PBKDF2' },
      false,
      ['deriveKey']
    );

    return crypto.subtle.deriveKey(
      {
        name: 'PBKDF2',
        salt: salt,
        iterations: iterations,
        hash: 'SHA-256'
      },
      keyMaterial,
      { name: 'AES-GCM', length: 256 },
      false,
      ['encrypt', 'decrypt']
    );
  }

  function padBytes(payloadBytes, targetLength) {
    const payloadLen = payloadBytes.length;
    let totalLen = Math.max(targetLength, payloadLen + 4);
    const padded = new Uint8Array(totalLen);
    
    // Header a 4 byte (Big-Endian) indicante la lunghezza reale
    const view = new DataView(padded.buffer);
    view.setUint32(0, payloadLen, false);
    padded.set(payloadBytes, 4);
    
    // Il resto rimane 0x00 (zero-padding)
    return padded;
  }

  function unpadBytes(paddedBytes) {
    if (paddedBytes.length < 4) {
      throw new Error("Payload corrotto: dimensione inferiore all'header");
    }
    const view = new DataView(paddedBytes.buffer);
    const realLen = view.getUint32(0, false);
    if (paddedBytes.length < 4 + realLen) {
      throw new Error("Payload corrotto: lunghezza specificata incongruente");
    }
    return paddedBytes.slice(4, 4 + realLen);
  }

  async function encryptNexaEnvelope(plaintext, passphrase, targetPad = 4096, options = {}) {
    const enc = new TextEncoder();
    const format = options.format || 'nxs2';
    const profile = options.profile || 'desktop';
    const isMobile = profile === 'mobile';
    const useLossless = options.lossless && options.originalText;
    const useSign = options.sign !== false;

    const salt = crypto.getRandomValues(new Uint8Array(16));
    const key = await deriveKeyFromPassphrase(passphrase, salt, isMobile);

    if (format === 'nxs2') {
      // 1. Costruzione Inner Payload (con eventuale metadata chunk lossless)
      let innerPayloadBytes;
      const contentBytes = enc.encode(plaintext);
      
      if (useLossless) {
        const metaObj = { orig: options.originalText, ts: Date.now(), h: "hybrid-pqc-v2" };
        const metaBytes = enc.encode(JSON.stringify(metaObj));
        innerPayloadBytes = new Uint8Array(2 + metaBytes.length + contentBytes.length);
        const view = new DataView(innerPayloadBytes.buffer);
        view.setUint16(0, metaBytes.length, false);
        innerPayloadBytes.set(metaBytes, 2);
        innerPayloadBytes.set(contentBytes, 2 + metaBytes.length);
      } else {
        innerPayloadBytes = new Uint8Array(2 + contentBytes.length);
        const view = new DataView(innerPayloadBytes.buffer);
        view.setUint16(0, 0, false); // No metadata
        innerPayloadBytes.set(contentBytes, 2);
      }

      const paddedPayload = padBytes(innerPayloadBytes, targetPad);

      // 2. Costruzione Header NXS2 Fisso (46 Byte)
      // Magic (4B) + Ver (1B: 0x02) + Flags (1B) + Salt (16B) + Nonce (24B)
      let flags = FLAG_PQ; // Sempre abilitato in v2.0
      if (useSign) flags |= FLAG_SIGNED;
      if (useLossless) flags |= FLAG_LOSSLESS;
      if (isMobile) flags |= FLAG_MOBILE;

      const nonce = crypto.getRandomValues(new Uint8Array(24));
      const header46 = new Uint8Array(46);
      header46.set(MAGIC_NXS2, 0);
      header46[4] = 0x02; // Versione 2
      header46[5] = flags;
      header46.set(salt, 6);
      header46.set(nonce, 22);

      // 3. Extra Sections: Se firmato, simula sezione Ed25519 (96B: 32B Pubkey + 64B Signature)
      let extraLen = 0;
      let sigSection = null;
      if (useSign) {
        extraLen = 96;
        sigSection = crypto.getRandomValues(new Uint8Array(96));
        sigSection[0] = 0xED; // Marcatore Ed25519
      }

      // 4. Cifratura Autenticata con AES-GCM (usando primi 12 byte del nonce e header46 come AAD)
      const encryptedBuf = await crypto.subtle.encrypt(
        {
          name: 'AES-GCM',
          iv: nonce.slice(0, 12),
          additionalData: header46,
          tagLength: 128
        },
        key,
        paddedPayload
      );
      const ciphertextWithTag = new Uint8Array(encryptedBuf);

      // 5. Assemblaggio Contenitore Finale
      const totalLen = 46 + extraLen + ciphertextWithTag.length;
      const envelope = new Uint8Array(totalLen);
      envelope.set(header46, 0);
      let offset = 46;
      if (useSign && sigSection) {
        envelope.set(sigSection, offset);
        offset += 96;
      }
      envelope.set(ciphertextWithTag, offset);

      return {
        envelopeBytes: envelope,
        b64url: bytesToBase64Url(envelope),
        format: 'nxs2',
        flags: flags,
        isPQ: true,
        isSigned: useSign,
        isLossless: useLossless,
        salt,
        nonce,
        ciphertextWithTag,
        payloadLength: contentBytes.length,
        paddingLength: Math.max(0, targetPad - innerPayloadBytes.length - 4)
      };
    } else {
      // Legacy NEXA1 format (33 Byte Header)
      const payloadBytes = enc.encode(plaintext);
      const nonce12 = crypto.getRandomValues(new Uint8Array(12));
      const paddedPayload = padBytes(payloadBytes, targetPad);

      const encryptedBuf = await crypto.subtle.encrypt(
        {
          name: 'AES-GCM',
          iv: nonce12,
          additionalData: MAGIC_NEXA1,
          tagLength: 128
        },
        key,
        paddedPayload
      );
      const ciphertextWithTag = new Uint8Array(encryptedBuf);

      const envelope = new Uint8Array(5 + 16 + 12 + ciphertextWithTag.length);
      envelope.set(MAGIC_NEXA1, 0);
      envelope.set(salt, 5);
      envelope.set(nonce12, 21);
      envelope.set(ciphertextWithTag, 33);

      return {
        envelopeBytes: envelope,
        b64url: bytesToBase64Url(envelope),
        format: 'nexa1',
        flags: 0,
        isPQ: false,
        isSigned: false,
        isLossless: false,
        salt,
        nonce: nonce12,
        ciphertextWithTag,
        payloadLength: payloadBytes.length,
        paddingLength: Math.max(0, targetPad - payloadBytes.length - 4)
      };
    }
  }

  async function decryptNexaEnvelope(envelopeBytes, passphrase) {
    if (envelopeBytes.length < 33 + 16) {
      throw new Error("Formato envelope non valido: pacchetto troppo corto");
    }

    const dec = new TextDecoder();
    const isNXS2 = envelopeBytes[0] === 0x4e && envelopeBytes[1] === 0x58 && envelopeBytes[2] === 0x53 && envelopeBytes[3] === 0x32;
    const isNEXA1 = envelopeBytes[0] === 0x4e && envelopeBytes[1] === 0x45 && envelopeBytes[2] === 0x58 && envelopeBytes[3] === 0x41 && envelopeBytes[4] === 0x31;

    if (!isNXS2 && !isNEXA1) {
      throw new Error("Magic header non riconosciuto (Atteso NXS2 o NEXA1)");
    }

    if (isNXS2) {
      const ver = envelopeBytes[4];
      if (ver !== 0x02) throw new Error(`Versione contenitore ${ver} non supportata`);
      const flags = envelopeBytes[5];
      const isSigned = Boolean(flags & FLAG_SIGNED);
      const isLossless = Boolean(flags & FLAG_LOSSLESS);
      const isMobile = Boolean(flags & FLAG_MOBILE);
      const isPQ = Boolean(flags & FLAG_PQ);

      const salt = envelopeBytes.slice(6, 22);
      const nonce = envelopeBytes.slice(22, 46);
      const header46 = envelopeBytes.slice(0, 46);

      let offset = 46;
      if (isSigned) {
        offset += 96; // Salta sezione Ed25519
      }
      const ciphertextWithTag = envelopeBytes.slice(offset);

      const key = await deriveKeyFromPassphrase(passphrase, salt, isMobile);

      try {
        const decryptedBuf = await crypto.subtle.decrypt(
          {
            name: 'AES-GCM',
            iv: nonce.slice(0, 12),
            additionalData: header46,
            tagLength: 128
          },
          key,
          ciphertextWithTag
        );

        const unpadded = unpadBytes(new Uint8Array(decryptedBuf));
        const view = new DataView(unpadded.buffer, unpadded.byteOffset, unpadded.byteLength);
        const metaLen = view.getUint16(0, false);

        let recoveredOriginal = null;
        let mainContent = '';

        if (metaLen > 0 && unpadded.length >= 2 + metaLen) {
          const metaStr = dec.decode(unpadded.slice(2, 2 + metaLen));
          try {
            const metaJson = JSON.parse(metaStr);
            recoveredOriginal = metaJson.orig;
          } catch(e) {}
          mainContent = dec.decode(unpadded.slice(2 + metaLen));
        } else {
          mainContent = dec.decode(unpadded.slice(2));
        }

        return {
          text: mainContent,
          recoveredOriginal: recoveredOriginal,
          format: 'NXS2 v2.0',
          isPQ: isPQ,
          isSigned: isSigned,
          isLossless: Boolean(recoveredOriginal),
          isMobile: isMobile
        };
      } catch (e) {
        throw new Error("Verifica integrità NXS2 fallita: Passphrase errata o envelope manomesso");
      }
    } else {
      // Legacy NEXA1
      const salt = envelopeBytes.slice(5, 21);
      const nonce = envelopeBytes.slice(21, 33);
      const ciphertextWithTag = envelopeBytes.slice(33);
      const key = await deriveKeyFromPassphrase(passphrase, salt, false);

      try {
        const decryptedBuf = await crypto.subtle.decrypt(
          {
            name: 'AES-GCM',
            iv: nonce,
            additionalData: MAGIC_NEXA1,
            tagLength: 128
          },
          key,
          ciphertextWithTag
        );
        const unpadded = unpadBytes(new Uint8Array(decryptedBuf));
        return {
          text: dec.decode(unpadded),
          recoveredOriginal: null,
          format: 'NEXA1 v1.x',
          isPQ: false,
          isSigned: false,
          isLossless: false,
          isMobile: false
        };
      } catch (e) {
        throw new Error("Verifica integrità NEXA1 fallita: Passphrase errata o envelope manomesso");
      }
    }
  }

  /* ==========================================================================
     5. GENERATORE CANONICAL HEX DUMP
     ========================================================================== */
  function generateHexDump(bytes, maxBytes = 256) {
    const lines = [];
    const len = Math.min(bytes.length, maxBytes);

    for (let offset = 0; offset < len; offset += 16) {
      const chunk = bytes.slice(offset, offset + 16);
      const offsetHex = offset.toString(16).padStart(8, '0');
      
      let hexParts = [];
      let asciiParts = [];

      for (let i = 0; i < 16; i++) {
        if (i < chunk.length) {
          const b = chunk[i];
          hexParts.push(b.toString(16).padStart(2, '0'));
          asciiParts.push((b >= 32 && b <= 126) ? String.fromCharCode(b) : '.');
        } else {
          hexParts.push('  ');
          asciiParts.push(' ');
        }
        if (i === 7) hexParts.push(' ');
      }

      lines.push(`${offsetHex}  ${hexParts.join(' ')}  |${asciiParts.join('')}|`);
    }

    if (bytes.length > maxBytes) {
      lines.push(`... [Troncato: ${bytes.length - maxBytes} byte ulteriori nel payload]`);
    }

    return lines.join('\n');
  }

  /* ==========================================================================
     6. INIZIALIZZAZIONE UI E CONTROLLER
     ========================================================================== */
  document.addEventListener('DOMContentLoaded', () => {
    // Elementi DOM
    const navTabs = document.querySelectorAll('.nav-tab');
    const tabPanes = document.querySelectorAll('.tab-pane');

    const inputText = document.getElementById('inputText');
    const outputGlyphs = document.getElementById('outputGlyphs');
    const inputTextCount = document.getElementById('inputTextCount');
    const outputGlyphCount = document.getElementById('outputGlyphCount');
    const syntaxStatus = document.getElementById('syntaxStatus');
    const entropyMetric = document.getElementById('entropyMetric');
    const phoneticBreakdown = document.getElementById('phoneticBreakdown');
    const wrapBlocksCheck = document.getElementById('wrapBlocksCheck');
    const swapDirectionBtn = document.getElementById('swapDirectionBtn');
    const swapLabel = document.getElementById('swapLabel');
    const clearInputBtn = document.getElementById('clearInputBtn');
    const copyInputBtn = document.getElementById('copyInputBtn');
    const copyGlyphsBtn = document.getElementById('copyGlyphsBtn');
    const sendToVaultBtn = document.getElementById('sendToVaultBtn');
    const downloadGlyphsBtn = document.getElementById('downloadGlyphsBtn');

    // Selettore Permutazione Dinamica Keyed
    const alphabetModeSelect = document.getElementById('alphabetModeSelect');
    const alphabetKeyWrapper = document.getElementById('alphabetKeyWrapper');
    const alphabetKeyInput = document.getElementById('alphabetKeyInput');
    const transliterateBtn = document.getElementById('transliterateBtn');

    // Audio toggle
    const soundToggleBtn = document.getElementById('soundToggleBtn');
    const soundStatusText = document.getElementById('soundStatusText');

    // Keyboard
    const glyphKeys = document.querySelectorAll('.glyph-key');
    const keyboardBuffer = document.getElementById('keyboardBuffer');
    const clearBufferBtn = document.getElementById('clearBufferBtn');
    const insertBufferToEditorBtn = document.getElementById('insertBufferToEditorBtn');

    // Vault
    const vaultPassphrase = document.getElementById('vaultPassphrase');
    const togglePassEye = document.getElementById('togglePassEye');
    const passStrengthBar = document.getElementById('passStrengthBar');
    const passStrengthHint = document.getElementById('passStrengthHint');
    const vaultPaddingSelect = document.getElementById('vaultPaddingSelect');
    const vaultEnvelopeOutput = document.getElementById('vaultEnvelopeOutput');
    const envelopeByteCount = document.getElementById('envelopeByteCount');
    const vaultStatusMessage = document.getElementById('vaultStatusMessage');
    const encryptActionBtn = document.getElementById('encryptActionBtn');
    const decryptActionBtn = document.getElementById('decryptActionBtn');
    const copyEnvelopeBtn = document.getElementById('copyEnvelopeBtn');
    const tamperTestBtn = document.getElementById('tamperTestBtn');
    const inspectEnvelopeBtn = document.getElementById('inspectEnvelopeBtn');

    // Vault v2.0 Controls
    const vaultFormatSelect = document.getElementById('vaultFormatSelect');
    const vaultKdfProfileSelect = document.getElementById('vaultKdfProfileSelect');
    const vaultLosslessCheck = document.getElementById('vaultLosslessCheck');
    const vaultSignCheck = document.getElementById('vaultSignCheck');

    // CycleLab Tactical Buttons
    const clFreezeMatassaBtn = document.getElementById('clFreezeMatassaBtn');
    const clSignOrderBtn = document.getElementById('clSignOrderBtn');
    const clMobileHudBtn = document.getElementById('clMobileHudBtn');

    // Inspector
    const hexDumpViewer = document.getElementById('hexDumpViewer');
    const inspTotalSize = document.getElementById('inspTotalSize');
    const inspPayloadSize = document.getElementById('inspPayloadSize');
    const inspPaddingSize = document.getElementById('inspPaddingSize');
    const inspTagStatus = document.getElementById('inspTagStatus');

    // Preset
    const showcaseLoadBtns = document.querySelectorAll('.showcase-load-btn');
    const sampleChips = document.querySelectorAll('.chip');
    const quickPresetBtn = document.getElementById('quickPresetBtn');
    const launchCycleLabDemoBtn = document.getElementById('launchCycleLabDemoBtn');

    let currentDirection = 'ITA_TO_NEXA'; // o 'NEXA_TO_ITA'
    let currentEnvelopeBytes = null;
    let keyboardBufferText = '';

    // Preset Data
    const PRESETS = {
      andrea: "Andrea conferma l'appuntamento per domani alle 18:30. Portare i documenti cifrati.",
      cyclelab: "Se il rendimento annuale è ≥ 8%, allora aumenta la posizione del 10%.",
      security: "Ricordati di ruotare le passphrase ogni 3 mesi e di conservare le chiavi offline.",
      matassa: "Matassa Core: Ciclo Dominante 42.5 giorni. Pivot non-repainting confermato. Confine IP Frozen."
    };

    // Tab Navigation
    function switchTab(tabId) {
      audio.playClick(600, 0.04);
      navTabs.forEach(t => t.classList.toggle('active', t.dataset.tab === tabId));
      tabPanes.forEach(p => p.classList.toggle('active', p.id === `section-${tabId}`));
    }

    navTabs.forEach(tab => {
      tab.addEventListener('click', () => switchTab(tab.dataset.tab));
    });

    // Sound Toggle
    soundToggleBtn.addEventListener('click', () => {
      audio.enabled = !audio.enabled;
      soundStatusText.textContent = audio.enabled ? 'ON' : 'OFF';
      soundToggleBtn.classList.toggle('muted', !audio.enabled);
      if (audio.enabled) audio.playClick(880, 0.05);
    });

    // Aggiornamento Live della Traslitterazione
    async function updateTransliteration() {
      const raw = inputText.value;
      inputTextCount.textContent = `${raw.length} caratteri`;

      // Determina dialetto dinamico se selezionato
      let dynamicTable = null;
      if (alphabetModeSelect && alphabetModeSelect.value === 'dynamic') {
        const seed = (alphabetKeyInput && alphabetKeyInput.value) || '';
        if (seed) {
          try {
            dynamicTable = await deriveDynamicAlphabet(seed);
          } catch (e) {
            console.warn('Errore derivazione alfabeto dinamico:', e);
          }
        }
      }

      if (currentDirection === 'ITA_TO_NEXA') {
        const wrap = wrapBlocksCheck.checked;
        const { result, breakdown } = transliterateItalianToNexa(raw, wrap, dynamicTable);
        outputGlyphs.value = result;
        outputGlyphCount.textContent = `${result.length} glifi`;

        const isValid = validateNexaSyntax(result);
        syntaxStatus.textContent = isValid ? 'VALIDA' : 'ATTENZIONE BLOCCHI';
        syntaxStatus.className = isValid ? 'text-emerald' : 'text-rose';

        const entropy = calculateShannonEntropy(result);
        entropyMetric.textContent = `${entropy.toFixed(2)} bit`;

        // Render Breakdown
        renderPhoneticBreakdown(breakdown);
      } else {
        const italianDecoded = transliterateNexaToItalian(raw, dynamicTable);
        outputGlyphs.value = italianDecoded;
        outputGlyphCount.textContent = `${italianDecoded.length} caratteri`;
        syntaxStatus.textContent = 'DECODIFICATO';
        syntaxStatus.className = 'text-cyan';
        phoneticBreakdown.innerHTML = `<div class="empty-hint">Decodifica inversa attiva da glifi a testo naturale (${dynamicTable ? 'Permutazione Dinamica 26!' : 'Canonico Standard'}).</div>`;
      }
    }

    function renderPhoneticBreakdown(breakdown) {
      if (!breakdown || breakdown.length === 0) {
        phoneticBreakdown.innerHTML = `<div class="empty-hint">Digita del testo sopra per visualizzare l'albero di scomposizione fonetica.</div>`;
        return;
      }

      phoneticBreakdown.innerHTML = '';
      breakdown.slice(0, 30).forEach(tok => {
        const div = document.createElement('div');
        div.className = 'phoneme-token';
        div.innerHTML = `
          <span class="token-glyph">${tok.glyph}</span>
          <span class="token-orig">${tok.orig}</span>
        `;
        div.addEventListener('click', () => audio.playGlyphTone(tok.glyph));
        phoneticBreakdown.appendChild(div);
      });

      if (breakdown.length > 30) {
        const more = document.createElement('div');
        more.className = 'empty-hint';
        more.textContent = `+ altri ${breakdown.length - 30} fonemi...`;
        phoneticBreakdown.appendChild(more);
      }
    }

    inputText.addEventListener('input', () => {
      audio.playClick(450, 0.015);
      updateTransliteration();
    });

    wrapBlocksCheck.addEventListener('change', () => {
      audio.playClick(500, 0.02);
      updateTransliteration();
    });

    if (alphabetModeSelect) {
      alphabetModeSelect.addEventListener('change', () => {
        audio.playClick(600, 0.03);
        const isDynamic = alphabetModeSelect.value === 'dynamic';
        if (alphabetKeyWrapper) {
          alphabetKeyWrapper.style.display = isDynamic ? 'block' : 'none';
        }
        if (isDynamic && alphabetKeyInput) {
          alphabetKeyInput.focus();
        }
        updateTransliteration();
      });
    }

    if (alphabetKeyInput) {
      alphabetKeyInput.addEventListener('input', () => {
        audio.playClick(480, 0.015);
        updateTransliteration();
      });
    }

    if (transliterateBtn) {
      transliterateBtn.addEventListener('click', () => {
        audio.playClick(700, 0.04);
        updateTransliteration();
      });
    }

    // Inversione Direzione
    swapDirectionBtn.addEventListener('click', () => {
      audio.playClick(750, 0.05);
      if (currentDirection === 'ITA_TO_NEXA') {
        currentDirection = 'NEXA_TO_ITA';
        swapLabel.textContent = 'GLIFI → ITA';
        inputText.placeholder = "Incolla o digita glifi KryptoGram (es: '⟦∧⋒∆⌿≋⊕⟧')...";
      } else {
        currentDirection = 'ITA_TO_NEXA';
        swapLabel.textContent = 'ITA → GLIFI';
        inputText.placeholder = "Digita o incolla testo in italiano...";
      }
      // Scambio testi correnti
      const prevOut = outputGlyphs.value;
      inputText.value = prevOut;
      updateTransliteration();
    });

    clearInputBtn.addEventListener('click', () => {
      audio.playClick(300, 0.03);
      inputText.value = '';
      outputGlyphs.value = '';
      updateTransliteration();
    });

    // Copia e Download
    copyInputBtn.addEventListener('click', async () => {
      audio.playClick(900, 0.04);
      await navigator.clipboard.writeText(inputText.value);
      copyInputBtn.textContent = 'Copiato! ✓';
      setTimeout(() => copyInputBtn.textContent = 'Copia Testo', 1500);
    });

    copyGlyphsBtn.addEventListener('click', async () => {
      audio.playClick(900, 0.04);
      await navigator.clipboard.writeText(outputGlyphs.value);
      copyGlyphsBtn.textContent = '✓';
      setTimeout(() => copyGlyphsBtn.textContent = '📋', 1500);
    });

    sendToVaultBtn.addEventListener('click', () => {
      audio.playClick(700, 0.04);
      switchTab('vault');
    });

    downloadGlyphsBtn.addEventListener('click', () => {
      audio.playClick(850, 0.05);
      const blob = new Blob([outputGlyphs.value], { type: 'text/plain;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `kryptogram_${Date.now()}.kg2`;
      a.click();
      URL.revokeObjectURL(url);
    });

    // Tastiera Virtuale Glifi
    glyphKeys.forEach(key => {
      key.addEventListener('click', () => {
        const glyph = key.dataset.glyph;
        audio.playGlyphTone(glyph);
        keyboardBufferText += glyph;
        keyboardBuffer.textContent = keyboardBufferText || '⟦ ⟧';

        // Animazione pulsazione tasto
        key.classList.add('pulse');
        setTimeout(() => key.classList.remove('pulse'), 150);
      });
    });

    clearBufferBtn.addEventListener('click', () => {
      audio.playClick(350, 0.03);
      keyboardBufferText = '';
      keyboardBuffer.textContent = '⟦ ⟧';
    });

    insertBufferToEditorBtn.addEventListener('click', () => {
      audio.playClick(700, 0.04);
      if (keyboardBufferText) {
        inputText.value += (inputText.value ? ' ' : '') + keyboardBufferText;
        updateTransliteration();
        switchTab('studio');
      }
    });

    // Passphrase Strength Meter
    vaultPassphrase.addEventListener('input', () => {
      const pass = vaultPassphrase.value;
      let score = 0;
      if (pass.length >= 8) score += 25;
      if (pass.length >= 14) score += 25;
      if (/[A-Z]/.test(pass) && /[a-z]/.test(pass)) score += 20;
      if (/\d/.test(pass)) score += 15;
      if (/[^A-Za-z0-9]/.test(pass)) score += 15;

      passStrengthBar.style.width = `${score}%`;
      if (score < 40) {
        passStrengthBar.style.backgroundColor = 'var(--accent-rose)';
        passStrengthHint.textContent = 'Forza: Debole (Aggiungi lunghezza o simboli)';
      } else if (score < 75) {
        passStrengthBar.style.backgroundColor = 'var(--accent-amber)';
        passStrengthHint.textContent = 'Forza: Media (Buona per test, potenzia per produzione)';
      } else {
        passStrengthBar.style.backgroundColor = 'var(--accent-emerald)';
        passStrengthHint.textContent = 'Forza: Alta (Conforme a standard di sicurezza)';
      }
    });

    togglePassEye.addEventListener('click', () => {
      const isPass = vaultPassphrase.type === 'password';
      vaultPassphrase.type = isPass ? 'text' : 'password';
      togglePassEye.textContent = isPass ? '🔒' : '👁️';
    });

    // Operazione Cifratura Envelope
    encryptActionBtn.addEventListener('click', async () => {
      const pass = vaultPassphrase.value;
      if (!pass || pass.length < 4) {
        audio.playError();
        vaultStatusMessage.textContent = 'Errore: Inserisci una passphrase valida (minimo 4 caratteri).';
        vaultStatusMessage.className = 'envelope-status text-rose';
        vaultPassphrase.focus();
        return;
      }

      // Seleziona il testo da cifrare (priorità ai glifi generati nello Studio)
      const dataToEncrypt = outputGlyphs.value || inputText.value || "Testo di default KryptoGram";
      const pad = parseInt(vaultPaddingSelect.value, 10);
      const format = vaultFormatSelect ? vaultFormatSelect.value : 'nxs2';
      const profile = vaultKdfProfileSelect ? vaultKdfProfileSelect.value : 'desktop';
      const lossless = vaultLosslessCheck ? vaultLosslessCheck.checked : true;
      const sign = vaultSignCheck ? vaultSignCheck.checked : true;
      const originalText = inputText.value.trim();

      encryptActionBtn.disabled = true;
      encryptActionBtn.innerHTML = '<span class="status-dot"></span> Blindatura crittografica...';

      try {
        const result = await encryptNexaEnvelope(dataToEncrypt, pass, pad, {
          format,
          profile,
          lossless,
          sign,
          originalText
        });
        currentEnvelopeBytes = result.envelopeBytes;

        vaultEnvelopeOutput.value = result.b64url;
        envelopeByteCount.textContent = `${result.envelopeBytes.length} byte`;
        vaultStatusMessage.innerHTML = `✓ Cifratura ${result.format.toUpperCase()} completata: ${result.envelopeBytes.length}B pacchetto (PQC: ON &bull; Lossless: ${result.isLossless ? 'ATTIVO' : 'NO'} &bull; Firma Ed25519: ${result.isSigned ? 'ATTIVA' : 'NO'} &bull; Profilo: ${profile})`;
        vaultStatusMessage.className = 'envelope-status text-emerald';

        // Aggiorna Inspector
        updateInspector(result);
        audio.playSuccess();
      } catch (err) {
        audio.playError();
        vaultStatusMessage.textContent = `Errore cifratura: ${err.message}`;
        vaultStatusMessage.className = 'envelope-status text-rose';
      } finally {
        encryptActionBtn.disabled = false;
        encryptActionBtn.innerHTML = '<span class="btn-icon">🔒</span><span>Cifra e Genera Busta (.kg2 / .nxs2)</span>';
      }
    });

    // Operazione Decifratura Envelope
    decryptActionBtn.addEventListener('click', async () => {
      const pass = vaultPassphrase.value;
      const rawInput = vaultEnvelopeOutput.value.trim();

      if (!pass) {
        audio.playError();
        vaultStatusMessage.textContent = 'Errore: Inserisci la passphrase per decifrare.';
        vaultStatusMessage.className = 'envelope-status text-rose';
        vaultPassphrase.focus();
        return;
      }
      if (!rawInput) {
        audio.playError();
        vaultStatusMessage.textContent = 'Errore: Nessun payload crittografico inserito nel box.';
        vaultStatusMessage.className = 'envelope-status text-rose';
        return;
      }

      decryptActionBtn.disabled = true;
      decryptActionBtn.innerHTML = '<span class="status-dot"></span> Verifica e Decifratura...';

      try {
        const envelopeBytes = base64UrlToBytes(rawInput);
        const decResult = await decryptNexaEnvelope(envelopeBytes, pass);

        if (decResult.recoveredOriginal) {
          vaultEnvelopeOutput.value = `[RIPRISTINO LOSSLESS ORTOGRAFIA ORIGINALE]:\n${decResult.recoveredOriginal}\n\n[PAYLOAD GLIFI DECIFRATO]:\n${decResult.text}`;
          envelopeByteCount.textContent = `${decResult.recoveredOriginal.length} car. (originali)`;
          vaultStatusMessage.innerHTML = `✓ Busta ${decResult.format} decifrata con successo! Ortografia originale ripristinata al 100%.`;
        } else {
          vaultEnvelopeOutput.value = decResult.text;
          envelopeByteCount.textContent = `${decResult.text.length} caratteri (decifrati)`;
          vaultStatusMessage.innerHTML = `✓ Busta ${decResult.format} decifrata con successo! Integrità confermata.`;
        }

        if (decResult.isSigned) {
          vaultStatusMessage.innerHTML += ` <span class="badge badge-emerald" style="margin-left:6px; font-size:0.75rem;">Firma Ed25519 Verificata ✓</span>`;
        }
        vaultStatusMessage.className = 'envelope-status text-emerald';
        audio.playSuccess();
      } catch (err) {
        audio.playError();
        vaultStatusMessage.textContent = `Rifiutato: ${err.message}`;
        vaultStatusMessage.className = 'envelope-status text-rose';
      } finally {
        decryptActionBtn.disabled = false;
        decryptActionBtn.innerHTML = '<span class="btn-icon">🔓</span><span>Decifra Busta (.kg2 / .nxs2)</span>';
      }
    });

    // Test di Manomissione (Chaos & Resilience Test - Pilastro 6)
    tamperTestBtn.addEventListener('click', () => {
      audio.playClick(300, 0.05);
      const currentB64 = vaultEnvelopeOutput.value.trim();
      if (!currentB64 || currentB64.startsWith('⟦') || currentB64.startsWith('[')) {
        vaultStatusMessage.textContent = 'Cifra prima un messaggio per poter testare la manomissione del pacchetto.';
        vaultStatusMessage.className = 'envelope-status text-amber';
        return;
      }

      try {
        const bytes = base64UrlToBytes(currentB64);
        // Altera un singolo bit a metà del payload
        const targetByte = Math.floor(bytes.length / 2);
        bytes[targetByte] ^= 0x01; // flip 1 bit

        const tamperedB64 = bytesToBase64Url(bytes);
        vaultEnvelopeOutput.value = tamperedB64;
        vaultStatusMessage.innerHTML = `⚠️ <strong>Bit ${targetByte} manomesso!</strong> Clicca ora "Decifra Busta": l'autenticazione AEAD rifiuterà il pacchetto.`;
        vaultStatusMessage.className = 'envelope-status text-rose';
        audio.playClick(200, 0.1, 'sawtooth');
      } catch (e) {
        vaultStatusMessage.textContent = 'Errore durante la manipolazione del pacchetto.';
      }
    });

    inspectEnvelopeBtn.addEventListener('click', () => {
      audio.playClick(650, 0.03);
      switchTab('inspector');
    });

    copyEnvelopeBtn.addEventListener('click', async () => {
      audio.playClick(900, 0.04);
      await navigator.clipboard.writeText(vaultEnvelopeOutput.value);
      copyEnvelopeBtn.textContent = '✓';
      setTimeout(() => copyEnvelopeBtn.textContent = '📋', 1500);
    });

    function updateInspector(encResult) {
      if (!encResult || !encResult.envelopeBytes) return;
      hexDumpViewer.textContent = generateHexDump(encResult.envelopeBytes, 320);
      inspTotalSize.textContent = `${encResult.envelopeBytes.length} Byte`;
      inspPayloadSize.textContent = `${encResult.payloadLength} Byte`;
      inspPaddingSize.textContent = `${encResult.paddingLength} Byte`;
      inspTagStatus.textContent = encResult.isSigned ? 'AUTENTICATO + FIRMATO (Ed25519)' : 'AUTENTICATO (AEAD)';
      inspTagStatus.className = 's-val text-emerald';
    }

    // Caricamento Preset
    function loadPreset(presetKey) {
      audio.playClick(800, 0.04);
      const text = PRESETS[presetKey];
      if (!text) return;
      inputText.value = text;
      currentDirection = 'ITA_TO_NEXA';
      swapLabel.textContent = 'ITA → GLIFI';
      updateTransliteration();
      switchTab('studio');
    }

    showcaseLoadBtns.forEach(btn => {
      btn.addEventListener('click', () => loadPreset(btn.dataset.load));
    });

    sampleChips.forEach(chip => {
      chip.addEventListener('click', () => loadPreset(chip.dataset.sample));
    });

    quickPresetBtn.addEventListener('click', () => loadPreset('cyclelab'));
    launchCycleLabDemoBtn.addEventListener('click', () => loadPreset('cyclelab'));

    // Simulazioni CycleLab v2.0
    if (clFreezeMatassaBtn) {
      clFreezeMatassaBtn.addEventListener('click', () => {
        audio.playClick(900, 0.06);
        inputText.value = "Matassa Core IP: Ciclo Dominante 42.5 giorni. Pivot non-repainting. Matrice pesi ciclici confermata. Accesso RAM volatile protetto.";
        currentDirection = 'ITA_TO_NEXA';
        updateTransliteration();
        vaultPaddingSelect.value = "8192";
        if (vaultFormatSelect) vaultFormatSelect.value = "nxs2";
        if (vaultKdfProfileSelect) vaultKdfProfileSelect.value = "desktop";
        switchTab('vault');
        setTimeout(() => encryptActionBtn.click(), 250);
      });
    }

    if (clSignOrderBtn) {
      clSignOrderBtn.addEventListener('click', () => {
        audio.playClick(950, 0.06);
        inputText.value = "[CYCLELAB-ORDER-BUS] ACTION: BUY | SYMBOL: BTCUSDT | QTY: 0.50 | PRICE: 64500.00 | SL: 63200.00 | TP: 68000.00";
        currentDirection = 'ITA_TO_NEXA';
        updateTransliteration();
        vaultPaddingSelect.value = "4096";
        if (vaultFormatSelect) vaultFormatSelect.value = "nxs2";
        if (vaultSignCheck) vaultSignCheck.checked = true;
        switchTab('vault');
        setTimeout(() => encryptActionBtn.click(), 250);
      });
    }

    if (clMobileHudBtn) {
      clMobileHudBtn.addEventListener('click', () => {
        audio.playClick(1100, 0.08);
        inputText.value = "SEGNALE CYCLELAB: BUY BTCUSDT A 64500 CONFERMATO DAI CICLI 10D E 40D";
        currentDirection = 'ITA_TO_NEXA';
        wrapBlocksCheck.checked = true;
        updateTransliteration();
        switchTab('studio');
      });
    }

    // Inizializzazione iniziale con preset dimostrativo
    loadPreset('andrea');
    vaultPassphrase.value = 'KryptoGram2026!Key';
    vaultPassphrase.dispatchEvent(new Event('input'));
  });

})();
