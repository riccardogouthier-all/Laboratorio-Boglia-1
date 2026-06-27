"""
importa_file.py — caricamento CSV con validazione formale e report errori
"""

import csv
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

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

            for n, row in enumerate(reader, start=2):
                nome        = row.get("Nome", "").strip()
                cognome     = row.get("Cognome", "").strip()
                data_nasc   = row.get("Data_Nascita", "").strip()
                email       = row.get("Email", "").strip()

                errori_riga = []
                if not nome:
                    errori_riga.append("Nome vuoto")
                if not cognome:
                    errori_riga.append("Cognome vuoto")
                if not _valida_data(data_nasc):
                    errori_riga.append(f"Data_Nascita non valida: '{data_nasc}'")
                if not _valida_email(email):
                    errori_riga.append(f"Email non valida: '{email}'")

                if errori_riga:
                    res.errori.append(ErroreRiga(p.name, n, "; ".join(errori_riga)))
                    res.ignorati += 1
                    continue

                try:
                    db.inserisci_studente(nome, cognome, data_nasc, email)
                    res.inseriti += 1
                except Exception as e:
                    res.errori.append(ErroreRiga(p.name, n, f"DB: {e}"))
                    res.ignorati += 1

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

                if db.get_studente(id_studente) is None:
                    res.errori.append(ErroreRiga(p.name, n,
                        f"IDStudente {id_studente} non esiste"))
                    res.ignorati += 1
                    continue

                try:
                    db.inserisci_voto(id_studente, materia, voto_f)
                    res.inseriti += 1
                except Exception as e:
                    res.errori.append(ErroreRiga(p.name, n, f"DB: {e}"))
                    res.ignorati += 1

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

                if db.get_studente(id_studente) is None:
                    res.errori.append(ErroreRiga(p.name, n,
                        f"IDStudente {id_studente} non esiste"))
                    res.ignorati += 1
                    continue

                try:
                    db.inserisci_assenza(id_studente, data)
                    res.inseriti += 1
                except Exception as e:
                    # UNIQUE constraint → duplicato silenzioso
                    if "UNIQUE" in str(e):
                        res.ignorati += 1
                    else:
                        res.errori.append(ErroreRiga(p.name, n, f"DB: {e}"))
                        res.ignorati += 1

    except FileNotFoundError:
        res.errori.append(ErroreRiga(p.name, 0, "file non trovato"))
    except UnicodeDecodeError:
        res.errori.append(ErroreRiga(p.name, 0, "encoding non supportato (atteso UTF-8)"))
    except csv.Error as e:
        res.errori.append(ErroreRiga(p.name, 0, f"CSV malformato: {e}"))

    return res
