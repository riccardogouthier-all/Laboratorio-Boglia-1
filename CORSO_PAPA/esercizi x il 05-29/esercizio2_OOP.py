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

if __name__ == "__main__":
    '''Test della classe Rettangolo con 3 oggetti'''
    r1 = Rettangolo(10, 8)
    r2 = Rettangolo(6, 4)
    r3 = Rettangolo(12, 3)

    print(f"\nRettangoli:\n{r1}\n{r2}\n{r3}")                                                                                   # print di tutti gli oggetti Rettangolo
    print(f"\nAree:\nArea r1: {r1.area()} \nArea r2: {r2.area()} \nArea r3: {r3.area()}")                                       # 80, 24, 36
    print(f"\nPerimetri:\nPerimetro r1: {r1.perimetro()} \nPerimetro r2: {r2.perimetro()} \nPerimetro r3: {r3.perimetro()}")    # 36, 20, 30

    if r1.contiene(r2):
        '''True con r2 → 10>6 e 8>4'''
        print("\nil primo rettangolo contiene il secondo\n")
    else:
        '''False con r3 → 10<12 (la base non è maggiore)'''
        print("\nil primo rettangolo è più piccolo del secondo\n")
