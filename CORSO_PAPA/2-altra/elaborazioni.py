"""
elaborazioni.py — query statistiche per reportistica
"""

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