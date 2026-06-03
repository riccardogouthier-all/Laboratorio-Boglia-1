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

    def _parole_ordinate_per_lunghezza(self):
        parole_uniche = list({p.lower() for p in self.parole})   # rimuove duplicati
        return sorted(parole_uniche, key=len, reverse=True)


    def parola_piu_lunga(self):
        if not self.parole:
            return None
        parola_più_lunga = self._parole_ordinate_per_lunghezza()[0]
        return parola_più_lunga
    
    def salva_parola_piu_lunga(self, output: str = "output.txt"):
        parola = self.parola_piu_lunga()
        if parola is None:
            print(" Nessuna parola trovata, file di output non scritto.")
            return
        with open(output, "w", encoding="utf-8") as f:
            f.write(f"Parola più lunga ({len(parola)} caratteri): {parola}\n")
        print(f' Parola più lunga salvata in "{output}": "{parola}" ({len(parola)} caratteri)')


    def prime_n_parole_piu_lunghe(self, n: int):
        ordinate = self._parole_ordinate_per_lunghezza()
        prime_n_parole_piu_lunghe = ordinate[:n]
        return prime_n_parole_piu_lunghe

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
analisi dei dati, automazione e molto altro ancora."""

with open("testo_esempio.txt", "w", encoding="utf-8") as f:
    f.write(testo_esempio)
print(' File "testo_esempio.txt" creato con testo di esempio.\n')

analizzatore = AnalizzatoreTesto("testo_esempio.txt")

print("=" * 45)
print("TEST 1 — Parola più lunga")
print("=" * 45)
print("\n")
analizzatore.salva_parola_piu_lunga("output.txt")

# Verifica lettura output
with open("output.txt", "r", encoding="utf-8") as f:
    print(f' Contenuto di output.txt:\n{f.read()}')

a = input("\nPremi qualsiasi tasto per continuare al Test 2 facoltativo || oppure digita 'exit' per uscire: ").strip().lower()
if a == "exit":
    print("Uscita dal programma.")
    quit()
else:
    print("=" * 45)
    print("TEST 2 — Prime N parole più lunghe")
    print("=" * 45)
    print("\n")
    try:
        n = int(input("Quante parole vuoi salvare? (N): "))
    except ValueError:
        print("\n Valore non valido, uso N=5 come default.\n")
        n = 5

    analizzatore.salva_prime_n_parole(n, "output.txt")

    with open("output.txt", "r", encoding="utf-8") as f:
        print(f'\n Contenuto aggiornato di output.txt:\n{f.read()}')