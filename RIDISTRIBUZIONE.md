# RIDISTRIBUZIONE

Proposta di riorganizzazione del repository `Laboratorio-Boglia-1`.
Oggi le 17 cartelle sono tutte allo stesso livello, con nomi di granularità diversa (una materia, un singolo corso AWS, un progetto). Qui sono raggruppate in 7 aree di pertinenza.

**Nessun file è stato spostato.** Questo documento descrive solo cosa andrebbe dove e perché.

## Struttura proposta

```
Laboratorio-Boglia-1/
├── 01_AWS_CLOUD/
│   ├── SICUREZZA_AWS/                  (da CORSO_SICUREZZA_AWS)
│   ├── SERVERLESS_AWS/                 (da CORSO_SERVERLESS_AWS)
│   ├── VM_RETI_STORAGE/                (da CORSO_VM_RETI_STORAGE)
│   ├── ARCHITETTURA_PROGETTAZIONE/     (da CORSO_ARCHITETTURA_PROGETTAZIONE)
│   └── REPORT_VERIFICA_DLVRBL.md       (dalla radice)
├── 02_INFRASTRUCTURE_AS_CODE/
│   ├── INFRASTRUCTURE_AS_A_CODE/       (da CORSO_INFRASTRUCTURE_AS_A_CODE)
│   └── CloudFormation_server3/         (da CORSO_OS_VIRTUALIZZAZIONE)
├── 03_DEVOPS_CONTAINER/
│   ├── CONTAINER_MICROSERVIZI/         (da CORSO_CONTAINER_MICROSERVIZI)
│   ├── AUTOMATION_PIPELINE/            (da CORSO_AUTOMATION_PIPELINE)
│   ├── VERSION_CONTROL/                (da CORSO_VERSION_CONTROL)
│   └── app_docker_python/              (da CORSO_JAVA)
├── 04_PROGRAMMAZIONE/
│   ├── PROGRAMMAZIONE/                 (da CORSO_PROGRAMMAZIONE)
│   ├── PYTHON_ESERCIZI_PAPA/           (da CORSO_PAPA)
│   └── API_NODE/                       (da CORSO_API)
├── 05_BASI_DI_DATI/
│   └── (da CORSO_BASI_DI_DATI)
├── 06_AI_E_PROMPT_ENGINEERING/
│   └── (da CORSO_AI_E_PROMPT_ENGENEERING)
└── 07_SOFT_SKILL_E_CARRIERA/
    ├── PARITA_E_NON_DISCRIMINAZIONE/   (da CORSO_PARITA'_E_NON_DISCRIMINAZIONE)
    ├── LEARNING_BY_PROJECT/            (da LEARNING BY PROJECT)
    └── preparazione.txt                (dalla radice)
```

## Gruppi: cosa va dove e perché

### 01 — AWS Cloud
| Cartella attuale | Contenuto | Perché qui |
|---|---|---|
| `CORSO_SICUREZZA_AWS` | 10 DLVRBL, script `WholeCourseProcedure`, screenshot | Corso AWS (IAM, backup, VPN, ecc.) |
| `CORSO_SERVERLESS_AWS` | 18 DLVRBL, 3 PDF di consegna, script, screenshot | Corso AWS (Lambda, API Gateway, costi) |
| `CORSO_VM_RETI_STORAGE` | 11 DLVRBL, PDF intermedia, script, screenshot | Corso AWS (EC2, VPC, S3, bilanciamento) |
| `CORSO_ARCHITETTURA_PROGETTAZIONE` | Schemi AWS, stima costi, verifica finale su scenario ShopShop | Progettazione di architetture su AWS. Stessi temi dei corsi sopra (pilastri, costi, EC2, SG, bucket) |
| `REPORT_VERIFICA_DLVRBL.md` (radice) | Verifica dei DLVRBL di Sicurezza, VM e Serverless | Parla solo di questi tre corsi AWS |

Motivo del raggruppamento: i tre corsi con DLVRBL hanno la stessa struttura (`DLVRBL-LAB-NN.md`, `WholeCourseProcedure.sh`, `screenshots-*`) e lo stesso strumento (Learner Lab AWS). Il report di verifica li riguarda tutti insieme. Architettura è il quarto corso AWS, in forma di schemi e relazioni invece che di laboratori.

### 02 — Infrastructure as Code
| Cartella attuale | Contenuto | Perché qui |
|---|---|---|
| `CORSO_INFRASTRUCTURE_AS_A_CODE` | CloudFormation (`ticketstorm.yaml`, SnackOverflow con nested stack), Terraform (`terraform-lab`, `ticketstorm-tf`, DriftHunter, Ordine&Conto), verifiche | È il corso IaC vero e proprio |
| `CORSO_OS_VIRTUALIZZAZIONE` | Solo `server3.yaml`: un template CloudFormation (VPC, IGW) | Nonostante il nome, il contenuto è IaC su AWS, non virtualizzazione/OS. Il nome attuale è fuorviante. Va con gli altri template CloudFormation |

Motivo: IaC ha un linguaggio e un flusso di lavoro propri (template, state, drift, moduli). Resta separato da AWS "a mano" (console e CLI) dei corsi del gruppo 01, anche se usa gli stessi servizi.

### 03 — DevOps e Container
| Cartella attuale | Contenuto | Perché qui |
|---|---|---|
| `CORSO_CONTAINER_MICROSERVIZI` | Docker Compose, progetto MusicLab a microservizi, manifest k8s e Portainer | Container e orchestrazione |
| `CORSO_AUTOMATION_PIPELINE` | Piano di ripasso UF3 (pipeline AWS, GitHub Actions), `MCPServer/server.py`, `site.zip/index.html` | CI/CD e automazione. Il server MCP è un'estensione AI della pipeline: se si vuole, va anche richiamato dal gruppo 06 |
| `CORSO_VERSION_CONTROL` | Appunti su Git | Base del flusso DevOps (la pipeline parte da Git) |
| `CORSO_JAVA` | `app.py`, `dockerfile`, `.dockerignore`, `.env` | Nonostante il nome, è un'app **Python** containerizzata con Docker. Nessun codice Java. Il nome attuale è fuorviante |

Motivo: tutto ruota attorno al ciclo build, pacchetto, esecuzione, deploy. Git, Docker e pipeline sono tre passaggi della stessa catena.

### 04 — Programmazione
| Cartella attuale | Contenuto | Perché qui |
|---|---|---|
| `CORSO_PROGRAMMAZIONE` | Python di base, OOP, DAO, geometria, biblioteca, Student Analytics Pipeline, verifica | Corso di programmazione |
| `CORSO_PAPA` | Esercizi Python per data (cicli, liste, tuple, dizionari, OOP, file), progetto Python con DB, grafici e report PDF | Stesso linguaggio e stessi argomenti di `CORSO_PROGRAMMAZIONE`. Il significato esatto della sigla PAPA non è ricavabile dai file |
| `CORSO_API` | Quattro app Node/Express (LibreriaOnline v1, v2, v2_final, MusicaMaestro) con `node_modules` | Sviluppo backend e API REST |

Motivo: sono tutti codice applicativo scritto a mano. `CORSO_API` è l'unica cartella in Node/JavaScript, ma resta qui perché è sviluppo applicativo e non infrastruttura.

### 05 — Basi di Dati
| Cartella attuale | Contenuto | Perché qui |
|---|---|---|
| `CORSO_BASI_DI_DATI` | Esercitazioni SQL (DDL, DML, DQL), magazzino, videogiochi, verifica, script Python con MySQL/SQLite | Materia autonoma con esami propri |

Motivo: il tema è unico e ben definito. Il codice Python di accesso ai dati (`mysql_connection.py`, `Regioni.db`) resta qui perché serve alle esercitazioni SQL. Nota: `CORSO_PROGRAMMAZIONE/Regioni.db` e `CORSO_PROGRAMMAZIONE/pitone/collegamento_db.py` sono affini a questa area ma restano in Programmazione, perché sono esercizi di linguaggio.

### 06 — AI e Prompt Engineering
| Cartella attuale | Contenuto | Perché qui |
|---|---|---|
| `CORSO_AI_E_PROMPT_ENGENEERING` | 4 riassunti (introduzione all'AI, LLM premium e offline, prompt engineering, tipologie di modelli) | Teoria su AI e LLM, non legata a un linguaggio o a un servizio AWS |

Motivo: area piccola ma distinta. Cartella consigliata da correggere nel nome: `ENGENEERING` è un refuso di `ENGINEERING`.

### 07 — Soft skill e carriera
| Cartella attuale | Contenuto | Perché qui |
|---|---|---|
| `CORSO_PARITA'_E_NON_DISCRIMINAZIONE` | Prova d'esame su parità e non discriminazione (PDF e bozze) | Corso trasversale, nessun contenuto tecnico |
| `LEARNING BY PROJECT` | Scheda cliente e riassunto di un caso aziendale (Thema Consulting / Pro Studio) | Lavoro per progetto: analisi del cliente, requisiti, offerta. Competenza di consulenza più che tecnica |
| `preparazione.txt` (radice) | Bozza di candidatura per lo stage curriculare | Documento di carriera. Contiene recapiti personali: non lasciarlo in un repository pubblico |

Motivo: raccoglie ciò che non è codice né infrastruttura. Se il materiale di `LEARNING BY PROJECT` cresce con parti cloud, si può spostare in 01.

## File nella radice

| File | Destinazione | Nota |
|---|---|---|
| `REPORT_VERIFICA_DLVRBL.md` | `01_AWS_CLOUD/` | Vedi sopra |
| `preparazione.txt` | `07_SOFT_SKILL_E_CARRIERA/` | Vedi sopra |
| `activatescript.txt` | `04_PROGRAMMAZIONE/` | Contiene solo il comando per attivare la `.venv` di `CORSO_PROGRAMMAZIONE`. Il percorso dentro va aggiornato dopo lo spostamento |
| `.gitignore` | resta nella radice | Elenca i file dei recovery code GitHub |
| `RIDISTRIBUZIONE.md` | resta nella radice | Questo documento |

## Da sistemare durante la riorganizzazione

1. **Nomi fuorvianti**: `CORSO_JAVA` (è Python + Docker) e `CORSO_OS_VIRTUALIZZAZIONE` (è CloudFormation).
2. **Refuso**: `ENGENEERING` in `CORSO_AI_E_PROMPT_ENGENEERING`.
3. **Apostrofo nel nome**: `CORSO_PARITA'_E_NON_DISCRIMINAZIONE` dà problemi in shell e script. Meglio `PARITA_E_NON_DISCRIMINAZIONE`.
4. **Spazi e simboli nei nomi** (`LEARNING BY PROJECT`, `Ordine&Conto`, `esercizi x il 03-09`, `VERIFICA FINALE — ...`): meglio con underscore, senza `&` e senza il trattino lungo.
5. **File che non dovrebbero stare nel repository**:
   - `node_modules` in `CORSO_API` (circa 6900 file su un totale di circa 7500). Va ignorato in `.gitignore` e rigenerato con `npm install`.
   - `__pycache__/` e `*.pyc` in programmazione, basi di dati e automation.
   - `CORSO_JAVA/.env`: può contenere segreti. Verificare e non versionarlo.
6. **Verifiche incompiute annotate nelle cartelle**: `z manca 11` (Sicurezza), `z mancano 12 e 13` (VM), `z arriva al 18 con i file md` (Serverless). Sono promemoria; vanno trasformati in una nota nel `README` di ogni corso.
7. **Percorsi dentro gli script**: gli script `WholeCourseProcedure.sh` e `activatescript.txt` possono contenere percorsi assoluti. Controllarli dopo lo spostamento.
8. **Uno `README.md` per area**, con due righe su cosa contiene e come si usa.

## Come procedere

Usare `git mv` per ogni cartella, così la cronologia dei file resta tracciata. Fare i gruppi uno alla volta con un commit per gruppo, partendo da quelli senza dipendenze incrociate (06 e 07), e lasciare 01 e 03 per ultimi perché hanno script con percorsi.
