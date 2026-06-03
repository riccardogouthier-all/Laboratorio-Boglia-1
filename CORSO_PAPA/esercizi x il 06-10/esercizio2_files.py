'''
Scrivi una classe che legga un file di testo e stampi sul file: “output.txt” la parola più lunga contenuta. 
[Facoltativo: stampi sul file: “output.txt” le prime N parole più lunghe, N è dato in input dall'utente]. 

Istanziare la classe e provare i metodi implementati. 
'''

import re

class AnalizzatoreTesto:
    def __init__(self, percorso_file: str):
        self.percorso_file = percorso_file
        self.parole = []
        self._leggi_file()

    def _leggi_file(self):
        try:
            with open(self.percorso_file, "r", encoding="utf-8") as f:
                testo = f.read()
            self.parole = re.findall(r"[a-zA-ZàèìòùÀÈÌÒÙéÉ']+", testo)
            print(f' File "{self.percorso_file}" letto: {len(self.parole)} parole trovate.\n')
        except FileNotFoundError:
            print(f' Errore: il file "{self.percorso_file}" non esiste.')
            self.parole = []

    def _parole_ordinate_per_lunghezza(self) -> list[str]:
        """Restituisce la lista di parole uniche ordinate per lunghezza decrescente."""
        parole_uniche = list({p.lower() for p in self.parole})   # rimuove duplicati
        return sorted(parole_uniche, key=len, reverse=True)

    # ----------------------------------------------------------
    # Metodi pubblici
    # ----------------------------------------------------------

    def parola_piu_lunga(self) -> str | None:
        """Restituisce la parola più lunga trovata nel testo."""
        if not self.parole:
            return None
        return self._parole_ordinate_per_lunghezza()[0]

    def prime_n_parole_piu_lunghe(self, n: int) -> list[str]:
        """Restituisce le prime N parole più lunghe (senza duplicati)."""
        ordinate = self._parole_ordinate_per_lunghezza()
        return ordinate[:n]

    def salva_parola_piu_lunga(self, output: str = "output.txt"):
        """Scrive la parola più lunga sul file di output."""
        parola = self.parola_piu_lunga()
        if parola is None:
            print(" Nessuna parola trovata, file di output non scritto.")
            return
        with open(output, "w", encoding="utf-8") as f:
            f.write(f"Parola più lunga ({len(parola)} caratteri): {parola}\n")
        print(f' Parola più lunga salvata in "{output}": "{parola}" ({len(parola)} caratteri)')

    def salva_prime_n_parole(self, n: int, output: str = "output.txt"):
        """Scrive le prime N parole più lunghe sul file di output."""
        parole = self.prime_n_parole_piu_lunghe(n)
        if not parole:
            print(" Nessuna parola trovata, file di output non scritto.")
            return
        with open(output, "w", encoding="utf-8") as f:
            f.write(f"Le {len(parole)} parole più lunghe trovate:\n")
            f.write("-" * 35 + "\n")
            for i, p in enumerate(parole, 1):
                f.write(f"  {i:>2}. {p:<30} ({len(p)} caratteri)\n")
        print(f' Top-{len(parole)} parole salvate in "{output}":')
        for i, p in enumerate(parole, 1):
            print(f'     {i:>2}. "{p}" ({len(p)} caratteri)')

testo_esempio = """Python è un linguaggio di programmazione straordinariamente versatile.
Viene utilizzato in molteplici settori: sviluppo web, intelligenza artificiale,
analisi dei dati, automazione e molto altro ancora.
La sua semplicità sintattica lo rende accessibile ai principianti,
mentre la sua potenza lo rende indispensabile agli esperti.
Imparare la programmazione richiede determinazione e costanza."""

with open("testo_esempio.txt", "w", encoding="utf-8") as f:
    f.write(testo_esempio)
print(' File "testo_esempio.txt" creato con testo di esempio.\n')


# ============================================================
#  Istanziazione e test della classe
# ============================================================

analizzatore = AnalizzatoreTesto("testo_esempio.txt")

# --- Test 1: parola più lunga ---
print("=" * 45)
print("TEST 1 — Parola più lunga")
print("=" * 45)
analizzatore.salva_parola_piu_lunga("output.txt")

# Verifica lettura output
with open("output.txt", "r", encoding="utf-8") as f:
    print(f' Contenuto di output.txt:\n{f.read()}')

# --- Test 2: prime N parole (facoltativo) ---
print("=" * 45)
print("TEST 2 — Prime N parole più lunghe")
print("=" * 45)
try:
    n = int(input("Quante parole vuoi salvare? (N): "))
except ValueError:
    print(" Valore non valido, uso N=5 come default.")
    n = 5

analizzatore.salva_prime_n_parole(n, "output.txt")

# Verifica lettura output
with open("output.txt", "r", encoding="utf-8") as f:
    print(f'\n Contenuto aggiornato di output.txt:\n{f.read()}')