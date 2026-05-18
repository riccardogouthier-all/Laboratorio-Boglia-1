diz1 = {'v1': 1, 'v2': 2, 'v3': 3}  
diz2 = {'v4': 4, 'v5': 5, 'v6': 6}
diz3 = {'v2': 7, 'v8': 8}

stringa= "aaaaaaaaa"
lista = ["aaaaaaaaaa"]
tupla = ("aaaaaaaaaaa")

def concat_dizionari(*dizionari)-> dict:
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
    # chiavi_c12 = check_chiavi(diz1, diz2)
    if len(tupla_diz)<2:
        print("Errore: un solo dizionario presente")
    else:
        if any(chiavi_tutte):
            print("Errore: chiavi condivise nei dizionari ", chiavi_tutte)
        else:
            print(concat_dizionari(*tupla_diz))
else:
    print("Errore: tutti gli argomenti devono essere dizionari")



# def check_chiavi(*d):      # <--- *d
#     if len(d)<2:
#         return "Errore: un solo dizionario presente"
#     chiavi_comuni = []
    
#     for n in d:
#         for chiave in n:
#             if chiave in :                                                # <--- Controlla se la chiave è presente in entrambi
#                 chiavi_comuni.append(chiave)
#         if not chiavi_comuni:
#             return concat_dizionari(d[0], d[1])
#         return "Errore: chiavi in comune", chiavi_comuni

# tupla_diz = [diz1, diz2, diz3]
# if all(isinstance(d, dict) for d in tupla_diz):                #   <--- Controllo per vedere se i parametri da inserire nella funzione sono dizionari 
#     dunito1 = check_chiavi(tupla_diz[0],tupla_diz[1])
#     if isinstance(dunito1, dict):
#         dunito2 = check_chiavi(dunito1, tupla_diz[2])
#         print("union: ", dunito2)
#     else:
#         print("union: ", dunito1)
# else:
#     print("Errore: tutti gli argomenti devono essere dizionari")


    
# if not check_chiavi(*tupla_diz):
#     print("controllo su tutti i dizionari: ", concat_dizionari(*tupla_diz))





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

# if all(isinstance(d, dict) for d in tupla_diz):                #   <--- Controllo per vedere se i parametri da inserire nella funzione sono dizionari 
#     # chiavi_c12 = check_chiavi(diz1, diz2)
#     if len(tupla_diz)<2:
#         print("Errore: un solo dizionario presente")
#     else:
#         if check_chiavi(diz1, diz2) or check_chiavi(diz2, diz3) or check_chiavi(diz1, diz3):
#             print("Dizionari 1/2: ", check_chiavi(diz1, diz2))
#             print("Dizionari 2/3: ", check_chiavi(diz2, diz3))
#             print("Dizionari 1/3: ", check_chiavi(diz1, diz3))
#             print("Errore: chiavi condivise nei dizionari sopra citati")
#         else:
#             print(concat_dizionari(*tupla_diz))
# else:
#     print("Errore: tutti gli argomenti devono essere dizionari")


# tupla = [{"a":1},{"a":1}]

# print(tupla[len(tupla)-1])

# for i in range(10):
#     i+=1
#     print(i)

# vuoi fare il controllo sulle chiavi, prendere quelle del primo dizionario e confrontarle una per una con le chiavi del secondo dizionario, se ci sono doppioni li aggiungi alla lista chiavi_doppione, finito il primo confronto unisci i dizionari con la funzione concat_dizionari e confronta il dizionario risultante con il terzo dizionario
# hai chiesto a perplexity, controlla l'ultima conversazione