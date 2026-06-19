"""
student_charts.py — VISUALIZZAZIONE GRAFICA

Contiene le funzioni per generare grafici con matplotlib e seaborn:
    - istogrammi_voti_per_materia()      → voti distribuiti per ogni materia
    - grafico_barre_comparative()        → confronto media tra materie
    - scatter_plot_correlazione()        → correlazione tra due materie
    - pie_chart_esiti()                  → % promossi vs bocciati
    - heatmap_voti_studenti()            → matrice voti per ogni studente
    - genera_tutti_i_grafici()           → esegue tutti i grafici insieme

Ogni grafico:
    - Accetta studenti (list[dict]) e opzionali config per personalizzazione
    - Salva automaticamente in report/charts/ con timestamp
    - Ritorna il percorso del file salvato
"""

# import librerie standard
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# Configurazione stilistica globale
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 7)
plt.rcParams['font.size'] = 10


# ─────────────────────────────────────────────────────────────────────────────
#  HELPER — Preparazione dati e cartelle
# ─────────────────────────────────────────────────────────────────────────────

def _crea_cartella_grafici() -> Path:
    """Crea la cartella report/charts/ se non esiste."""
    cartella = Path("report/charts")
    cartella.mkdir(parents=True, exist_ok=True)
    return cartella


def _timestamp_filename(nome_base: str) -> str:
    """Genera un nome file con timestamp: 'nome_base_YYYYMMDD_HHMMSS.png'"""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{nome_base}_{ts}.png"


def _studenti_to_dataframe(studenti: list[dict]) -> pd.DataFrame:
    """Converte lista di studenti in DataFrame pandas per analisi."""
    dati = []
    for s in studenti:
        row = {
            "id": s["id"],
            "nome": s["nome"],
            "cognome": s["cognome"],
            "assenze": s["assenze"],
            "media_personale": s.get("media_personale", 0),
            "esito": s.get("esito", "—"),
            "debiti": len(s.get("debiti", [])),
        }
        # Aggiungi singoli voti come colonne
        for materia, voto in s["voti"].items():
            row[materia] = voto
        dati.append(row)
    
    return pd.DataFrame(dati)


# ─────────────────────────────────────────────────────────────────────────────
#  1. ISTOGRAMMI DEI VOTI PER MATERIA
# ─────────────────────────────────────────────────────────────────────────────

def istogrammi_voti_per_materia(
    studenti: list[dict],
    config: dict | None = None
) -> Path:
    """Genera istogrammi dei voti per ogni materia (distribuzione).
    
    Un istogramma per materia, mostra la frequenza di ogni voto (2-10).
    
    Args:
        studenti:   lista di dizionari studente
        config:     dict con 'materie' (opzionale, altrimenti dedotto da studenti)
    
    Returns:
        Path del file salvato in report/charts/
    """
    if not config:
        materie = set()
        for s in studenti:
            materie.update(s["voti"].keys())
        materie = sorted(materie)
    else:
        materie = config.get("materie", [])
    
    n_materie = len(materie)
    n_cols = 3
    n_rows = (n_materie + n_cols - 1) // n_cols
    
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 5 * n_rows))
    axes = axes.flatten()  # rendi 1D l'array di assi
    
    for idx, materia in enumerate(materie):
        voti = [s["voti"][materia] for s in studenti if materia in s["voti"]]
        
        ax = axes[idx]
        ax.hist(voti, bins=range(2, 12), color='steelblue', edgecolor='black', alpha=0.7)
        ax.set_title(f'Distribuzione voti — {materia}', fontweight='bold', fontsize=12)
        ax.set_xlabel('Voto')
        ax.set_ylabel('Frequenza')
        ax.set_xticks(range(2, 11))
        ax.grid(axis='y', alpha=0.3)
    
    # Nascondi gli assi non usati
    for idx in range(n_materie, len(axes)):
        axes[idx].axis('off')
    
    plt.tight_layout()
    
    cartella = _crea_cartella_grafici()
    percorso = cartella / _timestamp_filename("istogrammi_voti_per_materia")
    plt.savefig(percorso, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"[Grafico] Istogrammi salvati in: {percorso}")
    return percorso


# ─────────────────────────────────────────────────────────────────────────────
#  2. GRAFICI A BARRE COMPARATIVI TRA MATERIE
# ─────────────────────────────────────────────────────────────────────────────

def grafico_barre_comparative(
    studenti: list[dict],
    config: dict | None = None
) -> Path:
    """Grafico a barre che confronta la media dei voti tra materie.
    
    Una sola figura con tutte le materie, ordinate per media decrescente.
    
    Args:
        studenti:   lista di dizionari studente
        config:     dict con 'materie' (opzionale)
    
    Returns:
        Path del file salvato
    """
    df = _studenti_to_dataframe(studenti)
    
    if not config:
        materie = [col for col in df.columns if col not in 
                   ['id', 'nome', 'cognome', 'assenze', 'media_personale', 'esito', 'debiti']]
    else:
        materie = config.get("materie", [])
    
    medie_materie = {}
    for materia in materie:
        if materia in df.columns:
            medie_materie[materia] = df[materia].mean()
    
    # Ordina per media decrescente
    materie_ord = sorted(medie_materie.items(), key=lambda x: x[1], reverse=True)
    nomi, medie = zip(*materie_ord)
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    colori = plt.cm.RdYlGn(np.linspace(0.3, 0.9, len(nomi)))  # sfumatura rosso-giallo-verde
    bars = ax.bar(nomi, medie, color=colori, edgecolor='black', linewidth=1.5)
    
    # Aggiungi etichette sui bar
    for bar, media in zip(bars, medie):
        altura = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2., altura,
                f'{media:.2f}',
                ha='center', va='bottom', fontweight='bold')
    
    ax.set_ylabel('Media voti', fontweight='bold')
    ax.set_title('Confronto media voti per materia', fontweight='bold', fontsize=14)
    ax.set_ylim(0, 10)
    ax.grid(axis='y', alpha=0.3)
    plt.xticks(rotation=45, ha='right')
    
    plt.tight_layout()
    
    cartella = _crea_cartella_grafici()
    percorso = cartella / _timestamp_filename("grafico_barre_comparative")
    plt.savefig(percorso, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"[Grafico] Barre comparative salvate in: {percorso}")
    return percorso


# ─────────────────────────────────────────────────────────────────────────────
#  3. SCATTER PLOT — CORRELAZIONE TRA DUE MATERIE
# ─────────────────────────────────────────────────────────────────────────────

def scatter_plot_correlazione(
    studenti: list[dict],
    materia_a: str = "Matematica",
    materia_b: str = "Informatica"
) -> Path:
    """Scatter plot che mostra la correlazione tra i voti di due materie.
    
    Ogni punto rappresenta uno studente.
    Include linea di tendenza (regressione lineare).
    
    Args:
        studenti:   lista di dizionari studente
        materia_a:  nome della materia sull'asse X
        materia_b:  nome della materia sull'asse Y
    
    Returns:
        Path del file salvato
    """
    df = _studenti_to_dataframe(studenti)
    
    # Filtra studenti che hanno entrambi i voti
    dati_validi = df[(df[materia_a].notna()) & (df[materia_b].notna())]
    
    if len(dati_validi) < 2:
        print(f"[ERRORE] Non abbastanza dati per correlazione {materia_a} vs {materia_b}")
        return None
    
    fig, ax = plt.subplots(figsize=(10, 7))
    
    # Scatter plot
    scatter = ax.scatter(dati_validi[materia_a], dati_validi[materia_b],
                        s=100, alpha=0.6, color='steelblue', edgecolor='black', linewidth=0.5)
    
    # Linea di tendenza (regressione lineare)
    z = np.polyfit(dati_validi[materia_a], dati_validi[materia_b], 1)
    p = np.poly1d(z)
    x_line = np.linspace(dati_validi[materia_a].min(), dati_validi[materia_a].max(), 100)
    ax.plot(x_line, p(x_line), "r--", linewidth=2, label='Linea di tendenza')
    
    # Calcola correlazione di Pearson
    correlazione = dati_validi[materia_a].corr(dati_validi[materia_b])
    
    ax.set_xlabel(f'{materia_a} (voto)', fontweight='bold', fontsize=11)
    ax.set_ylabel(f'{materia_b} (voto)', fontweight='bold', fontsize=11)
    ax.set_title(f'Correlazione {materia_a} ↔ {materia_b}\n(r = {correlazione:.3f})',
                 fontweight='bold', fontsize=13)
    ax.set_xlim(1.5, 10.5)
    ax.set_ylim(1.5, 10.5)
    ax.grid(alpha=0.3)
    ax.legend()
    
    plt.tight_layout()
    
    cartella = _crea_cartella_grafici()
    percorso = cartella / _timestamp_filename(f"scatter_correlazione_{materia_a}_vs_{materia_b}")
    plt.savefig(percorso, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"[Grafico] Scatter plot correlazione salvato in: {percorso}")
    return percorso


# ─────────────────────────────────────────────────────────────────────────────
#  4. PIE CHART — PROMOSSI vs BOCCIATI
# ─────────────────────────────────────────────────────────────────────────────

def pie_chart_esiti(studenti: list[dict]) -> Path:
    """Pie chart che mostra la percentuale di promossi vs bocciati.
    
    Richiede che 'esito' sia stato calcolato (run cmd_logica prima).
    
    Args:
        studenti:   lista di dizionari studente (con campo 'esito')
    
    Returns:
        Path del file salvato
    """
    # Conta esiti
    promossi = sum(1 for s in studenti if s.get("esito") == "Promosso")
    bocciati = len(studenti) - promossi
    
    fig, ax = plt.subplots(figsize=(9, 7))
    
    labels = ['Promossi', 'Bocciati']
    valori = [promossi, bocciati]
    colori = ['#2ecc71', '#e74c3c']  # verde, rosso
    explode = (0.05, 0.05)  # stacca un po' le fette
    
    wedges, texts, autotexts = ax.pie(
        valori, labels=labels, colors=colori, autopct='%1.1f%%',
        startangle=90, explode=explode, textprops={'fontsize': 12, 'fontweight': 'bold'}
    )
    
    # Colora il testo percentuale
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
        autotext.set_fontsize(13)
    
    ax.set_title(f'Esiti finali\n(Promossi: {promossi}, Bocciati: {bocciati})',
                 fontweight='bold', fontsize=14, pad=20)
    
    plt.tight_layout()
    
    cartella = _crea_cartella_grafici()
    percorso = cartella / _timestamp_filename("pie_chart_esiti")
    plt.savefig(percorso, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"[Grafico] Pie chart esiti salvato in: {percorso}")
    return percorso


# ─────────────────────────────────────────────────────────────────────────────
#  5. HEATMAP — VOTI PER OGNI STUDENTE
# ─────────────────────────────────────────────────────────────────────────────

def heatmap_voti_studenti(
    studenti: list[dict],
    config: dict | None = None,
    max_studenti: int = 30
) -> Path:
    """Heatmap che mostra i voti di ogni studente per ogni materia.
    
    Matrice: righe = studenti, colonne = materie.
    Colori indicano il valore del voto (rosso basso, verde alto).
    
    Args:
        studenti:      lista di dizionari studente
        config:        dict con 'materie' (opzionale)
        max_studenti:  limitare a max_studenti per leggibilità (default 30)
    
    Returns:
        Path del file salvato
    """
    df = _studenti_to_dataframe(studenti)
    
    # Determina le colonne materie
    if not config:
        materie = [col for col in df.columns if col not in 
                   ['id', 'nome', 'cognome', 'assenze', 'media_personale', 'esito', 'debiti']]
    else:
        materie = config.get("materie", [])
    
    # Prepara matrice voti
    matrice_voti = df[['nome', 'cognome'] + materie].head(max_studenti)
    
    # Crea etichetta studente (nome + cognome)
    etichette_studenti = [f"{row['nome']} {row['cognome']}" 
                          for _, row in matrice_voti.iterrows()]
    matrice_voti = matrice_voti[materie].values
    
    fig, ax = plt.subplots(figsize=(12, max(8, len(etichette_studenti) * 0.3)))
    
    # Heatmap con colorbar
    sns.heatmap(matrice_voti, 
                xticklabels=materie,
                yticklabels=etichette_studenti,
                annot=True,  # mostra i valori
                fmt='d',
                cmap='RdYlGn',  # rosso (basso) a verde (alto)
                vmin=2, vmax=10,
                cbar_kws={'label': 'Voto'},
                ax=ax,
                linewidths=0.5)
    
    ax.set_title('Heatmap voti per studente', fontweight='bold', fontsize=14, pad=20)
    ax.set_xlabel('Materia', fontweight='bold')
    ax.set_ylabel('Studente', fontweight='bold')
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    
    plt.tight_layout()
    
    cartella = _crea_cartella_grafici()
    percorso = cartella / _timestamp_filename("heatmap_voti_studenti")
    plt.savefig(percorso, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"[Grafico] Heatmap salvata in: {percorso}")
    return percorso


# ─────────────────────────────────────────────────────────────────────────────
#  6. BONUS: GRAFICO MEDIA PERSONALE vs ASSENZE
# ─────────────────────────────────────────────────────────────────────────────

def scatter_media_vs_assenze(studenti: list[dict]) -> Path:
    """Scatter plot: relazione tra media personale e assenze.
    
    Mostra se gli studenti con tante assenze hanno media più bassa.
    
    Args:
        studenti:   lista di dizionari studente
    
    Returns:
        Path del file salvato
    """
    df = _studenti_to_dataframe(studenti)
    
    fig, ax = plt.subplots(figsize=(10, 7))
    
    # Colori in base all'esito
    colori = df['esito'].map({'Promosso': '#2ecc71', 'Bocciato': '#e74c3c', '—': '#95a5a6'})
    
    scatter = ax.scatter(df['assenze'], df['media_personale'],
                        s=100, c=colori, alpha=0.6, edgecolor='black', linewidth=0.5)
    
    ax.set_xlabel('Assenze', fontweight='bold', fontsize=11)
    ax.set_ylabel('Media personale', fontweight='bold', fontsize=11)
    ax.set_title('Relazione Media personale vs Assenze', fontweight='bold', fontsize=13)
    ax.grid(alpha=0.3)
    
    # Legenda
    from matplotlib.patches import Patch
    legenda = [
        Patch(facecolor='#2ecc71', edgecolor='black', label='Promosso'),
        Patch(facecolor='#e74c3c', edgecolor='black', label='Bocciato'),
    ]
    ax.legend(handles=legenda, loc='best')
    
    plt.tight_layout()
    
    cartella = _crea_cartella_grafici()
    percorso = cartella / _timestamp_filename("scatter_media_vs_assenze")
    plt.savefig(percorso, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"[Grafico] Scatter media vs assenze salvato in: {percorso}")
    return percorso


# ─────────────────────────────────────────────────────────────────────────────
#  FUNZIONE AGGREGATA — Genera tutti i grafici insieme
# ─────────────────────────────────────────────────────────────────────────────

def genera_tutti_i_grafici(
    studenti: list[dict],
    config: dict | None = None,
    materia_a: str = "Matematica",
    materia_b: str = "Informatica"
) -> dict[str, Path]:
    """Esegue TUTTI i grafici in sequenza e ritorna i percorsi.
    
    Args:
        studenti:   lista di dizionari studente (con esito calcolato per pie chart)
        config:     dict con config (opzionale)
        materia_a:  prima materia per scatter (default Matematica)
        materia_b:  seconda materia per scatter (default Informatica)
    
    Returns:
        Dizionario con i percorsi di tutti i grafici:
        {
            'istogrammi': Path,
            'barre_comparative': Path,
            'scatter_correlazione': Path,
            'pie_chart': Path,
            'heatmap': Path,
            'media_vs_assenze': Path,
        }
    """
    print("\n" + "="*60)
    print("  GENERAZIONE GRAFICI")
    print("="*60 + "\n")
    print("Generazione grafici in corso...\n")

    risultati = {}
    
    try:
        risultati['istogrammi'] = istogrammi_voti_per_materia(studenti, config)
    except Exception as e:
        print(f"[ERRORE] Istogrammi: {e}")
    
    try:
        risultati['barre_comparative'] = grafico_barre_comparative(studenti, config)
    except Exception as e:
        print(f"[ERRORE] Barre comparative: {e}")
    
    try:
        risultati['scatter_correlazione'] = scatter_plot_correlazione(studenti, materia_a, materia_b)
    except Exception as e:
        print(f"[ERRORE] Scatter correlazione: {e}")
    
    try:
        risultati['pie_chart'] = pie_chart_esiti(studenti)
    except Exception as e:
        print(f"[ERRORE] Pie chart: {e}")
    
    try:
        risultati['heatmap'] = heatmap_voti_studenti(studenti, config)
    except Exception as e:
        print(f"[ERRORE] Heatmap: {e}")
    
    try:
        risultati['media_vs_assenze'] = scatter_media_vs_assenze(studenti)
    except Exception as e:
        print(f"[ERRORE] Media vs assenze: {e}")
    
    print("\n" + "="*60)
    print(f"  Grafici generati: {len([r for r in risultati.values() if r])} file")
    print("="*60 + "\n")
    
    return risultati


# ─────────────────────────────────────────────────────────────────────────────
#  DEMO — Esecuzione da terminale
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    """Demo: leggi dati da studenti_validi.json e genera tutti i grafici."""
    import sys
    import json
    
    json_path = "data/output/studenti_validi.json"
    
    if not Path(json_path).exists():
        print(f"[ERRORE] {json_path} non trovato. Esegui prima 'python main.py report'")
        sys.exit(1)
    
    with open(json_path, "r", encoding="utf-8") as f:
        studenti = json.load(f)
    
    # Carica config
    config_path = Path("configurations/config.json")
    config = {}
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    
    # Genera tutti i grafici
    risultati = genera_tutti_i_grafici(studenti, config)
    
    print("\nRisultati:")
    for nome_grafico, percorso in risultati.items():
        if percorso:
            print(f"  ✓ {nome_grafico}: {percorso}")