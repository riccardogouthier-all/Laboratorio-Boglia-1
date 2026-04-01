'''
Autore:  Riccardo Gouthier 
Data: 06/03/2026 
Titolo: Scrivere un programma che legga i coefficienti a e b di un'equazione di primo
        grado ax=b e ne scriva la soluzione (attenzione al dominio del coefficiente a)  
'''

# Sezione di input Dati 
# Inizializzazioni variabili 
a = float(input("Inserisci il primo numero: "))
while a == 0 :
    print("errore matematico")
    a = float(input("Inserisci il primo numero: "))

b = float(input("Inserisci il secondo numero: "))
# Elaborazione 

x = float(b/a)
# Eventuali sotto processi di Elaborazione
# Sezione di output
print(f'Il valore di ax = b ha come valore di x {x}')