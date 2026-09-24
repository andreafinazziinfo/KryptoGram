# Tutorial NEXA-S – Primi passi pratici

## 1) Installazione

```bash
cd output
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## 2) Cifrare un file (con NEXA-S opzionale)

```bash
echo "Appuntamento domani alle 18." > nota.txt
python nexa_encrypt.py encrypt --in nota.txt --out nota.nexa --new-passphrase --pad 4096 --nexa
```

- Inserisci due volte la passphrase quando richiesto.
- `nota.nexa` è Base64url: puoi incollarlo in chat o salvarlo su cloud.

## 3) Decifrare

```bash
python nexa_encrypt.py decrypt --in nota.nexa --out nota_decifrata.txt --nexa
cat nota_decifrata.txt
```

## 4) Usare la GUI (opzionale)

```bash
python gui_nexa.py
```

- Seleziona file in input/output, inserisci passphrase, spunta “Usa traslitterazione NEXA-S” se vuoi.
- Clicca “Cifra” o “Decifra”.

## 5) Provare l’estensione VS Code

1. Copia la cartella `vscode_nexa_s` in `~/.vscode/extensions/nexa-s`.
2. Riavvia VS Code.
3. Apri un file `.nexa` per vedere l’evidenziazione sintassi.

## 6) Integrare age (opzionale, avanzato)

```bash
age-keygen -o key.txt
age --encrypt --recipient $(age-keygen -o key.txt 2>/dev/null | grep "# public key:" | awk '{print $4}') --in nota.txt --out nota.age
age --decrypt --identity key.txt --in nota.age --out nota2.txt
```

Oppure usa `nexa_age.py` come wrapper semplice.
