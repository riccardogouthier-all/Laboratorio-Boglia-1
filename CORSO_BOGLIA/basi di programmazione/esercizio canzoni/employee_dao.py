import database
from dataclasses import dataclass

@dataclass
class Impiegato:
    nome : str
    cognome : str
    ruolo : str


DB_impiegati = database.connetti()

impiegati = database.interroga(DB_impiegati, "select FirstName, LastName, Title from employee")

scatola = [Impiegato(n, c, r) for n, c, r in impiegati]

print(scatola)