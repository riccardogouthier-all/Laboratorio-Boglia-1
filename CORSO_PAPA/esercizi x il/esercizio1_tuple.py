'''
Primo Esercizio 
Scrivere un programma per rimuovere l'n- esimo elemento da una tupla non vuota.
'''

def rimouvi_carattere(tupla, posizione):
    if posizione > 0:
        nuova_tupla = tupla[:posizione-1] + tupla[posizione:]
        return nuova_tupla
    # elif posizione < 0:
    #     nuova_tupla = tupla[:posizione] + tupla[posizione:]
    #     return nuova_tupla
    elif posizione == -1:
         nuova_tupla = ()
         nuova_tupla = tupla[:len(tupla)-1]
         return nuova_tupla
    return nuova_tupla

tupla = ([10, 20, 40],"python",[40, 50, 60],"Miss Italia",[70, 80, 90])
posizione = -1

if posizione > len(tupla) or posizione < -len(tupla):
    print("La parola ha meno caratteri del numero inserito")
    posizione = len(tupla)
elif posizione == 0:
        print(tupla, "|  non hai eliminato nessun posizione dalla tupla")
else:
    print(rimouvi_carattere(tupla, posizione))