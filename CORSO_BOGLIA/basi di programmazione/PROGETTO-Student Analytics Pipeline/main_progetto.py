"""
student_pipeline — main.py
Pipeline completa per generare, validare e analizzare dati studenti.
Uso:
python main.py generate   → crea il CSV con studenti casuali
python main.py validate   → valida il CSV e produce il JSON
python main.py report     → calcola statistiche e produce il report
python main.py all        → esegue tutto in sequenza
"""


import sys           # Step 10 — CLI
import os            # Step 0, 9 — cartelle e backup
import json          # Step 1, 5, 6 — config e JSON
import csv           # Step 3, 4 — lettura/scrittura CSV
import re            # Step 4 — validazione con espressioni regolari
import random        # Step 2 — generazione dati casuali
import math          # Step 6 — arrotondamenti
import statistics    # Step 6 — media, mediana, stdev
import shutil        # Step 9 — copia file (backup)
from pathlib  import Path      # Step 0, 3 — gestione percorsi
from datetime import datetime, date  # Step 2, 3, 8 — date e timestamp
from collections import Counter      # Step 4, 7 — conteggio errori

def crea_cartelle():            # STEP 0 - Preparazione: creazione delle cartelle di progetto
    """Crea la struttura di cartelle del progetto se non esistono."""
    path = Path("CORSO_BOGLIA","basi di programmazione","PROGETTO-Student Analytics Pipeline")
    base_path = path

    cartelle = [
        base_path / "data/input",
        base_path / "data/output",
        base_path / "data/backup",
        base_path / "report",
    ]
    for cartella in cartelle:
        cartella.mkdir(parents=True, exist_ok=True)
    print("[Step 0] Cartelle create/verificate.")

def carica_config() -> dict:       # STEP 1 - dizionario impostazioni
    path = Path("CORSO_BOGLIA","basi di programmazione","PROGETTO-Student Analytics Pipeline")    
    CONFIG_PATH = path / "config.json"
    
    DEFAULT_CONFIG = {
        "numero_studenti": 50,
        "voto_min": 2,
        "voto_max": 10,
        "materie": ["Matematica", "Informatica", "Italiano"],
        "classe": "5A"
        }

    """Crea config.json con valori di default se non esiste, poi lo legge."""
    if not CONFIG_PATH.exists():
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, indent=2, ensure_ascii=False)
        print("[Step 1] config.json creato con valori di default.")
    else:
        print("[Step 1] config.json trovato, caricamento in corso.")
 
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)
    return config       # dizionario impostazioni

def genera_data_nascita() -> str:         # STEP 2 - stringa con la data
    """Genera una data di nascita casuale tra il 2004 e il 2009."""
    inizio = date(2004, 1, 1).toordinal()
    fine   = date(2009, 12, 31).toordinal()
    giorno_casuale = random.randint(inizio, fine)
    return date.fromordinal(giorno_casuale).isoformat()         #stringa con la data
'''GENERAZIONE STUDENTI'''
def genera_studenti(config: dict) -> list[dict]:        # STEP 2 - lista di studenti in python

    NOMI = [
    "Luca", "Marco", "Andrea", "Giulia", "Sofia", "Elena",
    "Matteo", "Lorenzo", "Alice", "Chiara", "Davide", "Sara",
    "Federica", "Simone", "Valentina", "Roberto", "Anna", "Paolo",
    "Marta", "Giorgio", "Laura", "Francesco", "Alessia", "Riccardo"
    ]
    COGNOMI = [
    "Rossi", "Ferrari", "Esposito", "Bianchi", "Romano", "Colombo",
    "Ricci", "Marino", "Greco", "Bruno", "Gallo", "Conti",
    "De Luca", "Mancini", "Costa", "Giordano", "Rizzo", "Lombardi",
    "Moreno", "Barbieri", "Fontana", "Santoro", "Mariani", "Rinaldi"
    ]
    """
    Genera una lista di dizionari studente in base alla configurazione.
    Ogni studente ha: id, nome, cognome, data_nascita, email, voti, AGGIUNGO IO |assenze|.
    """
    studenti = []
    for i in range(1, config["numero_studenti"] + 1):
        nome    = random.choice(NOMI)
        cognome = random.choice(COGNOMI)
        email   = f"{nome.lower()}.{cognome.lower().replace(' ', '')}{i}@scuola.it"
        voti    = {
            materia: random.randint(config["voto_min"], config["voto_max"])
            for materia in config["materie"]
        }
        # Extra C — campo assenze
        assenze = random.randint(0, 20)
 
        studente = {
            "id":           i,
            "nome":         nome,
            "cognome":      cognome,
            "data_nascita": genera_data_nascita(),
            "email":        email,
            "voti":         voti,
            "assenze":      assenze,
        }
        studenti.append(studente)
 
    print(f"[Step 2] Generati {len(studenti)} studenti.")
    return studenti         #lista di studenti in python
'''GENERAZIONE STUDENTI'''
def salva_su_csv(studenti: list[dict], config:dict) -> Path:       # STEP 3 - SALVATAGGIO SU CSV - path sistema x la lista python
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    path = Path("CORSO_BOGLIA","basi di programmazione","PROGETTO-Student Analytics Pipeline")    
    percorso = path / "data/input/" / f"studenti_{timestamp}.csv"

    materie = config["materie"]
    nomicampi = ["id","nome","cognome","data_nascita","email"] + materie +["assenze"]

    with open(percorso, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames= nomicampi)
        writer.writeheader()

        for studente in studenti:
            riga = {
                "id": studente["id"],
                "nome": studente["nome"],
                "cognome": studente["cognome"],
                "data_nascita": studente["data_nascita"],
                "email": studente["email"],
                "assenze": studente["assenze"]
            }
            for materia in materie:
                riga[materia] = studente["voti"][materia]
            writer.writerow(riga)

    print(f"[Step 3] CSV salvato in: {percorso}")
    return percorso       # path sistema x la lista python

def valida_studenti(percorso_csv: Path, config: dict) -> tuple[list,list,Counter]:       # STEP 4 - Lettura CSV e validazione - ritorna lista validi e scartati python e conteggio errori (contatore)

    # Pattern regex per validare l'email: testo@testo.dominio
    PATTERN_EMAIL = re.compile(r"^[\w.\-]+@[\w.\-]+\.\w{2,}$")
    # Pattern per la data in formato YYYY-MM-DD
    PATTERN_DATA  = re.compile(r"^\d{4}-\d{2}-\d{2}$")

    validi = []
    scartati = []
    conteggio_errori = Counter()
    materie = config["materie"]

    with open(percorso_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for riga in reader:
            errori = []

            if not PATTERN_EMAIL.match(riga["email"]):
                errori.append("email_non_valida")
                conteggio_errori["email_non_valida"] += 1

            if not PATTERN_DATA.match(riga["data_nascita"]):
                errori.append("email_non_valida")
                conteggio_errori["email_non_valida"] += 1
            else:
                try:
                    datetime.strptime(riga["data_nascita"], "%Y-%m-%d")
                except ValueError:
                    errori.append("email_non_valida")
                    conteggio_errori["email_non_valida"] += 1

            for materia in materie:
                try:
                    voto = int(riga[materia])
                    if not (config["voto_min"] <= voto <= config["voto_max"]):
                        errori.append("voto_fuori_range")
                        conteggio_errori["voto_fuori_range"] += 1
                except (ValueError, KeyError):
                        errori.append("voto_non_numerico")
                        conteggio_errori["voto_non_numerico"] += 1


            studente = {
                "id":           int(riga["id"]),
                "nome":         riga["nome"],
                "cognome":      riga["cognome"],
                "data_nascita": riga["data_nascita"],
                "email":        riga["email"],
                "assenze":      int(riga.get("assenze", 0)),
                "voti":         {m: int(riga[m]) for m in materie if riga.get(m, "").isdigit()},
                # Extra B — timestamp di importazione
                "timestamp_import": datetime.now().isoformat(),
                }
            
            if errori:
                studente["errori"] = errori
                scartati.append(studente)
            else:
                validi.append(studente)

    print(f"[Step 4] Validi: {len(validi)} | Scartati: {len(scartati)}")
    print(f"         Errori trovati: {dict(conteggio_errori) or 'nessuno'}")
    return validi, scartati, conteggio_errori       # ritorna lista validi, scartati python e conteggio errori (contatore)

def salva_json_validi(studenti: list[dict]) -> Path:            # STEP 5 — Conversione PERCORSO CSV → JSON
    path = Path("CORSO_BOGLIA","basi di programmazione","PROGETTO-Student Analytics Pipeline") 

    percorso = path / "data/output" / "studenti_validi.json"
    with open(percorso, "w", encoding= "utf-8") as f:
        json.dump(studenti, f, indent=2, ensure_ascii=False)
    print(f"[Step 5] JSON validi salvati in: {percorso}")
    return percorso         # percorso json_validi

def salva_json_scartati(scartati: list[dict]) -> Path:          # STEP 5 — Conversione PERCORSO CSV → JSON
    path = Path("CORSO_BOGLIA","basi di programmazione","PROGETTO-Student Analytics Pipeline")
    percorso = path / "data/output" / "studenti_scartati.json"
    with open(percorso, "w", encoding= "utf-8") as f:
        
        json.dump(scartati, f, indent=2, ensure_ascii=False)
    print(f"[Step 5] JSON scartati salvati in: {percorso} | ({len(scartati)} record)")
    return percorso         # percorso json_scartati

def calcola_statistica(studenti: list[dict], config: dict) -> dict:         # STEP 6 - Calcolo statistiche per materia
    stats = {}
    for materia in config["materie"]:
        voti = [s["voti"][materia] for s in studenti if materia in s["voti"]]
        if len(voti) < 2:
            continue

        stats[materia] = {
            "media": round(statistics.mean(voti), 2),
            "mediana": statistics.median(voti),
            "stdev": round(statistics.stdev(voti), 2),
            "min": min(voti),
            "max": max(voti)
        }
        soglia = math.floor(statistics.mean(voti))
        stats[materia]["soglia_floor"] = soglia

    print(f"[Step 6] Statistiche calcolate per {len(stats)} materie.")
    return stats

crea_cartelle()
config = carica_config()
studenti = genera_studenti(config= config)
print(studenti)
lista_csv = salva_su_csv(studenti= studenti ,config= config)
validi, scartati, _ = valida_studenti(percorso_csv= lista_csv, config= config)
salva_json_validi(validi)
salva_json_scartati(scartati)
statistica = calcola_statistica(studenti= studenti, config= config)
print(f"{statistica}")