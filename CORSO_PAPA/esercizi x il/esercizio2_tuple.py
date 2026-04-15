'''
Secondo Esercizio 
Scrivere un programma per invertire una tupla 
Esempio: tpleIN=('a','c',f') tpleOUT=('f','c','a') 
'''

def inverti_tupla(tupla):
    return tupla[::-1]

tupla = ([10, 20, 40],"python",[40, 50, 60],"Miss Italia",[70, 80, 90])

if len(tupla) == 0:
    print("La tupla è vuota")
else:
    print(inverti_tupla(tupla))
