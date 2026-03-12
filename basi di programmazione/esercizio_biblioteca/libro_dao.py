import mysql.connector
from libro import Libro

db = mysql.connector.connect(
    host = 'localhost',
    user = 'root',
    password = 'root',
    database = 'biblioteca'
)

cursor = db.cursor()

cursor.execute("SELECT * FROM Libri")

libri = cursor.fetchall()

tabella_libri = []

# print(libri)

for libro in libri:

    libroID = libro[0]
    titolo = libro[3]  
    editore = libro[4]
    autore = libro[2]

    classificazione = libro[8]
    collocazione = libro[1]


    libro = Libro(libroID, collocazione, titolo, autore, editore, classificazione)
    tabella_libri.append(libro)

    print(libro)