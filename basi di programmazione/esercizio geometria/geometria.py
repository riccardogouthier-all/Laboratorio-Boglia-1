from filepunto import Punto

A = Punto(2,2)
B = Punto(6,2)
C = Punto(2,5)

print(A)    
print(B)    
print(C)    


'''Introduco il calcolo per i segmenti con le rispettive proprietà'''
from segmento import Segmento

AB = Segmento(A, B)
AC = Segmento(A, C)
BC = Segmento(B, C)

'''stampa formattazione con richiamo del metodo'''
print(f"la lunghezza del segmento AB è: {AB.lunghezza()}")
print(f"la lunghezza del segmento AC è: {AC.lunghezza()}")
print(f"la lunghezza del segmento BC è: {BC.lunghezza()}")


'''Introduco il calcolo per i triangoli con le rispettive proprietà'''
from triangolo import Triangolo

t1 = Triangolo(A, B, C)
t2 = Triangolo(Punto(5,5), Punto(9,9), Punto(15,6))

'''stampa solo il metodo che restituisce già la stringa formattata'''
print(t1.perimetro())
print(t1.area())
print(t1)

print(t2.perimetro())
print(t2.area())
print(t2)
