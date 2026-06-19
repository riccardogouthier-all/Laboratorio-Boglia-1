from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from datetime import datetime
from pathlib import Path

from student_stats import (
    distribuzione_voti,
    peggiori_per_materia,
    studenti_a_rischio,
)
from student_charts import genera_tutti_i_grafici


def genera_report_docx(
    config: dict,
    validi: list[dict],
    scartati: list[dict],
    stats: dict,
    top5: list[dict],
    fasce: dict | None = None,
    classifica_media: list[dict] | None = None,
    classifica_assenze: list[dict] | None = None,
    genera_grafici: bool = True,
) -> Path:
    """Genera il report completo in formato .docx in report/."""

    oggi     = datetime.now()
    percorso = Path("report") / f"report_{oggi.strftime('%Y%m%d')}.docx"
    percorso.parent.mkdir(parents=True, exist_ok=True)

    doc = Document()

    # ── helpers di formattazione ──────────────────────────────────────────────

    def aggiungi_titolo(testo: str, livello: int = 1):
        doc.add_heading(testo, level=livello)

    def aggiungi_riga(testo: str, grassetto: bool = False, colore: RGBColor | None = None):
        """Aggiunge un paragrafo normale, opzionalmente in grassetto o colorato."""
        p = doc.add_paragraph()
        run = p.add_run(testo)
        run.bold = grassetto
        if colore:
            run.font.color.rgb = colore

    def aggiungi_voce_lista(testo: str, stile: str = "List Bullet"):
        doc.add_paragraph(testo, style=stile)

    # ── INTESTAZIONE ─────────────────────────────────────────────────────────
    aggiungi_titolo("Report Studenti — Pipeline Python", livello=0)

    aggiungi_riga(f"Classe:              {config['classe']}", grassetto=True)
    aggiungi_riga(f"Data generazione:    {oggi.strftime('%d/%m/%Y %H:%M:%S')}")
    aggiungi_riga(f"Studenti totali:     {len(validi) + len(scartati)}")
    aggiungi_riga(f"Studenti validi:     {len(validi)}")
    aggiungi_riga(f"Studenti scartati:   {len(scartati)}")

    # ── STATISTICHE PER MATERIA ───────────────────────────────────────────────
    aggiungi_titolo("Statistiche per Materia")
    for materia, s in stats.items():
        aggiungi_riga(materia, grassetto=True)
        aggiungi_voce_lista(f"Media:            {s['media']}")
        aggiungi_voce_lista(f"Mediana:          {s['mediana']}")
        aggiungi_voce_lista(f"Dev. standard:    {s['stdev']}")
        aggiungi_voce_lista(f"Voto minimo:      {s['min']}")
        aggiungi_voce_lista(f"Voto massimo:     {s['max']}")

    # ── DISTRIBUZIONE VOTI ────────────────────────────────────────────────────
    aggiungi_titolo("Distribuzione Voti (globale)")
    dist        = distribuzione_voti(studenti=validi)
    totale_voti = sum(dist.values())
    for voto, conteggio in dist.items():
        pct = round(conteggio / totale_voti * 100, 1) if totale_voti else 0
        aggiungi_riga(f"  Voto {voto:>2}:  {conteggio:>3} studenti  ({pct:>4}%)")

    # ── PEGGIORI PER MATERIA ──────────────────────────────────────────────────
    aggiungi_titolo("Peggiori per Materia (top 3)")
    for materia, lista in peggiori_per_materia(studenti=validi, top_n=3).items():
        aggiungi_riga(materia, grassetto=True)
        for pos, s in enumerate(lista, 1):
            aggiungi_voce_lista(
                f"{pos}. {s['nome']} {s['cognome']}  —  voto: {s['voto']}"
            )

    # ── STUDENTI A RISCHIO ────────────────────────────────────────────────────
    rischio = studenti_a_rischio(
        studenti=validi,
        soglia_voto=float(config.get("soglia_voto", 6.0)),
        soglia_assenze=int(config.get("soglia_assenze", 15)),
    )
    aggiungi_titolo("Studenti a Rischio")
    aggiungi_riga(
        f"Media insufficiente (<{config.get('soglia_voto', 6.0)}):  "
        f"{len(rischio['media_insufficiente'])} studenti"
    )
    aggiungi_riga(
        f"Troppe assenze (>{config.get('soglia_assenze', 15)}):       "
        f"{len(rischio['troppe_assenze'])} studenti"
    )
    aggiungi_riga(
        f"Entrambi i problemi:          {len(rischio['entrambi'])} studenti"
    )
    if rischio["entrambi"]:
        aggiungi_riga("Dettaglio (entrambi i problemi):", grassetto=True)
        for s in rischio["entrambi"]:
            aggiungi_voce_lista(
                f"⚠  {s['nome']} {s['cognome']}  —  "
                f"media: {s['media']}   assenze: {s['assenze']}",
                stile="List Bullet",
            )

    # ── TOP 5 STUDENTI ────────────────────────────────────────────────────────
    aggiungi_titolo("Top 5 Studenti")
    for i, s in enumerate(top5, 1):
        aggiungi_voce_lista(
            f"{i}. {s['nome']} {s['cognome']}  —  "
            f"media: {s.get('media', s.get('media_personale', '—'))}  "
            f"assenze: {s['assenze']}"
        )

    # ── ESITI FINALI ──────────────────────────────────────────────────────────
    ha_esito = validi and "esito" in validi[0]
    if ha_esito:
        n_promossi = sum(1 for s in validi if s["esito"] == "Promosso")
        n_bocciati = len(validi) - n_promossi
        aggiungi_titolo("Esiti Finali")
        aggiungi_riga(f"Promossi:   {n_promossi}")
        aggiungi_riga(f"Bocciati:   {n_bocciati}")
        bocciati = [s for s in validi if s["esito"] == "Bocciato"]
        if bocciati:
            aggiungi_riga("Dettaglio bocciati:", grassetto=True)
            for s in bocciati:
                motivi_str = "; ".join(s.get("motivi_esito", []))
                aggiungi_voce_lista(
                    f"• {s['nome']} {s['cognome']}  —  "
                    f"voto finale: {s.get('voto_finale', '—')}  "
                    f"debiti: {len(s.get('debiti', []))}  "
                    f"[{motivi_str}]"
                )

    # ── FASCE DI RENDIMENTO ───────────────────────────────────────────────────
    if fasce:
        aggiungi_titolo("Fasce di Rendimento")
        for nome_fascia, lista_fascia in fasce.items():
            aggiungi_riga(f"{nome_fascia}  —  {len(lista_fascia)} studenti", grassetto=True)
            for s in lista_fascia:
                debiti_str = ", ".join(s.get("debiti", [])) or "nessuno"
                aggiungi_voce_lista(
                    f"{s['nome']} {s['cognome']}  —  "
                    f"media: {s.get('media_personale', '—')}  "
                    f"voto: {s.get('voto_finale', '—')}  "
                    f"debiti: {debiti_str}"
                )

    # ── CLASSIFICA PER MEDIA ──────────────────────────────────────────────────
    if classifica_media:
        aggiungi_titolo("Classifica per Media (bubble sort)")
        for pos, s in enumerate(classifica_media, 1):
            aggiungi_voce_lista(
                f"{pos:>3}. {s['nome']} {s['cognome']}  —  "
                f"media: {s.get('media_personale', '—')}  "
                f"esito: {s.get('esito', '—')}"
            )

    # ── CLASSIFICA PER ASSENZE ────────────────────────────────────────────────
    if classifica_assenze:
        aggiungi_titolo("Classifica per Assenze (quick sort, crescente)")
        for pos, s in enumerate(classifica_assenze, 1):
            aggiungi_voce_lista(
                f"{pos:>3}. {s['nome']} {s['cognome']}  —  "
                f"assenze: {s['assenze']}  "
                f"media: {s.get('media_personale', '—')}"
            )

    # ── STEP 17 — GENERAZIONE GRAFICI (integrato nel report) ─────────────────
    if genera_grafici and validi and ha_esito:
        aggiungi_titolo("Grafici e Visualizzazioni")
        aggiungi_riga("Generazione grafici in corso...", grassetto=True)
        try:
            grafici = genera_tutti_i_grafici(validi, config)

            # Titoli leggibili per ogni grafico, nello stesso ordine di generazione
            titoli_grafici = {
                "istogrammi": "Distribuzione voti per materia",
                "barre_comparative": "Confronto media voti per materia",
                "scatter_correlazione": "Correlazione tra materie",
                "pie_chart": "Esiti finali (promossi vs bocciati)",
                "heatmap": "Heatmap voti per studente",
                "media_vs_assenze": "Media personale vs assenze",
            }

            n_inseriti = 0
            for chiave, percorso_grafico in grafici.items():
                if not percorso_grafico:
                    continue
                aggiungi_riga(titoli_grafici.get(chiave, chiave), grassetto=True)
                doc.add_picture(str(percorso_grafico), width=Inches(6))
                n_inseriti += 1

            aggiungi_riga(f"Grafici generati con successo in report/charts/ ({n_inseriti} file)")
            print("[Step 17] Grafici generati con successo in report/charts/")
        except Exception as e:
            aggiungi_riga(f"⚠  Avvertimento: impossibile generare grafici: {e}")
            print(f"[Step 17] ⚠  Avvertimento: impossibile generare grafici: {e}")

    # ── SALVATAGGIO ───────────────────────────────────────────────────────────
    doc.save(percorso)
    print(f"[Step 8] Report DOCX salvato in: {percorso}")
    return percorso