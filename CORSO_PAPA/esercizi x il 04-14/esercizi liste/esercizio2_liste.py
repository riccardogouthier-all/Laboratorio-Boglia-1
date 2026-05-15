'''
Secondo Esercizio 
Scrivere un programma che date due liste stampi "OK"  se hanno almeno un membro comune altrimenti stampi "KO".  
Esempio: 
● lista1=[1,5,8] lista2=[3,1,10]  -> output: "OK" 
● lista1=[1,5,8] lista2=[3,11,10] -> output: "KO" 
'''


def have_common(lista1, lista2):
    for elemento in lista1:
        if elemento in lista2:
            return True
    return False

def elementi_comuni(lista1, lista2):
    in_comune = []
    for elemento in lista1:
        if elemento in lista2:
            in_comune.append(elemento)
    return in_comune

lista1 = [7, 9, 1, 5, 8]
lista2 = [7, 9, 3, 1, 10]
in_comune = []

if have_common(lista1, lista2):
    print(f"OK {elementi_comuni(lista1, lista2)}")
else:
    print("KO")