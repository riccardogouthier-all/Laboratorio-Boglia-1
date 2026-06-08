# Demo Docker Compose

Include una componente di back-end Python implementata con FastAPI che pubblica le API disponibili su Swagger e un DB PostgreSQL su cui vengono scritti i dati.

## Build, start, stop, gestione

Nelle sezioni seguenti sono elencati i comandi per gestire lo stack 

### Build dell’immagine Python

Eseguire il build dell’applicazione Python usando il Dockerfile nella cartella `app/`:

```bash
docker compose build
```

### Avvio servizi

Avviare tutti i servizi (app, db, pgAdmin) in background:

```bash
docker compose up -d
```

### Verificare stato container

```bash
docker compose ps
```

### Stop e teardown dello stack

Per fermare i container senza rimuoverli:

```bash
docker compose stop
```

Per fermare e rimuovere container, network e risorse temporanee:

```bash
docker compose down
```

### Gestione dei volumi del database:

Elenco dei volumi disponibili:

```bash
docker volume ls
```

Rimozione del volume del DB (elimina tutti i dati):

```bash
docker volume rm project_db-data
```

### Monitoraggio e gestione dei servizi

Visualizzare i log aggregati di tutti i servizi dello stack in tempo reale:

```bash
docker compose logs -f
```

Per riavviare un singolo servizio, ad es. l'app Python o il DB PostgreSQL (notare l'utilizzo del nome definito nel file docker-compose.yml):

```bash
docker compose restart app
docker compose restart db
docker compose restart pgadmin
```

### Re-build delle immagini dopo una modifica

Ricostruisce solo le immagini modificate e riavvia lo stack:

```bash
docker compose up -d --build
```

## Accesso ai servizi

Una volta avviato lo stack, le API Swagger sono disponibili alla URL:

http://localhost:8000/docs

Sono disponibili due API:

* GET /studenti (lista studenti, con nome, matricola e corso)
* POST /studenti (inserire nuovi studenti)

I dati sono salvati su PostgreSQL: ogni POST crea una riga nella tabella 
studenti.

I dati inseriti nel DB si possono visualizzare tramite pgAdmin:

http://localhost:8080

## Configurazione di pgAdmin

Dopo aver avviato lo stack, collegarsi alla URL di pgAdmin:

http://localhost:8080

- Utilizzare le credenziali predefinite (Email: admin@example.com, Password: admin)
- Aggiungere il server PostgreSQL cliccando su Add New Server
- Compilare i vari campi: nel Tab General inserire Name = demo-db, nel Tab: Connection inserire Host = db, Port = 5432,Username = demo, Password = demo, Database = demo
- Salva le modifiche ed eseguire connessione

### Visualizzazione tabelle in pgAdmin

Seguire il percorso:

```
Servers
  └── demo-db
        └── Databases
              └── demo
                    └── Schemas
                          └── public
                                └── Tables
```

Con il tasto destro selezionare View/Edit Data e poi All Rows oppure utilizzare il Query Tool:

```bash
SELECT * FROM studenti;
```

## Creazione diagrammi UML (opzionale)

Aprire il progetto con VSCode, installare l'estensione PlantUML oppure copiare il contenuto dei file .puml sul server online PlantUML.