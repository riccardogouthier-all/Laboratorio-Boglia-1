"""
main.py — GUI tkinter: gestione completa studenti/voti/assenze/materie + report PDF
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from datetime import datetime
import threading
import io

# ── assicura import dal package locale ────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))

import database as db
import importa_file as imp
import elaborazioni as el
import grafici as gr
import report_pdf as rpdf

# ── matplotlib embed ──────────────────────────────────────────────────────────
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

# ─── PALETTE ─────────────────────────────────────────────────────────────────
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
#  WIDGET HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _label(parent, text, **kw):
    return tk.Label(parent, text=text, bg=kw.pop("bg", BG2),
                    fg=kw.pop("fg", TESTO), font=kw.pop("font", FONT), **kw)


def _entry(parent, textvariable=None, **kw):
    e = ttk.Entry(parent, textvariable=textvariable, font=FONT, **kw)
    return e


def _btn(parent, text, cmd, **kw):
    bg = kw.pop("bg", BLU2)
    fg = kw.pop("fg", "white")
    b = tk.Button(parent, text=text, command=cmd, bg=bg, fg=fg,
                  font=FONT_B, relief="flat", padx=10, pady=4,
                  activebackground=BLU, activeforeground="white", cursor="hand2",
                  **kw)
    return b


def _tree(parent, cols: list[str], heights=12):
    tv = ttk.Treeview(parent, columns=cols, show="headings", height=heights)
    for c in cols:
        tv.heading(c, text=c)
        tv.column(c, anchor="w", width=max(80, len(c) * 11))
    sb = ttk.Scrollbar(parent, orient="vertical", command=tv.yview)
    tv.configure(yscrollcommand=sb.set)
    return tv, sb


def _titolo(parent, text):
    f = tk.Frame(parent, bg=BLU)
    tk.Label(f, text=text, bg=BLU, fg="white",
             font=FONT_T, padx=16, pady=10).pack(side="left")
    return f


def _sep(parent):
    return ttk.Separator(parent, orient="horizontal")


def _status(parent):
    sv = tk.StringVar(value="Pronto.")
    bar = tk.Label(parent, textvariable=sv, bg=BLU, fg="white",
                   font=FONT_S, anchor="w", padx=8)
    return bar, sv


# ─────────────────────────────────────────────────────────────────────────────
#  DIALOGO GENERICO STUDENTE
# ─────────────────────────────────────────────────────────────────────────────

class DialogStudente(tk.Toplevel):
    def __init__(self, parent, titolo, dati=None):
        super().__init__(parent)
        self.title(titolo)
        self.configure(bg=BG)
        self.resizable(False, False)
        self.grab_set()
        self.risultato = None

        self._build(dati or {})

    def _build(self, dati):
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
        self.risultato = {
            "nome": self.v_nome.get().strip(),
            "cognome": self.v_cogn.get().strip(),
            "data_nascita": self.v_data.get().strip(),
            "email": self.v_email.get().strip(),
        }
        for k, v in self.risultato.items():
            if not v:
                messagebox.showerror("Errore", f"Campo '{k}' obbligatorio.", parent=self)
                return
        self.destroy()


# ─────────────────────────────────────────────────────────────────────────────
#  DIALOGO VOTO
# ─────────────────────────────────────────────────────────────────────────────

class DialogVoto(tk.Toplevel):
    def __init__(self, parent, titolo, studenti, materie, dati=None):
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

        self.cb_mat = ttk.Combobox(self, values=self._materie, width=30, font=FONT)
        self.cb_mat.grid(row=1, column=1, sticky="ew", **pad)
        if dati.get("materia"):
            self.cb_mat.set(dati["materia"])

        self.v_voto = tk.StringVar(value=str(dati.get("voto", "")))
        _entry(self, self.v_voto, width=12).grid(row=2, column=1, sticky="w", **pad)

        f = tk.Frame(self, bg=BG)
        f.grid(row=3, column=0, columnspan=2, pady=10)
        _btn(f, "✔  Salva", self._salva).pack(side="left", padx=6)
        _btn(f, "✖  Annulla", self.destroy, bg=ACCENT).pack(side="left", padx=6)

    def _salva(self):
        idx = self.cb_stud.current()
        if idx < 0:
            messagebox.showerror("Errore", "Seleziona uno studente.", parent=self); return
        materia = self.cb_mat.get().strip()
        if not materia:
            messagebox.showerror("Errore", "Seleziona una materia.", parent=self); return
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
#  DIALOGO ASSENZA
# ─────────────────────────────────────────────────────────────────────────────

class DialogAssenza(tk.Toplevel):
    def __init__(self, parent, titolo, studenti, dati=None):
        super().__init__(parent)
        self.title(titolo)
        self.configure(bg=BG)
        self.resizable(False, False)
        self.grab_set()
        self.risultato = None
        self._studenti = studenti
        self._build(dati or {})

    def _build(self, dati):
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
        idx = self.cb_stud.current()
        if idx < 0:
            messagebox.showerror("Errore", "Seleziona uno studente.", parent=self); return
        data = self.v_data.get().strip()
        import re
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", data):
            messagebox.showerror("Errore", "Data non valida. Formato: YYYY-MM-DD", parent=self); return
        self.risultato = {
            "id_studente": self._studenti[idx]["id"],
            "data": data,
        }
        self.destroy()


# ─────────────────────────────────────────────────────────────────────────────
#  TAB: STUDENTI
# ─────────────────────────────────────────────────────────────────────────────

class TabStudenti(tk.Frame):
    def __init__(self, parent, status_var):
        super().__init__(parent, bg=BG)
        self._sv = status_var
        self._build()
        self.aggiorna()

    def _build(self):
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
        self.v_cerca.trace_add("write", lambda *_: self.aggiorna())
        _entry(frk, self.v_cerca, width=28).pack(side="left", padx=6)

        # Treeview
        frm = tk.Frame(self, bg=BG)
        frm.pack(fill="both", expand=True, padx=10, pady=4)
        self.tv, sb = _tree(frm, ["ID", "Cognome", "Nome", "Data Nascita", "Email"])
        self.tv.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

    def aggiorna(self, *_):
        self.tv.delete(*self.tv.get_children())
        q = self.v_cerca.get().strip()
        rows = db.cerca_studente(q) if q else db.get_tutti_studenti()
        for r in rows:
            self.tv.insert("", "end",
                           values=(r["id"], r["cognome"], r["nome"],
                                   r["data_nascita"], r["email"]))
        self._sv.set(f"{len(rows)} studenti")

    def _sel_id(self):
        sel = self.tv.selection()
        if not sel:
            messagebox.showinfo("Info", "Seleziona uno studente.")
            return None
        return self.tv.item(sel[0])["values"][0]

    def _nuovo(self):
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
        sid = self._sel_id()
        if sid is None: return
        if messagebox.askyesno("Conferma", f"Eliminare studente ID {sid}?\n"
                               "(Voti e assenze associati saranno eliminati)"):
            db.cancella_studente(sid)
            self.aggiorna()
            self._sv.set("Studente eliminato.")


# ─────────────────────────────────────────────────────────────────────────────
#  TAB: VOTI
# ─────────────────────────────────────────────────────────────────────────────

class TabVoti(tk.Frame):
    def __init__(self, parent, status_var):
        super().__init__(parent, bg=BG)
        self._sv = status_var
        self._build()
        self.aggiorna()

    def _build(self):
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
        self.tv.delete(*self.tv.get_children())
        rows = db.get_tutti_voti()
        for r in rows:
            self.tv.insert("", "end",
                           values=(r["id"], r["studente"], r["materia"], r["voto"]))
        self._sv.set(f"{len(rows)} voti")

    def _sel_id(self):
        sel = self.tv.selection()
        if not sel:
            messagebox.showinfo("Info", "Seleziona un voto.")
            return None
        return self.tv.item(sel[0])["values"][0]

    def _nuovo(self):
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
        vid = self._sel_id()
        if vid is None: return
        if messagebox.askyesno("Conferma", f"Eliminare voto ID {vid}?"):
            db.cancella_voto(vid)
            self.aggiorna()
            self._sv.set("Voto eliminato.")


# ─────────────────────────────────────────────────────────────────────────────
#  TAB: ASSENZE
# ─────────────────────────────────────────────────────────────────────────────

class TabAssenze(tk.Frame):
    def __init__(self, parent, status_var):
        super().__init__(parent, bg=BG)
        self._sv = status_var
        self._build()
        self.aggiorna()

    def _build(self):
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
        self.tv.delete(*self.tv.get_children())
        rows = db.get_tutte_assenze()
        for r in rows:
            self.tv.insert("", "end", values=(r["id"], r["studente"], r["data"]))
        self._sv.set(f"{len(rows)} assenze")

    def _sel_id(self):
        sel = self.tv.selection()
        if not sel:
            messagebox.showinfo("Info", "Seleziona un'assenza."); return None
        return self.tv.item(sel[0])["values"][0]

    def _nuovo(self):
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
        aid = self._sel_id()
        if aid is None: return
        if messagebox.askyesno("Conferma", f"Eliminare assenza ID {aid}?"):
            db.cancella_assenza(aid)
            self.aggiorna()
            self._sv.set("Assenza eliminata.")


# ─────────────────────────────────────────────────────────────────────────────
#  TAB: MATERIE
# ─────────────────────────────────────────────────────────────────────────────

class TabMaterie(tk.Frame):
    def __init__(self, parent, status_var):
        super().__init__(parent, bg=BG)
        self._sv = status_var
        self._build()
        self.aggiorna()

    def _build(self):
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
        self.tv.delete(*self.tv.get_children())
        rows = db.get_tutte_materie()
        for r in rows:
            self.tv.insert("", "end", values=(r["id"], r["nome"]))
        self._sv.set(f"{len(rows)} materie")

    def _sel(self):
        sel = self.tv.selection()
        if not sel:
            messagebox.showinfo("Info", "Seleziona una materia."); return None, None
        v = self.tv.item(sel[0])["values"]
        return v[0], v[1]

    def _nuovo(self):
        nome = simpledialog.askstring("Nuova materia", "Nome materia:", parent=self)
        if nome and nome.strip():
            try:
                db.inserisci_materia(nome.strip())
                self.aggiorna()
                self._sv.set("Materia inserita.")
            except Exception as e:
                messagebox.showerror("Errore DB", str(e))

    def _modifica(self):
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
        mid, mnome = self._sel()
        if mid is None: return
        if messagebox.askyesno("Conferma", f"Eliminare materia '{mnome}'?"):
            db.cancella_materia(mid)
            self.aggiorna()
            self._sv.set("Materia eliminata.")


# ─────────────────────────────────────────────────────────────────────────────
#  TAB: IMPORTAZIONE FILE
# ─────────────────────────────────────────────────────────────────────────────

class TabImport(tk.Frame):
    def __init__(self, parent, status_var):
        super().__init__(parent, bg=BG)
        self._sv = status_var
        self._build()

    def _build(self):
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
        p = filedialog.askopenfilename(filetypes=[("CSV", "*.csv"), ("Tutti", "*")])
        if p:
            self._paths[tipo].set(p)

    def _importa(self):
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
#  TAB: REPORT / GRAFICI
# ─────────────────────────────────────────────────────────────────────────────

class TabReport(tk.Frame):
    def __init__(self, parent, status_var):
        super().__init__(parent, bg=BG)
        self._sv = status_var
        self._build()

    def _build(self):
        left = tk.Frame(self, bg=BG, width=260)
        left.pack(side="left", fill="y", padx=0)
        left.pack_propagate(False)

        tk.Label(left, text="Analisi", font=FONT_T, bg=BLU, fg="white",
                 padx=8, pady=8).pack(fill="x")

        self._canvas_frame = tk.Frame(self, bg=BG2)
        self._canvas_frame.pack(side="right", fill="both", expand=True)

        pad = dict(fill="x", padx=8, pady=3)
        reports = [
            ("6.1 Media materia × studente", self._r61),
            ("6.2 Media per materia",        self._r62),
            ("6.3 Assenze per studente",     self._r63),
            ("6.4 Assenti in un giorno",     self._r64),
            ("6.5 Studenti per materia",     self._r65),
            ("6.7 Sufficienti/Insufficienti",self._r67),
        ]
        for label, cmd in reports:
            _btn(left, label, cmd, bg=BLU2).pack(**pad)

        _sep(left).pack(fill="x", pady=6, padx=8)
        _btn(left, "📄 Esporta PDF completo", self._esporta_pdf, bg=ACCENT).pack(**pad)
        _btn(left, "📄 PDF con filtri attuali", self._esporta_pdf_focus, bg=ACCENT).pack(**pad)

    def _clear_canvas(self):
        for w in self._canvas_frame.winfo_children():
            w.destroy()

    def _mostra_png(self, png_bytes: bytes | None, titolo=""):
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

    def _mostra_testo(self, testo: str):
        self._clear_canvas()
        t = tk.Text(self._canvas_frame, font=FONT, bg=BG2, relief="flat", wrap="word")
        t.insert("end", testo)
        t.configure(state="disabled")
        t.pack(fill="both", expand=True, padx=8, pady=8)

    # ── 6.1 ──
    def _r61(self):
        materie  = db.get_nomi_materie()
        studenti = db.get_tutti_studenti()
        if not materie or not studenti:
            messagebox.showinfo("Info", "Dati insufficienti."); return

        w = tk.Toplevel(self)
        w.title("6.1 — Media materia per studente")
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
        dati = el.medie_per_materia_tutti()
        if not dati:
            messagebox.showinfo("Info", "Nessun voto registrato."); return
        png = gr.grafico_media_per_materia(dati)
        self._mostra_png(png, "Media per materia")
        righe = "\n".join(
            f"  {d['materia']:20s}  media {d['media']:.2f}  ({d['n_studenti']} studenti)"
            for d in dati)
        self._sv.set("6.2 completata.")

    # ── 6.3 ──
    def _r63(self):
        dati = el.assenze_per_studente_tutti()
        png  = gr.grafico_assenze_studenti(dati)
        self._mostra_png(png, "Assenze per studente")
        self._sv.set("6.3 completata.")

    # ── 6.4 ──
    def _r64(self):
        data = simpledialog.askstring("6.4", "Data (YYYY-MM-DD):",
                                      initialvalue=datetime.now().strftime("%Y-%m-%d"),
                                      parent=self)
        if not data: return
        assenti = el.studenti_assenti_giorno(data)
        png = gr.grafico_assenti_giorno(assenti, data)
        self._mostra_png(png, f"Assenti {data}")
        txt = f"Assenti il {data}: {len(assenti)}\n\n"
        txt += "\n".join(f"  • {a['studente']}" for a in assenti) or "  (nessuno)"
        self._sv.set(f"6.4: {len(assenti)} assenti il {data}.")

    # ── 6.5 ──
    def _r65(self):
        materie = db.get_nomi_materie()
        if not materie:
            messagebox.showinfo("Info", "Nessuna materia."); return
        mat = simpledialog.askstring("6.5", "Materia:", parent=self)
        if not mat: return
        n = el.num_studenti_per_materia(mat)
        messagebox.showinfo("6.5", f"Studenti iscritti a '{mat}': {n}")
        self._sv.set(f"6.5: {n} studenti in {mat}.")

    # ── 6.7 ──
    def _r67(self):
        ris = el.studenti_sufficienti_insufficienti()
        png = gr.grafico_sufficienti_insufficienti(ris)
        self._mostra_png(png, "Sufficienti/Insufficienti")
        self._sv.set(f"6.7: {len(ris['sufficienti'])} suff. / {len(ris['insufficienti'])} insuff.")

    # ── PDF ──
    def _esporta_pdf(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile="report_studenti.pdf"
        )
        if not path: return
        self._sv.set("Generazione PDF in corso…")
        def _gen():
            try:
                rpdf.genera_report_completo(path)
                self._sv.set(f"PDF salvato: {path}")
                messagebox.showinfo("PDF", f"Report salvato:\n{path}")
            except Exception as e:
                messagebox.showerror("Errore PDF", str(e))
                self._sv.set("Errore PDF.")
        threading.Thread(target=_gen, daemon=True).start()

    def _esporta_pdf_focus(self):
        """PDF con sezione 6.1 personalizzata + sezioni globali."""
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
    def __init__(self):
        super().__init__()
        db.init_db()

        self.title("Gestione Studenti")
        self.geometry("1100x680")
        self.configure(bg=BG)
        self.resizable(True, True)

        self._build()

    def _build(self):
        # Header
        hdr = tk.Frame(self, bg=BLU, height=52)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="🎓  Gestione Studenti",
                 font=("Segoe UI", 15, "bold"), bg=BLU, fg="white",
                 padx=16).pack(side="left", pady=10)

        # Status bar
        self._status_bar, self._sv = _status(self)
        self._status_bar.pack(side="bottom", fill="x")

        # Notebook
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
