import mysql.connector

class Connessione:


    def connetti(self):

        def __init__(self):
            pass

        self.db = mysql.connector.connect(
            host='localhost',
            user='root',
            password='root',
            database='magazzino'
        )

        if self.db:
            print('sei connesso al db')
            return self.db
        else:
            print('non connesso al db')

    def chiudi(self):
        if self.db.is_connected():
            self.db.close()

if __name__=='__main__':
    con = Connessione()
    con.connetti()
    con.chiudi()