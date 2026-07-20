"""
database.py — gestisce il database SQLite: crea le tabelle e contiene
le funzioni per aggiungere, leggere, modificare e cancellare
studenti, voti, assenze e materie.
"""

import sqlite3
import os
from pathlib import Path

DB_PATH = Path(__file__).parent / "studenti.db"


def get_conn() -> sqlite3.Connection:
    """
    Apre una connessione al database.
    Usiamo questa funzione ovunque invece di scrivere il codice di
    connessione ogni volta, così tutte le connessioni sono uguali:
    possiamo leggere le colonne per nome (row_factory) e i vincoli
    di chiave esterna sono sempre attivi (servono per cancellare
    automaticamente voti e assenze quando si cancella uno studente).
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """
    Crea le tabelle del database, solo se non esistono già.
    Questa funzione viene chiamata una volta all'avvio del programma
    (vedi App.__init__ in main.py), così il database è sempre pronto
    all'uso anche la prima volta che si avvia l'app. Gli indici creati
    alla fine servono a rendere più veloci le ricerche più comuni
    (per studente, per materia, per data, in ordine di cognome).
    """
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS materie (
                id   INTEGER PRIMARY KEY,
                nome TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS studenti (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                nome          TEXT NOT NULL,
                cognome       TEXT NOT NULL,
                data_nascita  TEXT NOT NULL,
                email         TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS voti (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                id_studente INTEGER NOT NULL REFERENCES studenti(id) ON DELETE CASCADE,
                materia     TEXT NOT NULL,
                voto        REAL NOT NULL CHECK(voto >= 0 AND voto <= 10)
            );

            CREATE TABLE IF NOT EXISTS assenze (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                id_studente INTEGER NOT NULL REFERENCES studenti(id) ON DELETE CASCADE,
                data        TEXT NOT NULL,
                UNIQUE(id_studente, data)
            );

            CREATE INDEX IF NOT EXISTS idx_voti_studente    ON voti(id_studente);
            CREATE INDEX IF NOT EXISTS idx_voti_materia     ON voti(materia);
            CREATE INDEX IF NOT EXISTS idx_assenze_studente ON assenze(id_studente);
            CREATE INDEX IF NOT EXISTS idx_assenze_data     ON assenze(data);
            CREATE INDEX IF NOT EXISTS idx_studenti_cognome ON studenti(cognome, nome);
        """)


# ─── STUDENTI ────────────────────────────────────────────────────────────────

def inserisci_studente(nome, cognome, data_nascita, email) -> int:
    """
    Aggiunge un nuovo studente al database e restituisce il suo id.
    Serve al form "Nuovo studente" nella scheda Studenti della GUI.
    """
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO studenti (nome, cognome, data_nascita, email) VALUES (?,?,?,?)",
            (nome, cognome, data_nascita, email)
        )
        return cur.lastrowid


def modifica_studente(id_studente, nome, cognome, data_nascita, email):
    """
    Aggiorna i dati di uno studente già esistente.
    Permette di correggere un errore (es. email sbagliata) senza
    dover cancellare e ricreare lo studente.
    """
    with get_conn() as conn:
        conn.execute(
            "UPDATE studenti SET nome=?, cognome=?, data_nascita=?, email=? WHERE id=?",
            (nome, cognome, data_nascita, email, id_studente)
        )


def cancella_studente(id_studente):
    """
    Cancella uno studente dal database.
    Grazie a ON DELETE CASCADE (impostato nelle tabelle), vengono
    cancellati automaticamente anche i suoi voti e le sue assenze,
    senza doverlo fare a mano riga per riga in Python.
    """
    with get_conn() as conn:
        conn.execute("DELETE FROM studenti WHERE id=?", (id_studente,))


def inserisci_studenti_batch(righe: list[tuple]) -> int:
    """Inserisce tanti studenti insieme, in un'unica operazione.
    righe: lista di (nome, cognome, data_nascita, email)
    Viene usata quando importiamo un file CSV (importa_file.py):
    invece di fare una query per ogni riga, le inseriamo tutte
    insieme, così l'importazione è molto più veloce."""
    with get_conn() as conn:
        cur = conn.executemany(
            "INSERT INTO studenti (nome, cognome, data_nascita, email) VALUES (?,?,?,?)",
            righe
        )
        return cur.rowcount


def get_studente(id_studente):
    """
    Recupera un singolo studente dato il suo id.
    Serve alla GUI per riempire il form di modifica con i dati
    già presenti dello studente selezionato.
    """
    with get_conn() as conn:
        return conn.execute("SELECT * FROM studenti WHERE id=?", (id_studente,)).fetchone()


def get_tutti_studenti():
    """
    Restituisce tutti gli studenti, ordinati per cognome e nome.
    Serve a riempire la tabella della scheda Studenti e i menu a
    tendina usati nei form di Voti/Assenze/Report.
    """
    with get_conn() as conn:
        return conn.execute("SELECT * FROM studenti ORDER BY cognome, nome").fetchall()


def cerca_studente(query: str):
    """
    Cerca gli studenti il cui nome, cognome o email contiene il testo
    cercato (senza distinguere maiuscole/minuscole).
    Serve per la barra di ricerca nella scheda Studenti, per trovare
    velocemente uno studente anche con tanti dati inseriti.
    """
    like = f"%{query}%"
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM studenti WHERE nome LIKE ? OR cognome LIKE ? OR email LIKE ?",
            (like, like, like)
        ).fetchall()


# ─── VOTI ────────────────────────────────────────────────────────────────────

def inserisci_voto(id_studente, materia, voto) -> int:
    """
    Aggiunge un nuovo voto per uno studente in una materia.
    Il vincolo scritto nella tabella (CHECK) garantisce che il voto
    sia sempre tra 0 e 10.
    """
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO voti (id_studente, materia, voto) VALUES (?,?,?)",
            (id_studente, materia, float(voto))
        )
        return cur.lastrowid


def inserisci_voti_batch(righe: list[tuple]) -> int:
    """Inserisce tanti voti insieme, in un'unica operazione.
    righe: lista di (id_studente, materia, voto)
    Come per gli studenti, viene usata durante l'importazione da CSV
    per essere veloce anche con tanti dati."""
    with get_conn() as conn:
        cur = conn.executemany(
            "INSERT INTO voti (id_studente, materia, voto) VALUES (?,?,?)",
            righe
        )
        return cur.rowcount


def modifica_voto(id_voto, id_studente, materia, voto):
    """
    Aggiorna un voto già esistente (studente, materia e/o valore).
    Serve per correggere un voto inserito per sbaglio, senza doverlo
    cancellare e reinserire.
    """
    with get_conn() as conn:
        conn.execute(
            "UPDATE voti SET id_studente=?, materia=?, voto=? WHERE id=?",
            (id_studente, materia, float(voto), id_voto)
        )


def cancella_voto(id_voto):
    """
    Cancella un singolo voto.
    Usata dal pulsante "Elimina" nella scheda Voti.
    """
    with get_conn() as conn:
        conn.execute("DELETE FROM voti WHERE id=?", (id_voto,))


def get_tutti_voti():
    """
    Restituisce tutti i voti, già uniti (JOIN) al nome e cognome dello
    studente, pronti per essere mostrati in tabella.
    Fare un'unica query con JOIN è più veloce che cercare il nome
    dello studente separatamente per ogni voto.
    """
    with get_conn() as conn:
        return conn.execute(
            """SELECT v.id, s.cognome||' '||s.nome AS studente,
                      v.materia, v.voto, v.id_studente
               FROM voti v JOIN studenti s ON v.id_studente = s.id
               ORDER BY s.cognome, v.materia"""
        ).fetchall()


# ─── ASSENZE ─────────────────────────────────────────────────────────────────

def inserisci_assenza(id_studente, data) -> int:
    """
    Registra un'assenza per uno studente in una certa data.
    Il vincolo UNIQUE sulla tabella (stesso studente + stessa data)
    impedisce di registrare due volte la stessa assenza.
    """
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO assenze (id_studente, data) VALUES (?,?)",
            (id_studente, data)
        )
        return cur.lastrowid


def inserisci_assenze_batch(righe: list[tuple]) -> int:
    """Inserisce tante assenze insieme (i doppioni vengono scartati
    automaticamente con INSERT OR IGNORE).
    righe: lista di (id_studente, data)
    Usata durante l'importazione da CSV: se un'assenza è già presente
    nel database, viene semplicemente ignorata invece di dare errore."""
    with get_conn() as conn:
        cur = conn.executemany(
            "INSERT OR IGNORE INTO assenze (id_studente, data) VALUES (?,?)",
            righe
        )
        return cur.rowcount


def modifica_assenza(id_assenza, id_studente, data):
    """
    Aggiorna lo studente e/o la data di un'assenza già esistente.
    Serve per correggere un'assenza inserita per errore.
    """
    with get_conn() as conn:
        conn.execute(
            "UPDATE assenze SET id_studente=?, data=? WHERE id=?",
            (id_studente, data, id_assenza)
        )


def cancella_assenza(id_assenza):
    """
    Cancella una singola assenza.
    Usata dal pulsante "Elimina" nella scheda Assenze.
    """
    with get_conn() as conn:
        conn.execute("DELETE FROM assenze WHERE id=?", (id_assenza,))


def get_tutte_assenze():
    """
    Restituisce tutte le assenze, con nome e cognome dello studente
    già uniti (JOIN), a partire dalla più recente.
    Serve a riempire la tabella della scheda Assenze: le assenze più
    recenti sono quelle più utili da vedere subito.
    """
    with get_conn() as conn:
        return conn.execute(
            """SELECT a.id, s.cognome||' '||s.nome AS studente,
                      a.data, a.id_studente
               FROM assenze a JOIN studenti s ON a.id_studente = s.id
               ORDER BY a.data DESC"""
        ).fetchall()


# ─── MATERIE ─────────────────────────────────────────────────────────────────

def inserisci_materia(nome) -> int:
    """
    Crea una nuova materia.
    Le materie sono salvate in una tabella a parte (non solo come
    testo dentro i voti) così i menu a tendina mostrano sempre un
    elenco coerente, e i voti possono riferirsi solo a materie che
    esistono davvero.
    """
    with get_conn() as conn:
        cur = conn.execute("INSERT INTO materie (nome) VALUES (?)", (nome,))
        return cur.lastrowid


def upsert_materia(nome: str):
    """Inserisce la materia solo se non esiste già.
    Usata quando importiamo i voti da un file CSV: se il file cita
    una materia nuova, viene creata al volo senza dare errore se
    esiste già (INSERT OR IGNORE)."""
    with get_conn() as conn:
        conn.execute("INSERT OR IGNORE INTO materie (nome) VALUES (?)", (nome,))


def modifica_materia(id_materia, nome):
    """
    Cambia il nome di una materia già esistente.
    Attenzione: non aggiorna il nome già scritto nei voti collegati,
    perché i voti salvano il nome della materia come testo, non un
    riferimento (id) alla tabella materie.
    """
    with get_conn() as conn:
        conn.execute("UPDATE materie SET nome=? WHERE id=?", (nome, id_materia))


def cancella_materia(id_materia):
    """
    Cancella una materia e, insieme, tutti i voti che le appartengono.
    Dato che i voti salvano il nome della materia come testo (non un
    id collegato), il database da solo non può cancellare i voti in
    automatico: qui prima leggiamo il nome della materia, poi
    cancelliamo a mano i voti con quel nome (ignorando maiuscole e
    minuscole), e infine cancelliamo la materia stessa.
    """
    with get_conn() as conn:
        # Prendiamo il nome prima di cancellare, per poter cancellare anche i voti collegati
        row = conn.execute("SELECT nome FROM materie WHERE id=?", (id_materia,)).fetchone()
        if row:
            conn.execute("DELETE FROM voti WHERE LOWER(materia)=LOWER(?)", (row["nome"],))
        conn.execute("DELETE FROM materie WHERE id=?", (id_materia,))


def get_tutte_materie():
    """
    Restituisce tutte le materie, ordinate per nome.
    Serve a riempire la tabella della scheda Materie.
    """
    with get_conn() as conn:
        return conn.execute("SELECT * FROM materie ORDER BY nome").fetchall()


def get_id_studenti_esistenti() -> set[int]:
    """Restituisce l'insieme di tutti gli id degli studenti esistenti.
    Serve durante l'importazione di voti/assenze da CSV, per
    controllare velocemente se un IDStudente scritto nel file esiste
    davvero, senza dover fare una query per ogni riga del file."""
    with get_conn() as conn:
        rows = conn.execute("SELECT id FROM studenti").fetchall()
        return {r["id"] for r in rows}


def get_email_esistenti() -> set[str]:
    """Restituisce l'insieme di tutte le email già salvate (in minuscolo).
    Stessa idea della funzione precedente, ma per controllare che le
    email nel file CSV non siano già usate, senza violare il vincolo
    UNIQUE della tabella con troppe query."""
    with get_conn() as conn:
        rows = conn.execute("SELECT LOWER(email) AS e FROM studenti").fetchall()
        return {r["e"] for r in rows}


def get_nomi_materie() -> list[str]:
    """
    Restituisce solo i nomi delle materie (una lista di testo), in ordine.
    Comodo per riempire subito i menu a tendina della GUI, che vogliono
    una lista di stringhe e non righe del database.
    """
    with get_conn() as conn:
        rows = conn.execute("SELECT nome FROM materie ORDER BY nome").fetchall()
        return [r["nome"] for r in rows]