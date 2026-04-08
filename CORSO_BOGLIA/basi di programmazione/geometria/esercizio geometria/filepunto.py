'''Classe che rappresenta il punto sul piano Cartesiano'''


class Punto :

    def __init__ (self, x: int, y: int):
        self.x = x
        self.y = y


    '''print(f"Ho creato un nuovo punto di coordinate: ({self.x}, {self.y})") '''
    def __str__(self) :
        return f"le coordinate di questo punto sono: ({self.x}, {self.y})"



















