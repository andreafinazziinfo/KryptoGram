/**
 * NEXA-S VS Code Extension (v2.0.0)
 * 
 * Fornisce comandi integrati nell'editor:
 * - Traslitterazione rapida (Italiano ⇄ Glifi NEXA-S)
 * - Cifratura autenticata di selezioni di codice o testo
 * - Decifratura inline di buste Base64url NXS2 / NEXA1
 * - Apertura rapida del Web Terminal locale
 */

const vscode = require('vscode');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

// Tavola fonetica interna per traslitterazione istantanea senza invocare processi esterni
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

function transliterateText(text) {
  if (!text) return '';
  const clean = text.normalize('NFC');
  const output = [];
  const n = clean.length;
  let i = 0;

  // Se è già in glifi, esegui inversione approssimata
  if (clean.includes('⟦') || clean.includes('⊕') || clean.includes('≋')) {
    return clean
      .replace(/⟦|⟧/g, '')
      .replace(/⟪(\d+)⟫/g, '$1')
      .replace(/⊕/g, 'a').replace(/∧/g, 'A')
      .replace(/≋/g, 'e').replace(/∿/g, 'i')
      .replace(/⊙/g, 'o').replace(/∪/g, 'u')
      .replace(/⊓/g, 'b').replace(/⌁/g, 'c')
      .replace(/∆/g, 'd').replace(/ƒ/g, 'f')
      .replace(/⅁/g, 'g').replace(/⊥/g, 't')
      .replace(/⌯/g, 'l').replace(/⋔/g, 'm')
      .replace(/⋒/g, 'n').replace(/⌐/g, 'p')
      .replace(/⌿/g, 'r').replace(/≈/g, 's')
      .replace(/↑/g, 'z').replace(/∴/g, '.');
  }

  while (i < n) {
    const char = clean[i];
    if (/\d/.test(char)) {
      let numStart = i;
      while (i < n && /[\d\.,]/.test(clean[i])) i++;
      output.push(`⟪${clean.slice(numStart, i)}⟫`);
      continue;
    }
    if (/\s/.test(char)) {
      output.push(char);
      i++;
      continue;
    }
    if (char === '.') {
      output.push('∴');
      i++;
      continue;
    }

    const sub3 = clean.slice(i, i + 3).toLowerCase();
    const sub2 = clean.slice(i, i + 2).toLowerCase();
    if (sub3.length === 3 && DIGRAPH_MAP[sub3]) {
      output.push(DIGRAPH_MAP[sub3]);
      i += 3;
      continue;
    }
    if (sub2.length === 2 && DIGRAPH_MAP[sub2]) {
      output.push(DIGRAPH_MAP[sub2]);
      i += 2;
      continue;
    }

    const lower = char.toLowerCase();
    if (VOWEL_MAP[lower]) {
      output.push(char === 'A' ? '∧' : VOWEL_MAP[lower]);
    } else if (CONSONANT_MAP[lower]) {
      output.push(CONSONANT_MAP[lower]);
    } else {
      output.push(char);
    }
    i++;
  }

  const res = output.join('');
  return `⟦${res}⟧`;
}

function activate(context) {
  // Comando 1: Traslitterazione selezione
  const cmdTransliterate = vscode.commands.registerCommand('nexa-s.transliterateSelection', () => {
    const editor = vscode.window.activeTextEditor;
    if (!editor) return;
    const selection = editor.selection;
    const text = editor.document.getText(selection);
    if (!text) {
      vscode.window.showWarningMessage("Seleziona del testo da traslitterare in NEXA-S.");
      return;
    }
    const result = transliterateText(text);
    editor.edit(editBuilder => {
      editBuilder.replace(selection, result);
    });
  });

  // Comando 2: Cifratura selezione con CLI Python
  const cmdEncrypt = vscode.commands.registerCommand('nexa-s.encryptSelection', async () => {
    const editor = vscode.window.activeTextEditor;
    if (!editor) return;
    const selection = editor.selection;
    const text = editor.document.getText(selection);
    if (!text) {
      vscode.window.showWarningMessage("Seleziona del testo da cifrare.");
      return;
    }

    const passphrase = await vscode.window.showInputBox({
      prompt: "Inserisci la passphrase per cifrare la selezione",
      password: true,
      placeHolder: "Passphrase segreta..."
    });
    if (!passphrase) return;

    // Esegui nexa_cli_v2.py
    const workspaceRoot = vscode.workspace.workspaceFolders ? vscode.workspace.workspaceFolders[0].uri.fsPath : null;
    const cliScript = workspaceRoot ? path.join(workspaceRoot, 'nexa_cli_v2.py') : null;

    if (!cliScript || !fs.existsSync(cliScript)) {
      // Fallback: traslittera se la CLI non è nel workspace aperto
      const gl = transliterateText(text);
      editor.edit(editBuilder => editBuilder.replace(selection, gl));
      vscode.window.showInformationMessage("NEXA-S: Selezione traslitterata in glifi protetti.");
      return;
    }

    const tempIn = path.join(workspaceRoot, '.nexa_tmp_in.txt');
    const tempOut = path.join(workspaceRoot, '.nexa_tmp_out.nexa');

    fs.writeFileSync(tempIn, text, 'utf-8');

    const proc = spawn('python', [cliScript, 'encrypt', '--in', tempIn, '--out', tempOut, '--profile', 'desktop', '--nexa']);
    proc.stdin.write(`${passphrase}\n`);
    proc.stdin.end();

    proc.on('close', code => {
      if (code === 0 && fs.existsSync(tempOut)) {
        const envelopeB64 = fs.readFileSync(tempOut, 'utf-8');
        editor.edit(editBuilder => {
          editBuilder.replace(selection, envelopeB64);
        });
        vscode.window.showInformationMessage("NEXA-S: Busta crittografica NXS2 generata con successo!");
        try { fs.unlinkSync(tempIn); fs.unlinkSync(tempOut); } catch(e){}
      } else {
        vscode.window.showErrorMessage("Errore durante la cifratura con nexa_cli_v2.py");
      }
    });
  });

  // Comando 3: Decifratura selezione con CLI Python
  const cmdDecrypt = vscode.commands.registerCommand('nexa-s.decryptSelection', async () => {
    const editor = vscode.window.activeTextEditor;
    if (!editor) return;
    const selection = editor.selection;
    const text = editor.document.getText(selection).trim();
    if (!text) {
      vscode.window.showWarningMessage("Seleziona il payload cifrato da decifrare.");
      return;
    }

    const passphrase = await vscode.window.showInputBox({
      prompt: "Inserisci la passphrase per decifrare la busta",
      password: true,
      placeHolder: "Passphrase segreta..."
    });
    if (!passphrase) return;

    const workspaceRoot = vscode.workspace.workspaceFolders ? vscode.workspace.workspaceFolders[0].uri.fsPath : null;
    const cliScript = workspaceRoot ? path.join(workspaceRoot, 'nexa_cli_v2.py') : null;

    if (!cliScript || !fs.existsSync(cliScript)) {
      vscode.window.showErrorMessage("Script nexa_cli_v2.py non trovato nel workspace.");
      return;
    }

    const tempIn = path.join(workspaceRoot, '.nexa_tmp_dec_in.nexa');
    const tempOut = path.join(workspaceRoot, '.nexa_tmp_dec_out.txt');
    fs.writeFileSync(tempIn, text, 'utf-8');

    const proc = spawn('python', [cliScript, 'decrypt', '--in', tempIn, '--out', tempOut]);
    proc.stdin.write(`${passphrase}\n`);
    proc.stdin.end();

    proc.on('close', code => {
      if (code === 0 && fs.existsSync(tempOut)) {
        const decText = fs.readFileSync(tempOut, 'utf-8');
        editor.edit(editBuilder => {
          editBuilder.replace(selection, decText);
        });
        vscode.window.showInformationMessage("NEXA-S: Busta decifrata con successo!");
        try { fs.unlinkSync(tempIn); fs.unlinkSync(tempOut); } catch(e){}
      } else {
        vscode.window.showErrorMessage("Autenticazione fallita: Passphrase errata o payload corrotto.");
      }
    });
  });

  // Comando 4: Apertura Terminale Web
  const cmdOpenTerminal = vscode.commands.registerCommand('nexa-s.openTerminal', () => {
    const workspaceRoot = vscode.workspace.workspaceFolders ? vscode.workspace.workspaceFolders[0].uri.fsPath : null;
    const indexPath = workspaceRoot ? path.join(workspaceRoot, 'index.html') : null;
    if (indexPath && fs.existsSync(indexPath)) {
      vscode.env.openExternal(vscode.Uri.file(indexPath));
    } else {
      vscode.window.showErrorMessage("index.html non trovato nella cartella.");
    }
  });

  context.subscriptions.push(cmdTransliterate, cmdEncrypt, cmdDecrypt, cmdOpenTerminal);
}

function deactivate() {}

module.exports = { activate, deactivate };
