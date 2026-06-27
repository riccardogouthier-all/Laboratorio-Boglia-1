"""
grafici.py — generazione grafici matplotlib (PNG su disco o in memoria)
Usa Figure+FigureCanvasAgg direttamente: nessuna dipendenza dal backend globale,
thread-safe rispetto al TkAgg di main.py.
"""

import io
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
import numpy as np

PALETTE = ["#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B2",
           "#937860", "#DA8BC3", "#8C8C8C", "#CCB974", "#64B5CD"]


def _fig(figsize) -> tuple:
    """Crea Figure + Agg canvas; ritorna (fig, ax) per subplot singolo."""
    fig = Figure(figsize=figsize)
    FigureCanvasAgg(fig)
    return fig, fig.add_subplot(111)


def _salva(fig: Figure, path: str | None) -> bytes | None:
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
    """Barchart media complessiva per ogni materia."""
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


# ─── 6.3 ─────────────────────────────────────────────────────────────────────

def grafico_assenze_studenti(
    dati: list[dict],
    path: str | None = None,
    top_n: int = 15,
) -> bytes | None:
    """Barchart assenze per studente (top N)."""
    if not dati:
        return None
    dati_sorted = sorted(dati, key=lambda d: d["num_assenze"], reverse=True)[:top_n]
    nomi   = [d["studente"]    for d in dati_sorted]
    valori = [d["num_assenze"] for d in dati_sorted]

    fig, ax = _fig((max(6, len(nomi) * 0.9), 5))
    ax.barh(nomi[::-1], valori[::-1], color=PALETTE[4], edgecolor="white")
    ax.set_xlabel("Numero assenze")
    ax.set_title(f"Assenze per studente (top {min(top_n, len(nomi))})")
    for i, v in enumerate(valori[::-1]):
        ax.text(v + 0.1, i, str(v), va="center", fontsize=8)
    fig.tight_layout()
    return _salva(fig, path)


# ─── 6.4 ─────────────────────────────────────────────────────────────────────

def grafico_assenti_giorno(
    studenti: list[dict],
    data: str,
    tot_studenti: int,
    path: str | None = None,
) -> bytes | None:
    """Pie chart assenti vs presenti in un giorno."""
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
    """Donut chart sufficienti vs insufficienti + barchart medie."""
    suff   = risultato["sufficienti"]
    insuff = risultato["insufficienti"]
    soglia = risultato["soglia"]

    fig = Figure(figsize=(12, 5))
    FigureCanvasAgg(fig)
    ax1 = fig.add_subplot(121)
    ax2 = fig.add_subplot(122)

    # Donut
    n_s, n_i = len(suff), len(insuff)
    if n_s + n_i > 0:
        ax1.pie(
            [n_s, n_i],
            labels=[f"Sufficienti\n({n_s})", f"Insufficienti\n({n_i})"],
            colors=[PALETTE[0], PALETTE[3]],
            autopct="%1.0f%%",
            startangle=90,
            pctdistance=0.75,
            wedgeprops={"width": 0.55, "edgecolor": "white", "linewidth": 2},
        )
        ax1.set_title(f"Distribuzione (soglia {soglia})")
    else:
        ax1.text(0.5, 0.5, "Nessun dato", ha="center", transform=ax1.transAxes)

    # Barchart medie
    tutti = sorted(suff + insuff, key=lambda d: d["media"], reverse=True)
    if tutti:
        nomi   = [d["studente"] for d in tutti]
        medie  = [d["media"]    for d in tutti]
        colori = [PALETTE[0] if d["media"] >= soglia else PALETTE[3] for d in tutti]
        ax2.barh(nomi[::-1], medie[::-1], color=colori[::-1], edgecolor="white")
        ax2.axvline(soglia, color="gray", linestyle="--", linewidth=1.2)
        ax2.set_xlabel("Media generale")
        ax2.set_title("Media per studente")
        ax2.set_xlim(0, 10.5)

    fig.suptitle("Analisi sufficienti / insufficienti", fontsize=13, fontweight="bold")
    fig.tight_layout()
    return _salva(fig, path)


# ─── Distribuzione voti (istogramma) ─────────────────────────────────────────

def grafico_distribuzione_voti(
    voti: list[float],
    materia: str,
    path: str | None = None,
) -> bytes | None:
    """Istogramma distribuzione voti di una materia."""
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