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

def check_valori(*d):
    valori_comuni = []                      # Prendo tutti i valori del primo dizionario in una lista
    valori0 = list(d[0].values())
    valori1 = list(d[1].values())
    for v in valori0:
        if v in valori1:                    # controlla se il valore è presente anche nel secondo dizionario
            if v not in valori_comuni:      # evita duplicati nella lista finale
                valori_comuni.append(v)
    return valori_comuni

lista_diz = [diz1, diz2, diz3]
coppie = [(diz1, diz2), (diz2, diz3), (diz3, diz1)]
chiavi_tutte = [check_chiavi(d1, d2) for d1, d2 in coppie]
valori_tutti = [check_valori(d1, d2) for d1, d2 in coppie]

if all(isinstance(d, dict) for d in lista_diz):                #   <--- Controllo per vedere se i parametri da inserire nella funzione sono dizionari 
    if len(lista_diz)<2:
        print("Errore: un solo dizionario presente")
    else:
        if any(chiavi_tutte):
            print("Errore: chiavi condivise nei dizionari:")
            for chiave in chiavi_tutte:
                print(chiave)
            if any(valori_tutti):
                print("Errore: valori condivisi a coppie:")    
                for valore in valori_tutti:
                    print(valore)
        else:
            print(concat_dizionari(*lista_diz))
            if any(valori_tutti):
                print("Errore: valori condivisi a coppie:")    
                for valore in valori_tutti:
                    print(valore)
else:
    print("Errore: tutti gli argomenti devono essere dizionari")

