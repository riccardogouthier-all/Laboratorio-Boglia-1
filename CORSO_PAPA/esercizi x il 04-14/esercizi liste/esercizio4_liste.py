'''
Quarto esercizio 
Scrivere un programma Python per dividere una data lista 
in due parti in cui viene data la lunghezza della prima 
parte della lista. 

Esempio:  
Lista originale: [1, 1, 2, 3, 4, 4, 5, 1]  
Lunghezza della prima parte della lista: 3  

Output :  
Prima parte: [1, 1, 2] ,  
Seconda parte: [3, 4, 4, 5, 1] 
'''


def dividi_lista(lista, n):
    primo = lista[:n]
    secondo = lista[n:]
    return primo, secondo

lista = [1,2,1,2,3,4,5,6,7,8,9]
n = 4
prima_parte, seconda_parte = dividi_lista(lista, n)
print(f"Hai inserito come lista: {lista} e hai scelto di dividerla dal carattere numero {n}. \nPrima parte: {prima_parte} \nSeconda parte: {seconda_parte}")