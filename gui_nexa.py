#!/usr/bin/env python3
"""NEXA-S GUI minimale (Tkinter) per cifrare/decifrare con opzione NEXA-S."""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import sys
from pathlib import Path

try:
    from nexa_lib import italian_to_nexa, nexa_to_italian
except ImportError:
    pass

def run_encrypt(in_path, out_path, passphrase, pad, use_nexa):
    cmd = [sys.executable, "nexa_encrypt.py", "encrypt",
           "--in", str(in_path), "--out", str(out_path), "--pad", str(pad)]
    if use_nexa:
        cmd.append("--nexa")
    proc = subprocess.run(cmd, input=f"{passphrase}\n{passphrase}\n", text=True, capture_output=True)
    return proc.returncode == 0, proc.stderr

def run_decrypt(in_path, out_path, passphrase, use_nexa):
    cmd = [sys.executable, "nexa_encrypt.py", "decrypt",
           "--in", str(in_path), "--out", str(out_path)]
    if use_nexa:
        cmd.append("--nexa")
    proc = subprocess.run(cmd, input=f"{passphrase}\n", text=True, capture_output=True)
    return proc.returncode == 0, proc.stderr

class App:
    def __init__(self, root):
        root.title("NEXA-S Secure Envelope")
        root.geometry("700x500")
        ttk.Label(root, text="File input:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.in_var = tk.StringVar()
        ttk.Entry(root, textvariable=self.in_var, width=50).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(root, text="Sfoglia...", command=self.browse_in).grid(row=0, column=2, padx=5, pady=5)

        ttk.Label(root, text="File output:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.out_var = tk.StringVar()
        ttk.Entry(root, textvariable=self.out_var, width=50).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(root, text="Sfoglia...", command=self.browse_out).grid(row=1, column=2, padx=5, pady=5)

        ttk.Label(root, text="Passphrase:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.pass_var = tk.StringVar()
        ttk.Entry(root, textvariable=self.pass_var, show="*", width=40).grid(row=2, column=1, padx=5, pady=5)

        self.nexa_var = tk.BooleanVar()
        ttk.Checkbutton(root, text="Usa traslitterazione NEXA-S", variable=self.nexa_var).grid(row=3, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(root, text="Padding (0=none):").grid(row=4, column=0, sticky="w", padx=5, pady=5)
        self.pad_var = tk.IntVar(value=4096)
        ttk.Entry(root, textvariable=self.pad_var, width=10).grid(row=4, column=1, sticky="w", padx=5, pady=5)

        ttk.Button(root, text="Cifra", command=self.do_encrypt).grid(row=5, column=0, padx=5, pady=10)
        ttk.Button(root, text="Decifra", command=self.do_decrypt).grid(row=5, column=1, padx=5, pady=10)

        self.log = tk.Text(root, height=12, width=80)
        self.log.grid(row=6, column=0, columnspan=3, padx=5, pady=5)

    def browse_in(self):
        p = filedialog.askopenfilename()
        if p: self.in_var.set(p)
    def browse_out(self):
        p = filedialog.asksaveasfilename()
        if p: self.out_var.set(p)

    def do_encrypt(self):
        inp, outp, pas, pad, nexa = self.in_var.get(), self.out_var.get(), self.pass_var.get(), self.pad_var.get(), self.nexa_var.get()
        if not inp or not outp or not pas:
            messagebox.showerror("Errore", "Compila input, output e passphrase")
            return
        ok, err = run_encrypt(inp, outp, pas, pad, nexa)
        self.log.insert("end", f"Encrypt: {'OK' if ok else 'FAIL'}\n{err}\n")
    def do_decrypt(self):
        inp, outp, pas, nexa = self.in_var.get(), self.out_var.get(), self.pass_var.get(), self.nexa_var.get()
        if not inp or not outp or not pas:
            messagebox.showerror("Errore", "Compila input, output e passphrase")
            return
        ok, err = run_decrypt(inp, outp, pas, nexa)
        self.log.insert("end", f"Decrypt: {'OK' if ok else 'FAIL'}\n{err}\n")

if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
