''' 
Primo Esercizio 
Scrivere un programma per rimuovere l'n- esimo carattere da una stringa non vuota.
Progettare una funzione che accetti la stringa, la posizione del carattere e restituisca la stringa modificata. 
'''



def rimouvi_carattere(stringa, lettera):
    return stringa[:lettera] + stringa[lettera+1:]

stringa = "capra"
lettera = 3

if lettera > len(stringa):
    print("La parola ha meno caratteri del numero inserito")
    lettera = len(stringa)
else:
    print(rimouvi_carattere(stringa, lettera))