# diz1 = {'v1': 1, 'v2': 2, 'v3': 3}  
# diz2 = {'v4': 4, 'v5': 5, 'v6': 6}
# diz3 = {'v3': 7, 'v8': 8}

# stringa= "aaaaaaaaa"
# lista = ["aaaaaaaaaa"]
# tupla = ("aaaaaaaaaaa")

# def concat_dizionari(*dizionari)-> dict:
#     risultato = {}
#     for d in dizionari:
#         risultato.update(d)                                             # <--- Unisce i dizionari
#     return risultato

# def check_chiavi(*d):      # <--- *d
#     if len(d)<2:
#         return "Errore: un solo dizionario presente"
#     chiavi_comuni = []
    
#     for chiave in d[]:
#         if chiave in d[n+1]:                                                # <--- Controlla se la chiave è presente in entrambi
#             chiavi_comuni.append(chiave)
#     if not chiavi_comuni:
#         return concat_dizionari(d[0], d[1])
#     return "Errore: chiavi in comune", chiavi_comuni


# tupla_diz = [diz1]
# if all(isinstance(d, dict) for d in tupla_diz):                #   <--- Controllo per vedere se i parametri da inserire nella funzione sono dizionari 
#     dunito1 = check_chiavi(tupla_diz[0],tupla_diz[1])
#     if isinstance(dunito1, dict):
#         dunito2 = check_chiavi(dunito1, tupla_diz[2])
#         print("union: ", dunito2)
#     else:
#         print("union: ", dunito1)
# else:
#     print("Errore: tutti gli argomenti devono essere dizionari")


    
# tupla = [{"a":1},{"a":1}]

# print(tupla[len(tupla)-1])



for i in range(10):
    i+=1
    print(i)