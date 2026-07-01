"""
importa_file.py — caricamento CSV con validazione formale e report errori
"""

import csv
import re
from dataclasses import dataclass, field
from pathlib import Path

import database as db


# ─── TIPI ────────────────────────────────────────────────────────────────────

@dataclass
class ErroreRiga:
    file: str
    riga: int
    motivo: str

    def __str__(self):
        return f"[{self.file}] riga {self.riga}: {self.motivo}"


@dataclass
class RisultatoImport:
    tipo: str
    inseriti: int = 0
    ignorati: int = 0
    errori: list[ErroreRiga] = field(default_factory=list)

    @property
    def ok(self):
        return len(self.errori) == 0


# ─── VALIDATORI ──────────────────────────────────────────────────────────────

RE_DATA = re.compile(r"^\d{4}-\d{2}-\d{2}$")
RE_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _valida_data(val: str) -> bool:
    if not RE_DATA.match(val):
        return False
    try:
        import datetime
        datetime.date.fromisoformat(val)
        return True
    except ValueError:
        return False


def _valida_email(val: str) -> bool:
    return bool(RE_EMAIL.match(val))


def _valida_voto(val: str) -> tuple[bool, float]:
    try:
        v = float(val.replace(",", "."))
        return (0 <= v <= 10), v
    except ValueError:
        return False, 0.0


# ─── IMPORTATORI ─────────────────────────────────────────────────────────────

def importa_studenti(path: str) -> RisultatoImport:
    """
    CSV atteso: ID,Nome,Cognome,Data_Nascita,Email
    ID ignorato (auto-increment DB). Email deve essere unica.
    """
    p = Path(path)
    res = RisultatoImport(tipo="studenti")
    campi_attesi = {"id", "nome", "cognome", "data_nascita", "email"}

    try:
        with open(p, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)

            # Verifica intestazioni
            if reader.fieldnames is None:
                res.errori.append(ErroreRiga(p.name, 0, "file vuoto o senza intestazione"))
                return res

            intestazioni = {h.strip().lower() for h in reader.fieldnames}
            mancanti = campi_attesi - intestazioni
            if mancanti:
                res.errori.append(ErroreRiga(p.name, 0,
                    f"colonne mancanti: {', '.join(sorted(mancanti))}"))
                return res

            email_db = db.get_email_esistenti()
            email_viste_csv: set[str] = set()
            righe_valide: list[tuple] = []

            for n, row in enumerate(reader, start=2):
                nome        = row.get("Nome", "").strip()
                cognome     = row.get("Cognome", "").strip()
                data_nasc   = row.get("Data_Nascita", "").strip()
                email       = row.get("Email", "").strip()
                email_l     = email.lower()

                errori_riga = []
                if not nome:
                    errori_riga.append("Nome vuoto")
                if not cognome:
                    errori_riga.append("Cognome vuoto")
                if not _valida_data(data_nasc):
                    errori_riga.append(f"Data_Nascita non valida: '{data_nasc}'")
                if not _valida_email(email):
                    errori_riga.append(f"Email non valida: '{email}'")
                elif email_l in email_db or email_l in email_viste_csv:
                    errori_riga.append(f"Email duplicata: '{email}'")

                if errori_riga:
                    res.errori.append(ErroreRiga(p.name, n, "; ".join(errori_riga)))
                    res.ignorati += 1
                    continue

                email_viste_csv.add(email_l)
                righe_valide.append((nome, cognome, data_nasc, email))

            if righe_valide:
                try:
                    db.inserisci_studenti_batch(righe_valide)
                    res.inseriti += len(righe_valide)
                except Exception as e:
                    res.errori.append(ErroreRiga(p.name, 0, f"DB (batch): {e}"))
                    res.ignorati += len(righe_valide)

    except FileNotFoundError:
        res.errori.append(ErroreRiga(p.name, 0, "file non trovato"))
    except UnicodeDecodeError:
        res.errori.append(ErroreRiga(p.name, 0, "encoding non supportato (atteso UTF-8)"))
    except csv.Error as e:
        res.errori.append(ErroreRiga(p.name, 0, f"CSV malformato: {e}"))

    return res


def importa_voti(path: str) -> RisultatoImport:
    """
    CSV atteso: IDStudente,Voto,Materia
    IDStudente deve esistere in DB.
    """
    p = Path(path)
    res = RisultatoImport(tipo="voti")
    campi_attesi = {"idstudente", "voto", "materia"}

    try:
        with open(p, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)

            if reader.fieldnames is None:
                res.errori.append(ErroreRiga(p.name, 0, "file vuoto o senza intestazione"))
                return res

            intestazioni = {h.strip().lower() for h in reader.fieldnames}
            mancanti = campi_attesi - intestazioni
            if mancanti:
                res.errori.append(ErroreRiga(p.name, 0,
                    f"colonne mancanti: {', '.join(sorted(mancanti))}"))
                return res

            id_studenti_ok = db.get_id_studenti_esistenti()
            materie_viste: set[str] = set()
            righe_valide: list[tuple] = []

            for n, row in enumerate(reader, start=2):
                # header-case insensitive lookup
                id_str  = (row.get("IDStudente") or row.get("idstudente") or "").strip()
                voto_s  = (row.get("Voto") or row.get("voto") or "").strip()
                materia = (row.get("Materia") or row.get("materia") or "").strip()

                errori_riga = []

                try:
                    id_studente = int(id_str)
                except ValueError:
                    errori_riga.append(f"IDStudente non intero: '{id_str}'")
                    id_studente = -1

                valido_v, voto_f = _valida_voto(voto_s)
                if not valido_v:
                    errori_riga.append(f"Voto non valido (0-10): '{voto_s}'")

                if not materia:
                    errori_riga.append("Materia vuota")

                if errori_riga:
                    res.errori.append(ErroreRiga(p.name, n, "; ".join(errori_riga)))
                    res.ignorati += 1
                    continue

                if id_studente not in id_studenti_ok:
                    res.errori.append(ErroreRiga(p.name, n,
                        f"IDStudente {id_studente} non esiste"))
                    res.ignorati += 1
                    continue

                righe_valide.append((id_studente, materia, voto_f))
                materie_viste.add(materia)

            if righe_valide:
                try:
                    db.inserisci_voti_batch(righe_valide)
                    for m in materie_viste:
                        db.upsert_materia(m)
                    res.inseriti += len(righe_valide)
                except Exception as e:
                    res.errori.append(ErroreRiga(p.name, 0, f"DB (batch): {e}"))
                    res.ignorati += len(righe_valide)

    except FileNotFoundError:
        res.errori.append(ErroreRiga(p.name, 0, "file non trovato"))
    except UnicodeDecodeError:
        res.errori.append(ErroreRiga(p.name, 0, "encoding non supportato (atteso UTF-8)"))
    except csv.Error as e:
        res.errori.append(ErroreRiga(p.name, 0, f"CSV malformato: {e}"))

    return res


def importa_assenze(path: str) -> RisultatoImport:
    """
    CSV atteso: IDStudente,DATA
    DATA formato YYYY-MM-DD. Duplicati ignorati silenziosamente.
    """
    p = Path(path)
    res = RisultatoImport(tipo="assenze")
    campi_attesi = {"idstudente", "data"}

    try:
        with open(p, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)

            if reader.fieldnames is None:
                res.errori.append(ErroreRiga(p.name, 0, "file vuoto o senza intestazione"))
                return res

            intestazioni = {h.strip().lower() for h in reader.fieldnames}
            mancanti = campi_attesi - intestazioni
            if mancanti:
                res.errori.append(ErroreRiga(p.name, 0,
                    f"colonne mancanti: {', '.join(sorted(mancanti))}"))
                return res

            id_studenti_ok = db.get_id_studenti_esistenti()
            chiavi_viste: set[tuple] = set()
            righe_valide: list[tuple] = []
            duplicati_csv = 0

            for n, row in enumerate(reader, start=2):
                id_str = (row.get("IDStudente") or row.get("idstudente") or "").strip()
                data   = (row.get("DATA") or row.get("data") or "").strip()

                errori_riga = []

                try:
                    id_studente = int(id_str)
                except ValueError:
                    errori_riga.append(f"IDStudente non intero: '{id_str}'")
                    id_studente = -1

                if not _valida_data(data):
                    errori_riga.append(f"DATA non valida (YYYY-MM-DD): '{data}'")

                if errori_riga:
                    res.errori.append(ErroreRiga(p.name, n, "; ".join(errori_riga)))
                    res.ignorati += 1
                    continue

                if id_studente not in id_studenti_ok:
                    res.errori.append(ErroreRiga(p.name, n,
                        f"IDStudente {id_studente} non esiste"))
                    res.ignorati += 1
                    continue

                chiave = (id_studente, data)
                if chiave in chiavi_viste:
                    duplicati_csv += 1
                    continue
                chiavi_viste.add(chiave)
                righe_valide.append(chiave)

            if righe_valide:
                try:
                    n_inseriti = db.inserisci_assenze_batch(righe_valide)
                    res.inseriti += n_inseriti
                    # righe valide ma già presenti in DB (INSERT OR IGNORE) → ignorate
                    res.ignorati += duplicati_csv + (len(righe_valide) - n_inseriti)
                except Exception as e:
                    res.errori.append(ErroreRiga(p.name, 0, f"DB (batch): {e}"))
                    res.ignorati += len(righe_valide)
            else:
                res.ignorati += duplicati_csv

    except FileNotFoundError:
        res.errori.append(ErroreRiga(p.name, 0, "file non trovato"))
    except UnicodeDecodeError:
        res.errori.append(ErroreRiga(p.name, 0, "encoding non supportato (atteso UTF-8)"))
    except csv.Error as e:
        res.errori.append(ErroreRiga(p.name, 0, f"CSV malformato: {e}"))

    return res