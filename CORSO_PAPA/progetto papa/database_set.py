"""
Legge un elenco di studenti da un file di testo (campi separati da virgola)
e popola un database MySQL "scuola_db", nello stile:

{'id': 27, 'nome': 'Aurora', 'cognome': 'Pellegrini', 'data_nascita': '2008-11-29',
 'email': 'aurora.pellegrini@scuola.it',
 'voti': {'Matematica': 8, 'Informatica': 7, 'Italiano': 6, 'Storia': 9,
          'Inglese': 7, 'Educazione Fisica': 8},
 'assenze': 5}

FORMATO DEL FILE TXT (una riga per studente, valori separati da virgola):

    id,nome,cognome,data_nascita,email,voto_matematica,voto_informatica,
    voto_italiano,voto_storia,voto_inglese,voto_edfisica,assenze

Esempio di riga:
    27,Aurora,Pellegrini,2008-11-29,aurora.pellegrini@scuola.it,8,7,6,9,7,8,5

Note sul file:
    - data_nascita deve essere nel formato AAAA-MM-GG
    - i 6 voti vanno indicati nell'ordine: Matematica, Informatica, Italiano,
      Storia, Inglese, Educazione Fisica
    - le righe vuote o che iniziano con "#" vengono ignorate (utile per commenti)

Requisiti:
    pip install mysql-connector-python

Prima di eseguire, modifica i parametri di connessione in CONFIG_DB e,
se necessario, il percorso del file in PERCORSO_FILE.
"""

import datetime
import re
import mysql.connector

# ---------------------------------------------------------------------
# CONFIGURAZIONE (modifica con i tuoi dati)
# ---------------------------------------------------------------------
CONFIG_DB = {
    "host": "localhost",
    "user": "root",
    "password": "password",
}

NOME_DATABASE = "scuola_db"
PERCORSO_FILE = "studenti.txt"

MATERIE = [
    "Matematica",
    "Informatica",
    "Italiano",
    "Storia",
    "Inglese",
    "Educazione Fisica",
]

# Numero di campi attesi per riga: id, nome, cognome, data_nascita, email,
# 6 voti, assenze
NUMERO_CAMPI_ATTESI = 5 + len(MATERIE) + 1

REGEX_DATA = re.compile(r"^\d{4}-\d{2}-\d{2}$")
REGEX_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def valida_studente(studente: dict, numero_riga: int):
    """Controlla che i dati di uno studente siano coerenti, altrimenti
    solleva un errore chiaro che indica la riga problematica."""

    if not REGEX_DATA.match(studente["data_nascita"]):
        raise ValueError(
            f"Riga {numero_riga}: data di nascita non valida "
            f"'{studente['data_nascita']}' (formato richiesto AAAA-MM-GG)"
        )

    try:
        datetime.date.fromisoformat(studente["data_nascita"])
    except ValueError:
        raise ValueError(
            f"Riga {numero_riga}: data di nascita inesistente "
            f"'{studente['data_nascita']}'"
        )

    if not REGEX_EMAIL.match(studente["email"]):
        raise ValueError(
            f"Riga {numero_riga}: email non valida '{studente['email']}'"
        )

    for materia, voto in studente["voti"].items():
        if not (0 <= voto <= 10):
            raise ValueError(
                f"Riga {numero_riga}: voto di {materia} fuori range (0-10): {voto}"
            )

    if studente["assenze"] < 0:
        raise ValueError(
            f"Riga {numero_riga}: numero di assenze negativo: {studente['assenze']}"
        )


def leggi_studenti_da_file(percorso: str) -> list[dict]:
    """Legge il file txt e restituisce una lista di dizionari studente."""
    studenti = []

    with open(percorso, "r", encoding="utf-8") as file:
        for numero_riga, riga in enumerate(file, start=1):
            riga = riga.strip()

            if not riga or riga.startswith("#"):
                continue

            campi = [c.strip() for c in riga.split(",")]

            if len(campi) != NUMERO_CAMPI_ATTESI:
                raise ValueError(
                    f"Riga {numero_riga}: trovati {len(campi)} campi invece di "
                    f"{NUMERO_CAMPI_ATTESI} attesi -> '{riga}'"
                )

            id_studente, nome, cognome, data_nascita, email, *resto = campi
            voti_grezzi, assenze_grezza = resto[:len(MATERIE)], resto[len(MATERIE)]

            try:
                voti = {
                    materia: int(voto)
                    for materia, voto in zip(MATERIE, voti_grezzi)
                }
            except ValueError:
                raise ValueError(
                    f"Riga {numero_riga}: uno dei voti non e' un numero intero -> '{riga}'"
                )

            try:
                id_studente = int(id_studente)
                assenze = int(assenze_grezza)
            except ValueError:
                raise ValueError(
                    f"Riga {numero_riga}: id o assenze non sono numeri interi -> '{riga}'"
                )

            studente = {
                "id": id_studente,
                "nome": nome,
                "cognome": cognome,
                "data_nascita": data_nascita,
                "email": email,
                "voti": voti,
                "assenze": assenze,
            }

            valida_studente(studente, numero_riga)
            studenti.append(studente)

    return studenti


def crea_database_e_tabelle(cursor):
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {NOME_DATABASE}")
    cursor.execute(f"USE {NOME_DATABASE}")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS studenti (
            id INT PRIMARY KEY,
            nome VARCHAR(50) NOT NULL,
            cognome VARCHAR(50) NOT NULL,
            data_nascita DATE NOT NULL,
            email VARCHAR(100) NOT NULL UNIQUE,
            assenze INT NOT NULL DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS voti (
            id INT AUTO_INCREMENT PRIMARY KEY,
            studente_id INT NOT NULL,
            materia VARCHAR(50) NOT NULL,
            voto INT NOT NULL,
            FOREIGN KEY (studente_id) REFERENCES studenti(id)
                ON DELETE CASCADE,
            UNIQUE KEY uniq_studente_materia (studente_id, materia)
        )
    """)


def inserisci_studenti(cursor, studenti: list[dict]):
    sql_studente = """
        INSERT INTO studenti (id, nome, cognome, data_nascita, email, assenze)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            nome = VALUES(nome),
            cognome = VALUES(cognome),
            data_nascita = VALUES(data_nascita),
            email = VALUES(email),
            assenze = VALUES(assenze)
    """
    sql_voto = """
        INSERT INTO voti (studente_id, materia, voto)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE voto = VALUES(voto)
    """

    for studente in studenti:
        cursor.execute(sql_studente, (
            studente["id"],
            studente["nome"],
            studente["cognome"],
            studente["data_nascita"],
            studente["email"],
            studente["assenze"],
        ))
        for materia, voto in studente["voti"].items():
            cursor.execute(sql_voto, (studente["id"], materia, voto))


def main():
    studenti = leggi_studenti_da_file(PERCORSO_FILE)

    if not studenti:
        print(f"Nessuno studente trovato in '{PERCORSO_FILE}'.")
        return

    print(f"Letti {len(studenti)} studenti da '{PERCORSO_FILE}'.")
    print("Esempio:")
    print(studenti[0])

    connessione = mysql.connector.connect(**CONFIG_DB)
    cursor = connessione.cursor()

    crea_database_e_tabelle(cursor)
    inserisci_studenti(cursor, studenti)

    connessione.commit()
    cursor.close()
    connessione.close()

    print(f"Database '{NOME_DATABASE}' popolato con {len(studenti)} studenti.")


if __name__ == "__main__":
    main()