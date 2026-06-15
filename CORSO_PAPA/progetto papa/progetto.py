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
# import random        # Step 2 — generazione dati casuali
import math          # Step 6 — arrotondamenti
import statistics    # Step 6 — media, mediana, stdev
import shutil        # Step 9 — copia file (backup)
from pathlib  import Path      # Step 0, 3 — gestione percorsi
from datetime import datetime, date  # Step 2, 3, 8 — date e timestamp
from collections import Counter      # Step 4, 7 — conteggio errori
import ast


def crea_cartelle():            # STEP 0 - Preparazione: creazione delle cartelle di progetto
    """Crea la struttura di cartelle del progetto se non esistono."""
    path = Path.cwd()#("PROGETTO-Student Analytics Pipeline")      #"CORSO_BOGLIA","basi di programmazione",
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
    path = Path.cwd()                       #("PROGETTO-Student Analytics Pipeline")    #"CORSO_BOGLIA","basi di programmazione",
    CONFIG_PATH = path / "config.json"
    

    DEFAULT_CONFIG = {
        "numero_studenti": 50,
        "voto_min": 2,
        "voto_max": 10,
        # "materie": ["Matematica", "Informatica", "Italiano"],
        "materie": ["Matematica", "Informatica", "Italiano", "Storia", "Inglese", "Educazione Fisica"],
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
'''
def genera_data_nascita() -> str:         # STEP 2 - stringa con la data
    """Genera una data di nascita casuale tra il 2004 e il 2009."""
    inizio = date(2004, 1, 1).toordinal()
    fine   = date(2009, 12, 31).toordinal()
    giorno_casuale = random.randint(inizio, fine)
    return date.fromordinal(giorno_casuale).isoformat()         #stringa con la data
    # GENERAZIONE STUDENTI TRAMITE CODICE PYTHON
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
    # GENERAZIONE STUDENTI TRAMITE CODICE PYTHON
'''
def salva_su_csv(studenti: list[dict], config:dict) -> Path:       # STEP 3 - SALVATAGGIO SU CSV - path sistema x la lista python
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    path = Path("data","input")    
    percorso = path / f"studenti_{timestamp}.csv"

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

def aggiungi_errori(percorso_csv: Path, config: dict) -> None:       # STEP 2B - Aggiunta studenti non validi per attivare controllo errori
    with open(percorso_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        righe = list(reader)
    
    ultimo_id = max(int(r["id"]) for r in righe) if righe else 0

    studenti_da_scartare = [
            {
            "id":            ultimo_id + 1,
            "nome":          "Carlo",
            "cognome":       "Verdi",
            "data_nascita":  "99-99-9999",        # data non valida
            "email":         "carlo.verdiATscuola.it",  # email senza @
            **{m: config["voto_max"] + 3 for m in config["materie"]},  # voti fuori range
            "assenze":       5,
            },
            {
            "id":            ultimo_id + 2,
            "nome":          "Paola",
            "cognome":       "Neri",
            "data_nascita":  "2005-13-40",        # mese e giorno impossibili
            "email":         "paola.neri@scuola.it",  # email valida
            **{m: config["voto_max"] - config["voto_max"] for m in config["materie"]},  # voti = 0
            "assenze":       3,
            }
            ]
    
    righe.extend(studenti_da_scartare)

    with open(percorso_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames= fieldnames)
        writer.writeheader()
        writer.writerows(righe)
    print(f"[Step 2B] studenti non validi aggiunti in: {percorso_csv}")

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
                errori.append("data_nascita_non_valida")
                conteggio_errori["data_nascita_non_valida"] += 1
            else:
                try:
                    datetime.strptime(riga["data_nascita"], "%Y-%m-%d")
                except ValueError:
                    errori.append("data_nascita_non_valida")
                    conteggio_errori["data_nascita_non_valida"] += 1

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

def salva_json_validi(studenti: list[dict]) -> Path:            # STEP 5 - Conversione PERCORSO CSV → JSON - ritorna il percorso json_validi
    path = Path("data/output")       #("CORSO_BOGLIA","basi di programmazione","PROGETTO-Student Analytics Pipeline") 
    percorso = path / "studenti_validi.json"
    with open(percorso, "w", encoding= "utf-8") as f:
        json.dump(studenti, f, indent=2, ensure_ascii=False)
    print(f"[Step 5] JSON validi salvati in: {percorso}")
    return percorso         # percorso json_validi

def salva_json_scartati(scartati: list[dict]) -> Path:          # STEP 5 - Conversione PERCORSO CSV → JSON - ritorno il percorso json_scartati
    path = Path("data/output")       #("CORSO_BOGLIA","basi di programmazione","PROGETTO-Student Analytics Pipeline") 
    percorso = path / "studenti_scartati.json"
    with open(percorso, "w", encoding= "utf-8") as f:
        json.dump(scartati, f, indent=2, ensure_ascii=False)
    print(f"[Step 5] JSON scartati salvati in: {percorso} | ({len(scartati)} record)")
    return percorso         # percorso json_scartati

def calcola_statistica(studenti: list[dict], config: dict) -> dict:         # STEP 6 - Calcolo statistiche per materia - ritorna dizionario di materie con le loro statistiche
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

def classifica_studenti(studenti: list[dict], top_n: int) -> list[dict]:            # STEP 7 - Classifica migliori studenti - ritorna dizionario di studenti con le loro statistiche
    for studente in studenti:
        voti_lista = list(studente["voti"].values())
        studente["media_personale"] = round(statistics.mean(voti_lista), 2)

    classifica = sorted(studenti,key=lambda s:s["media_personale"], reverse=True)
    top = classifica[:top_n]

    print(f"[Step 7] Top {top_n} studenti calcolati.")
    for i, s in enumerate(top, 5):
        print(f"L'alunno con la media più alta è il numero {i}: {s['nome']} {s['cognome']} con una media di: {s['media_personale']}")
        return top

def genera_report(config, validi, scartati, stats, top5) -> Path:           # STEP 8 - Report finale - crea file txt in report/reportXXX.txt e ritorna il percorso
    oggi= datetime.now()
    nome_file = f"report_{oggi.strftime('%Y%m%d')}.txt"
    path = Path("report")
    percorso  = path / nome_file

    righe = []
    righe.append("=" * 60)
    righe.append("  REPORT STUDENTI — PIPELINE PYTHON")
    righe.append("=" * 60)
    righe.append(f"Classe:              {config['classe']}")
    righe.append(f"Data generazione:    {oggi.strftime('%d/%m/%Y %H:%M:%S')}")
    righe.append(f"Studenti totali:     {len(validi) + len(scartati)}")
    righe.append(f"Studenti validi:     {len(validi)}")
    righe.append(f"Studenti scartati:   {len(scartati)}")
    righe.append("")
    
    righe.append("-" * 60)
    righe.append("  STATISTICHE PER MATERIA")
    righe.append("-" * 60)
    for materia, s in stats.items():
        righe.append(f"\n  {materia}")
        righe.append(f"    Media:            {s['media']}")
        righe.append(f"    Mediana:          {s['mediana']}")
        righe.append(f"    Dev. standard:    {s['stdev']}")
        righe.append(f"    Voto minimo:      {s['min']}")
        righe.append(f"    Voto massimo:     {s['max']}")

    righe.append("")
    righe.append("-" * 60)
    righe.append("  TOP 5 STUDENTI")
    righe.append("-" * 60)
    for i, s in enumerate(top5, 1):
        righe.append(
            f"  {i}. {s['nome']:<12} {s['cognome']:<15} "
            f"media: {s['media_personale']}  assenze: {s['assenze']}"
        )
    if validi:
        righe.append("")
        righe.append("-" * 60)
        righe.append("  CORRELAZIONE ASSENZE SU STUDENTI VALIDI")
        righe.append("-" * 60)
        alta_ass   = [s for s in validi if s["assenze"] >= 10]
        nomi_alta = [f"\n      {s['nome']} {s['cognome']}" for s in alta_ass]
        bassa_ass  = [s for s in validi if s["assenze"] <  10]
        nomi_bassa = [f"\n      {s['nome']} {s['cognome']}" for s in bassa_ass]
        if alta_ass and nomi_alta:
            # media_alta  = round(statistics.mean(s["media_personale"] for s in alta_ass), 2)
            # media_bassa = round(statistics.mean(s["media_personale"] for s in bassa_ass), 2)
            righe.append(f"  Studenti con ≥10 assenze ({len(alta_ass)}): {', '.join(nomi_alta)}")#: media voti = {media_alta}")
        if bassa_ass and nomi_bassa:
            righe.append(f"\n  Studenti con <10 assenze ({len(bassa_ass)}): {', '.join(nomi_bassa)}")#): media voti = {media_bassa}")

    righe.append("")
    righe.append("=" * 60)

    directory = Path("report")    
    percorso_completo = os.path.join(directory, nome_file)
    with open(percorso_completo, "w", encoding="utf-8") as f:
        f.write("\n".join(righe))

    print(f"[Step 8] Report salvato in: {percorso}")
    return percorso

def backup_csv(percorso_csv : Path) -> Path:            # STEP 9 - Backup automatico
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    directory = Path("data","backup")          #("PROGETTO-Student Analytics Pipeline","data","backup")
    destinazione = directory / f"backup_studenti_{timestamp}.csv"
    shutil.copy2(percorso_csv, destinazione)
    print(f"[Step 9] Backup salvato in {destinazione}")
    return destinazione
##################################################################################################################################################
##################################################################################################################################################
def cmd_generate(config):           # STEP 10 — Gestione CLI con sys.argv
    # studenti = genera_studenti(config)        # STEP 2
    # path = Path("studenti.txt")        # input tramite file per permettere all'utente di scrivere in input i propri studenti (opzionale).
    # studenti = path.read_text().splitlines()       # se il file esiste, lo legge e genera la lista studenti da lì, altrimenti genera studenti casuali

    # lidea è che vuoi collegare un database che con cursor stampa in studenti txt e da li continui col programma
    
    with open("studenti.txt", encoding="utf-8") as f:
        contenuto = f.read()
    studenti = ast.literal_eval("[" + contenuto + "]")    
    # print(studenti)
    lista_csv = salva_su_csv(studenti= studenti ,config= config)       # STEP 3
    aggiungi_errori(lista_csv, config)         # STEP 2B
    backup_csv(lista_csv)         # STEP 9
    return lista_csv
##################################################################################################################################################
def cmd_validate(config):           # STEP 10 — Gestione CLI con sys.argv
    directory = Path("data/input")
    file_csv = sorted(directory.glob("studenti_*.csv"))
    if not file_csv:
        print("[ERRORE] Nessun file CSV trovato in data/input/. Esegui prima 'generate'.")
        sys.exit(1)
    percorso_csv = file_csv[-1]         # solo per stampare in ordine alfabetico
    print(f"[Step 4] Lettura file: {percorso_csv}")

    validi, scartati, _ = valida_studenti(percorso_csv, config)       # STEP 4
    salva_json_validi(validi)            # STEP 5
    salva_json_scartati(scartati)            # STEP 5
    return validi, scartati
##################################################################################################################################################
def cmd_report(config):           # STEP 10 — Gestione CLI con sys.argv
    directory = Path("data/output")
    json_path = directory / "studenti_validi.json"
    if not json_path.exists():
        print("[ERRORE] studenti_validi.json non trovato. Esegui prima 'validate'.")
        sys.exit(1)
    with open(json_path, "r", encoding="utf-8") as f:
        validi = json.load(f)

    scartati_path = directory / "scartati."
    scartati = []
    if scartati_path.exists():
        with open(scartati_path, "r", encoding="utf-8") as f:
            scartati = json.load(f)

    statistica_per_materia = calcola_statistica(validi, config)         # STEP 6
    classifica = classifica_studenti(validi, top_n=5)            # STEP 7
    genera_report(config, validi, scartati, statistica_per_materia, classifica)            # STEP 8
##################################################################################################################################################
def cmd_aggregate_generate_validate(config):           # STEP 10 — Gestione CLI con sys.argv
    print("\n FASE 1 — Generazione dati")
    cmd_generate(config)

    print("\n FASE 2 — Validazione e conversione")
    cmd_validate(config)

def cmd_all(config):           # STEP 10 — Gestione CLI con sys.argv
    print("\n FASE 1 — Generazione dati")
    cmd_generate(config)

    print("\n FASE 2 — Validazione e conversione")
    validi, scartati = cmd_validate(config)

    print("\n FASE 3 — Statistiche e report")
    statistica_per_materia = calcola_statistica(validi, config)         # STEP 6
    classifica = classifica_studenti(validi, top_n=5)            # STEP 7
    genera_report(config, validi, scartati, statistica_per_materia, classifica)            # STEP 8

    print("\n Pipeline completata con successo.")
##################################################################################################################################################
def help():           # STEP 10 — Gestione CLI con sys.argv
    print("""
        Uso:  python progetto.py <comando>
        
        Comandi disponibili:
            generate - Genera in base a una lista di studenti inserita in input un file CSV in data/input/
            validate - Valida il CSV e produce JSON in data/output/
            generate and validate - Esegue la generazione e la validazione in sequenza (senza report)
            report   - Calcola statistiche su un file CSV esistente e genera il report in report/
            all      - Esegue l'intera pipeline dall'inizio alla fine
        """)
##################################################################################################################################################
##################################################################################################################################################
# def main():         # STEP CLI - GESTIONE INPUT
if __name__ == "__main__":
    crea_cartelle()            # STEP 0 
    config = carica_config()       # STEP 1
    
    if len(sys.argv) <2:
        help()
        sys.exit(0)

    # comando = input().lower()
    comando = sys.argv[1].lower()

    if comando == "generate":
        cmd_generate(config)
    elif comando == "validate":
        cmd_validate(config)
    elif comando == "report":
        cmd_report(config)
    elif comando == "generate and validate":
        cmd_aggregate_generate_validate(config)
    elif comando == "all":
        cmd_all(config)
    else:
        print(f"[ERRORE] Comando sconosciuto: '{comando}'")
        help()
        sys.exit(1)
