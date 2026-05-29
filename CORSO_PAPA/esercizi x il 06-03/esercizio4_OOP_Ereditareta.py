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
    @property
    def nome(self):      return self.__nome
    
    @property
    def indirizzo(self): return self.__indirizzo
    
    @property
    def eta(self):       return self.__eta

    # setter
    @nome.setter
    def nome(self, nome):           self.__nome = nome
    
    @indirizzo.setter
    def indirizzo(self, indirizzo): self.__indirizzo = indirizzo
    
    @eta.setter
    def eta(self, eta):             self.__eta = eta

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
    @property
    def scuola(self):      return self.__scuola
    @property
    def media_voti(self):  return self.__media_voti

    # setter aggiuntivi
    @scuola.setter
    def scuola(self, scuola):          self.__scuola = scuola
    @media_voti.setter
    def media_voti(self, media_voti):  self.__media_voti = media_voti

    def __str__(self):
        return (super().__str__().replace("Persona:", "Studente:") +
                f"\n  scuola    : {self.__scuola}"
                f"\n  media     : {self.__media_voti}")

'''Sottoclasse Lavoratore'''

class Lavoratore(Persona):
    def __init__(self, nome, indirizzo, eta, azienda, stipendio):
        super().__init__(nome, indirizzo, eta)
        self.__azienda = azienda
        self.__stipendio = stipendio

    # getter aggiuntivi
    @property
    def azienda(self): return self.__azienda
    @property
    def stipendio(self): return self.__stipendio

    # setter aggiuntivi
    @azienda.setter
    def azienda(self, azienda): self.__azienda = azienda
    @stipendio.setter
    def stipendio(self, stipendio): self.__stipendio = stipendio

    def __str__(self):
        return (super().__str__().replace("Persona:", "Lavoratore:") +
                f"\n  azienda   : {self.__azienda}"
                f"\n  stipendio : {self.__stipendio} €")


'''Test'''

p = Persona("Mario Rossi", "Via Roma 1, Milano", 40)
print(p)
print("\nCambio il nome e l'età dell'oggetto persona usando i metodi setter")
p.nome = "Luca Bianchi"
p.eta = 20
print(f"Nuovo print della persona usando i metodi:\n  nome: {p.nome}\n  indirizzo: {p.indirizzo}\n  età: {p.eta}\n")

print("\n","=" * 100,"\n")

s = Studente("Giulia Ferrari", "Via Po 7, Torino", 19, "Università di Torino", 25)
print(s)
print("\nCambio il nome, l'età e la media dell'oggetto studente usando i metodi setter")
s.nome = "Marco Neri"
s.eta = 29
s.media_voti = 29.0
print(f"Nuovo print dello studente usando i metodi:\n  nome: {s.nome}\n  indirizzo: {s.indirizzo}\n  età: {s.eta}\n  scuola: {s.scuola}\n  media: {s.media_voti}")

print("\n","=" * 100,"\n")

l = Lavoratore("Carlo Verdi", "Corso Italia 3, Roma", 35, "TechSrl", 2500)
print(l)
print("\nCambio il nome, l'età e lo stipendio dell'oggetto lavoratore usando i metodi setter")
l.nome = "Giulia Rossi"
l.eta = 45
l.stipendio = 3000
print(f"Nuovo print dello lavoratore usando i metodi:\n  nome: {l.nome}\n  indirizzo: {l.indirizzo}\n  età: {l.eta}\n  azienda: {l.azienda}\n  stipendio: {l.stipendio} €")


