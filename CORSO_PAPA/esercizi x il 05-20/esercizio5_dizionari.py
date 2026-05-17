'''
Quinto esercizio
Scrivete un programma Python per creare un dizionario da una stringa. Le lettere della stringa rappresentano le chiavi, i valori rappresentano le occorrenze della chiave nella stringa 
'''

def crea_dizionario_da_stringa(string):
    """Crea un dizionario contando le occorrenze di ogni lettera nella stringa"""
    dizionario = {}
    stringa = "".join(sorted(string.replace(" ","").replace(",","").replace("'","").replace("!","").replace("?","").replace(".","").lower()))
    for lettera in stringa:
        if lettera in dizionario:
            dizionario[lettera] += 1  # incrementa il conteggio
        else:
            dizionario[lettera] = 1   # inizializza a 1
    return dizionario

actual_input = "Da un sentiero partono sempre due strade, una che ti riporta da dove sei partito e l'altra chissa'."
risultato = crea_dizionario_da_stringa(actual_input)
print("Stringa originale:", actual_input)
print("Dizionario:", risultato)