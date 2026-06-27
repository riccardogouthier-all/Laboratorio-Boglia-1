"""
database.py — SQLite layer: schema, CRUD studenti/voti/assenze/materie
"""

import sqlite3
import os
from pathlib import Path

DB_PATH = Path(__file__).parent / "studenti.db"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS materie (
                id   INTEGER PRIMARY KEY AUTOINCREMENT,
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
        """)


# ─── STUDENTI ────────────────────────────────────────────────────────────────

def inserisci_studente(nome, cognome, data_nascita, email) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO studenti (nome, cognome, data_nascita, email) VALUES (?,?,?,?)",
            (nome, cognome, data_nascita, email)
        )
        return cur.lastrowid


def modifica_studente(id_studente, nome, cognome, data_nascita, email):
    with get_conn() as conn:
        conn.execute(
            "UPDATE studenti SET nome=?, cognome=?, data_nascita=?, email=? WHERE id=?",
            (nome, cognome, data_nascita, email, id_studente)
        )


def cancella_studente(id_studente):
    with get_conn() as conn:
        conn.execute("DELETE FROM studenti WHERE id=?", (id_studente,))


def get_studente(id_studente):
    with get_conn() as conn:
        return conn.execute("SELECT * FROM studenti WHERE id=?", (id_studente,)).fetchone()


def get_tutti_studenti():
    with get_conn() as conn:
        return conn.execute("SELECT * FROM studenti ORDER BY cognome, nome").fetchall()


def cerca_studente(query: str):
    like = f"%{query}%"
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM studenti WHERE nome LIKE ? OR cognome LIKE ? OR email LIKE ?",
            (like, like, like)
        ).fetchall()


# ─── VOTI ────────────────────────────────────────────────────────────────────

def inserisci_voto(id_studente, materia, voto) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO voti (id_studente, materia, voto) VALUES (?,?,?)",
            (id_studente, materia, float(voto))
        )
        return cur.lastrowid


def modifica_voto(id_voto, id_studente, materia, voto):
    with get_conn() as conn:
        conn.execute(
            "UPDATE voti SET id_studente=?, materia=?, voto=? WHERE id=?",
            (id_studente, materia, float(voto), id_voto)
        )


def cancella_voto(id_voto):
    with get_conn() as conn:
        conn.execute("DELETE FROM voti WHERE id=?", (id_voto,))


def get_voti_studente(id_studente):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM voti WHERE id_studente=? ORDER BY materia",
            (id_studente,)
        ).fetchall()


def get_tutti_voti():
    with get_conn() as conn:
        return conn.execute(
            """SELECT v.id, s.cognome||' '||s.nome AS studente,
                      v.materia, v.voto, v.id_studente
               FROM voti v JOIN studenti s ON v.id_studente = s.id
               ORDER BY s.cognome, v.materia"""
        ).fetchall()


# ─── ASSENZE ─────────────────────────────────────────────────────────────────

def inserisci_assenza(id_studente, data) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO assenze (id_studente, data) VALUES (?,?)",
            (id_studente, data)
        )
        return cur.lastrowid


def modifica_assenza(id_assenza, id_studente, data):
    with get_conn() as conn:
        conn.execute(
            "UPDATE assenze SET id_studente=?, data=? WHERE id=?",
            (id_studente, data, id_assenza)
        )


def cancella_assenza(id_assenza):
    with get_conn() as conn:
        conn.execute("DELETE FROM assenze WHERE id=?", (id_assenza,))


def get_assenze_studente(id_studente):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM assenze WHERE id_studente=? ORDER BY data",
            (id_studente,)
        ).fetchall()


def get_tutte_assenze():
    with get_conn() as conn:
        return conn.execute(
            """SELECT a.id, s.cognome||' '||s.nome AS studente,
                      a.data, a.id_studente
               FROM assenze a JOIN studenti s ON a.id_studente = s.id
               ORDER BY a.data DESC"""
        ).fetchall()


# ─── MATERIE ─────────────────────────────────────────────────────────────────

def inserisci_materia(nome) -> int:
    with get_conn() as conn:
        cur = conn.execute("INSERT INTO materie (nome) VALUES (?)", (nome,))
        return cur.lastrowid


def modifica_materia(id_materia, nome):
    with get_conn() as conn:
        conn.execute("UPDATE materie SET nome=? WHERE id=?", (nome, id_materia))


def cancella_materia(id_materia):
    with get_conn() as conn:
        conn.execute("DELETE FROM materie WHERE id=?", (id_materia,))


def get_tutte_materie():
    with get_conn() as conn:
        return conn.execute("SELECT * FROM materie ORDER BY nome").fetchall()


def get_nomi_materie() -> list[str]:
    with get_conn() as conn:
        rows = conn.execute("SELECT nome FROM materie ORDER BY nome").fetchall()
        return [r["nome"] for r in rows]
