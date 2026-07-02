"""
report_pdf.py — generazione report PDF con reportlab + grafici embedded
"""

import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    BaseDocTemplate, Frame, Image, PageTemplate,
    Paragraph, Spacer, Table, TableStyle, HRFlowable,
    PageBreak, KeepTogether,
)

import elaborazioni as el
import grafici as gr

# ─── COLORI TEMA ─────────────────────────────────────────────────────────────
BLU      = colors.HexColor("#2D4A8A")
BLU_CH   = colors.HexColor("#4C72B0")
ROSSO    = colors.HexColor("#C44E52")
GRIGIO   = colors.HexColor("#666666")
GRIGIO_L = colors.HexColor("#F2F4F8")
BIANCO   = colors.white

W, H = A4


# ─── STILI ───────────────────────────────────────────────────────────────────

def _stili():
    s = getSampleStyleSheet()
    extra = {
        "Titolo": ParagraphStyle("Titolo", fontSize=22, textColor=BLU,
                                 spaceAfter=4, fontName="Helvetica-Bold",
                                 alignment=TA_CENTER),
        "Sottotitolo": ParagraphStyle("Sottotitolo", fontSize=11, textColor=GRIGIO,
                                      spaceAfter=12, alignment=TA_CENTER),
        "H2": ParagraphStyle("H2", fontSize=14, textColor=BLU,
                             fontName="Helvetica-Bold", spaceBefore=14, spaceAfter=6),
        "H3": ParagraphStyle("H3", fontSize=11, textColor=BLU_CH,
                             fontName="Helvetica-Bold", spaceBefore=8, spaceAfter=4),
        "Normal2": ParagraphStyle("Normal2", fontSize=9, textColor=colors.black,
                                  spaceAfter=4, leading=13),
        "Kpi": ParagraphStyle("Kpi", fontSize=26, textColor=BLU,
                              fontName="Helvetica-Bold", alignment=TA_CENTER),
        "KpiLabel": ParagraphStyle("KpiLabel", fontSize=9, textColor=GRIGIO,
                                   alignment=TA_CENTER),
        "Footer": ParagraphStyle("Footer", fontSize=7, textColor=GRIGIO,
                                 alignment=TA_RIGHT),
    }
    s.add(extra["Titolo"])
    for k, v in extra.items():
        if k != "Titolo":
            s.add(v)
    return s


def _png_flowable(png_bytes: bytes, width=14*cm) -> Image:
    img = Image(io.BytesIO(png_bytes))
    ratio = img.imageHeight / img.imageWidth
    img.drawWidth  = width
    img.drawHeight = width * ratio
    return img


def _tabella(dati, intestazione, col_w=None) -> Table:
    righe = [intestazione] + dati
    t = Table(righe, colWidths=col_w, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0), BLU),
        ("TEXTCOLOR",   (0, 0), (-1, 0), BIANCO),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [BIANCO, GRIGIO_L]),
        ("GRID",        (0, 0), (-1, -1), 0.3, colors.HexColor("#CCCCCC")),
        ("ALIGN",       (0, 0), (-1, -1), "LEFT"),
        ("TOPPADDING",  (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


# ─── HEADER / FOOTER ─────────────────────────────────────────────────────────

def _header_footer(canvas, doc):
    canvas.saveState()
    # Header bar
    canvas.setFillColor(BLU)
    canvas.rect(0, H - 1.2*cm, W, 1.2*cm, fill=1, stroke=0)
    canvas.setFillColor(BIANCO)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawString(1.5*cm, H - 0.8*cm, "Gestione Studenti — Report")
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(W - 1.5*cm, H - 0.8*cm,
                           datetime.now().strftime("%d/%m/%Y %H:%M"))
    # Footer bar
    canvas.setFillColor(GRIGIO_L)
    canvas.rect(0, 0, W, 1*cm, fill=1, stroke=0)
    canvas.setFillColor(GRIGIO)
    canvas.setFont("Helvetica", 7)
    canvas.drawString(1.5*cm, 0.35*cm, "Dati riservati — uso interno")
    canvas.drawRightString(W - 1.5*cm, 0.35*cm,
                           f"Pagina {doc.page}")
    canvas.restoreState()


# ─── SEZIONE: frontespizio ───────────────────────────────────────────────────

def _frontespizio(story, stili):
    story.append(Spacer(1, 4*cm))
    story.append(Paragraph("Gestione Studenti", stili["Titolo"]))
    story.append(Paragraph("Report Statistico", stili["Sottotitolo"]))
    story.append(HRFlowable(width="80%", thickness=2, color=BLU, spaceAfter=10))
    story.append(Paragraph(
        f"Generato il {datetime.now().strftime('%d/%m/%Y alle %H:%M')}",
        stili["Sottotitolo"]
    ))
    story.append(PageBreak())


# ─── SEZIONE 6.2 ─────────────────────────────────────────────────────────────

def _sezione_media_per_materia(story, stili):
    story.append(Paragraph("Media per materia", stili["H2"]))
    dati = el.medie_per_materia_tutti()
    if not dati:
        story.append(Paragraph("Nessun dato disponibile.", stili["Normal2"]))
        return

    righe = [[d["materia"], f"{d['media']:.2f}", str(d["n_studenti"])]
              for d in dati]
    t = _tabella(righe,
                 ["Materia", "Media voto", "N° studenti"],
                 col_w=[8*cm, 4*cm, 4*cm])
    story.append(t)
    story.append(Spacer(1, 0.5*cm))

    png = gr.grafico_media_per_materia(dati)
    if png:
        story.append(_png_flowable(png))
    story.append(Spacer(1, 0.5*cm))


# ─── SEZIONE 6.7 ─────────────────────────────────────────────────────────────

def _sezione_sufficienti(story, stili, soglia=6.0):
    story.append(Paragraph(
        f"Studenti sufficienti / insufficienti (soglia {soglia})", stili["H2"]))
    ris = el.studenti_sufficienti_insufficienti(soglia)

    n_s = len(ris["sufficienti"])
    n_i = len(ris["insufficienti"])
    tot = n_s + n_i

    # KPI box
    kpi_data = [[
        Paragraph(str(n_s), stili["Kpi"]),
        Paragraph(str(n_i), stili["Kpi"]),
        Paragraph(f"{n_s/tot*100:.0f}%" if tot else "—", stili["Kpi"]),
    ], [
        Paragraph("Sufficienti", stili["KpiLabel"]),
        Paragraph("Insufficienti", stili["KpiLabel"]),
        Paragraph("% Sufficienza", stili["KpiLabel"]),
    ]]
    kpi_t = Table(kpi_data, colWidths=[5.5*cm, 5.5*cm, 5.5*cm])
    kpi_t.setStyle(TableStyle([
        ("BOX",      (0, 0), (0, -1), 1, BLU_CH),
        ("BOX",      (1, 0), (1, -1), 1, ROSSO),
        ("BOX",      (2, 0), (2, -1), 1, GRIGIO),
        ("ALIGN",    (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(KeepTogether([kpi_t, Spacer(1, 0.4*cm)]))

    # Tabelle dettaglio
    for label, lista, colore in [
        ("Sufficienti", ris["sufficienti"], BLU_CH),
        ("Insufficienti", ris["insufficienti"], ROSSO),
    ]:
        story.append(Paragraph(label, stili["H3"]))
        if lista:
            righe = [[d["studente"], f"{d['media']:.2f}"] for d in lista]
            story.append(_tabella(righe, ["Studente", "Media generale"],
                                  col_w=[12*cm, 4*cm]))
        else:
            story.append(Paragraph("Nessuno.", stili["Normal2"]))
        story.append(Spacer(1, 0.3*cm))

    png = gr.grafico_sufficienti_insufficienti(ris)
    if png:
        story.append(_png_flowable(png, width=16*cm))


# ─── SEZIONE 6.1 per una specifica materia+studente ──────────────────────────

def _sezione_media_materia_studente(story, stili, materia: str, id_studente: int,
                                     nome_studente: str):
    story.append(Paragraph(
        f"Media {materia} — {nome_studente}", stili["H2"]))
    media = el.media_materia_studente(materia, id_studente)
    if media is None:
        story.append(Paragraph("Nessun voto registrato.", stili["Normal2"]))
        return
    story.append(Paragraph(
        f"Media: <b>{media:.2f}</b>  {'✔ Sufficiente' if media >= 6 else '✖ Insufficiente'}",
        stili["Normal2"]
    ))
    voti_raw = el.distribuzione_voti_materia(materia)
    png = gr.grafico_distribuzione_voti(voti_raw, materia)
    if png:
        story.append(Spacer(1, 0.3*cm))
        story.append(_png_flowable(png, width=12*cm))


# ─── ENTRY POINT ─────────────────────────────────────────────────────────────

def genera_report_completo(
    output_path: str,
    soglia_sufficienza: float = 6.0,
    materia_focus: str | None = None,
    id_studente_focus: int | None = None,
    nome_studente_focus: str | None = None,
):
    stili = _stili()

    doc = BaseDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=1.5*cm,
        rightMargin=1.5*cm,
        topMargin=1.8*cm,
        bottomMargin=1.5*cm,
    )

    frame = Frame(
        doc.leftMargin, doc.bottomMargin + 1*cm,
        doc.width, doc.height - 1.2*cm,
        id="main",
    )
    template = PageTemplate(id="base", frames=[frame],
                            onPage=_header_footer)
    doc.addPageTemplates([template])

    story = []
    _frontespizio(story, stili)

    if materia_focus and id_studente_focus and nome_studente_focus:
        _sezione_media_materia_studente(
            story, stili, materia_focus, id_studente_focus, nome_studente_focus)
        story.append(PageBreak())

    _sezione_media_per_materia(story, stili)
    story.append(PageBreak())

    _sezione_sufficienti(story, stili, soglia_sufficienza)

    doc.build(story)