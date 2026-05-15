'''
Quarto esercizio
Scrivete un programma Python per rimuovere i duplicati dal dizionario.  
'''

dizionario = {
    "a": 1,
    "b": 2,
    "c": 1,  # duplicato di "a"
    "d": 3,
    "e": 2,   # duplicato di "b"
    "f":"casa",
    "g":"casa",
    "h":"a"
}

def controlla_dizionario(d):
    if not d:
        return "Il dizionario è vuoto.", d
    chiavi_vuote = [k for k, v in d.items() if v is None]
    if chiavi_vuote:
        return "Chiavi non valorizzate correttamente", d    
    return "Il dizionario non è vuoto e tutte le chiavi hanno un valore.", d

def rimuovi_duplicati(d):
    ddpartenza = {}
    valori_visti = []
    for chiave, valore in d.items():
        if valore not in valori_visti:
            ddpartenza[chiave] = valore
            valori_visti.append(valore)    
    return ddpartenza

print("Dizionario originale:", dizionario)
messaggio, dizio_controll = controlla_dizionario(dizionario)
if messaggio == "Il dizionario è vuoto.":
    print(messaggio)
else:
    print(messaggio)
    dsduplicati = rimuovi_duplicati(dizio_controll)
    print("Dizionario senza duplicati:", dsduplicati)
