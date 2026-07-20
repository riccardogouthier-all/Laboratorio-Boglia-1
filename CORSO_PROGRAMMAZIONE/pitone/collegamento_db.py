import mysql.connector
from dataclasses import dataclass

@dataclass
class Prodotto:
    nome : str
    prezzo : float
    giacenza : int

magazzino = mysql.connector.connect(
    host = 'localhost',
    user = 'root',
    password = 'root',
    database = 'magazzino'
)

cursore = magazzino.cursor()

query = "select nome, prezzo_unitario, quantita_stock from prodotti"

cursore.execute(query)

prodotti = cursore.fetchall()           #preleva gli elementi letti

# tendina = []

tendina = [Prodotto(n,p,q) for n, p, q in prodotti]

# for p in prodotti:
#     tendina.append(p[0])

with open("Esercitazione_magazzino.txt", "w") as f:
    f.write(query)
    
    print(query)
    for p in tendina:
        # f.write(f"{row.nome:30}{row.prezzo:10}{row.giacenza:10} '\n'") # per elementi in una lista
        f.write(f"{p.nome:30} {p.prezzo:10} {p.giacenza:10} '\n'") # per elementi in una lista


 