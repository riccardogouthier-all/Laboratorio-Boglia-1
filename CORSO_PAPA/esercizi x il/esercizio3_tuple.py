'''
Terzo Esercizio 
Scrivere un programma per sostituire l'ultimo valore delle liste in una tupla con un valore richiesto in input. 
Esempio: 
valore : 100 
TuplaIN: ([10, 20, 40], [40, 50, 60], [70, 80, 90]) 
TuplaOUT: ([10, 20, 100], [40, 50, 100], [70, 80, 100])
'''


def controllo_liste_tupla(tupla):
    """
    Verifica che tutti gli elementi della tupla siano liste.
    In ingresso => 
    tupla: Tupla da verificare
    Ritorna =>
    bool: True se tutti gli elementi sono liste, False altrimenti
    """
    permesso = all(isinstance(elemento, list) for elemento in tupla)    #   all() rende bool la variabile
    return permesso     #   ritorna valore bool (True False)

def sostituisci_ultimo_valore(tupla_liste, valore):
    """
    Sostituisce l'ultimo elemento di ogni lista nella tupla con nuovo_valore.
    In ingresso => 
    tupla_liste: Tupla contenente SOLO liste
    nuovo_valore: Valore da inserire come ultimo elemento
    Ritorna => 
    Tupla con le liste modificate o None se la tupla non contiene solo liste
    """
    nuovi_elemnti = []
    for lista in tupla_liste:
        nuovo_elemnto = lista[:-1] + [valore]
        nuovi_elemnti.append(nuovo_elemnto)
    return nuovi_elemnti

valore = 100    #   valore da sostituire nelle liste dalla tupla, senza restrizione
TuplaIN = ([10, 20, 40], [40, 50, 60], [70, 80, 90])    #   tupla di liste

# print(TuplaIN)    #   print per controllare gli errori
if controllo_liste_tupla(TuplaIN) == False:
    '''
    richiamo al metodo controllo_liste_tupla e se il metodo restituisce false stampa l'errore
    '''
    print("La tupla non contiene solo liste")
else:
    if any(len(lista) == 0 for lista in TuplaIN):   
        '''
        any() controlla che tutti gli argomenti inseriti nella funzione restituiscano true, 
        per cui inserendo un ciclo for e una condizione controlla se la condizione 
        viene restituita almeno una volta dal ciclo e stampa l'errore
        '''
        print("La tupla contiene almeno una lista vuota")
    else:
        '''
        Se non ci sono errori richiama normalmente il metodo usando la tupla e il valore dati in inizializzazione
        '''
        print(sostituisci_ultimo_valore(TuplaIN, valore))
