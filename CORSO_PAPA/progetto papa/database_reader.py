import sqlite3

def leggi_studenti_da_db(percorso_db: str) -> list[dict]:
    """Legge il database SQLite e restituisce una lista di dizionari studente,
    con i voti raggruppati per materia in un sotto-dizionario."""
    connessione = sqlite3.connect(percorso_db)
    cursor = connessione.cursor()

    cursor.execute("""
        SELECT  s.id, s.nome, s.cognome, s.data_nascita, s.email, s.assenze,
                v.materia, v.voto
        FROM studenti s
        LEFT JOIN voti v ON v.studente_id = s.id
        ORDER BY s.id
    """)

    righe = cursor.fetchall()
    cursor.close()
    connessione.close()

    studenti = {}
    for id_, nome, cognome, data_nascita, email, assenze, materia, voto in righe:
        if id_ not in studenti:
            studenti[id_] = {
                "id": id_,
                "nome": nome,
                "cognome": cognome,
                "data_nascita": data_nascita,
                "email": email,
                "voti": {},
                "assenze": assenze,
            }
        if materia is not None:           # gestisce eventuali studenti senza voti registrati
            studenti[id_]["voti"][materia] = voto

    return list(studenti.values())

if __name__ == "__main__":
    lista_studenti = leggi_studenti_da_db("scuola_db.db")
    for studente in lista_studenti:
        print(studente)