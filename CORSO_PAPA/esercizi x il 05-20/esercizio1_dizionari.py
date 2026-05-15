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
diz3 = {'v1': 7, 'v2': 8}

stringa= "aaaaaaaaa"
lista = ["aaaaaaaaaa"]
tupla = ("aaaaaaaaaaa")

if all(isinstance(d, dict) for d in [diz1, diz2, diz3]):                #   <--- Controllo per vedere se i parametri da inserire nella funzione sono dizionari 
    print(concat_dizionari(diz1, diz2, diz3))
else:
    print("Errore: tutti gli argomenti devono essere dizionari")

def controllo_chiavi_duplicate(*d) -> list:
    ddpartenza = {}
    chiavi_viste = []
    chiavi_doppione= []
    for chiave, valore in d.items():
        if chiave not in chiavi_viste:
            ddpartenza[chiave] = valore
            chiavi_viste.append(chiave)    
    return ddpartenza
    return chiavi_viste

print(controllo_chiavi_duplicate(diz1))

# vuoi fare il controllo sulle chiavi, prendere quelle del primo dizionario e confrontarle una per una con le chiavi del secondo dizionario, se ci sono doppioni li aggiungi alla lista chiavi_doppione, finito il primo confronto unisci i dizionari con la funzione concat_dizionari e confronta il dizionario risultante con il terzo dizionario
# hai chiesto a perplexity, controlla l'ultima conversazione