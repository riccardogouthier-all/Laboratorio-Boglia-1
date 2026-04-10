'''
Terzo esercizio 
Scrivi un programma per trovare il secondo numero più 
piccolo in una lista. 
'''

def piccolo(lista):
    lista_ordinata = sorted(lista)
    numero = []
    for elemento in lista_ordinata:
        if elemento not in numero:
            numero += [elemento]
    return int(numero[1])

lista = [4, 2, 7, 1, 3, 1]

print(f"Lista: {lista}")
print(f"Secondo numero più piccolo: {piccolo(lista)}")