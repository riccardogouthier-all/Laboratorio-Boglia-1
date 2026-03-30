import mysql.connector

magazzino = mysql.connector.connect(
    host = 'localhost',
    user = 'root',
    password = 'root',
    database = 'magazzino'
)

cursore = magazzino.cursor()

query = "select * from prodotti"

cursore.execute(query)

prodotti = cursore.fetchall()

print(prodotti)

