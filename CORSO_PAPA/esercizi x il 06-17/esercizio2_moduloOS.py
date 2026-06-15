'''
Scrivere un programma che esamini tutte le directories sotto un dato percorso e conti tutti i files con una determinata estensione data in input.
[In prima battuta fermatevi al primo livello di profondità delle directories]
'''

import os

def conta_file_per_estensione(percorso, estensione):
    if not estensione.startswith('.'):
        estensione = '.' + estensione
    conteggio = 0

    for elemento in os.listdir(percorso):
        percorso_completo = os.path.join(percorso, elemento)
        if os.path.isfile(percorso_completo) and elemento.endswith(estensione):
            conteggio += 1

    return conteggio

if __name__ == "__main__":
    percorso = input("Inserisci il percorso: ")
    estensione = input("Inserisci l'estensione (es. .txt): ")

    n = conta_file_per_estensione(percorso, estensione)
    print(f"File con estensione '{estensione}' trovati: {n}")