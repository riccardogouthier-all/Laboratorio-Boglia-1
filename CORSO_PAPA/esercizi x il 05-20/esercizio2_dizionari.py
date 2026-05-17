'''
Secondo esercizio
Scrivete uno script Python per generare e stampare un dizionario che contenga un numero (compreso tra 1 e n) nella forma (x, x*x). 
'''

n = 5

if n <= 0 or not isinstance(n, int):
    print("Cambiare il valore in input in un numero intero e maggiore di 0")
else:
    dizionario = {}
    for x in range(1, n + 1):
        dizionario[x] = x * x
    print(dizionario)

    