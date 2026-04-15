'''
Terzo Esercizio 
Scrivere un programma per sostituire l'ultimo valore delle liste in una tupla con un valore richiesto in input. 
Esempio: 
valore : 100 
TuplaIN: ([10, 20, 40], [40, 50, 60], [70, 80, 90]) 
TuplaOUT: ([10, 20, 100], [40, 50, 100], [70, 80, 100])
'''


def controllo_liste_tupla(tupla):
    permesso = all(isinstance(elemento, list) for elemento in tupla)
    return permesso

def sostituisci_ultimo_valore(tupla_liste, valore):

    nuovi_elemnti = []
    for lista in tupla_liste:
        nuovo_elemnto = lista[:-1] + [valore]
        nuovi_elemnti.append(nuovo_elemnto)
    return nuovi_elemnti

valore = 100 
TuplaIN = ([10, 20, 40], [40, 50, 60], [70, 80, 90])

print(TuplaIN)
if not controllo_liste_tupla(TuplaIN):
    print("La tupla non contiene solo liste")
else:
    if any(len(lista) == 0 for lista in TuplaIN):
        print("La tupla contiene almeno una lista vuota")
    if controllo_liste_tupla(TuplaIN) and not any(len(lista) == 0 for lista in TuplaIN):
        print(sostituisci_ultimo_valore(TuplaIN, valore))
