'''
Autore:  Riccardo Gouthier 
Data: 06/03/2026 
Titolo: Scrivere un programma  che legga i coefficienti a, b e c di un'equazione di secondo grado ax2+bx+c=0 e ne scriva le soluzioni.   
'''

import math

# Sezione di input Dati 
# Inizializzazioni variabili 
a = float(input("Inserisci il primo numero: "))
while a == 0 :
    print("errore matematico")
    a = float(input("Inserisci il primo numero: "))

b = float(input("Inserisci il secondo numero: "))
c = float(input("Inserisci il terzo numero: "))

# Elaborazione 
delta = b*b - 4*(a*c)
x1 = float((-b + math.sqrt(delta))/2*a)

x2 = float((-b - math.sqrt(delta))/2*a)

# Eventuali sotto processi di Elaborazione
# Sezione di output
print(f'L espressione ax^2+bx+c = 0 ha come valori di x {x1} e {x2}')