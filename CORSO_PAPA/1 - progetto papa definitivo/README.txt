# GESTIONE STUDENTI — README
# ══════════════════════════════════════════════════════════════════
# Dipendenze
# ══════════════════════════════════════════════════════════════════

# Installa con:
#   pip install -r requirements.txt
# oppure su Linux/macOS:
#   pip3 install -r requirements.txt

matplotlib>=3.7
reportlab>=4.0
# sqlite3 e tkinter → inclusi in Python standard library

# ══════════════════════════════════════════════════════════════════
# Avvio
# ══════════════════════════════════════════════════════════════════

# Windows:
#   python main.py

# macOS / Linux:
#   python3 main.py

# ══════════════════════════════════════════════════════════════════
# Struttura progetto
# ══════════════════════════════════════════════════════════════════
#
# gestione_studenti/
# ├── main.py           ← entry point, GUI tkinter (6 tab)
# ├── database.py       ← SQLite layer, CRUD completo
# ├── importa_file.py   ← caricamento CSV con validazione formale
# ├── elaborazioni.py   ← query statistiche (6.1–6.7)
# ├── grafici.py        ← generazione PNG matplotlib
# ├── report_pdf.py     ← esportazione PDF (reportlab)
# ├── studenti.db       ← creato automaticamente al primo avvio
# ├── sample_studenti.csv
# ├── sample_voti.csv
# └── sample_assenze.csv
#
# ══════════════════════════════════════════════════════════════════
# Flusso consigliato primo avvio
# ══════════════════════════════════════════════════════════════════
# 1. Tab "Materie" → aggiungi: Matematica, Italiano, Storia, Scienze
# 2. Tab "Importa" → carica sample_studenti.csv → Importa
# 3. Tab "Importa" → carica sample_voti.csv     → Importa
# 4. Tab "Importa" → carica sample_assenze.csv  → Importa
# 5. Tab "Report"  → esplora analisi e genera PDF

# ══════════════════════════════════════════════════════════════════
# Formato CSV atteso
# ══════════════════════════════════════════════════════════════════
# STUDENTI:  ID,Nome,Cognome,Data_Nascita,Email
# VOTI:      IDStudente,Voto,Materia
# ASSENZE:   IDStudente,DATA
#
# Encoding: UTF-8 (con o senza BOM)
# Separatore: virgola
# Date: YYYY-MM-DD
# Voti: 0–10, decimali con punto o virgola
