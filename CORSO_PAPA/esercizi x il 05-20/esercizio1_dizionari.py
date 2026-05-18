'''
Primo esercizio
Progettare una funzione che accetti un numero indefinito di dizionari e restituisca un dizionario che è la concatenazione di tutti i dizionari indicati come parametro formale alla funzione. Scrivete uno script che utilizzi tale funzione.
'''

diz1 = {'v1': 1, 'v2': 2, 'v3': 3}  
diz2 = {'v4': 4, 'v5': 5, 'v6': 6}
diz3 = {'v7': 7, 'v8': 8}

stringa= "aaaaaaaaa"
lista = ["aaaaaaaaaa"]
tupla = ("aaaaaaaaaa")

def concat_dizionari(*dizionari):
    risultato = {}
    for d in dizionari:
        risultato.update(d)                                             # <--- Unisce i dizionari
    return risultato

def check_chiavi(*d):
    chiavi_comuni = []
    for chiave in d[0]:
        if chiave in d[1]:                                                # <--- Controlla se la chiave è presente in entrambi
            chiavi_comuni.append(chiave)
    return chiavi_comuni

tupla_diz = [diz1, diz2, diz3]
coppie = [(diz1, diz2), (diz2, diz3), (diz1, diz3)]
chiavi_tutte = [check_chiavi(d1, d2) for d1, d2 in coppie]

if all(isinstance(d, dict) for d in tupla_diz):                #   <--- Controllo per vedere se i parametri da inserire nella funzione sono dizionari 
    if len(tupla_diz)<2:
        print("Errore: un solo dizionario presente")
    else:
        if any(chiavi_tutte):
            print("Errore: chiavi condivise nei dizionari ", chiavi_tutte)
        else:
            print(concat_dizionari(*tupla_diz))
else:
    print("Errore: tutti gli argomenti devono essere dizionari")

