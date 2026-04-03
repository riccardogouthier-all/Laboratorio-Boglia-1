'''  
Autore:  Riccardo Gouthier     
Data: 26/03/2026     
Titolo: 
La seguente è la formula per valutare numericamente il numero di Nepero e:
        e:= sum n=0 to ∞ di { 1/(n!) = 1 0! + 1 1! +...+ 1 n! +... }

4.a Scrivere una funzione che restituisca un valore approssimato di e all'ennesimo termine, dove N è inserito come parametro formale alla funzione.  
    Esempio: calcola_e(3) restituirà il valore di e calcolato con tre termini della (1), cioè:
            e= 1/0! + 1/1! + 1/2! = 1 + 1 + 0.5 = 2.5 
    La funzione calcola_e deve richiamare la funzione di calcolo del fattoriale. 
    Scrivere il codice della funzione e il programma principale che la chiama chiedendo in input il numero N. 
    
4.b Supponendo di porre il numero di Nepero = 2.718281828459045 dico che  errore = calcola_e(N) - Nepero  sia l'errore che commetto nella valutazione di e. 
    Modificare la funzione che restituisce la valutazione di e con N termini andando a far restituire anche l'errore commesso nella valutazione.  
    Suggerimento: la funzione calcola_e(N) dovrà restituire due valori,  2.718281828459045 potrebbe essere memorizzato in una variabile globale. 
    esempio: valuta_e(3) restituisce il valore calcolato nel punto 4.a 2.5 e 0,218281828459045 che rappresenta la differenza tra 2.718281828459045 e 2.5 
'''

import math

"""Metodo 1: Costante predefinita"""

e_val = math.e
print(f"Valore di e (math.e): {e_val}")

"""Metodo 2: Serie di Taylor (approssimazione)"""

n = 20 # Numero di termini
e_approx = sum(1/math.factorial(i) for i in range(n))
print(f"Valore di e (serie Taylor): {e_approx}")


