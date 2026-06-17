"""
Legge un elenco di studenti da un file di testo (campi separati da virgola)
e popola un database MySQL "scuola_db", nello stile:

{'id': 27, 'nome': 'Aurora', 'cognome': 'Pellegrini', 'data_nascita': '2008-11-29',
    'email': 'aurora.pellegrini@scuola.it',
    'voti': {'Matematica': 8, 'Informatica': 7, 'Italiano': 10, 'Storia': 9,
        'Inglese': 7, 'Educazione Fisica': 8},
    'assenze': 5}

FORMATO DEL FILE TXT (una riga per studente, valori separati da virgola):

    id,nome,cognome,data_nascita,email, voto_matematica,voto_informatica,voto_italiano,voto_storia,voto_inglese,voto_edfisica,assenze

Esempio di riga:
    27,Aurora,Pellegrini,2008-11-29,aurora.pellegrini@scuola.it,8,7,6,9,7,8,5

Note sul file:
    - data_nascita deve essere nel formato AAAA-MM-GG
    - i 6 voti vanno indicati nell'ordine: Matematica, Informatica, Italiano,
        Storia, Inglese, Educazione Fisica
    - le righe vuote o che iniziano con "#" vengono ignorate (utile per commenti)
"""

import datetime
import json
from pathlib import Path
import re
import sqlite3

def carica_configdb() -> dict:       # STEP 1 - dizionario impostazioni
    """Crea configdb.json con valori di nome database, percorso file, materie, campi attesi, data e email se non esiste, poi lo legge."""
    path = Path.cwd()                       #("PROGETTO-Student Analytics Pipeline")    #"CORSO_BOGLIA","basi di programmazione",
    CONFIG_PATH = path / "configdb.json"

    if not CONFIG_PATH.exists():
        NOME_DATABASE = "scuola_db"
        PERCORSO_FILE = input("Inserisci il percorso del file studenti.txt (default: studenti.txt): ") or "studenti.txt"
        # PERCORSO_FILE = "studenti.txt"
        
        MATERIE = [
            "Matematica",
            "Informatica",
            "Italiano",
            "Storia",
            "Inglese",
            "Educazione Fisica",
        ]

        REGEX_DATA = re.compile(r"^\d{4}-\d{2}-\d{2}$")
        REGEX_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump({
                "NOME_DATABASE": NOME_DATABASE,
                "PERCORSO_FILE": PERCORSO_FILE,
                "MATERIE": MATERIE,
                # "NUMERO_CAMPI_ATTESI": NUMERO_CAMPI_ATTESI,
                "REGEX_DATA": REGEX_DATA.pattern,
                "REGEX_EMAIL": REGEX_EMAIL.pattern
            }, f, indent=2, ensure_ascii=False)
        print("[Step 1] configdb.json creato con valori di default.")
    else:
        print("[Step 1] configdb.json trovato, caricamento in corso.")

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)
    config["NUMERO_CAMPI_ATTESI"] = 5 + len(config["MATERIE"]) + 1  # non serve salvarlo nel file come numero fisso perché dipende da quante materie ci sono, quindi lo calcoliamo

    return config       # dizionario impostazioni

def valida_studente(studente: dict, numero_riga: int, config: dict):
    """Controlla che i dati di uno studente siano coerenti, altrimenti
    solleva un errore chiaro che indica la riga problematica."""
    regex_data = re.compile(config["REGEX_DATA"])
    regex_email = re.compile(config["REGEX_EMAIL"])


    if not regex_data.match(studente["data_nascita"]):
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

    if not regex_email.match(studente["email"]):
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

def leggi_studenti_da_file(config: dict) -> list[dict]:
    """Legge il file txt e restituisce una lista di dizionari studente."""
    percorso = config["PERCORSO_FILE"]
    studenti = []

    with open(percorso, "r", encoding="utf-8") as file:
        for numero_riga, riga in enumerate(file, start=1):
            riga = riga.strip()

            if not riga or riga.startswith("#"):
                continue

            campi = [c.strip() for c in riga.split(",")]

            if len(campi) != config["NUMERO_CAMPI_ATTESI"]:
                raise ValueError(
                    f"Riga {numero_riga}: trovati {len(campi)} campi invece di "
                    f"{config['NUMERO_CAMPI_ATTESI']} attesi -> '{riga}'"
                )


            # Numero di campi attesi per riga: id, nome, cognome, data_nascita, email,
            id_studente, nome, cognome, data_nascita, email, *resto = campi
            # 6 voti, assenze
            voti_grezzi, assenze_grezza = resto[:len(config["MATERIE"])], resto[len(config["MATERIE"]):]

            try:
                voti = {
                    materia: int(voto)
                    for materia, voto in zip(config["MATERIE"], voti_grezzi)
                }
            except ValueError:
                raise ValueError(
                    f"Riga {numero_riga}: uno dei voti non e' un numero intero valido -> '{riga}'"
                )

            try:
                id_studente = int(id_studente)
                assenze = int(assenze_grezza[0])
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

            valida_studente(studente, numero_riga, config=config)
            studenti.append(studente)

    return studenti

def crea_database_e_tabelle(cursor):
    # studenti
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS studenti (
            id INTEGER PRIMARY KEY,
            nome TEXT NOT NULL,
            cognome TEXT NOT NULL,
            data_nascita TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            assenze INTEGER NOT NULL DEFAULT 0
        )
    """) # no formato DATE in sqlite, usiamo TEXT e validiamo il formato a livello codice Python
    # voti
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS voti (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            studente_id INTEGER NOT NULL,
            materia TEXT NOT NULL,
            voto INTEGER NOT NULL,
            FOREIGN KEY (studente_id) REFERENCES studenti(id)
                ON DELETE CASCADE,
            UNIQUE (studente_id, materia)
        )
    """)

def inserisci_studenti(cursor, studenti: list[dict]):
    sql_studente = """
        INSERT INTO studenti (id, nome, cognome, data_nascita, email, assenze)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            nome = excluded.nome,
            cognome = excluded.cognome,
            data_nascita = excluded.data_nascita,
            email = excluded.email,
            assenze = excluded.assenze
    """
    sql_voto = """
        INSERT INTO voti (studente_id, materia, voto)
        VALUES (?, ?, ?)
        ON CONFLICT(studente_id, materia) DO UPDATE SET voto = excluded.voto
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
    config = carica_configdb()
    studenti = leggi_studenti_da_file(config)

    if not studenti:
        print(f"Nessuno studente trovato in '{config['PERCORSO_FILE']}'.")
        return

    print(f"Letti {len(studenti)} studenti da '{config['PERCORSO_FILE']}'.")
    # print("Esempio:")
    # print(studenti[0])

    connessione = sqlite3.connect(f"{config['NOME_DATABASE']}.db")
    cursor = connessione.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")     # senza, SQLite ignora i vincoli FOREIGN KEY e l'ON DELETE CASCADE non funzionerebbe.

    crea_database_e_tabelle(cursor)
    inserisci_studenti(cursor, studenti)

    connessione.commit()
    cursor.close()
    connessione.close()

    print(f"Database '{config['NOME_DATABASE']}' popolato con {len(studenti)} studenti.")
    return config['NOME_DATABASE']

if __name__ == "__main__":
    main()