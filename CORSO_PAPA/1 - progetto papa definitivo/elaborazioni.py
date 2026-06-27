"""
elaborazioni.py — query statistiche per reportistica
"""

import sqlite3
from database import get_conn


def media_materia_studente(materia: str, id_studente: int) -> float | None:
    """6.1 media voti di una materia per uno studente specifico"""
    with get_conn() as conn:
        row = conn.execute(
            """SELECT AVG(voto) as media
               FROM voti
               WHERE LOWER(materia)=LOWER(?) AND id_studente=?""",
            (materia, id_studente)
        ).fetchone()
        return row["media"] if row and row["media"] is not None else None


def media_materia(materia: str) -> float | None:
    """6.2 media voti di una materia su tutti gli studenti"""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT AVG(voto) as media FROM voti WHERE LOWER(materia)=LOWER(?)",
            (materia,)
        ).fetchone()
        return row["media"] if row and row["media"] is not None else None


def voti_materia_per_studente(materia: str) -> list[dict]:
    """Dettaglio: tutti i voti di una materia con nome studente"""
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT s.id, s.cognome||' '||s.nome AS studente,
                      AVG(v.voto) AS media, COUNT(v.id) AS num_voti
               FROM voti v
               JOIN studenti s ON v.id_studente = s.id
               WHERE LOWER(v.materia)=LOWER(?)
               GROUP BY s.id
               ORDER BY s.cognome""",
            (materia,)
        ).fetchall()
        return [dict(r) for r in rows]


def num_assenze_studente(id_studente: int) -> int:
    """6.3 numero assenze di uno studente"""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) as n FROM assenze WHERE id_studente=?",
            (id_studente,)
        ).fetchone()
        return row["n"] if row else 0


def studenti_assenti_giorno(data: str) -> list[dict]:
    """6.4 studenti assenti in una data specifica"""
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT s.id, s.cognome||' '||s.nome AS studente, s.email
               FROM assenze a
               JOIN studenti s ON a.id_studente = s.id
               WHERE a.data=?
               ORDER BY s.cognome""",
            (data,)
        ).fetchall()
        return [dict(r) for r in rows]


def num_studenti_per_materia(materia: str) -> int:
    """6.5 numero studenti distinti con voti in una materia"""
    with get_conn() as conn:
        row = conn.execute(
            """SELECT COUNT(DISTINCT id_studente) as n
               FROM voti WHERE LOWER(materia)=LOWER(?)""",
            (materia,)
        ).fetchone()
        return row["n"] if row else 0


def studenti_sufficienti_insufficienti(soglia: float = 6.0) -> dict:
    """6.7 studenti con media generale >= soglia (sufficienti) vs < soglia"""
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT id_studente, AVG(voto) as media_gen
               FROM voti
               GROUP BY id_studente"""
        ).fetchall()

        sufficienti = [r for r in rows if r["media_gen"] >= soglia]
        insufficienti = [r for r in rows if r["media_gen"] < soglia]

        # Arricchisci con nome
        def _enrich(lst):
            out = []
            for r in lst:
                s = conn.execute(
                    "SELECT cognome||' '||nome AS studente FROM studenti WHERE id=?",
                    (r["id_studente"],)
                ).fetchone()
                out.append({
                    "id": r["id_studente"],
                    "studente": s["studente"] if s else "—",
                    "media": round(r["media_gen"], 2)
                })
            return out

        return {
            "sufficienti": _enrich(sufficienti),
            "insufficienti": _enrich(insufficienti),
            "soglia": soglia,
        }


def assenze_per_studente_tutti() -> list[dict]:
    """Assenze aggregate per tutti gli studenti (per grafici)"""
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT s.id, s.cognome||' '||s.nome AS studente,
                      COUNT(a.id) AS num_assenze
               FROM studenti s
               LEFT JOIN assenze a ON s.id = a.id_studente
               GROUP BY s.id
               ORDER BY num_assenze DESC""",
        ).fetchall()
        return [dict(r) for r in rows]


def medie_per_materia_tutti() -> list[dict]:
    """Media per ogni materia (per grafici)"""
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT materia, AVG(voto) AS media, COUNT(DISTINCT id_studente) AS n_studenti
               FROM voti
               GROUP BY materia
               ORDER BY materia"""
        ).fetchall()
        return [dict(r) for r in rows]


def distribuzione_voti_materia(materia: str) -> list[float]:
    """Tutti i voti di una materia (per istogramma)"""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT voto FROM voti WHERE LOWER(materia)=LOWER(?)",
            (materia,)
        ).fetchall()
        return [r["voto"] for r in rows]
