'''
Secondo Esercizio 
Creare una classe Rettangolo con attributi base e altezza. 
Costruire tutti i metodi setter e getter per gli attributi. Aggiungere i metodi per il calcolo dell’area e del perimetro. 
Implementare un metodo di nome: “contiene” che ha come parametro un oggetto  rettangolo. 
Tale metodo deve restituire true se il rettangolo oggetto chiamante contiene il rettangolo oggetto parametro, false se non lo contiene. 
Un rettangolo “contiene” un altro quando la sua altezza e la sua base sono maggiori rispettivamente della base e dell’altezza del secondo rettangolo. 
'''

class Rettangolo:
    def __init__(self, base, altezza):
        self.__base = base
        self.__altezza = altezza

    '''Getter e setter base'''
    def get_base(self):
        return self.__base

    def set_base(self, base):
        if base > 0:
            self.__base = base
        else:
            print("La base deve essere positiva.")

    '''Getter e setter altezza'''
    def get_altezza(self):
        return self.__altezza

    def set_altezza(self, altezza):
        if altezza > 0:
            self.__altezza = altezza
        else:
            print("L'altezza deve essere positiva.")

    '''Metodi di calcolo'''
    def area(self):
        return self.__base * self.__altezza

    def perimetro(self):
        return 2 * (self.__base + self.__altezza)

    '''Metodo contiene'''
    def contiene(self, altro):
        return self.__base > altro.get_base() and self.__altezza > altro.get_altezza()

    def __str__(self):
        return f"Rettangolo(base={self.__base}, altezza={self.__altezza})"

r1 = Rettangolo(10, 8)
r2 = Rettangolo(6, 4)
r3 = Rettangolo(12, 3)

print(r1)                                   # Rettangolo ( base=10, altezza=8 )
print(f"Area r1: {r1.area()}")              # 80
print(f"Perimetro r1: {r1.perimetro()}")    # 36

if r1.contiene(r2):
    '''True con r2 → 10>6 e 8>4'''
    print("il primo rettangolo contiene il secondo")
else:
    '''False con r3 → 10<12 (la base non è maggiore)'''
    print("il primo rettangolo è più piccolo del secondo")
