'''Classe che rappresenta il segmento sul piano Cartesiano'''
from filepunto import Punto
import math 

'''from geometria import A, B'''

class Segmento :

    def __init__ (self,  A: Punto,  B: Punto):
        self.A = A
        self.B = B
        
    def lunghezza(self):
        
        lungh = math.sqrt(pow(self.B.x - self.A.x, 2) + pow(self.B.y - self.A.y, 2))
        return lungh
    
'''
    print(f"Ho creato un nuovo segmento con lunghezza: {lunghezza()}")
'''




