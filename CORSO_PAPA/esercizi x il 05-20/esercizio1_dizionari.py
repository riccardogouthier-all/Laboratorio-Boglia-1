'''
Primo esercizio
Progettare una funzione che accetti un numero indefinito di dizionari e restituisca un dizionario che è la concatenazione di tutti i dizionari indicati come parametro formale alla funzione. Scrivete uno script che utilizzi tale funzione.
'''

def concat_dizionari(*dizionari)-> dict:
    risultato = {}
    for d in dizionari:
        risultato.update(d)
    return risultato

diz1 = {'v1': 1, 'v2': 2, 'v3': 3}
diz2 = {'v4': 4, 'v5': 5, 'v6': 6}
diz3 = {'v7': 7, 'v8': 8}

stringa= "aaaaaaaaa"
lista = ["aaaaaaaaaa"]
tupla = ("aaaaaaaaaaa")

if all(isinstance(d, dict) for d in [diz1, diz2, diz3]):                #   <--- Controllo per vedere se i parametri da inserire nella funzione sono dizionari 
    print(concat_dizionari(diz1, diz2, diz3))
else:
    print("Errore: tutti gli argomenti devono essere dizionari")

    