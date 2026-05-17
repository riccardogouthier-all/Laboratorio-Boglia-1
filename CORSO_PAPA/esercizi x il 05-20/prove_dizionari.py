diz1 = {'v1': 1, 'v2': 2, 'v3': 3}  
diz2 = {'v4': 4, 'v2': 5, 'v6': 6}
diz3 = {'v2': 7, 'v3': 8}

stringa= "aaaaaaaaa"
lista = ["aaaaaaaaaa"]
tupla = ("aaaaaaaaaaa")

def concat_dizionari(*dizionari)-> dict:
    risultato = {}
    for d in dizionari:
        risultato.update(d)                                             # <--- Unisce i dizionari
    return risultato

def check_chiavi(d1, d2):
    chiavi_comuni = []
    for chiave in d1:
        if chiave in d2:                                                # <--- Controlla se la chiave è presente in entrambi
            chiavi_comuni.append(chiave)
    if not chiavi_comuni:
        return concat_dizionari(d1,d2)
    return "Errore: chiavi in comune", chiavi_comuni

if all(isinstance(d, dict) for d in [diz1, diz2, diz3]):                #   <--- Controllo per vedere se i parametri da inserire nella funzione sono dizionari 
    # chiavi_c12 = check_chiavi(diz1, diz2)
    # if check_chiavi(diz1, diz2) or check_chiavi(diz2, diz3) or check_chiavi(diz1, diz3):
        # print("Dizionari 1/2: ", check_chiavi(diz1, diz2))
        # print("Dizionari 2/3: ", check_chiavi(diz2, diz3))
        # print("Dizionari 1/3: ", check_chiavi(diz1, diz3))
    ddd1 = check_chiavi(diz1, diz2)
    print(ddd1)
    if isinstance(ddd1, dict):
        ddd2 = check_chiavi(ddd1, diz3)
        print(ddd2)

    #     print("Errore: chiavi condivise nei dizionari sopra citati")
    # else:
    #     print(concat_dizionari(diz1, diz2, diz3))
else:
    print("Errore: tutti gli argomenti devono essere dizionari")