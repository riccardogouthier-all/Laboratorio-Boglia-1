"""
main.py — interfaccia grafica (GUI) con tkinter: gestisce studenti,
voti, assenze, materie e la creazione del report in PDF
"""

import os
import re
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from datetime import datetime
import threading
import io

# ── serve per poter importare i file .py che si trovano nella stessa cartella ──
sys.path.insert(0, os.path.dirname(__file__))

import database as db
import importa_file as imp
import elaborazioni as el
import grafici as gr
import report_pdf as rpdf

# ── per mostrare i grafici matplotlib dentro la finestra tkinter ──────────────
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

# ─── COLORI E FONT DELL'APP ───────────────────────────────────────────────────
BLU  = "#2D4A8A"
BLU2 = "#4C72B0"
BG   = "#F4F6FA"
BG2  = "#FFFFFF"
ACCENT = "#DD8452"
TESTO  = "#1A1A2E"
SUCC   = "#27AE60"
ERR    = "#C0392B"

FONT_B = ("Segoe UI", 10, "bold")
FONT   = ("Segoe UI", 9)
FONT_S = ("Segoe UI", 8)
FONT_T = ("Segoe UI", 16, "bold")


# ─────────────────────────────────────────────────────────────────────────────
#  FUNZIONI PER CREARE I WIDGET
# ─────────────────────────────────────────────────────────────────────────────
# Questa parte raccoglie funzioni brevi per creare i widget tkinter più
# usati (etichetta, campo di testo, bottone, tabella, titolo, riga
# separatrice, barra di stato), così ogni finestra dell'app usa sempre
# lo stesso stile grafico (colori, font) senza dover ripetere gli
# stessi parametri decine di volte.

def _label(parent, text, **kw):
    """Crea una tk.Label con lo stile standard dell'app (sfondo BG2,
    testo colore TESTO, font FONT); i parametri passati in kw possono
    sovrascrivere questi valori di default."""
    return tk.Label(parent, text=text, bg=kw.pop("bg", BG2),
                    fg=kw.pop("fg", TESTO), font=kw.pop("font", FONT), **kw)


def _entry(parent, textvariable=None, **kw):
    """Crea un campo di testo (ttk.Entry) collegato a una variabile,
    con il font standard dell'app, per rendere uguali tutti i campi
    di input nei form."""
    e = ttk.Entry(parent, textvariable=textvariable, font=FONT, **kw)
    return e


def _btn(parent, text, cmd, **kw):
    """Crea un bottone (tk.Button) con lo stile standard dell'app
    (sfondo blu di default, testo bianco, bordo piatto, cursore a
    manina), così tutti i bottoni dell'interfaccia sono uguali."""
    bg = kw.pop("bg", BLU2)
    fg = kw.pop("fg", "white")
    b = tk.Button(parent, text=text, command=cmd, bg=bg, fg=fg,
                  font=FONT_B, relief="flat", padx=10, pady=4,
                  activebackground=BLU, activeforeground="white", cursor="hand2",
                  **kw)
    return b


def _tree(parent, cols: list[str], heights=12):
    """Crea una tabella (ttk.Treeview) con le colonne indicate e una
    barra di scorrimento verticale collegata; la larghezza di ogni
    colonna viene stimata in base alla lunghezza del suo titolo.
    Tutte le schede con tabelle (Studenti, Voti, Assenze, Materie)
    usano questa stessa funzione, così sono tutte fatte allo stesso
    modo senza ripetere il codice ogni volta."""
    tv = ttk.Treeview(parent, columns=cols, show="headings", height=heights)
    for c in cols:
        tv.heading(c, text=c)
        tv.column(c, anchor="w", width=max(80, len(c) * 11))
    sb = ttk.Scrollbar(parent, orient="vertical", command=tv.yview)
    tv.configure(yscrollcommand=sb.set)
    return tv, sb


def _titolo(parent, text):
    """Crea un riquadro con un'etichetta in stile "titolo di sezione"
    (sfondo blu, testo bianco, font grande). Nota: è definita ma non
    viene usata direttamente nelle schede attuali (che costruiscono
    la loro intestazione in un altro modo), resta disponibile come
    funzione pronta all'uso per nuove sezioni future."""
    f = tk.Frame(parent, bg=BLU)
    tk.Label(f, text=text, bg=BLU, fg="white",
             font=FONT_T, padx=16, pady=10).pack(side="left")
    return f


def _sep(parent):
    """Crea una riga separatrice orizzontale, usata per dividere
    visivamente gruppi di bottoni (ad esempio tra i report e i
    bottoni per esportare il PDF)."""
    return ttk.Separator(parent, orient="horizontal")


def _status(parent):
    """Crea la barra di stato in fondo alla finestra principale,
    collegata a una variabile di testo condivisa.
    Restituisce sia il widget della barra sia la variabile, così ogni
    scheda può aggiornare il messaggio di stato (es. "12 studenti")
    semplicemente scrivendo dentro quella variabile."""
    sv = tk.StringVar(value="Pronto.")
    bar = tk.Label(parent, textvariable=sv, bg=BLU, fg="white",
                   font=FONT_S, anchor="w", padx=8)
    return bar, sv


# ─────────────────────────────────────────────────────────────────────────────
#  FINESTRA: NUOVO/MODIFICA STUDENTE
# ─────────────────────────────────────────────────────────────────────────────

class DialogStudente(tk.Toplevel):
    """
    Finestra popup per inserire o modificare uno studente.
    Una sola classe gestisce sia il caso "nuovo studente" (dati=None)
    sia il caso "modifica studente" (dati già precompilati), così non
    serve scrivere due volte lo stesso form in due classi diverse. Il
    risultato scelto dall'utente viene salvato in self.risultato, che
    chi ha aperto la finestra legge dopo che è stata chiusa (wait_window).
    """

    def __init__(self, parent, titolo, dati=None):
        """Prepara la finestra popup (grab_set la rende bloccante, cioè
        non si può usare il resto dell'app finché non viene chiusa) e
        costruisce il form, riempito con 'dati' se presenti (caso modifica)."""
        super().__init__(parent)
        self.title(titolo)
        self.configure(bg=BG)
        self.resizable(False, False)
        self.grab_set()
        self.risultato = None

        self._build(dati or {})

    def _build(self, dati):
        """Costruisce i campi del form (nome, cognome, data di
        nascita, email) collegati a variabili di testo, e i bottoni
        Salva/Annulla.
        Separiamo la costruzione grafica dall'__init__ per rendere il
        codice più facile da leggere."""
        pad = dict(padx=12, pady=5)
        _label(self, "Nome *", bg=BG).grid(row=0, column=0, sticky="e", **pad)
        _label(self, "Cognome *", bg=BG).grid(row=1, column=0, sticky="e", **pad)
        _label(self, "Data nascita (YYYY-MM-DD) *", bg=BG).grid(row=2, column=0, sticky="e", **pad)
        _label(self, "Email *", bg=BG).grid(row=3, column=0, sticky="e", **pad)

        self.v_nome  = tk.StringVar(value=dati.get("nome", ""))
        self.v_cogn  = tk.StringVar(value=dati.get("cognome", ""))
        self.v_data  = tk.StringVar(value=dati.get("data_nascita", ""))
        self.v_email = tk.StringVar(value=dati.get("email", ""))

        for r, v in [(0, self.v_nome), (1, self.v_cogn),
                    (2, self.v_data), (3, self.v_email)]:
            _entry(self, v, width=32).grid(row=r, column=1, sticky="ew", **pad)

        f = tk.Frame(self, bg=BG)
        f.grid(row=4, column=0, columnspan=2, pady=10)
        _btn(f, "✔  Salva", self._salva).pack(side="left", padx=6)
        _btn(f, "✖  Annulla", self.destroy, bg=ACCENT).pack(side="left", padx=6)

    def _salva(self):
        """
        Controlla tutti i campi del form (che non siano vuoti, che
        nome e cognome non abbiano numeri o simboli strani, che la
        data sia scritta bene ed esista davvero, che l'email sia
        valida) e, solo se tutto è corretto, salva i dati in
        self.risultato e chiude la finestra.
        Controllare subito nella finestra (prima ancora di chiedere
        al database) permette di far vedere all'utente un messaggio
        di errore chiaro e specifico, invece di un generico errore
        del database dopo che ha già provato a salvare.
        """
        nome  = self.v_nome.get().strip()
        cogn  = self.v_cogn.get().strip()
        data  = self.v_data.get().strip()
        email = self.v_email.get().strip()

        # ── campi obbligatori ────────────────────────────────────────────────
        if not nome:
            messagebox.showerror("Errore", "Il campo 'Nome' è obbligatorio.", parent=self); return
        if not cogn:
            messagebox.showerror("Errore", "Il campo 'Cognome' è obbligatorio.", parent=self); return
        if not data:
            messagebox.showerror("Errore", "Il campo 'Data nascita' è obbligatorio.", parent=self); return
        if not email:
            messagebox.showerror("Errore", "Il campo 'Email' è obbligatorio.", parent=self); return

        # ── nome/cognome: solo lettere, spazi, apostrofo e trattino ─────────
        _nome_re = re.compile(r"^[A-Za-zÀ-ÖØ-öø-ÿ\s'\-]+$")
        if not _nome_re.match(nome):
            messagebox.showerror(
                "Errore",
                "Il Nome non può contenere numeri o caratteri speciali.",
                parent=self
            ); return
        if not _nome_re.match(cogn):
            messagebox.showerror(
                "Errore",
                "Il Cognome non può contenere numeri o caratteri speciali.",
                parent=self
            ); return

        # ── data di nascita: formato YYYY-MM-DD e data che esiste davvero ───
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", data):
            messagebox.showerror(
                "Errore",
                "Data di nascita non valida.\nFormato atteso: YYYY-MM-DD (es. 2001-03-15)",
                parent=self
            ); return
        try:
            from datetime import date as _date
            _date.fromisoformat(data)
        except ValueError:
            messagebox.showerror(
                "Errore",
                f"Data di nascita '{data}' non è una data valida nel calendario.",
                parent=self
            ); return

        # ── email: formato base ──────────────────────────────────────────────
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            messagebox.showerror(
                "Errore",
                f"Email '{email}' non è valida.\nFormato atteso: nome@dominio.ext",
                parent=self
            ); return

        self.risultato = {
            "nome": nome,
            "cognome": cogn,
            "data_nascita": data,
            "email": email,
        }
        self.destroy()


# ─────────────────────────────────────────────────────────────────────────────
#  FINESTRA: NUOVO/MODIFICA VOTO
# ─────────────────────────────────────────────────────────────────────────────

class DialogVoto(tk.Toplevel):
    """
    Finestra popup per inserire o modificare un voto.
    Come DialogStudente, gestisce con un'unica classe sia la
    creazione sia la modifica; riceve già pronte le liste di
    studenti e materie caricate da chi apre la finestra, per riempire
    i menu a tendina senza dover interrogare il database più volte
    per la stessa lista.
    """

    def __init__(self, parent, titolo, studenti, materie, dati=None):
        """Prepara la finestra popup salvando le liste di studenti e
        materie disponibili, e costruisce il form."""
        super().__init__(parent)
        self.title(titolo)
        self.configure(bg=BG)
        self.resizable(False, False)
        self.grab_set()
        self.risultato = None

        self._studenti = studenti
        self._materie  = materie
        self._build(dati or {})

    def _build(self, dati):
        """Costruisce i campi del form: menu a tendina per lo
        studente (si può anche scrivere, con l'elenco "id — cognome
        nome"), menu a tendina per la materia (solo scelta tra quelle
        esistenti) e campo di testo per il voto. Se 'dati' contiene
        già un voto, riempie i menu con la scelta corrispondente."""
        pad = dict(padx=12, pady=5)
        _label(self, "Studente *", bg=BG).grid(row=0, column=0, sticky="e", **pad)
        _label(self, "Materia *",  bg=BG).grid(row=1, column=0, sticky="e", **pad)
        _label(self, "Voto (0-10) *", bg=BG).grid(row=2, column=0, sticky="e", **pad)

        nomi_stud = [f"{s['id']} — {s['cognome']} {s['nome']}" for s in self._studenti]
        self.cb_stud = ttk.Combobox(self, values=nomi_stud, width=30, font=FONT)
        self.cb_stud.grid(row=0, column=1, sticky="ew", **pad)
        if dati.get("id_studente"):
            for i, s in enumerate(self._studenti):
                if s["id"] == dati["id_studente"]:
                    self.cb_stud.current(i)

        self.cb_mat = ttk.Combobox(self, values=self._materie, width=30, font=FONT,
                                   state="readonly")
        self.cb_mat.grid(row=1, column=1, sticky="ew", **pad)
        if dati.get("materia"):
            if dati["materia"] in self._materie:
                self.cb_mat.set(dati["materia"])

        self.v_voto = tk.StringVar(value=str(dati.get("voto", "")))
        _entry(self, self.v_voto, width=12).grid(row=2, column=1, sticky="w", **pad)

        f = tk.Frame(self, bg=BG)
        f.grid(row=3, column=0, columnspan=2, pady=10)
        _btn(f, "✔  Salva", self._salva).pack(side="left", padx=6)
        _btn(f, "✖  Annulla", self.destroy, bg=ACCENT).pack(side="left", padx=6)

    def _salva(self):
        """
        Controlla la scelta fatta (studente selezionato, materia tra
        quelle esistenti, voto numerico tra 0 e 10) e, se tutto è
        corretto, salva i dati in self.risultato e chiude la finestra.
        Il controllo sul voto (0-10) rispecchia il vincolo scritto
        nel database, così l'errore si vede subito ed è chiaro; se la
        materia non esiste ancora, viene detto all'utente di crearla
        prima nella scheda Materie.
        """
        idx = self.cb_stud.current()
        if idx < 0:
            messagebox.showerror("Errore", "Seleziona uno studente.", parent=self); return
        materia = self.cb_mat.get().strip()
        if not materia:
            messagebox.showerror("Errore", "Seleziona una materia dall'elenco.", parent=self); return
        if materia not in self._materie:
            messagebox.showerror(
                "Errore",
                f"La materia '{materia}' non esiste.\n"
                "Aggiungila prima nella scheda 'Materie'.",
                parent=self
            ); return
        try:
            voto = float(self.v_voto.get().replace(",", "."))
            assert 0 <= voto <= 10
        except (ValueError, AssertionError):
            messagebox.showerror("Errore", "Voto deve essere un numero tra 0 e 10.", parent=self); return

        self.risultato = {
            "id_studente": self._studenti[idx]["id"],
            "materia": materia,
            "voto": voto,
        }
        self.destroy()


# ─────────────────────────────────────────────────────────────────────────────
#  FINESTRA: NUOVA/MODIFICA ASSENZA
# ─────────────────────────────────────────────────────────────────────────────

class DialogAssenza(tk.Toplevel):
    """
    Finestra popup per inserire o modificare un'assenza.
    Stesso schema di DialogStudente/DialogVoto applicato alle
    assenze, per tenere il codice e l'esperienza d'uso coerenti in
    tutta l'app.
    """

    def __init__(self, parent, titolo, studenti, dati=None):
        """Prepara la finestra popup salvando la lista di studenti
        disponibili, e costruisce il form."""
        super().__init__(parent)
        self.title(titolo)
        self.configure(bg=BG)
        self.resizable(False, False)
        self.grab_set()
        self.risultato = None
        self._studenti = studenti
        self._build(dati or {})

    def _build(self, dati):
        """Costruisce i campi del form: menu a tendina studente e
        campo data, già riempito con la data di oggi se non viene
        specificato altro (caso tipico "nuova assenza": oggi)."""
        pad = dict(padx=12, pady=5)
        _label(self, "Studente *", bg=BG).grid(row=0, column=0, sticky="e", **pad)
        _label(self, "Data (YYYY-MM-DD) *", bg=BG).grid(row=1, column=0, sticky="e", **pad)

        nomi = [f"{s['id']} — {s['cognome']} {s['nome']}" for s in self._studenti]
        self.cb_stud = ttk.Combobox(self, values=nomi, width=30, font=FONT)
        self.cb_stud.grid(row=0, column=1, sticky="ew", **pad)
        if dati.get("id_studente"):
            for i, s in enumerate(self._studenti):
                if s["id"] == dati["id_studente"]:
                    self.cb_stud.current(i)

        self.v_data = tk.StringVar(value=dati.get("data", datetime.now().strftime("%Y-%m-%d")))
        _entry(self, self.v_data, width=14).grid(row=1, column=1, sticky="w", **pad)

        f = tk.Frame(self, bg=BG)
        f.grid(row=2, column=0, columnspan=2, pady=10)
        _btn(f, "✔  Salva", self._salva).pack(side="left", padx=6)
        _btn(f, "✖  Annulla", self.destroy, bg=ACCENT).pack(side="left", padx=6)

    def _salva(self):
        """
        Controlla la scelta fatta (studente selezionato, data scritta
        come YYYY-MM-DD) e, se corretta, salva i dati in
        self.risultato e chiude la finestra.
        Il controllo sul formato della data avviene qui, prima che i
        dati arrivino al database, dove invece il controllo sui
        doppioni (stesso studente + stessa data) è già gestito dal
        vincolo UNIQUE.
        """
        idx = self.cb_stud.current()
        if idx < 0:
            messagebox.showerror("Errore", "Seleziona uno studente.", parent=self); return
        data = self.v_data.get().strip()
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", data):
            messagebox.showerror("Errore", "Data non valida. Formato: YYYY-MM-DD", parent=self); return
        self.risultato = {
            "id_studente": self._studenti[idx]["id"],
            "data": data,
        }
        self.destroy()


# ─────────────────────────────────────────────────────────────────────────────
#  SCHEDA: STUDENTI
# ─────────────────────────────────────────────────────────────────────────────

class TabStudenti(tk.Frame):
    """
    Scheda dell'app dedicata all'anagrafica degli studenti: elenco
    con ricerca in tempo reale, e operazioni per creare, modificare
    ed eliminare uno studente.
    Tenere tutto il codice sugli studenti in questa classe permette
    di lasciare la classe App (la finestra principale) semplice, con
    il solo compito di gestire le varie schede.
    """

    def __init__(self, parent, status_var):
        """Prepara la scheda, costruisce i widget e carica subito
        l'elenco degli studenti dal database."""
        super().__init__(parent, bg=BG)
        self._sv = status_var
        self._build()
        self.aggiorna()

    def _build(self):
        """Costruisce la barra dei bottoni (Nuovo/Modifica/Elimina/
        Aggiorna), il campo di ricerca in tempo reale e la tabella
        con le colonne anagrafiche."""
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=10, pady=6)
        _btn(top, "➕ Nuovo",   self._nuovo).pack(side="left", padx=4)
        _btn(top, "✏  Modifica", self._modifica).pack(side="left", padx=4)
        _btn(top, "🗑  Elimina", self._elimina, bg=ERR).pack(side="left", padx=4)
        _btn(top, "🔄 Aggiorna", self.aggiorna, bg=BLU).pack(side="right", padx=4)

        # Ricerca
        frk = tk.Frame(self, bg=BG)
        frk.pack(fill="x", padx=10)
        _label(frk, "Cerca:").pack(side="left")
        self.v_cerca = tk.StringVar()
        self._debounce_id = None
        self.v_cerca.trace_add("write", lambda *_: self._cerca_debounced())
        _entry(frk, self.v_cerca, width=28).pack(side="left", padx=6)

        # Tabella
        frm = tk.Frame(self, bg=BG)
        frm.pack(fill="both", expand=True, padx=10, pady=4)
        self.tv, sb = _tree(frm, ["ID", "Cognome", "Nome", "Data Nascita", "Email"])
        self.tv.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

    def _cerca_debounced(self, ritardo_ms: int = 250):
        """Aspetta che l'utente smetta di scrivere per ritardo_ms
        millisecondi prima di lanciare davvero la ricerca, così non
        facciamo una query al database a ogni singolo carattere
        digitato (utile soprattutto con tanti dati)."""
        if self._debounce_id is not None:
            self.after_cancel(self._debounce_id)
        self._debounce_id = self.after(ritardo_ms, self.aggiorna)

    def aggiorna(self, *_):
        """
        Ricarica la tabella con l'elenco studenti aggiornato: se c'è
        del testo nel campo di ricerca applica il filtro
        (db.cerca_studente), altrimenti mostra tutti gli studenti.
        Questa è l'unica funzione che aggiorna la tabella, ed è
        chiamata sia dal bottone "Aggiorna" sia dopo ogni operazione
        di scrittura (nuovo/modifica/elimina) sia dalla ricerca, per
        avere sempre la tabella allineata con il database.
        """
        self._debounce_id = None
        self.tv.delete(*self.tv.get_children())
        q = self.v_cerca.get().strip()
        rows = db.cerca_studente(q) if q else db.get_tutti_studenti()
        for r in rows:
            self.tv.insert("", "end",
                           values=(r["id"], r["cognome"], r["nome"],
                                   r["data_nascita"], r["email"]))
        self._sv.set(f"{len(rows)} studenti")

    def _sel_id(self):
        """Restituisce l'id dello studente selezionato nella tabella,
        oppure None (mostrando un avviso) se non è selezionato niente.
        Questa funzione è usata sia da modifica sia da elimina, per
        non ripetere due volte lo stesso controllo."""
        sel = self.tv.selection()
        if not sel:
            messagebox.showinfo("Info", "Seleziona uno studente.")
            return None
        return self.tv.item(sel[0])["values"][0]

    def _nuovo(self):
        """Apre la finestra per inserire un nuovo studente e, se
        l'utente conferma con dati corretti, lo salva nel database e
        aggiorna la tabella. Un eventuale errore del database (per
        esempio un'email duplicata sfuggita al controllo della
        finestra) viene mostrato in un messaggio."""
        d = DialogStudente(self, "Nuovo studente")
        self.wait_window(d)
        if d.risultato:
            try:
                db.inserisci_studente(**d.risultato)
                self.aggiorna()
                self._sv.set("Studente inserito.")
            except Exception as e:
                messagebox.showerror("Errore DB", str(e))

    def _modifica(self):
        """Apre la finestra di modifica già riempita con i dati dello
        studente selezionato, e salva le modifiche se confermate."""
        sid = self._sel_id()
        if sid is None: return
        s = db.get_studente(sid)
        d = DialogStudente(self, "Modifica studente", dict(s))
        self.wait_window(d)
        if d.risultato:
            try:
                db.modifica_studente(sid, **d.risultato)
                self.aggiorna()
                self._sv.set("Studente aggiornato.")
            except Exception as e:
                messagebox.showerror("Errore DB", str(e))

    def _elimina(self):
        """Chiede conferma (avvisando che verranno cancellati anche
        voti e assenze collegati) e, se confermato, cancella lo
        studente selezionato."""
        sid = self._sel_id()
        if sid is None: return
        if messagebox.askyesno("Conferma", f"Eliminare studente ID {sid}?\n"
                               "(Voti e assenze associati saranno eliminati)"):
            db.cancella_studente(sid)
            self.aggiorna()
            self._sv.set("Studente eliminato.")


# ─────────────────────────────────────────────────────────────────────────────
#  SCHEDA: VOTI
# ─────────────────────────────────────────────────────────────────────────────

class TabVoti(tk.Frame):
    """
    Scheda dedicata alla gestione dei voti: elenco (con già scritto
    il nome dello studente) e operazioni per creare, modificare ed
    eliminare un voto.
    Stessa idea di TabStudenti: tutto il codice sui voti sta qui.
    """

    def __init__(self, parent, status_var):
        """Prepara la scheda, costruisce i widget e carica l'elenco
        dei voti dal database."""
        super().__init__(parent, bg=BG)
        self._sv = status_var
        self._build()
        self.aggiorna()

    def _build(self):
        """Costruisce la barra dei bottoni e la tabella dei voti
        (ID, Studente, Materia, Voto)."""
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=10, pady=6)
        _btn(top, "➕ Nuovo",    self._nuovo).pack(side="left", padx=4)
        _btn(top, "✏  Modifica", self._modifica).pack(side="left", padx=4)
        _btn(top, "🗑  Elimina", self._elimina, bg=ERR).pack(side="left", padx=4)
        _btn(top, "🔄 Aggiorna", self.aggiorna, bg=BLU).pack(side="right", padx=4)

        frm = tk.Frame(self, bg=BG)
        frm.pack(fill="both", expand=True, padx=10, pady=4)
        self.tv, sb = _tree(frm, ["ID", "Studente", "Materia", "Voto"])
        self.tv.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

    def aggiorna(self):
        """Ricarica la tabella con tutti i voti presenti nel database
        (già uniti al nome dello studente dalla query)."""
        self.tv.delete(*self.tv.get_children())
        rows = db.get_tutti_voti()
        for r in rows:
            self.tv.insert("", "end",
                           values=(r["id"], r["studente"], r["materia"], r["voto"]))
        self._sv.set(f"{len(rows)} voti")

    def _sel_id(self):
        """Restituisce l'id del voto selezionato nella tabella,
        oppure None con un avviso se non è selezionato niente."""
        sel = self.tv.selection()
        if not sel:
            messagebox.showinfo("Info", "Seleziona un voto.")
            return None
        return self.tv.item(sel[0])["values"][0]

    def _nuovo(self):
        """Apre la finestra per inserire un nuovo voto, controllando
        prima che esistano almeno uno studente e una materia
        (altrimenti i menu a tendina sarebbero vuoti e inutilizzabili),
        e salva il voto se confermato."""
        studenti = db.get_tutti_studenti()
        materie  = db.get_nomi_materie()
        if not studenti:
            messagebox.showinfo("Info", "Nessuno studente. Inseriscine uno prima."); return
        if not materie:
            messagebox.showinfo("Info", "Nessuna materia. Inseriscine una prima."); return
        d = DialogVoto(self, "Nuovo voto", studenti, materie)
        self.wait_window(d)
        if d.risultato:
            try:
                db.inserisci_voto(**d.risultato)
                self.aggiorna()
                self._sv.set("Voto inserito.")
            except Exception as e:
                messagebox.showerror("Errore DB", str(e))

    def _modifica(self):
        """Recupera il voto direttamente dal database (con una query
        diretta, perché get_tutti_voti restituisce solo la versione
        già pronta per la tabella) e apre la finestra di modifica
        già riempita con i suoi dati."""
        vid = self._sel_id()
        if vid is None: return
        with db.get_conn() as conn:
            row = conn.execute("SELECT * FROM voti WHERE id=?", (vid,)).fetchone()
        if not row: return
        studenti = db.get_tutti_studenti()
        materie  = db.get_nomi_materie()
        d = DialogVoto(self, "Modifica voto", studenti, materie, dict(row))
        self.wait_window(d)
        if d.risultato:
            try:
                db.modifica_voto(vid, **d.risultato)
                self.aggiorna()
                self._sv.set("Voto aggiornato.")
            except Exception as e:
                messagebox.showerror("Errore DB", str(e))

    def _elimina(self):
        """Chiede conferma e cancella il voto selezionato."""
        vid = self._sel_id()
        if vid is None: return
        if messagebox.askyesno("Conferma", f"Eliminare voto ID {vid}?"):
            db.cancella_voto(vid)
            self.aggiorna()
            self._sv.set("Voto eliminato.")


# ─────────────────────────────────────────────────────────────────────────────
#  SCHEDA: ASSENZE
# ─────────────────────────────────────────────────────────────────────────────

class TabAssenze(tk.Frame):
    """
    Scheda dedicata alla gestione delle assenze: elenco (le più
    recenti per prime) e operazioni per creare, modificare ed
    eliminare un'assenza.
    Stessa idea delle altre schede: tutto il codice sulle assenze
    sta in questa classe.
    """

    def __init__(self, parent, status_var):
        """Prepara la scheda, costruisce i widget e carica l'elenco
        delle assenze dal database."""
        super().__init__(parent, bg=BG)
        self._sv = status_var
        self._build()
        self.aggiorna()

    def _build(self):
        """Costruisce la barra dei bottoni e la tabella delle assenze
        (ID, Studente, Data)."""
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=10, pady=6)
        _btn(top, "➕ Nuova",    self._nuovo).pack(side="left", padx=4)
        _btn(top, "✏  Modifica", self._modifica).pack(side="left", padx=4)
        _btn(top, "🗑  Elimina", self._elimina, bg=ERR).pack(side="left", padx=4)
        _btn(top, "🔄 Aggiorna", self.aggiorna, bg=BLU).pack(side="right", padx=4)

        frm = tk.Frame(self, bg=BG)
        frm.pack(fill="both", expand=True, padx=10, pady=4)
        self.tv, sb = _tree(frm, ["ID", "Studente", "Data"])
        self.tv.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

    def aggiorna(self):
        """Ricarica la tabella con tutte le assenze presenti nel database."""
        self.tv.delete(*self.tv.get_children())
        rows = db.get_tutte_assenze()
        for r in rows:
            self.tv.insert("", "end", values=(r["id"], r["studente"], r["data"]))
        self._sv.set(f"{len(rows)} assenze")

    def _sel_id(self):
        """Restituisce l'id dell'assenza selezionata nella tabella,
        oppure None con un avviso se non è selezionato niente."""
        sel = self.tv.selection()
        if not sel:
            messagebox.showinfo("Info", "Seleziona un'assenza."); return None
        return self.tv.item(sel[0])["values"][0]

    def _nuovo(self):
        """Apre la finestra per inserire una nuova assenza
        (controllando prima che esista almeno uno studente) e la
        salva se confermata."""
        studenti = db.get_tutti_studenti()
        if not studenti:
            messagebox.showinfo("Info", "Nessuno studente."); return
        d = DialogAssenza(self, "Nuova assenza", studenti)
        self.wait_window(d)
        if d.risultato:
            try:
                db.inserisci_assenza(**d.risultato)
                self.aggiorna()
                self._sv.set("Assenza inserita.")
            except Exception as e:
                messagebox.showerror("Errore DB", str(e))

    def _modifica(self):
        """Recupera l'assenza direttamente dal database e apre la
        finestra di modifica già riempita con i suoi dati."""
        aid = self._sel_id()
        if aid is None: return
        with db.get_conn() as conn:
            row = conn.execute("SELECT * FROM assenze WHERE id=?", (aid,)).fetchone()
        studenti = db.get_tutti_studenti()
        d = DialogAssenza(self, "Modifica assenza", studenti, dict(row))
        self.wait_window(d)
        if d.risultato:
            try:
                db.modifica_assenza(aid, **d.risultato)
                self.aggiorna()
                self._sv.set("Assenza aggiornata.")
            except Exception as e:
                messagebox.showerror("Errore DB", str(e))

    def _elimina(self):
        """Chiede conferma e cancella l'assenza selezionata."""
        aid = self._sel_id()
        if aid is None: return
        if messagebox.askyesno("Conferma", f"Eliminare assenza ID {aid}?"):
            db.cancella_assenza(aid)
            self.aggiorna()
            self._sv.set("Assenza eliminata.")


# ─────────────────────────────────────────────────────────────────────────────
#  SCHEDA: MATERIE
# ─────────────────────────────────────────────────────────────────────────────

class TabMaterie(tk.Frame):
    """
    Scheda dedicata alla gestione delle materie: elenco e operazioni
    per creare, modificare ed eliminare una materia.
    Le materie sono gestite come dati a sé stanti (non solo come
    testo scritto dentro i voti), così i menu a tendina che
    mostrano le materie sono sempre coerenti in tutta l'app.
    """

    def __init__(self, parent, status_var):
        """Prepara la scheda, costruisce i widget e carica l'elenco
        delle materie dal database."""
        super().__init__(parent, bg=BG)
        self._sv = status_var
        self._build()
        self.aggiorna()

    def _build(self):
        """Costruisce la barra dei bottoni e la tabella delle materie
        (ID, Nome)."""
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=10, pady=6)
        _btn(top, "➕ Nuova",    self._nuovo).pack(side="left", padx=4)
        _btn(top, "✏  Modifica", self._modifica).pack(side="left", padx=4)
        _btn(top, "🗑  Elimina", self._elimina, bg=ERR).pack(side="left", padx=4)
        _btn(top, "🔄 Aggiorna", self.aggiorna, bg=BLU).pack(side="right", padx=4)

        frm = tk.Frame(self, bg=BG)
        frm.pack(fill="both", expand=True, padx=10, pady=4)
        self.tv, sb = _tree(frm, ["ID", "Nome"])
        self.tv.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

    def aggiorna(self):
        """Ricarica la tabella con tutte le materie presenti nel database."""
        self.tv.delete(*self.tv.get_children())
        rows = db.get_tutte_materie()
        for r in rows:
            self.tv.insert("", "end", values=(r["id"], r["nome"]))
        self._sv.set(f"{len(rows)} materie")

    def _sel(self):
        """Restituisce (id, nome) della materia selezionata nella
        tabella, oppure (None, None) con un avviso se non è
        selezionato niente.
        A differenza delle altre schede, qui serve anche il nome
        (non solo l'id) per riempire la finestra di modifica con
        simpledialog.askstring."""
        sel = self.tv.selection()
        if not sel:
            messagebox.showinfo("Info", "Seleziona una materia."); return None, None
        v = self.tv.item(sel[0])["values"]
        return v[0], v[1]

    def _nuovo(self):
        """Chiede il nome della nuova materia con una semplice
        finestra di dialogo (basta un solo campo, non serve un form
        completo) e la inserisce nel database."""
        nome = simpledialog.askstring("Nuova materia", "Nome materia:", parent=self)
        if nome and nome.strip():
            try:
                db.inserisci_materia(nome.strip())
                self.aggiorna()
                self._sv.set("Materia inserita.")
            except Exception as e:
                messagebox.showerror("Errore DB", str(e))

    def _modifica(self):
        """Chiede il nuovo nome (già scritto quello attuale) per la
        materia selezionata e lo aggiorna nel database."""
        mid, mnome = self._sel()
        if mid is None: return
        nuovo = simpledialog.askstring("Modifica materia", "Nuovo nome:", initialvalue=mnome,
                                       parent=self)
        if nuovo and nuovo.strip():
            try:
                db.modifica_materia(mid, nuovo.strip())
                self.aggiorna()
                self._sv.set("Materia aggiornata.")
            except Exception as e:
                messagebox.showerror("Errore DB", str(e))

    def _elimina(self):
        """Chiede conferma (avvisando che anche i voti collegati alla
        materia verranno cancellati, come gestito in
        db.cancella_materia) e cancella la materia selezionata."""
        mid, mnome = self._sel()
        if mid is None: return
        if messagebox.askyesno("Conferma", f"Eliminare la materia '{mnome}'?\n"
                               "(Tutti i voti associati a questa materia saranno eliminati)"):
            db.cancella_materia(mid)
            self.aggiorna()
            self._sv.set("Materia eliminata.")


# ─────────────────────────────────────────────────────────────────────────────
#  SCHEDA: IMPORTAZIONE FILE
# ─────────────────────────────────────────────────────────────────────────────

class TabImport(tk.Frame):
    """
    Scheda dedicata a importare tanti dati insieme da file CSV
    (studenti, voti, assenze), con un log di testo che mostra il
    risultato.
    Questa scheda è separata da quelle di gestione (Studenti, Voti,
    ecc.) per dare all'utente uno strumento dedicato quando deve
    caricare tanti dati insieme (per esempio l'importazione iniziale
    di tutta la classe), senza doverli inserire uno alla volta a mano.
    """

    def __init__(self, parent, status_var):
        """Prepara la scheda e costruisce i widget (non carica niente
        all'avvio: la scheda parte vuota finché l'utente non sceglie
        e importa dei file)."""
        super().__init__(parent, bg=BG)
        self._sv = status_var
        self._build()

    def _build(self):
        """Costruisce, per ogni tipo di file (studenti/voti/assenze),
        una riga con il percorso del file e un bottone per scegliere
        il file, il bottone per avviare l'importazione e un'area di
        testo in stile console per mostrare il risultato e gli
        eventuali errori riga per riga."""
        tk.Label(self, text="Importazione file CSV", font=FONT_T,
                 bg=BG, fg=BLU).pack(pady=12)

        frg = tk.LabelFrame(self, text="File da importare", bg=BG, font=FONT_B, fg=BLU,
                             padx=10, pady=8)
        frg.pack(fill="x", padx=16, pady=4)

        self._paths = {}
        for tipo, label in [("studenti", "Studenti (CSV)"),
                             ("voti",    "Voti (CSV)"),
                             ("assenze", "Assenze (CSV)")]:
            row = tk.Frame(frg, bg=BG)
            row.pack(fill="x", pady=3)
            _label(row, f"{label}:", width=18, anchor="e").pack(side="left")
            sv = tk.StringVar()
            self._paths[tipo] = sv
            _entry(row, sv, width=38).pack(side="left", padx=6)
            _btn(row, "📂", lambda t=tipo: self._scegli(t), bg=BLU).pack(side="left")

        btns = tk.Frame(self, bg=BG)
        btns.pack(pady=12)
        _btn(btns, "▶  Importa selezionati", self._importa).pack(side="left", padx=8)

        # Log
        frlog = tk.LabelFrame(self, text="Log importazione", bg=BG, font=FONT_B, fg=BLU,
                               padx=6, pady=6)
        frlog.pack(fill="both", expand=True, padx=16, pady=4)
        self.log = tk.Text(frlog, height=12, font=FONT_S, bg="#1E1E2E", fg="#EEEEEE",
                           relief="flat", wrap="word")
        sb = ttk.Scrollbar(frlog, command=self.log.yview)
        self.log.configure(yscrollcommand=sb.set)
        self.log.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

    def _scegli(self, tipo):
        """Apre la finestra di sistema per scegliere un file CSV e
        salva il percorso scelto nella variabile giusta, in base al
        tipo di file (studenti/voti/assenze)."""
        p = filedialog.askopenfilename(filetypes=[("CSV", "*.csv"), ("Tutti", "*")])
        if p:
            self._paths[tipo].set(p)

    def _importa(self):
        """
        Per ogni tipo di file che ha un percorso impostato, chiama la
        funzione di importazione giusta (in importa_file.py) e
        scrive nel log il riepilogo (inseriti/ignorati) e gli
        eventuali errori riga per riga.
        Questo è l'unico punto da cui parte l'importazione: usa una
        mappa tipo→funzione invece di scrivere tanti if/elif uguali,
        così in futuro è facile aggiungere un nuovo tipo di file da
        importare.
        """
        self.log.delete("1.0", "end")
        fn_map = {"studenti": imp.importa_studenti,
                  "voti":    imp.importa_voti,
                  "assenze": imp.importa_assenze}
        for tipo, fn in fn_map.items():
            path = self._paths[tipo].get().strip()
            if not path:
                continue
            res = fn(path)
            self.log.insert("end", f"=== {tipo.upper()} ===\n")
            self.log.insert("end", f"  Inseriti: {res.inseriti}  |  Ignorati: {res.ignorati}\n")
            if res.errori:
                self.log.insert("end", "  ERRORI:\n")
                for e in res.errori:
                    self.log.insert("end", f"    • {e}\n")
            self.log.insert("end", "\n")
        self._sv.set("Importazione completata.")


# ─────────────────────────────────────────────────────────────────────────────
#  SCHEDA: REPORT / GRAFICI
# ─────────────────────────────────────────────────────────────────────────────

class TabReport(tk.Frame):
    """
    Scheda dedicata ai report: bottoni per generare ogni grafico
    statistico su richiesta (mostrato direttamente nella scheda) e
    per esportare il report PDF completo, con o senza filtri.
    Mette insieme in un solo pannello tutte le funzioni di analisi
    (elaborazioni.py + grafici.py + report_pdf.py), separando "vedere
    a schermo" (grafici interattivi con Tkinter/matplotlib) da
    "esportare" (creare un PDF da salvare e condividere).
    """

    def __init__(self, parent, status_var):
        """Prepara la scheda e costruisce il pannello con i comandi e
        l'area dove vengono mostrati i grafici."""
        super().__init__(parent, bg=BG)
        self._sv = status_var
        self._build()

    def _build(self):
        """Costruisce il layout a due colonne: a sinistra i bottoni
        per i singoli report/grafici e per l'esportazione PDF, a
        destra il riquadro dove viene disegnato il grafico richiesto
        (self._canvas_frame)."""
        left = tk.Frame(self, bg=BG, width=260)
        left.pack(side="left", fill="y", padx=0)
        left.pack_propagate(False)

        tk.Label(left, text="Analisi", font=FONT_T, bg=BLU, fg="white",
                 padx=8, pady=8).pack(fill="x")

        self._canvas_frame = tk.Frame(self, bg=BG2)
        self._canvas_frame.pack(side="right", fill="both", expand=True)

        pad = dict(fill="x", padx=8, pady=3)
        reports = [
            ("Media materia per studente", self._r61),
            ("Media per materia",          self._r62),
            ("Assenti in un giorno",       self._r64),
            ("Studenti per materia",       self._r65),
            ("Sufficienti/Insufficienti",  self._r67),
            ("Istogrammi per materia",     self._r_istogrammi),
        ]
        for label, cmd in reports:
            _btn(left, label, cmd, bg=BLU2).pack(**pad)

        _sep(left).pack(fill="x", pady=6, padx=8)
        _btn(left, "📄 Esporta PDF completo", self._esporta_pdf, bg=ACCENT).pack(**pad)
        _btn(left, "📄 PDF con filtri attuali", self._esporta_pdf_focus, bg=ACCENT).pack(**pad)

    def _clear_canvas(self):
        """Distrugge tutti i widget presenti nell'area del grafico,
        per fare spazio a una nuova visualizzazione.
        Serve per evitare che i grafici vecchi restino sovrapposti a
        ogni nuova richiesta di report."""
        for w in self._canvas_frame.winfo_children():
            w.destroy()

    def _mostra_png(self, png_bytes: bytes | None, titolo=""):
        """
        Mostra un'immagine PNG (byte tenuti in memoria) dentro la
        scheda usando un canvas matplotlib (FigureCanvasTkAgg),
        oppure un messaggio "nessun dato" se png_bytes è None.
        I grafici creati da grafici.py sono già byte PNG in memoria
        (pensati per essere riusati anche nel PDF): questa funzione
        li fa vedere nella finestra senza doverli scrivere su disco,
        semplicemente leggendoli con plt.imread e disegnandoli in un
        nuovo canvas dentro il riquadro.
        """
        self._clear_canvas()
        if not png_bytes:
            tk.Label(self._canvas_frame, text="Nessun dato da visualizzare.",
                     bg=BG2, font=FONT).pack(expand=True)
            return
        img = plt.imread(io.BytesIO(png_bytes))
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.imshow(img)
        ax.axis("off")
        canvas = FigureCanvasTkAgg(fig, master=self._canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    # ── 6.1 ──
    def _r61(self):
        """
        Apre una finestra con due menu a tendina (materia, studente)
        e un bottone "Calcola" che mostra a schermo la media dello
        studente scelto nella materia scelta.
        Realizza a schermo la richiesta 6.1; a differenza degli altri
        report, qui il calcolo dipende da due scelte fatte
        dall'utente, quindi serve un piccolo form dedicato invece di
        un bottone diretto.
        """
        materie  = db.get_nomi_materie()
        studenti = db.get_tutti_studenti()
        if not materie or not studenti:
            messagebox.showinfo("Info", "Dati insufficienti."); return

        w = tk.Toplevel(self)
        w.title("— Media materia per studente")
        w.configure(bg=BG)
        w.grab_set()

        tk.Label(w, text="Materia:", bg=BG, font=FONT).grid(row=0, column=0, padx=8, pady=6)
        cb_mat = ttk.Combobox(w, values=materie, width=20, font=FONT)
        cb_mat.grid(row=0, column=1, padx=8)

        nomi_s = [f"{s['id']} — {s['cognome']} {s['nome']}" for s in studenti]
        tk.Label(w, text="Studente:", bg=BG, font=FONT).grid(row=1, column=0, padx=8, pady=6)
        cb_stu = ttk.Combobox(w, values=nomi_s, width=28, font=FONT)
        cb_stu.grid(row=1, column=1, padx=8)

        res_var = tk.StringVar(value="—")
        tk.Label(w, textvariable=res_var, bg=BG, font=("Segoe UI", 14, "bold"),
                 fg=BLU).grid(row=2, column=0, columnspan=2, pady=8)

        def calcola():
            """Legge cosa è stato scelto nei due menu a tendina,
            calcola la media con elaborazioni.media_materia_studente
            e aggiorna l'etichetta del risultato (oppure scrive
            "Nessun voto." se non c'è nessun dato)."""
            if cb_mat.current() < 0 or cb_stu.current() < 0:
                return
            mat  = cb_mat.get()
            sid  = studenti[cb_stu.current()]["id"]
            m = el.media_materia_studente(mat, sid)
            if m is None:
                res_var.set("Nessun voto.")
            else:
                tag = "✔ Sufficiente" if m >= 6 else "✖ Insufficiente"
                res_var.set(f"Media: {m:.2f}  {tag}")

        _btn(w, "Calcola", calcola).grid(row=3, column=0, columnspan=2, pady=8)

    # ── 6.2 ──
    def _r62(self):
        """Calcola la media di ogni materia e mostra il grafico a
        barre corrispondente nell'area dedicata. Realizza a schermo
        la richiesta 6.2."""
        dati = el.medie_per_materia_tutti()
        if not dati:
            messagebox.showinfo("Info", "Nessun voto registrato."); return
        png = gr.grafico_media_per_materia(dati)
        self._mostra_png(png, "Media per materia")
        self._sv.set("Media per materia completata.")

    # ── 6.4 ──
    def _r64(self):
        """Chiede una data all'utente (già scritta la data di oggi),
        calcola gli assenti in quel giorno e mostra il grafico a
        torta presenti/assenti. Realizza a schermo la richiesta 6.4."""
        data = simpledialog.askstring("Assenti in un giorno", "Data (YYYY-MM-DD):",
                                      initialvalue=datetime.now().strftime("%Y-%m-%d"),
                                      parent=self)
        if not data: return
        assenti = el.studenti_assenti_giorno(data)
        tot = len(db.get_tutti_studenti())
        png = gr.grafico_assenti_giorno(assenti, data, tot)
        self._mostra_png(png, f"Assenti {data}")
        self._sv.set(f"Assenti in un giorno: {len(assenti)} assenti il {data}.")

    # ── 6.5 ──
    def _r65(self):
        """Chiede il nome di una materia e mostra (in un messaggio,
        non con un grafico) il numero di studenti valutati in quella
        materia. Realizza la richiesta 6.5, che essendo un solo
        numero non ha bisogno di un grafico apposta."""
        materie = db.get_nomi_materie()
        if not materie:
            messagebox.showinfo("Info", "Nessuna materia."); return
        mat = simpledialog.askstring("Studenti per materia", "Materia:", parent=self)
        if not mat: return
        n = el.num_studenti_per_materia(mat)
        messagebox.showinfo("Studenti per materia", f"Studenti iscritti a '{mat}': {n}")
        self._sv.set(f"Studenti per materia: {n} studenti in {mat}.")

    # ── 6.7 ──
    def _r67(self):
        """Calcola la divisione tra sufficienti e insufficienti e
        mostra il grafico a torta corrispondente. Realizza a schermo
        la richiesta 6.7."""
        ris = el.studenti_sufficienti_insufficienti()
        png = gr.grafico_sufficienti_insufficienti(ris)
        self._mostra_png(png, "Sufficienti/Insufficienti")
        self._sv.set(f"Sufficienti/Insufficienti: {len(ris['sufficienti'])} suff. / {len(ris['insufficienti'])} insuff.")

    # ── Istogrammi multi-materia ──
    def _r_istogrammi(self):
        """
        Raccoglie la distribuzione dei voti di ogni materia esistente
        (scartando le materie senza nessun voto) e mostra la griglia
        di istogrammi risultante.
        Non fa parte dei punti numerati 6.x, ma dà una vista
        d'insieme in più, utile per confrontare al volo l'andamento
        di tutte le materie insieme.
        """
        materie = db.get_nomi_materie()
        if not materie:
            messagebox.showinfo("Info", "Nessuna materia."); return
        dati = {m: el.distribuzione_voti_materia(m) for m in materie}
        dati = {m: v for m, v in dati.items() if v}
        if not dati:
            messagebox.showinfo("Info", "Nessun voto registrato."); return
        png = gr.grafico_istogrammi_per_materia(dati)
        self._mostra_png(png, "Istogrammi per materia")
        self._sv.set(f"Istogrammi: {len(dati)} materie.")

    # ── PDF ──
    def _esporta_pdf(self):
        """
        Chiede all'utente dove salvare il PDF e avvia in un thread
        separato (in background) la creazione del report completo
        con report_pdf.genera_report_completo.
        Creare il PDF (grafici + reportlab) può richiedere qualche
        secondo; farlo in un thread separato evita che la finestra
        dell'app si blocchi durante l'attesa, restando reattiva.
        """
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile="report_studenti.pdf"
        )
        if not path: return
        self._sv.set("Generazione PDF in corso…")
        def _gen():
            """Funzione eseguita nel thread in background: crea il
            PDF e aggiorna lo stato/il messaggio in caso di successo
            o di errore."""
            try:
                rpdf.genera_report_completo(path)
                self._sv.set(f"PDF salvato: {path}")
                messagebox.showinfo("PDF", f"Report salvato:\n{path}")
            except Exception as e:
                messagebox.showerror("Errore PDF", str(e))
                self._sv.set("Errore PDF.")
        threading.Thread(target=_gen, daemon=True).start()

    def _esporta_pdf_focus(self):
        """PDF con la sezione "Media materia per studente"
        personalizzata, più le sezioni generali.
        A differenza di _esporta_pdf (report standard), qui l'utente
        può scegliere (se vuole) una materia e uno studente
        specifici da mettere come sezione dedicata all'inizio del
        report, tramite un piccolo form (materia e studente sono
        entrambi facoltativi, con l'opzione "(nessuna)"/"(nessuno)")."""
        materie  = db.get_nomi_materie()
        studenti = db.get_tutti_studenti()
        if not materie or not studenti:
            messagebox.showinfo("Info", "Aggiungi almeno una materia e uno studente."); return

        w = tk.Toplevel(self)
        w.title("Filtri PDF")
        w.configure(bg=BG)
        w.grab_set()

        tk.Label(w, text="Materia (opz.):", bg=BG, font=FONT).grid(row=0, column=0, padx=8, pady=6)
        cb_mat = ttk.Combobox(w, values=["(nessuna)"] + materie, width=22, font=FONT)
        cb_mat.current(0)
        cb_mat.grid(row=0, column=1, padx=8)

        nomi_s = ["(nessuno)"] + [f"{s['id']} — {s['cognome']} {s['nome']}" for s in studenti]
        tk.Label(w, text="Studente (opz.):", bg=BG, font=FONT).grid(row=1, column=0, padx=8, pady=6)
        cb_stu = ttk.Combobox(w, values=nomi_s, width=28, font=FONT)
        cb_stu.current(0)
        cb_stu.grid(row=1, column=1, padx=8)

        def _genera():
            """Legge cosa è stato scelto (o None se è rimasto su
            "(nessuna/o)"), chiede dove salvare il PDF e avvia la
            creazione in un thread in background, come in
            _esporta_pdf."""
            path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF", "*.pdf")],
                initialfile="report_focus.pdf"
            )
            if not path: return
            mat   = cb_mat.get() if cb_mat.current() > 0 else None
            idx_s = cb_stu.current()
            sid   = studenti[idx_s - 1]["id"] if idx_s > 0 else None
            snome = (studenti[idx_s - 1]["cognome"] + " " +
                     studenti[idx_s - 1]["nome"]) if idx_s > 0 else None
            w.destroy()
            def _gen():
                """Funzione eseguita nel thread in background: crea il
                PDF con i filtri scelti e aggiorna lo stato/il messaggio."""
                try:
                    rpdf.genera_report_completo(path, materia_focus=mat,
                                                id_studente_focus=sid,
                                                nome_studente_focus=snome)
                    self._sv.set(f"PDF salvato: {path}")
                    messagebox.showinfo("PDF", f"Report salvato:\n{path}")
                except Exception as e:
                    messagebox.showerror("Errore PDF", str(e))
            threading.Thread(target=_gen, daemon=True).start()

        _btn(w, "Genera PDF", _genera).grid(row=2, column=0, columnspan=2, pady=10)


# ─────────────────────────────────────────────────────────────────────────────
#  APP PRINCIPALE
# ─────────────────────────────────────────────────────────────────────────────

class App(tk.Tk):
    """
    Finestra principale dell'applicazione: inizializza il database e
    ospita, tramite un Notebook (un contenitore di schede), tutte le
    schede dell'app (Importa, Studenti, Voti, Assenze, Materie, Report).
    È il punto di partenza della GUI: prepara il database e crea la
    barra di stato condivisa, che viene passata a ogni scheda così
    tutte possono scrivere messaggi di stato allo stesso modo.
    """

    def __init__(self):
        """Prepara il database (creando le tabelle se mancano),
        imposta la finestra principale (titolo, dimensioni, colore di
        sfondo) e collega la funzione personalizzata per la chiusura."""
        super().__init__()
        db.init_db()

        self.title("Gestione Studenti")
        self.geometry("1100x680")
        self.configure(bg=BG)
        self.resizable(True, True)

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build()

    def _on_close(self):
        """Chiude la finestra e termina il programma in modo pulito.
        Usiamo os._exit(0) invece del semplice destroy() per essere
        sicuri che il programma si chiuda subito anche se sono
        rimasti thread in background ancora attivi (per esempio la
        creazione del PDF non ancora finita), evitando che l'app
        resti "appesa" in memoria dopo aver chiuso la finestra."""
        try:
            self.destroy()
        finally:
            os._exit(0)

    def _build(self):
        """
        Costruisce il layout della finestra principale: intestazione
        con il titolo dell'app, barra di stato in basso, e un
        Notebook con una scheda per ogni funzione (Importa, Studenti,
        Voti, Assenze, Materie, Report).
        Usare un Notebook con classi separate per ogni scheda rende
        l'app facile da modificare: per aggiungere una nuova funzione
        basta creare una nuova classe Frame e aggiungerla alla lista
        'tabs', senza toccare le altre schede.
        """
        # Intestazione
        hdr = tk.Frame(self, bg=BLU, height=52)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="🎓  Gestione Studenti",
                 font=("Segoe UI", 15, "bold"), bg=BLU, fg="white",
                 padx=16).pack(side="left", pady=10)

        # Barra di stato
        self._status_bar, self._sv = _status(self)
        self._status_bar.pack(side="bottom", fill="x")

        # Notebook (contenitore delle schede)
        style = ttk.Style()
        style.configure("TNotebook", background=BG)
        style.configure("TNotebook.Tab", font=FONT_B, padding=[12, 6])

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=0, pady=0)

        tabs = [
            ("📂 Importa",  TabImport),
            ("👤 Studenti", TabStudenti),
            ("📝 Voti",     TabVoti),
            ("❌ Assenze",  TabAssenze),
            ("📚 Materie",  TabMaterie),
            ("📊 Report",   TabReport),
        ]
        for label, cls in tabs:
            frame = cls(nb, self._sv)
            nb.add(frame, text=label)


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = App()
    app.mainloop()