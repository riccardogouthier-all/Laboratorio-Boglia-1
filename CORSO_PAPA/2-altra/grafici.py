"""
grafici.py — generazione grafici matplotlib (PNG su disco o in memoria)
Usa Figure+FigureCanvasAgg direttamente: nessuna dipendenza dal backend globale,
thread-safe rispetto al TkAgg di main.py.
"""

import io
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.patches import Patch
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


# ─── Istogrammi multi-materia ─────────────────────────────────────────────────

def grafico_istogrammi_per_materia(
    dati_materie: dict[str, list[float]],
    path: str | None = None,
    soglia: float = 6.0,
) -> bytes | None:
    """Griglia di istogrammi, uno per ogni materia.

    Args:
        dati_materie: {nome_materia: [voti]}
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


# ─── Scatter correlazione tra due materie ────────────────────────────────────

def grafico_scatter_correlazione(
    voti_a: list[float],
    voti_b: list[float],
    materia_a: str,
    materia_b: str,
    path: str | None = None,
) -> bytes | None:
    """Scatter plot voti materia_a vs materia_b con linea di tendenza.

    Args:
        voti_a/voti_b: liste di voti allineate per studente (stessa lunghezza)
        materia_a/b:   nomi materie
    """
    if len(voti_a) < 2 or len(voti_b) < 2 or len(voti_a) != len(voti_b):
        return None
    va = np.array(voti_a)
    vb = np.array(voti_b)

    fig, ax = _fig((8, 6))
    ax.scatter(va, vb, s=80, alpha=0.7, color=PALETTE[0],
               edgecolor="white", linewidth=0.5)

    z = np.polyfit(va, vb, 1)
    x_line = np.linspace(va.min(), va.max(), 100)
    ax.plot(x_line, np.poly1d(z)(x_line), color=PALETTE[3],
            linestyle="--", linewidth=1.8, label="Tendenza")

    corr = float(np.corrcoef(va, vb)[0, 1])
    ax.set_xlabel(materia_a, fontsize=10)
    ax.set_ylabel(materia_b, fontsize=10)
    ax.set_title(f"Correlazione {materia_a} ↔ {materia_b}  (r = {corr:.3f})",
                 fontsize=11, fontweight="bold")
    ax.set_xlim(0, 10.5)
    ax.set_ylim(0, 10.5)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    return _salva(fig, path)


# ─── Heatmap voti studenti × materie ─────────────────────────────────────────

def grafico_heatmap_voti(
    studenti: list[dict],
    materie: list[str],
    path: str | None = None,
) -> bytes | None:
    """Heatmap matrice studenti (righe) × materie (colonne).

    Args:
        studenti: list[dict] con chiavi 'studente' (str) e 'voti' (dict materia→voto)
                  Formato: {"studente": "Rossi Mario", "voti": {"Matematica": 7.0, ...}}
        materie:  lista materie (colonne)
    """
    if not studenti or not materie:
        return None

    nomi  = [s["studente"] for s in studenti]
    mat_v = np.full((len(nomi), len(materie)), np.nan)
    for r, s in enumerate(studenti):
        for c, mat in enumerate(materie):
            v = s.get("voti", {}).get(mat)
            if v is not None:
                mat_v[r, c] = v

    h = max(5, len(nomi) * 0.4)
    w = max(6, len(materie) * 1.2)
    fig = Figure(figsize=(w, h))
    FigureCanvasAgg(fig)
    ax = fig.add_subplot(111)

    import matplotlib.cm as mcm
    im = ax.imshow(mat_v, cmap=mcm.RdYlGn, vmin=0, vmax=10, aspect="auto")
    fig.colorbar(im, ax=ax, label="Voto")

    ax.set_xticks(range(len(materie)))
    ax.set_xticklabels(materie, rotation=40, ha="right", fontsize=8)
    ax.set_yticks(range(len(nomi)))
    ax.set_yticklabels(nomi, fontsize=8)
    ax.set_title("Heatmap voti studenti × materie", fontsize=11, fontweight="bold")

    for r in range(len(nomi)):
        for c in range(len(materie)):
            if not np.isnan(mat_v[r, c]):
                ax.text(c, r, f"{mat_v[r,c]:.0f}", ha="center", va="center",
                        fontsize=7, color="black")

    fig.tight_layout()
    return _salva(fig, path)


# ─── Scatter media personale vs assenze ──────────────────────────────────────

def grafico_scatter_media_vs_assenze(
    dati: list[dict],
    soglia: float = 6.0,
    path: str | None = None,
) -> bytes | None:
    """Scatter media generale vs numero assenze per studente.

    Args:
        dati: list[dict] con chiavi 'studente', 'media', 'num_assenze'
    """
    if not dati:
        return None

    nomi    = [d["studente"]    for d in dati]
    medie   = np.array([d["media"]       for d in dati])
    assenze = np.array([d["num_assenze"] for d in dati])
    colori  = [PALETTE[0] if m >= soglia else PALETTE[3] for m in medie]

    fig, ax = _fig((9, 6))
    ax.scatter(assenze, medie, s=90, c=colori, alpha=0.8,
               edgecolor="white", linewidth=0.5)

    for nome, x, y in zip(nomi, assenze, medie):
        ax.annotate(nome, (x, y), textcoords="offset points",
                    xytext=(5, 3), fontsize=7, alpha=0.8)

    ax.axhline(soglia, color="gray", linestyle="--", linewidth=1.2,
               label=f"Soglia {soglia}")
    ax.set_xlabel("Numero assenze", fontsize=10)
    ax.set_ylabel("Media generale", fontsize=10)
    ax.set_title("Media vs Assenze per studente", fontsize=11, fontweight="bold")
    ax.set_ylim(0, 10.5)
    ax.grid(alpha=0.3)

    legenda = [
        Patch(facecolor=PALETTE[0], label=f"Sufficiente (≥{soglia})"),
        Patch(facecolor=PALETTE[3], label=f"Insufficiente (<{soglia})"),
    ]
    ax.legend(handles=legenda, fontsize=8)
    fig.tight_layout()
    return _salva(fig, path)