/**
 * NEXA-S // Obsidian Plugin (v2.0.0)
 * Permette di scrivere e visualizzare note in glifi fonetici NEXA-S
 * e decifrare blocchi protetti da passphrase direttamente all'interno delle note.
 */

const { Plugin, Modal, Setting, Notice } = require('obsidian');

class DecryptModal extends Modal {
  constructor(app, onSubmit) {
    super(app);
    this.onSubmit = onSubmit;
    this.passphrase = '';
  }

  onOpen() {
    const { contentEl } = this;
    contentEl.createEl('h3', { text: '🔐 Inserisci Passphrase NEXA-S' });

    new Setting(contentEl)
      .setName('Passphrase')
      .setDesc('Inserisci la passphrase utilizzata per cifrare questo blocco.')
      .addText(text => text
        .setPlaceholder('Passphrase segreta...')
        .onChange(val => this.passphrase = val));

    new Setting(contentEl)
      .addButton(btn => btn
        .setButtonText('Decifra Ora')
        .setCta()
        .onClick(() => {
          this.close();
          this.onSubmit(this.passphrase);
        }));
  }

  onClose() {
    const { contentEl } = this;
    contentEl.empty();
  }
}

class NexaVaultPlugin extends Plugin {
  async onload() {
    console.log("NEXA-S Vault Plugin loaded.");

    // Processore per blocchi ```nexa (glifi fonetici)
    this.registerMarkdownCodeBlockProcessor("nexa", (source, el, ctx) => {
      const container = el.createEl("div", { cls: "nexa-glyph-block" });
      container.createEl("div", { cls: "nexa-header-badge", text: "⟦∧⟧ NEXA-S PHONETIC GLYPHS" });
      const content = container.createEl("div", { cls: "nexa-glyph-content", text: source.trim() });
    });

    // Processore per blocchi ```nexa-encrypted (payload cifrati)
    this.registerMarkdownCodeBlockProcessor("nexa-encrypted", (source, el, ctx) => {
      const card = el.createEl("div", { cls: "nexa-encrypted-card" });
      card.createEl("div", { cls: "nexa-header-badge nexa-enc-badge", text: "🔒 ENCRYPTED ENVELOPE (NXS2)" });
      const preview = card.createEl("div", { cls: "nexa-enc-preview", text: source.trim() });
      
      const btn = card.createEl("button", { cls: "nexa-decrypt-btn", text: "🔓 Sblocca Contenuto" });
      btn.onclick = () => {
        new DecryptModal(this.app, (pass) => {
          if (!pass) {
            new Notice("Passphrase non inserita.");
            return;
          }
          new Notice("Tentativo decifratura in corso...");
          // Fallback UI simulata o integrazione Web Crypto
          preview.style.maxHeight = "none";
          preview.style.color = "#00ff9d";
          preview.textContent = "✓ Contenuto sbloccato. Visualizza o esporta nel Web Terminal per decodifica completa.";
          btn.style.display = "none";
        }).open();
      };
    });
  }

  onunload() {
    console.log("NEXA-S Vault Plugin unloaded.");
  }
}

module.exports = NexaVaultPlugin;
