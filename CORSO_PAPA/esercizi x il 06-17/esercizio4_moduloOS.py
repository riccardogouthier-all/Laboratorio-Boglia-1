'''
Scrivere un programma che elimini tutti i files che contengono nel nome una sequenza di caratteri dati in input.
'''

import os

def elimina_file_con_sequenza(percorso, sequenza):
    eliminati = 0

    for elemento in os.listdir(percorso):
        percorso_completo = os.path.join(percorso, elemento)
        if os.path.isfile(percorso_completo) and sequenza in elemento:
            os.remove(percorso_completo)
            eliminati += 1
            print(f"Eliminato: {elemento}")

    return eliminati


if __name__ == "__main__":
    percorso = input("Inserisci il percorso: ")
    sequenza = input("Inserisci la sequenza di caratteri da cercare nel nome: ")

    n = elimina_file_con_sequenza(percorso, sequenza)
    print(f"File eliminati: {n}")

