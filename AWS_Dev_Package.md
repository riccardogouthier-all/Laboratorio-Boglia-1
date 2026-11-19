# AWS_Dev_Package

Inventario app installate (Impostazioni > App > App installate) per migrazione su nuova macchina. Fonte: 5 screenshot, 80 app. Data: 19/11/2026.

## Legenda

- **Dimensione**: valore mostrato da Windows (cartella di installazione). `n/d` = Windows non la riporta.
- **Tipo dimensione**: **Solo programma** = dati utente/DB/immagini/volumi stanno altrove e **non** sono conteggiati; **Programma + dati** = la dimensione include probabilmente anche dati salvati.
- **Dati da migrare**: ⚠️ = app con dati/configurazioni da copiare a parte (indicato cosa).
- **Gruppo**: app dipendenti, da installare insieme.
- **Possibili ridondanze** (stesso colore = stessa coppia/gruppo da valutare):
  - 🟨 ODBC Driver 17 ↔ ODBC Driver 18  (SPESSO COESISTONO PER COMPATIBILITA')
  - 🟥 Docker Desktop ↔ Rancher Desktop
  - 🟦 HashiCorp Terraform ↔ OpenTofu
  - 🟩 Java 8 ↔ JDK 25
  - 🟪 OLE DB Driver 18 ↔ OLE DB Driver 19
  - 🟧 Python 3.14.3 ↔ Python Install Manager ↔ Python Launcher

Interpretazione richiesta: 3 liste = **1) Preinstallate**, **2) Da installare con dati da migrare**, **3) Da installare senza dati da migrare**. In ogni lista le app con dimensione `n/d` stanno in fondo.

---

## Lista 1 — Preinstallate (14 app, ~1,92 GB)

Nessuna reinstallazione necessaria.

| # | App | Versione | Dimensione | Tipo dimensione | Dati da migrare |
|---|-----|----------|-----------:|-----------------|-----------------|
| 1 | Microsoft Edge WebView2 Runtime | 157.0.4341.60 | 1,39 GB | Solo programma | — |
| 2 | Microsoft OneDrive | 26.204.1019.0007 | 536 MB | Solo programma | ⚠️ file sincronizzati (si risincronizzano dall'account) |
| 3 | Windows Package Manager Source (winget) V2 | n/d | 3,74 MB | Solo programma | — |
| 4 | Hub di Feedback | n/d | 438 KB | Solo programma | — |
| 5 | Microsoft Windows App Runtime Singleton | n/d | 244 KB | Solo programma | — |
| 6 | Windows App Runtime Main (18/11/2026) | n/d | 136 KB | Solo programma | — |
| 7 | Terminale | n/d | 96,5 KB | Solo programma | — |
| 8 | Windows App Runtime Main (30/09/2026) | n/d | 16,0 KB | Solo programma | — |
| 9 | Microsoft Teams | n/d | 8,00 KB | Solo programma | — |
| 10 | Outlook for Windows | n/d | 8,00 KB | Solo programma | — |
| 11 | Connessione Desktop remoto | n/d | n/d | n/d | — |
| 12 | Microsoft Windows Application Compatibility Fix Database | n/d | n/d | n/d | — |
| 13 | Paint | n/d | n/d | n/d | — |
| 14 | Strumento di cattura | n/d | n/d | n/d | — |

---

## Lista 2 — Da installare CON dati da migrare (29 app, ~15,47 GB)

### Gruppo A — Suite MySQL 8.0 (7 app, ~2,98 GB)

| # | App | Versione | Dimensione | Tipo dimensione | Dati da migrare |
|---|-----|----------|-----------:|-----------------|-----------------|
| 1 | MySQL Workbench 8.0 CE | 8.0.46 | 1,08 GB | Solo programma | ⚠️ connessioni salvate |
| 2 | MySQL Shell | 8.0.45 | 605 MB | Solo programma | — |
| 3 | MySQL Installer | 1.6.16.0 | 572 MB | Solo programma | — |
| 4 | MySQL Server 8.0 | 8.0.45 | 549 MB | Solo programma | ⚠️ database (`ProgramData`) → dump |
| 5 | MySQL Router 8.0 | 8.0.45 | 134 MB | Solo programma | ⚠️ configurazione router |
| 6 | MySQL Documents | 8.0.45 | 86,7 MB | Solo programma | — |
| 7 | MySQL Examples and Samples | 8.0.45 | 3,63 MB | Solo programma | — |

### Gruppo B — SQL Server 2025 + driver/tool (10 app, ~0,17 GB noto)

| # | App | Versione | Dimensione | Tipo dimensione | Dati da migrare |
|---|-----|----------|-----------:|-----------------|-----------------|
| 8 | Microsoft SQL Server 2025 Setup (English) | 17.0.1135.8 | 102 MB | Solo programma | — |
| 9 | Browser per SQL Server 2025 | 17.0.1000.7 | 25,2 MB | Solo programma | — |
| 10 | 🟨 Microsoft ODBC Driver 18 for SQL Server | 18.5.2.1 | 15,9 MB | Solo programma | — |
| 11 | 🟪 Microsoft OLE DB Driver 19 per SQL Server | 19.4.1.0 | 16,6 MB | Solo programma | — |
| 12 | 🟪 Microsoft OLE DB Driver per SQL Server (18) | 18.7.5.0 | 8,42 MB | Solo programma | — |
| 13 | 🟨 Microsoft ODBC Driver 17 for SQL Server | 17.10.6.1 | 4,35 MB | Solo programma | — |
| 14 | Microsoft System CLR Types per SQL Server 2019 | 15.0.2000.5 | 3,79 MB | Solo programma | — |
| 15 | Microsoft VSS Writer per SQL Server 2025 | 17.0.1000.7 | 2,77 MB | Solo programma | — |

### Programmi singoli con dati

| # | App | Versione | Dimensione | Tipo dimensione | Dati da migrare |
|---|-----|----------|-----------:|-----------------|-----------------|
| 16 | 🟥 Docker Desktop | 4.75.0 | 3,49 GB | Solo programma | ⚠️ immagini, volumi, compose |
| 17 | 🟥 Rancher Desktop | 1.22.3 | 2,23 GB | Solo programma | ⚠️ VM, immagini, impostazioni |
| 18 | MongoDB 8.2.3 2008R2Plus SSL (64 bit) | 8.2.3 | 2,02 GB | Solo programma | ⚠️ database (cartella dati) → dump |
| 19 | Microsoft Visual Studio Code | 1.146.0 | 1,06 GB | Solo programma | ⚠️ estensioni, `settings.json`, snippet |
| 20 | Debian (WSL) | n/d | 1,02 GB | **Programma + dati** | ⚠️ file utente nella distro → `wsl --export` |
| 21 | XAMPP | 8.2.12-0 | 773 MB | **Programma + dati** | ⚠️ `htdocs`, `mysql/data`, config |
| 22 | Google Chrome | 157.0.8103.79 | 512 MB | Solo programma | ⚠️ profilo (sync account) |
| 23 | FortiClient VPN | 7.4.3.4726 | 374 MB | Solo programma | ⚠️ profili VPN |
| 24 | SoapUI 5.9.1 | 5.9.1 | 275 MB | Solo programma | ⚠️ progetti |
| 25 | Oracle VirtualBox 7.2.6 | 7.2.6 | 234 MB | Solo programma | ⚠️ VM (dischi virtuali) |
| 26 | Postman x64 12.29.2 | 12.29.2 | 200 MB | Solo programma | ⚠️ collection, environment |
| 27 | AWS Command Line Interface v2 | 2.34.25.0 | 181 MB | Solo programma | ⚠️ `~/.aws` credenziali/config |

### Dimensione n/d (in fondo)

| # | App | Versione | Dimensione | Gruppo | Dati da migrare |
|---|-----|----------|-----------:|--------|-----------------|
| 28 | Microsoft SQL Server 2025 (64-bit) | n/d | n/d | Gruppo B | ⚠️ database, login → backup/restore |
| 29 | SQL Server Management Studio 22 | 22.1.0 | n/d | Gruppo B | ⚠️ connessioni, impostazioni |

---

## Lista 3 — Da installare SENZA dati da migrare (37 app, ~4,43 GB noto)

### Gruppo C — Visual Studio (5 app)

| # | App | Versione | Dimensione | Tipo dimensione |
|---|-----|----------|-----------:|-----------------|
| 1 | Microsoft Web Deploy 4.0 | 10.0.9419 | 15,4 MB | Solo programma |
| 2 | Microsoft .NET SDK 10.0.401 (x64) from Visual Studio | 40.11.21517 | 400 KB | Solo programma |
| 3 | vs_CoreEditorFonts | 17.7.40001 | 728 KB | Solo programma |
| 4 | Visual Studio Community 2026 | 18.9.3 | n/d | n/d |
| 5 | Microsoft Visual Studio Installer | 4.10.30.62513 | n/d | n/d |

### Programmi singoli

| # | App | Versione | Dimensione | Tipo dimensione |
|---|-----|----------|-----------:|-----------------|
| 6 | Adobe Acrobat (64-bit) | 26.002.22031 | 1,14 GB | Solo programma |
| 7 | Cisco Packet Tracer 9.0.0 64Bit | 9.0.0.810 | 715 MB | Solo programma |
| 8 | Arduino IDE 2.3.7 | 2.3.7 | 526 MB | Solo programma |
| 9 | 🟩 Java(TM) SE Development Kit 25.0.1 (64-bit) | 25.0.1.0 | 364 MB | Solo programma |
| 10 | Git | 2.53.0 | 329 MB | Solo programma |
| 11 | GitHub Desktop | 3.6.11 | 264 MB | Solo programma |
| 12 | Microsoft Windows Desktop Runtime - 9.0.16 (x64) | 9.0.16.36030 | 227 MB | Solo programma |
| 13 | VMware Tools | 12.5.4.24964629 | 135 MB | Solo programma |
| 14 | PowerShell | n/d | 149 MB | Solo programma |
| 15 | 🟧 Python 3.14.3 | 3.14-64 | 123 MB | Solo programma |
| 16 | 🟩 Java 8 Update 471 | 8.0.4710.9 | 105 MB | Solo programma |
| 17 | Node.js | 24.13.0 | 103 MB | Solo programma |
| 18 | 🟧 Python Install Manager | n/d | 97,5 MB | Solo programma |
| 19 | RunCat 365 | n/d | 64,4 MB | Solo programma |
| 20 | Sublime Text | n/d | 53,6 MB | Solo programma |
| 21 | Balatro Mod Manager | 0.4.0 | 27,5 MB | Solo programma |
| 22 | SourceTree | 3.4.30 | 23,4 MB | Solo programma |
| 23 | Microsoft Visual C++ v14 Redistributable (x64) | 14.50.35719.0 | 20,7 MB | Solo programma |
| 24 | Microsoft Visual C++ v14 Redistributable (x86) | 14.50.35719.0 | 18,2 MB | Solo programma |
| 25 | 7-Zip 25.01 (x64) | 25.01 | 5,62 MB | Solo programma |
| 26 | TranslucentTB | n/d | 3,38 MB | Solo programma |
| 27 | 🟧 Python Launcher | 3.14.2150.0 | 1,52 MB | Solo programma |

### Dimensione n/d (in fondo)

| # | App | Versione | Dimensione | Gruppo |
|---|-----|----------|-----------:|--------|
| 28 | 🟦 HashiCorp Terraform | 1.15.8 | n/d | — |
| 29 | 🟦 OpenTofu | 1.11.6 | n/d | — |
| 30 | Infracost | 0.10.44 | n/d | — |
| 31 | terraform-docs | v0.24.0 | n/d | — |
| 32 | Copilot CLI | v1.0.59 | n/d | — |
| 33 | jq | 1.8.1 | n/d | — |
| 34 | Dev-C++ | 5.11 | n/d | — |
| 35 | Microsoft 365 Apps for enterprise - it-it | 16.0.20527.20196 | n/d | — |
| 36 | Spotify | 1.2.99.317.g9bd8c54d | n/d | — |
| 37 | VLC media player | 3.0.21 | n/d | — |

---

## Riepilogo dimensioni

| Lista | App | Dimensione nota |
|-------|----:|----------------:|
| 1 — Preinstallate | 14 | ~1,92 GB |
| 2 — Da installare con dati | 29 | ~15,47 GB |
| 3 — Da installare senza dati | 37 | ~4,43 GB |

## Totale pacchetto

| Utente | Pacchetto | App | Dimensione complessiva |
|--------|-----------|----:|-----------------------:|
| _utente_ | **AWS_Dev_Package** | 80 | **~21,82 GB** (di cui ~19,90 GB da installare) |

## Note

- Totali = somma delle sole dimensioni note (1 GB = 1024 MB); le 18 app `n/d` non sono incluse.
- Le dimensioni sono quelle del programma installato, non dei file di installazione da scaricare.
- Dati da migrare = stima per tipo di software; verificare sulla macchina di origine (percorsi dati reali, DB da esportare con dump/backup).
- Classificazione preinstallata/da installare = stima da nomi app; verificare Microsoft 365 Apps, PowerShell.
- Le ridondanze 🟥🟦🟩🟨🟪🟧 sono solo da valutare: nulla è obbligatorio rimuovere.
