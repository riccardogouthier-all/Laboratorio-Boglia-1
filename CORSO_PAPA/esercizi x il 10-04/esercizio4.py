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

def fattoriale(n):
    """Calcola il fattoriale di n in modo iterativo."""
    risultato = 1 
    for i in range(1, n+1):
        risultato *= i
    return risultato

def calcola_e(n):
    """Calcola il numero di Nepero e con n termini della serie."""
    somma = 0
    for i in range(n):
        somma += 1/fattoriale(i)
    return somma

def main():
    n = input("Inserisci il numero di termini N: ")
    while not n.isdigit():
            print("Hai sbagliato a inserire il valore, solo numeri ammessi")
            main()
            
    n = int(n)        
    e_approssimato = calcola_e(n)
    print(f"e approssimato con {n} termini: {e_approssimato:.6f}")
    print(f"e reale (valore di math.e):     {math.e:.6f}")

if __name__ == "__main__":
     main()    