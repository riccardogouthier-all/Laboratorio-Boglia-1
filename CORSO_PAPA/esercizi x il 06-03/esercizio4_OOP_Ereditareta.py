'''
Si definisca una classe Persona che abbia i seguenti attributi: 
● nome 
● indirizzo 
● età 

Tale classe contiene i seguenti metodi: 
il costruttore, 
l'overriding del metodo __str__, 
tutti i metodi getter e setter degli attributi. 

Si vogliono derivare dalla classe Persona le seguenti classi:  
● Studente 
La prima deve avere gli attributi aggiuntivi: 
● Scuola 
● Media voti 

● Lavoratore 
La seconda deve avere gli attributi aggiuntivi: 
● Azienda 
● Stipendio 

Aggiungere tutti i metodi getter e setter relativi agli attributi aggiuntivi. 
Inoltre effettuare l'overriding dei costruttori e del metodo str inserendo gli attributi aggiuntivi. 
Provare le tre classi instanziando almeno un oggetto per classe e provando qualche metodo. 
'''

'''Classe base'''

class Persona:
    def __init__(self, nome, indirizzo, eta):
        self.__nome      = nome
        self.__indirizzo = indirizzo
        self.__eta       = eta

    # getter
    def get_nome(self):      return self.__nome
    def get_indirizzo(self): return self.__indirizzo
    def get_eta(self):       return self.__eta

    # setter
    def set_nome(self, nome):           self.__nome = nome
    def set_indirizzo(self, indirizzo): self.__indirizzo = indirizzo
    def set_eta(self, eta):             self.__eta = eta

    def __str__(self):
        return (f"Persona:\n"
                f"  nome      : {self.__nome}\n"
                f"  indirizzo : {self.__indirizzo}\n"
                f"  età       : {self.__eta}")

'''Sottoclasse Studente'''

class Studente(Persona):
    def __init__(self, nome, indirizzo, eta, scuola, media_voti):
        super().__init__(nome, indirizzo, eta)
        self.__scuola     = scuola
        self.__media_voti = media_voti

    # getter aggiuntivi
    def get_scuola(self):      return self.__scuola
    def get_media_voti(self):  return self.__media_voti

    # setter aggiuntivi
    def set_scuola(self, scuola):          self.__scuola = scuola
    def set_media_voti(self, media_voti):  self.__media_voti = media_voti

    def __str__(self):
        return (super().__str__().replace("Persona:", "Studente:") +
                f"\n  scuola   : {self.__scuola}"
                f"\n  media    : {self.__media_voti}")

'''Sottoclasse Lavoratore'''

class Lavoratore(Persona):
    def __init__(self, nome, indirizzo, eta, azienda, stipendio):
        super().__init__(nome, indirizzo, eta)
        self.__azienda   = azienda
        self.__stipendio = stipendio

    # getter aggiuntivi
    def get_azienda(self):   return self.__azienda
    def get_stipendio(self): return self.__stipendio

    # setter aggiuntivi
    def set_azienda(self, azienda):     self.__azienda = azienda
    def set_stipendio(self, stipendio): self.__stipendio = stipendio

    def __str__(self):
        return (super().__str__().replace("Persona:", "Lavoratore:") +
                f"\n  azienda  : {self.__azienda}"
                f"\n  stipendio: {self.__stipendio} €")


'''Test'''

p = Persona("Mario Rossi", "Via Roma 1, Milano", 40)
print(p)
print("Cambio il nome e l'età dell'oggetto persona usando i metodi setter")
p.set_nome("Luca Bianchi")
p.set_eta(20)
print(p)
print("Nuovo print della persona usando i metodi:", p.get_nome(), p.get_indirizzo(), p.get_eta(), "\n")

# s = Studente("Giulia Ferrari", "Via Po 7, Torino", 19, "Università di Torino", 28.5)
# print(s)
# s.set_media_voti(29.0)
# print("→ get_scuola():", s.get_scuola())
# print("→ media aggiornata:", s.get_media_voti())
# print()

# l = Lavoratore("Carlo Verdi", "Corso Italia 3, Roma", 35, "TechSrl", 2500)
# print(l)
# l.set_stipendio(3000)
# print("→ get_azienda():", l.get_azienda())
# print("→ stipendio aggiornato:", l.get_stipendio())
