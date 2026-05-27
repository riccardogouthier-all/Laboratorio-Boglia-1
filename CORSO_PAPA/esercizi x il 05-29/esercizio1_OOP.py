'''
Primo Esercizio 
Creare una classe Insegnante con attributi nome, età e stipendio, dove stipendio deve essere un attributo privato. 
Costruire tutti i metodi getter e setter per gli attributi (anche per quelli pubblici) Effettuare l’overriding del metodo __str__ in maniera tale che restituisca gli attributi nome e età. 
Provare la classe istanziando almeno due oggetti. 
'''

class Insegnante:
    """Classe che rappresenta un insegnante con nome, età e stipendio (privato)."""

    def __init__(self, nome, eta, stipendio):
        self.nome = nome
        self.eta = eta
        self.__stipendio = stipendio

    # Getter e setter per NOME
    def get_nome(self):
        return self.nome

    def set_nome(self, nuovo_nome):
        if isinstance(nuovo_nome, str) and nuovo_nome.strip():
            self.nome = nuovo_nome
        else:
            raise ValueError("Il nome deve essere una stringa non vuota.")

    # Getter e setter per ETÀ
    def get_eta(self):
        return self.eta

    def set_eta(self, nuova_eta):
        if isinstance(nuova_eta, int) and nuova_eta > 0:
            self.eta = nuova_eta
        else:
            raise ValueError("L'età deve essere un intero positivo.")

    # Getter e setter per STIPENDIO (privato)
    def get_stipendio(self):
        return self.__stipendio

    def set_stipendio(self, nuovo_stipendio):
        if isinstance(nuovo_stipendio, (int, float)) and nuovo_stipendio >= 0:
            self.__stipendio = nuovo_stipendio
        else:
            raise ValueError("Lo stipendio deve essere un numero non negativo.")

    # Override di __str__: mostra solo nome ed età
    def __str__(self):
        return f"Insegnante: {self.nome}, età: {self.eta} anni"

# Test con due oggetti
if __name__ == "__main__":
    # Creazione dei due oggetti
    ins1 = Insegnante("Maria Rossi", 42, 2800.0)
    ins2 = Insegnante("Luca Bianchi", 35, 2500.0)

    # print("=== Stampa con __str__ ===")
    print(f"\n{ins1}\n{ins2}")

    print("\n=== Getter ins1===")
    print(f"Nome ins1:       {ins1.get_nome()} \nEtà ins1:        {ins1.get_eta()} \nStipendio ins1:  {ins1.get_stipendio()} €")
    
    print("\n=== Getter ins2===")
    print(f"Nome ins2:       {ins2.get_nome()} \nEtà ins2:        {ins2.get_eta()} \nStipendio ins2:  {ins2.get_stipendio()} €")

    print("\n=== Setter ===")
    ins1.set_nome("Maria Verdi")
    ins1.set_eta(43)
    # ins1.set_stipendio(3000.0)
    print(f"Modifica insegnante ins1 → {ins1}")
    print(f"Nuovo stipendio ins1: {ins1.get_stipendio()} €")
    
    print("\n=== Verifica attributo privato ===")
    # piccolo controllo per vedere se si riesce a accedere a __stipendio senza dover usare get
    if hasattr(ins2, "__stipendio"):
        print(f"Stipendio (diretto): {ins2.__stipendio}")
    else:
        print("Accesso diretto negato: '__stipendio' non è visibile dall'esterno.")
    # Accesso corretto solo tramite getter:
    print(f"Accesso tramite getter ins2: {ins2.get_stipendio()} €")

    print("\n=== Controllo del setter (cambio una età con un valore errato =-5) ===")
    nuova_eta = -5
    if isinstance(nuova_eta, int) and nuova_eta > 0:
        ins2.set_eta(nuova_eta)
        print(ins2)
    else:
        print(f"Valore non valido ({nuova_eta}): l'età deve essere un intero positivo.")
        print(ins2)
 