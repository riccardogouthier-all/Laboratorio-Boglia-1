'''
Terzo esercizio
Scrivete un programma Python per ottenere il valore massimo e minimo in un dizionario. 
'''

dizionario = {
    'a': -42, #
    'b': 17, 
    'c': 89, 
    'd': 5, 
    'e': 63, 
    'f': 31.9238467, 
    'g': 78, 
    'h': -14, 
    'i': 95.293874, #
    'j': 26
}

def controlla_dizionario(d):
    if not d:
        return "Il dizionario è vuoto.", d
    chiavi_vuote = [k for k, v in d.items() if v is None or isinstance(v, str)]
    if chiavi_vuote:
        return "Chiavi non valorizzate correttamente", d
    return "Il dizionario non è vuoto e tutte le chiavi hanno un valore.", d

messaggio, dizio_controll = controlla_dizionario(dizionario)

if messaggio == "Il dizionario è vuoto." or messaggio == "Chiavi non valorizzate correttamente":
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

