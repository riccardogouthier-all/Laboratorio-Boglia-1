diz1 = {'v1': 1, 'v2': 2, 'v3': 3}  
diz2 = {'v4': 4, 'v5': 5, 'v6': 6}
diz3 = {'v3': 7, 'v8': 8}

stringa= "aaaaaaaaa"
lista = ["aaaaaaaaaa"]
tupla = ("aaaaaaaaaaa")

def concat_dizionari(*dizionari)-> dict:
    risultato = {}
    for d in dizionari:
        risultato.update(d)                                             # <--- Unisce i dizionari
    return risultato

def check_chiavi(*d: dict):      # <--- *d
    chiavi_comuni = []
    for chiave in d[0]:
        if chiave in d[1]:                                                # <--- Controlla se la chiave è presente in entrambi
            chiavi_comuni.append(chiave)
    if not chiavi_comuni:
        return concat_dizionari(d[0], d[1])
    return "Errore: chiavi in comune", chiavi_comuni

if all(isinstance(d, dict) for d in [diz1, diz2, diz3]):                #   <--- Controllo per vedere se i parametri da inserire nella funzione sono dizionari 
    ddd1 = check_chiavi(diz1, diz2)
    if isinstance(ddd1, dict):
        ddd2 = check_chiavi(ddd1, diz3)
        print("union: ", ddd2)
    else:
        print("union: ", ddd1)
else:
    print("Errore: tutti gli argomenti devono essere dizionari")