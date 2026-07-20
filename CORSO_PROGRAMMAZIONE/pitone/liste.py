# provaprova sei il più bello

class Studente:
    def __init__(self, nome, cognome, valutazione):
        self.nome = nome
        self.cognome = cognome
        self.valutazione = valutazione

studenti = []

record1 = ['Pietro','Rossi',28]

studenti.append(Studente(nome=record1[0], cognome=record1[1], valutazione=record1[2]))

