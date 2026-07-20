"""
grafici.py — crea i grafici con matplotlib (li salva come PNG su disco
oppure li tiene in memoria)
Usiamo Figure+FigureCanvasAgg direttamente, senza passare da un
backend "globale": così questo codice funziona sempre allo stesso
modo, anche se viene eseguito in un thread diverso da quello della
finestra principale (che invece usa TkAgg), ad esempio quando si
genera il PDF in background.
"""

import io
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
import numpy as np

PALETTE = ["#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B2",
           "#937860", "#DA8BC3", "#8C8C8C", "#CCB974", "#64B5CD"]


def _fig(figsize) -> tuple:
    """Crea una Figure con il suo canvas e restituisce (fig, ax) per
    un grafico singolo.
    Usiamo questa funzione per non riscrivere sempre le stesse tre
    righe (Figure + FigureCanvasAgg + add_subplot) in ogni funzione
    che disegna un grafico."""
    fig = Figure(figsize=figsize)
    FigureCanvasAgg(fig)
    return fig, fig.add_subplot(111)


def _salva(fig: Figure, path: str | None) -> bytes | None:
    """
    Salva il grafico: se viene passato un percorso (path), lo scrive
    su file; altrimenti lo trasforma in un'immagine PNG tenuta in
    memoria e ne restituisce i byte.
    Tutte le funzioni di questo file usano questo comando per non
    ripetere la stessa logica di salvataggio. Avere entrambe le
    modalità (file oppure byte in memoria) ci permette di riusare gli
    stessi grafici sia nella finestra dell'app sia nel PDF, senza
    dover creare un file temporaneo ogni volta.
    """
    if path:
        fig.savefig(path, dpi=150, bbox_inches="tight")
        return None
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    buf.seek(0)
    return buf.read()


# ─── 6.2 ─────────────────────────────────────────────────────────────────────

def grafico_media_per_materia(
    dati: list[dict],
    path: str | None = None,
    soglia: float = 6.0,
) -> bytes | None:
    """Grafico a barre con la media generale di ogni materia.
    Serve per la richiesta 6.2 (media per materia). Le barre sono
    colorate in modo diverso se la media supera o no la soglia di
    sufficienza, così si vede subito quali materie vanno peggio, e
    sopra ogni barra scriviamo il numero esatto della media."""
    if not dati:
        return None
    materie = [d["materia"] for d in dati]
    medie   = [d["media"]   for d in dati]
    colori  = [PALETTE[0] if m >= soglia else PALETTE[3] for m in medie]

    fig, ax = _fig((max(6, len(materie) * 1.1), 5))
    bars = ax.bar(materie, medie, color=colori, edgecolor="white")
    ax.axhline(soglia, color="gray", linestyle="--", linewidth=1.2,
               label=f"Soglia {soglia}")
    ax.set_ylim(0, 10.5)
    ax.set_ylabel("Media voto")
    ax.set_title("Media per materia — tutti gli studenti")
    ax.set_xticks(range(len(materie)))
    ax.set_xticklabels(materie, rotation=30, ha="right")
    for bar, m in zip(bars, medie):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
                f"{m:.1f}", ha="center", va="bottom", fontsize=8)
    ax.legend(fontsize=8)
    fig.tight_layout()
    return _salva(fig, path)


# ─── 6.4 ─────────────────────────────────────────────────────────────────────

def grafico_assenti_giorno(
    studenti: list[dict],
    data: str,
    tot_studenti: int,
    path: str | None = None,
) -> bytes | None:
    """Torta con assenti e presenti in un giorno.
    Serve per la richiesta 6.4 (assenti in un giorno). Mostrare la
    proporzione con una torta è più facile da leggere rispetto a un
    numero da solo."""
    if tot_studenti == 0:
        return None
    n_assenti  = len(studenti)
    n_presenti = max(0, tot_studenti - n_assenti)

    fig, ax = _fig((5, 5))
    ax.pie(
        [n_presenti, n_assenti],
        labels=[f"Presenti ({n_presenti})", f"Assenti ({n_assenti})"],
        colors=[PALETTE[0], PALETTE[3]],
        autopct="%1.1f%%",
        startangle=90,
        wedgeprops={"edgecolor": "white", "linewidth": 1.5},
    )
    ax.set_title(f"Presenze/Assenze — {data}")
    fig.tight_layout()
    return _salva(fig, path)


# ─── 6.7 ─────────────────────────────────────────────────────────────────────

def grafico_sufficienti_insufficienti(
    risultato: dict,
    path: str | None = None,
) -> bytes | None:
    """Torta con sufficienti e insufficienti, con le percentuali.
    Serve per la richiesta 6.7 (dividere gli studenti tra sufficienti
    e insufficienti). La torta con le percentuali fa vedere subito
    quanta parte della classe è sufficiente."""
    suff   = risultato["sufficienti"]
    insuff = risultato["insufficienti"]
    soglia = risultato["soglia"]

    n_s, n_i = len(suff), len(insuff)
    if n_s + n_i == 0:
        return None

    fig, ax = _fig((6, 6))
    ax.pie(
        [n_s, n_i],
        labels=[f"Sufficienti\n({n_s})", f"Insufficienti\n({n_i})"],
        colors=[PALETTE[0], PALETTE[3]],
        autopct="%1.0f%%",
        startangle=90,
        wedgeprops={"edgecolor": "white", "linewidth": 1.5},
    )
    ax.set_title(f"Distribuzione sufficienti/insufficienti (soglia {soglia})",
                 fontsize=11, fontweight="bold")
    fig.tight_layout()
    return _salva(fig, path)


# ─── Distribuzione voti (istogramma) ─────────────────────────────────────────

def grafico_distribuzione_voti(
    voti: list[float],
    materia: str,
    path: str | None = None,
) -> bytes | None:
    """Istogramma con la distribuzione dei voti di una materia.
    Completa la richiesta 6.1: oltre alla media di un singolo
    studente, mostra come sono distribuiti tutti i voti della classe
    in quella materia, per dare un confronto. I gruppi (bin) larghi
    0.5 punti e la riga verticale sulla soglia 6 fanno vedere subito
    quanti voti sono sotto o sopra la sufficienza."""
    if not voti:
        return None
    fig, ax = _fig((6, 4))
    ax.hist(voti, bins=np.arange(0, 11.5, 0.5), color=PALETTE[1],
            edgecolor="white", linewidth=0.8)
    ax.axvline(6, color=PALETTE[3], linestyle="--", linewidth=1.5, label="Soglia 6")
    ax.set_xlabel("Voto")
    ax.set_ylabel("Frequenza")
    ax.set_title(f"Distribuzione voti — {materia}")
    ax.set_xticks(range(0, 11))
    ax.legend(fontsize=8)
    fig.tight_layout()
    return _salva(fig, path)


# ─── Istogrammi multi-materia ─────────────────────────────────────────────────

def grafico_istogrammi_per_materia(
    dati_materie: dict[str, list[float]],
    path: str | None = None,
    soglia: float = 6.0,
) -> bytes | None:
    """Tanti istogrammi insieme, uno per ogni materia.

    Args:
        dati_materie: {nome_materia: [voti]}

    Fa vedere tutte le materie in un solo grafico (una griglia con
    più colonne e righe, calcolata in base a quante materie ci sono),
    utile per confrontare velocemente le materie tra loro senza dover
    aprire N grafici separati. Le caselle della griglia che restano
    vuote vengono nascoste con axis("off").
    """
    if not dati_materie:
        return None
    materie = sorted(dati_materie.keys())
    n = len(materie)
    n_cols = min(3, n)
    n_rows = (n + n_cols - 1) // n_cols

    fig = Figure(figsize=(5 * n_cols, 4 * n_rows))
    FigureCanvasAgg(fig)

    for idx, mat in enumerate(materie):
        ax = fig.add_subplot(n_rows, n_cols, idx + 1)
        voti = dati_materie[mat]
        ax.hist(voti, bins=np.arange(0, 11.5, 0.5),
                color=PALETTE[1], edgecolor="white", linewidth=0.8)
        ax.axvline(soglia, color=PALETTE[3], linestyle="--",
                   linewidth=1.2, label=f"Soglia {soglia}")
        ax.set_title(mat, fontsize=9, fontweight="bold")
        ax.set_xlabel("Voto", fontsize=8)
        ax.set_ylabel("Freq.", fontsize=8)
        ax.set_xticks(range(0, 11))
        ax.tick_params(labelsize=7)
        ax.legend(fontsize=7)

    total_axes = n_rows * n_cols
    for idx in range(n, total_axes):
        fig.add_subplot(n_rows, n_cols, idx + 1).axis("off")

    fig.suptitle("Distribuzione voti per materia", fontsize=12, fontweight="bold")
    fig.tight_layout()
    return _salva(fig, path)