'''
Terzo esercizio
Scrivete un programma Python per ottenere il valore massimo e minimo in un dizionario. 
'''

dizionario = {
    "a": 10,
    "b": 3,
    "c": 25,
    "d": 7
}

def controlla_dizionario(d):
    if not d:
        return "Il dizionario è vuoto.", d

    chiavi_vuote = [k for k, v in d.items() if v is None or v == ""]

    if chiavi_vuote:
        return f"Chiavi non valorizzate: {chiavi_vuote}", d

    return "Il dizionario non è vuoto e tutte le chiavi hanno un valore.", d

messaggio, dizio_controll = controlla_dizionario(dizionario)

if "vuoto" in messaggio or "Chiavi" in messaggio:
    print(messaggio)
else:
    print(dizio_controll)
    valore_massimo = max(dizio_controll.values())
    valore_minimo = min(dizio_controll.values())

    if valore_massimo == valore_minimo:
        print("è presente un solo valore nel dizionario")
    else:
        print("Valore massimo:", valore_massimo)
        print("Valore minimo:", valore_minimo)


