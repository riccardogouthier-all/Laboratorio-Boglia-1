"""
analytics.py — Statistiche e analisi sul pool di studenti.

Funzioni disponibili:
    - media_per_studente        → media voti di ogni singolo studente
    - media_per_materia         → media della classe per ogni materia
    - classifica_studenti       → top N e peggiori N studenti per media
    - peggiori_per_materia      → studenti con il voto più basso per materia
    - distribuzione_voti        → conteggio quanti 6, 7, 8… per materia o globale
    - correlazione_materie      → coefficiente di correlazione tra due materie
    - studenti_a_rischio        → media < soglia_voto O assenze > soglia_assenze

Ogni funzione accetta:
    studenti : list[dict]   →  lista già in memoria  (da database_reader o da JSON)
    oppure
    percorso_db : str       →  percorso del file .db  (viene letto internamente)

Helper interno:
    _risolvi_studenti(studenti, percorso_db) → list[dict]
"""

import math
import statistics
from database_reader import leggi_studenti_da_db


# ─────────────────────────────────────────────
#  HELPER INTERNO
# ─────────────────────────────────────────────

def _risolvi_studenti(
    studenti: list[dict] | None,
    percorso_db: str | None
) -> list[dict]:
    """Restituisce la lista studenti dalla sorgente disponibile.

    Priorità: se studenti è fornita e non vuota la usa direttamente,
    altrimenti legge dal database indicato in percorso_db.

    Raises:
        ValueError  se né studenti né percorso_db sono forniti.
        FileNotFoundError  se percorso_db non esiste (gestita da sqlite3).
    """
    if studenti:
        return studenti
    if percorso_db:
        return leggi_studenti_da_db(percorso_db)
    raise ValueError(
        "Devi fornire 'studenti' (lista) oppure 'percorso_db' (percorso del .db)."
    )


def _media_voti(studente: dict) -> float:
    """Calcola e restituisce la media dei voti di uno studente (arrotondamento 2 dec)."""
    voti = list(studente["voti"].values())
    if not voti:
        return 0.0
    return round(statistics.mean(voti), 2)


# ─────────────────────────────────────────────
#  1. MEDIA PER STUDENTE
# ─────────────────────────────────────────────

def media_per_studente(
    studenti: list[dict] | None = None,
    percorso_db: str | None = None
) -> list[dict]:
    """Calcola la media voti di ogni studente.

    Returns:
        Lista di dizionari ordinata per media decrescente:
        [
            {
                "id": 3,
                "nome": "Aurora",
                "cognome": "Pellegrini",
                "media": 8.33,
                "assenze": 5
            },
            ...
        ]
    """
    studenti = _risolvi_studenti(studenti, percorso_db)

    risultati = [
        {
            "id":       s["id"],
            "nome":     s["nome"],
            "cognome":  s["cognome"],
            "media":    _media_voti(s),
            "assenze":  s["assenze"],
        }
        for s in studenti
    ]

    return sorted(risultati, key=lambda s: s["media"], reverse=True)


# ─────────────────────────────────────────────
#  2. MEDIA PER MATERIA
# ─────────────────────────────────────────────

def media_per_materia(
    studenti: list[dict] | None = None,
    percorso_db: str | None = None
) -> dict[str, float]:
    """Calcola la media della classe per ciascuna materia.

    Returns:
        Dizionario { materia: media_arrotondata } ordinato per media decrescente.
        Esempio:
        {
            "Educazione Fisica": 7.84,
            "Matematica":        6.92,
            ...
        }
    """
    studenti = _risolvi_studenti(studenti, percorso_db)

    voti_per_materia: dict[str, list[int]] = {}

    for s in studenti:
        for materia, voto in s["voti"].items():
            voti_per_materia.setdefault(materia, []).append(voto)

    medie = {
        materia: round(statistics.mean(voti), 2)
        for materia, voti in voti_per_materia.items()
    }

    return dict(sorted(medie.items(), key=lambda kv: kv[1], reverse=True))


# ─────────────────────────────────────────────
#  3. CLASSIFICA STUDENTI  (top N e ultimi N)
# ─────────────────────────────────────────────

def classifica_studenti(
    studenti: list[dict] | None = None,
    percorso_db: str | None = None,
    top_n: int = 10
) -> dict[str, list[dict]]:
    """Restituisce i migliori e i peggiori N studenti per media voti.

    Args:
        top_n:  quanti studenti includere in ciascuna lista (default 10).

    Returns:
        {
            "migliori": [ {id, nome, cognome, media, assenze}, ... ],   # i primi top_n
            "peggiori": [ {id, nome, cognome, media, assenze}, ... ],   # gli ultimi top_n
        }
    """
    studenti = _risolvi_studenti(studenti, percorso_db)
    classifica = media_per_studente(studenti=studenti)

    return {
        "migliori": classifica[:top_n],
        "peggiori": classifica[-top_n:][::-1],   # ultimi top_n dal peggiore al meno peggiore
    }


# ─────────────────────────────────────────────
#  4. PEGGIORI PER MATERIA
# ─────────────────────────────────────────────

def peggiori_per_materia(
    studenti: list[dict] | None = None,
    percorso_db: str | None = None,
    top_n: int = 3
) -> dict[str, list[dict]]:
    """Per ogni materia, restituisce i top_n studenti con il voto più basso.

    Returns:
        {
            "Matematica": [
                {"id": 12, "nome": "...", "cognome": "...", "voto": 3},
                ...
            ],
            "Informatica": [ ... ],
            ...
        }
    """
    studenti = _risolvi_studenti(studenti, percorso_db)

    # Raccoglie tutte le materie dal primo studente con voti
    materie = set()
    for s in studenti:
        materie.update(s["voti"].keys())

    risultato = {}
    for materia in sorted(materie):
        # studenti che hanno il voto per questa materia
        con_voto = [
            {
                "id":      s["id"],
                "nome":    s["nome"],
                "cognome": s["cognome"],
                "voto":    s["voti"][materia],
            }
            for s in studenti
            if materia in s["voti"]
        ]
        con_voto.sort(key=lambda x: x["voto"])
        risultato[materia] = con_voto[:top_n]

    return risultato


# ─────────────────────────────────────────────
#  5. DISTRIBUZIONE VOTI
# ─────────────────────────────────────────────

def distribuzione_voti(
    studenti: list[dict] | None = None,
    percorso_db: str | None = None,
    materia: str | None = None
) -> dict[int, int]:
    """Conta quanti studenti hanno ottenuto ciascun voto (1-10).

    Args:
        materia:  se specificata, analizza solo quella materia;
                  se None, considera tutti i voti di tutte le materie.

    Returns:
        Dizionario ordinato { voto: conteggio }.
        Esempio:  {4: 1, 5: 3, 6: 12, 7: 18, 8: 11, 9: 4, 10: 1}
    """
    studenti = _risolvi_studenti(studenti, percorso_db)

    conteggio: dict[int, int] = {}

    for s in studenti:
        if materia:
            voti_da_contare = [s["voti"][materia]] if materia in s["voti"] else []
        else:
            voti_da_contare = list(s["voti"].values())

        for voto in voti_da_contare:
            conteggio[voto] = conteggio.get(voto, 0) + 1

    return dict(sorted(conteggio.items()))


# ─────────────────────────────────────────────
#  6. CORRELAZIONE TRA DUE MATERIE
# ─────────────────────────────────────────────

def correlazione_materie(
    materia_a: str,
    materia_b: str,
    studenti: list[dict] | None = None,
    percorso_db: str | None = None
) -> dict:
    """Calcola il coefficiente di correlazione di Pearson tra i voti di due materie.

    Il coefficiente r è compreso tra -1 e +1:
        r ≈ +1  →  correlazione positiva forte  (chi va bene in A va bene in B)
        r ≈  0  →  nessuna correlazione
        r ≈ -1  →  correlazione negativa forte

    Returns:
        {
            "materia_a":    "Matematica",
            "materia_b":    "Informatica",
            "r":            0.73,          ← coefficiente di Pearson
            "n_studenti":   48,            ← studenti con entrambi i voti
            "interpretazione": "correlazione positiva moderata"
        }

    Raises:
        ValueError  se una delle due materie non esiste nei dati,
                    oppure se ci sono meno di 2 studenti con entrambi i voti.
    """
    studenti = _risolvi_studenti(studenti, percorso_db)

    coppie = [
        (s["voti"][materia_a], s["voti"][materia_b])
        for s in studenti
        if materia_a in s["voti"] and materia_b in s["voti"]
    ]

    if len(coppie) < 2:
        raise ValueError(
            f"Servono almeno 2 studenti con voti in entrambe le materie "
            f"('{materia_a}', '{materia_b}'). Trovati: {len(coppie)}."
        )

    x_vals = [c[0] for c in coppie]
    y_vals = [c[1] for c in coppie]

    # Coefficiente di Pearson manuale (nessuna dipendenza esterna)
    n    = len(coppie)
    mx   = statistics.mean(x_vals)
    my   = statistics.mean(y_vals)
    num  = sum((x - mx) * (y - my) for x, y in coppie)
    den  = math.sqrt(
        sum((x - mx) ** 2 for x in x_vals) *
        sum((y - my) ** 2 for y in y_vals)
    )

    r = round(num / den, 4) if den != 0 else 0.0

    # Interpretazione testuale
    r_abs = abs(r)
    if r_abs >= 0.8:
        forza = "forte"
    elif r_abs >= 0.5:
        forza = "moderata"
    elif r_abs >= 0.3:
        forza = "debole"
    else:
        forza = "assente o trascurabile"

    segno = "positiva" if r >= 0 else "negativa"
    interpretazione = f"correlazione {segno} {forza}" if r_abs >= 0.3 else "correlazione assente o trascurabile"

    return {
        "materia_a":       materia_a,
        "materia_b":       materia_b,
        "r":               r,
        "n_studenti":      n,
        "interpretazione": interpretazione,
    }


# ─────────────────────────────────────────────
#  7. STUDENTI A RISCHIO
# ─────────────────────────────────────────────

def studenti_a_rischio(
    studenti: list[dict] | None = None,
    percorso_db: str | None = None,
    soglia_voto: float = 6.0,
    soglia_assenze: int = 15
) -> dict[str, list[dict]]:
    """Individua gli studenti a rischio per media bassa e/o troppe assenze.

    Un studente è "a rischio" se:
        - media voti < soglia_voto          (default 6.0)
        - oppure assenze > soglia_assenze   (default 15)

    Returns:
        {
            "media_insufficiente": [
                {"id": ..., "nome": ..., "cognome": ..., "media": ..., "assenze": ...},
                ...
            ],
            "troppe_assenze": [
                {"id": ..., "nome": ..., "cognome": ..., "media": ..., "assenze": ...},
                ...
            ],
            "entrambi": [       ← studenti con ENTRAMBI i problemi
                ...
            ]
        }
    """
    studenti = _risolvi_studenti(studenti, percorso_db)

    arricchiti = [
        {
            "id":      s["id"],
            "nome":    s["nome"],
            "cognome": s["cognome"],
            "media":   _media_voti(s),
            "assenze": s["assenze"],
        }
        for s in studenti
    ]

    media_insuff = [s for s in arricchiti if s["media"] < soglia_voto]
    troppe_ass   = [s for s in arricchiti if s["assenze"] > soglia_assenze]
    entrambi     = [s for s in arricchiti if s["media"] < soglia_voto and s["assenze"] > soglia_assenze]

    return {
        "media_insufficiente": sorted(media_insuff, key=lambda s: s["media"]),
        "troppe_assenze":      sorted(troppe_ass,   key=lambda s: s["assenze"], reverse=True),
        "entrambi":            sorted(entrambi,     key=lambda s: s["media"]),
    }


# ─────────────────────────────────────────────
#  __main__  —  demo rapida da terminale
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    DB = sys.argv[1] if len(sys.argv) > 1 else "scuola_db.db"

    print(f"\n{'='*60}")
    print(f"  ANALYTICS — {DB}")
    print(f"{'='*60}")

    studenti = leggi_studenti_da_db(DB)

    # 1. Media per studente (top 5)
    print("\n── Media per studente (top 5) ──")
    for s in media_per_studente(studenti=studenti)[:5]:
        print(f"  {s['nome']:<12} {s['cognome']:<15} media: {s['media']}  assenze: {s['assenze']}")

    # 2. Media per materia
    print("\n── Media per materia ──")
    for materia, media in media_per_materia(studenti=studenti).items():
        print(f"  {materia:<22} {media}")

    # 3. Classifica top 3
    print("\n── Classifica (top 3 / peggiori 3) ──")
    cl = classifica_studenti(studenti=studenti, top_n=3)
    print("  Migliori:")
    for i, s in enumerate(cl["migliori"], 1):
        print(f"    {i}. {s['nome']} {s['cognome']} — {s['media']}")
    print("  Peggiori:")
    for i, s in enumerate(cl["peggiori"], 1):
        print(f"    {i}. {s['nome']} {s['cognome']} — {s['media']}")

    # 4. Peggiori per materia (primo per ogni materia)
    print("\n── Peggiori per materia (1° classificato) ──")
    for materia, lista in peggiori_per_materia(studenti=studenti, top_n=1).items():
        if lista:
            s = lista[0]
            print(f"  {materia:<22} {s['nome']} {s['cognome']} — voto: {s['voto']}")

    # 5. Distribuzione voti globale
    print("\n── Distribuzione voti (globale) ──")
    for voto, conteggio in distribuzione_voti(studenti=studenti).items():
        barra = "█" * conteggio
        print(f"  {voto:>2}: {barra} ({conteggio})")

    # 6. Correlazione Matematica ↔ Informatica
    print("\n── Correlazione Matematica ↔ Informatica ──")
    corr = correlazione_materie("Matematica", "Informatica", studenti=studenti)
    print(f"  r = {corr['r']}  ({corr['interpretazione']})  su {corr['n_studenti']} studenti")

    # 7. Studenti a rischio
    print("\n── Studenti a rischio ──")
    rischio = studenti_a_rischio(studenti=studenti, soglia_voto=6.0, soglia_assenze=15)
    print(f"  Media insufficiente (<6):   {len(rischio['media_insufficiente'])} studenti")
    print(f"  Troppe assenze (>15):       {len(rischio['troppe_assenze'])} studenti")
    print(f"  Entrambi i problemi:        {len(rischio['entrambi'])} studenti")
    if rischio["entrambi"]:
        for s in rischio["entrambi"]:
            print(f"    ⚠  {s['nome']} {s['cognome']} — media: {s['media']}  assenze: {s['assenze']}")

    print(f"\n{'='*60}\n")