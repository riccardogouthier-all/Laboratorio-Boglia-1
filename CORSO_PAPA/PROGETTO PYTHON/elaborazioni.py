"""
elaborazioni.py — funzioni che fanno i calcoli statistici per i report
"""

from database import get_conn


def media_materia_studente(materia: str, id_studente: int) -> float | None:
    """6.1 media dei voti di uno studente in una materia
    Risponde alla richiesta 6.1: "media di una materia per uno
    studente". Usata sia nella GUI (TabReport._r61) sia nel PDF, per
    mostrare la media di un singolo studente in una materia scelta.
    Restituisce None se lo studente non ha voti in quella materia,
    così sappiamo distinguere "media zero" da "nessun voto"."""
    with get_conn() as conn:
        row = conn.execute(
            """SELECT AVG(voto) as media
               FROM voti
               WHERE LOWER(materia)=LOWER(?) AND id_studente=?""",
            (materia, id_studente)
        ).fetchone()
        return row["media"] if row and row["media"] is not None else None


def studenti_assenti_giorno(data: str) -> list[dict]:
    """6.4 studenti assenti in una data
    Risponde alla richiesta 6.4: "elenco assenti in un giorno".
    Restituisce dei dizionari (non righe del database) già pronti
    per essere usati direttamente nei grafici o nel PDF."""
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
    """6.5 numero di studenti diversi che hanno un voto in una materia
    Risponde alla richiesta 6.5: "numero di studenti in una materia".
    Usiamo COUNT(DISTINCT ...) per non contare due volte uno studente
    che ha più voti nella stessa materia."""
    with get_conn() as conn:
        row = conn.execute(
            """SELECT COUNT(DISTINCT id_studente) as n
               FROM voti WHERE LOWER(materia)=LOWER(?)""",
            (materia,)
        ).fetchone()
        return row["n"] if row else 0


def studenti_sufficienti_insufficienti(soglia: float = 6.0) -> dict:
    """6.7 studenti con media generale sopra o sotto la soglia
    Risponde alla richiesta 6.7: "dividere gli studenti tra
    sufficienti e insufficienti". Prima calcoliamo la media generale
    (su tutte le materie) di ogni studente con un'unica query, poi
    aggiungiamo il nome di ogni studente con la funzione interna
    _enrich, così non ripetiamo lo stesso codice due volte (una per
    i sufficienti e una per gli insufficienti)."""
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT id_studente, AVG(voto) as media_gen
               FROM voti
               GROUP BY id_studente"""
        ).fetchall()

        sufficienti = [r for r in rows if r["media_gen"] >= soglia]
        insufficienti = [r for r in rows if r["media_gen"] < soglia]

        # Aggiunge il nome dello studente
        def _enrich(lst):
            """
            Funzione interna: per ogni riga (id_studente, media_gen)
            cerca il nome completo dello studente e costruisce un
            dizionario pronto da usare in tabelle e grafici.
            Serve sia per la lista dei sufficienti sia per quella
            degli insufficienti, così scriviamo questo codice una
            volta sola invece di due.
            """
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
    """Media di ogni materia (per i grafici)
    Risponde alla richiesta 6.2: "media per materia". Con un'unica
    query calcoliamo sia la media sia quanti studenti diversi hanno
    un voto in quella materia. Il risultato viene usato sia nella
    tabella del PDF sia nel grafico a barre (grafici.grafico_media_per_materia)."""
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT materia, AVG(voto) AS media, COUNT(DISTINCT id_studente) AS n_studenti
               FROM voti
               GROUP BY materia
               ORDER BY materia"""
        ).fetchall()
        return [dict(r) for r in rows]


def distribuzione_voti_materia(materia: str) -> list[float]:
    """Tutti i voti di una materia (per l'istogramma)
    Restituisce la lista di ogni singolo voto (non una media), dato
    che serve così com'è per disegnare l'istogramma in grafici.py,
    sia per una singola materia sia per la griglia con tutte le materie."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT voto FROM voti WHERE LOWER(materia)=LOWER(?)",
            (materia,)
        ).fetchall()
        return [r["voto"] for r in rows]