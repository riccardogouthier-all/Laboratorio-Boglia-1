class Animal:
    def __init__(self, nome):
        self.nome = nome

class Predatore(Animal):
    def __init__(self, nome):
        super().__init__(nome)

    def caccia(self):
        print(f"{self.nome} sta cacciando")
        
class Preda(Animal):
    def __init__(self, nome):
        super().__init__(nome)

    def scappa(self):
        print("Sto scappando")

class Tigre(Predatore):
    def __init__(self, nome):
        super().__init__(nome)
        print("oggetto di tipo tigre")

class Gazzella(Preda):
    def __init__(self, nome):
        super().__init__(nome)
        print("oggetto di tipo gazzella")

class Pesce(Predatore, Preda):
    def __init__(self, nome):
        super().__init__(nome)
        print("oggetto di tipo pesce")


hobbes = Tigre()
gazza = Gazzella()
nemo = Pesce()

hobbes.caccia()
gazza.scappa()

nemo.scappa()
nemo.caccia()