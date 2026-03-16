from filepunto import Punto
from segmento import Segmento
import math

class Triangolo :


    '''definisco cos'è'''
    def __init__ (self,  A: Punto,  B: Punto,  C: Punto):
        self.A = A
        self.B = B
        self.C = C

        self.AB = Segmento(A, B)
        self.AC = Segmento(A, C)
        self.BC = Segmento(B, C)

    '''Proprietà'''
    def perimetro(self) :
        return self.AB.lunghezza() + self.AC.lunghezza() + self.BC.lunghezza()

    def area(self) :
        sp = self.perimetro() /2
        
        return math.sqrt(sp*(sp-self.AB.lunghezza()) * (sp-self.AC.lunghezza()) * (sp-self.BC.lunghezza()))

    '''ToString()'''
    def __str__(self):
        return f"Il perimetro di questo triangolo è {self.perimetro()}, la superficie di questo triangolo è {self.area()}"