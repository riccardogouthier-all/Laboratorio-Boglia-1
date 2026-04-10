'''
Primo Esercizio 
Scrivere un programma python che rimuova gli elementi duplicati da una lista.  
Esempio:  
listaIN = [2, -4 ,5,6,5,5,2]  
listaOUT= [2,-4,5,6] 
'''

def remuovi_duplicati(lista):
    numeri = []
    for n in lista:
        if n not in numeri:
            numeri.append(n)
    return list(numeri)

lista_numeri = [1,2,3,4,5,6,7,8,9,1,2,3,4,5,6,1,2,3]
lista_OUTPUT = remuovi_duplicati(lista_numeri)

print(f"lista in input = {lista_numeri} \nlista in output = {lista_OUTPUT}")
