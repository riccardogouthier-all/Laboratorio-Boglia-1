'''Classe Libro, rappresenta un libro nel database'''

class Libro:

    def __init__(self, libroID, collocazione, titolo, autore, editore, classificazione):
        self.libroID = libroID
        self.collocazione = collocazione
        self.titolo = titolo
        self.autore = autore
        self.editore = editore
        self.classificazione = classificazione

    def __str__(self):
        return f"""
        Titolo: {self.titolo}, 
        autore: {self.autore}, 
        editore: {self.editore}, 
        Collocazione: {self.collocazione}       
        """
            
    def tohtml(self):

        return f"""
            <div>
                <h2>Titolo: {self.titolo}</h2>
                <h3>autore: {self.autore}</h2>
                <h4>editore: {self.editore}</h2>
                <h5>collocazione: {self.collocazione}</h2>        
            </div>
            """