
import os

NOME = input("Inserisci il tuo nome: ")  # <-- Modifica con il tuo nome
S = input("Inserisci la stringa da cercare: ")  # <-- Modifica con la stringa da cercare

def contiene_sottosequenza(riga, s):
    """Restituisce True se tutti i caratteri di s appaiono in riga nell'ordine."""
    indice = 0
    for carattere in riga:
        if carattere == s[indice]:
            indice += 1
        if indice == len(s):
            return True
    return False

def filtra_file(nome_file_input, nome_file_output, s):
    righe_scritte = 0

    try:
        with open(nome_file_input, "r") as f_in, open(nome_file_output, "w") as f_out:
            for riga in f_in:
                if contiene_sottosequenza(riga.rstrip("\n"), s):
                    f_out.write(riga)
                    righe_scritte += 1

        print(f"Filtro completato.")
        print(f"Stringa cercata: '{s}'")
        print(f"Righe scritte in '{nome_file_output}': {righe_scritte}")

    except FileNotFoundError:
        print(f"Errore: file '{nome_file_input}' non trovato.")

if __name__ == "__main__":
    cartella_script = os.path.dirname(os.path.abspath(__file__))
    percorso_input  = os.path.join(cartella_script, "input.txt")
    percorso_output = os.path.join(cartella_script, f"output_{NOME}.txt")
    filtra_file(percorso_input, percorso_output, S)