'''
Autore:  Riccardo Gouthier 
Data: 06/03/2026 
Titolo: Scrivere un programma che legga il raggio r di una circonferenza e ne calcoli l'area e la lunghezza.   
'''
import math

# Sezione di input Dati 
# Inizializzazioni variabili 
r = float(input("Inserisci il primo numero: "))
while r == 0 :
    print("errore matematico")
    r = float(input("Inserisci il primo numero: "))

# Elaborazione 
A = float(math.pi*r*r)
C = float(2*r*math.pi)


# Eventuali sotto processi di Elaborazione
# Sezione di output
print(f'Dato il raggio {r} la circonferenza ha valore {C} e area {A}')