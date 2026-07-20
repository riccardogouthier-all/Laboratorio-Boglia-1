"""
importa_file.py — carica dati da file CSV, controllando che siano
corretti e tenendo un elenco degli errori trovati
"""

import csv
import re
from dataclasses import dataclass, field
from pathlib import Path

import database as db


# ─── TIPI ────────────────────────────────────────────────────────────────────

@dataclass
class ErroreRiga:
    """
    Rappresenta un errore trovato in una riga del CSV durante
    l'importazione (file, numero di riga, spiegazione dell'errore).
    Usiamo una classe apposta (invece di semplici testi o tuple) così
    l'elenco degli errori è più chiaro da leggere e da mostrare sia
    nella GUI (TabImport) sia in un eventuale file di log, grazie al
    metodo __str__ che lo trasforma già in una frase leggibile.
    """
    file: str
    riga: int
    motivo: str

    def __str__(self):
        """Scrive l'errore come una frase leggibile
        "[file] riga N: motivo", usata direttamente nel log mostrato
        all'utente."""
        return f"[{self.file}] riga {self.riga}: {self.motivo}"


@dataclass
class RisultatoImport:
    """
    Contiene il risultato di un'importazione: che tipo di dato è
    stato importato, quante righe sono state inserite, quante
    ignorate, e l'elenco degli errori trovati.
    Mettere tutto in un solo oggetto rende più semplice per chi
    chiama la funzione (la GUI) mostrare un riepilogo chiaro, invece
    di gestire tanti valori separati.
    """
    tipo: str
    inseriti: int = 0
    ignorati: int = 0
    errori: list[ErroreRiga] = field(default_factory=list)

    @property
    def ok(self):
        """True se l'importazione non ha avuto nessun errore.
        Modo comodo per chi chiama la funzione, per sapere subito se
        è andato tutto bene senza dover controllare a mano la lista
        degli errori."""
        return len(self.errori) == 0


# ─── VALIDATORI ──────────────────────────────────────────────────────────────

RE_DATA = re.compile(r"^\d{4}-\d{2}-\d{2}$")
RE_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _valida_data(val: str) -> bool:
    """
    Controlla che una stringa sia una data valida in formato YYYY-MM-DD.
    Il controllo avviene in due passi: prima controlliamo il formato
    con un'espressione regolare (veloce, scarta subito le date
    scritte male), poi controlliamo che la data esista davvero con
    date.fromisoformat (per non accettare date scritte bene ma che
    non esistono nel calendario, come il 30 febbraio).
    """
    if not RE_DATA.match(val):
        return False
    try:
        import datetime
        datetime.date.fromisoformat(val)
        return True
    except ValueError:
        return False


def _valida_email(val: str) -> bool:
    """
    Controlla che una stringa somigli a un'email valida (qualcosa
    seguito da @ e poi da un dominio, senza spazi).
    È un controllo semplice richiesto prima di salvare l'email nel
    database, dove deve anche essere unica.
    """
    return bool(RE_EMAIL.match(val))


def _valida_voto(val: str) -> tuple[bool, float]:
    """
    Trasforma e controlla un voto scritto come testo, accettando sia
    il punto che la virgola come separatore decimale, e verifica che
    sia tra 0 e 10.
    I file CSV possono arrivare da un foglio di calcolo che usa la
    virgola al posto del punto: sistemiamo qui questo dettaglio, così
    non serve pensarci più avanti nel codice, e teniamo la regola
    "voto tra 0 e 10" scritta in un solo punto.
    """
    try:
        v = float(val.replace(",", "."))
        return (0 <= v <= 10), v
    except ValueError:
        return False, 0.0


# ─── IMPORTATORI ─────────────────────────────────────────────────────────────

def importa_studenti(path: str) -> RisultatoImport:
    """
    Importa gli studenti da un file CSV.

    Colonne attese nel CSV: ID,Nome,Cognome,Data_Nascita,Email
    La colonna ID viene ignorata (il database genera l'id da solo).
    L'email deve essere unica.

    Fa l'importazione richiesta dalla scheda "Importa" della GUI.
    Controlla ogni riga separatamente (campi obbligatori, formato
    data, formato email, email non ripetuta né nel database né nelle
    righe già lette dello stesso file) e inserisce nel database solo
    le righe corrette tutte insieme: così un errore su una riga non
    blocca l'importazione delle altre. Ogni errore viene salvato per
    essere poi mostrato nel log della GUI.
    """
    p = Path(path)
    res = RisultatoImport(tipo="studenti")
    campi_attesi = {"id", "nome", "cognome", "data_nascita", "email"}

    try:
        with open(p, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)

            # Controlla che ci siano le intestazioni delle colonne
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
    Importa i voti da un file CSV.

    Colonne attese nel CSV: IDStudente,Voto,Materia
    IDStudente deve corrispondere a uno studente già presente nel database.

    Come importa_studenti, controlla ogni riga (id studente numero
    intero ed esistente, voto numerico tra 0 e 10, materia non vuota)
    e inserisce nel database solo le righe corrette, tutte insieme.
    Le materie scritte nel CSV vengono create in automatico nel
    database con upsert_materia, così non serve crearle a mano prima
    di importare i voti.
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
                # cerca la colonna sia con la lettera maiuscola che minuscola
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
    Importa le assenze da un file CSV.

    Colonne attese nel CSV: IDStudente,DATA
    DATA in formato YYYY-MM-DD. I doppioni vengono ignorati senza errore.

    Controlla ogni riga (id studente esistente, data scritta bene) e
    gestisce i doppioni sia dentro allo stesso file CSV (con
    chiavi_viste) sia rispetto a quelli già nel database (tramite
    INSERT OR IGNORE, che sfrutta il vincolo UNIQUE): in entrambi i
    casi la riga viene contata come "ignorata" ma non come errore,
    perché un'assenza ripetuta non è un dato sbagliato, solo inutile
    da inserire due volte.
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
                    # righe corrette ma già presenti nel database (INSERT OR IGNORE) → contate come ignorate
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