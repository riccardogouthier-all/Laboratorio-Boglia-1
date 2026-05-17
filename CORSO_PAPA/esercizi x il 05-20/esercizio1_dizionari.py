'''
Primo esercizio
Progettare una funzione che accetti un numero indefinito di dizionari e restituisca un dizionario che è la concatenazione di tutti i dizionari indicati come parametro formale alla funzione. Scrivete uno script che utilizzi tale funzione.
'''

diz1 = {'v1': 1, 'v2': 2, 'v3': 3}  
diz2 = {'v4': 4, 'v5': 5, 'v6': 6}
diz3 = {'v7': 7, 'v8': 8}

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
    return chiavi_comuni

if all(isinstance(d, dict) for d in [diz1, diz2, diz3]):                #   <--- Controllo per vedere se i parametri da inserire nella funzione sono dizionari 
    # chiavi_c12 = check_chiavi(diz1, diz2)
    if check_chiavi(diz1, diz2) or check_chiavi(diz2, diz3) or check_chiavi(diz1, diz3):
        print("Dizionari 1/2: ", check_chiavi(diz1, diz2))
        print("Dizionari 2/3: ", check_chiavi(diz2, diz3))
        print("Dizionari 1/3: ", check_chiavi(diz1, diz3))
        print("Errore: chiavi condivise nei dizionari sopra citati")
    else:
        print(concat_dizionari(diz1, diz2, diz3))
else:
    print("Errore: tutti gli argomenti devono essere dizionari")

# if diz1.keys() == diz3.keys(): # or diz1.keys() == diz2.keys() or diz2.keys() == diz3.keys():
    # chiavi_diz = []
    # chiavi_diz.append([k for k, v in diz1.items()])
# 
    # print("Le chiavi sono le stesse", chiavi_diz)
# else:
    # print("Le chiavi sono diverse")
    # print(concat_dizionari(diz1, diz2, diz3))


# def controllo_chiavi_duplicate(*d) -> list:
#     ddpartenza = {}
#     chiavi_viste = []
#     # chiavi_doppione= []
#     for chiave, valore in d.items():
#         if chiave not in chiavi_viste:
#             ddpartenza[chiave] = valore
#             chiavi_viste.append(valore)    
#     return ddpartenza
#     # return chiavi_viste

# print(controllo_chiavi_duplicate(diz1, diz2, diz3))

# vuoi fare il controllo sulle chiavi, prendere quelle del primo dizionario e confrontarle una per una con le chiavi del secondo dizionario, se ci sono doppioni li aggiungi alla lista chiavi_doppione, finito il primo confronto unisci i dizionari con la funzione concat_dizionari e confronta il dizionario risultante con il terzo dizionario
# hai chiesto a perplexity, controlla l'ultima conversazione