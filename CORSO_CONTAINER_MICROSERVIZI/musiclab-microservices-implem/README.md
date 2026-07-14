# MusicLab – Catalogo Musicale a Microservizi

Applicazione di gestione di un catalogo musicale (canzoni + playlist),
riorganizzata da monolite a **architettura a microservizi** con Docker
Compose, registry Docker locale, message broker e monitoraggio via
Portainer.

Scenario: gestione di canzoni e playlist (diverso dall'esempio "gestione
studenti" usato a lezione).

---

## 1. Architettura

```
                         ┌───────────────────────────┐
   Browser  ───────────► │   frontend (Nginx, :8080) │
                         │   serve index.html        │
                         │   + proxy /api/* ───────┐ │
                         └─────────────────────────┼─┘
                                                   │
                                  rete "public-net"│
                         ┌─────────────────────────▼───────┐
                         │  api-gateway (Nginx)            │
                         │  /api/canzoni  /api/playlist    │
                         └───────┬───────────────────────┬─┘
                                 │ rete "backend-net"    │
                 ┌───────────────▼────┐      ┌────────────▼────────────┐
                 │  songs-service     │      │  playlist-service       │
                 │  Node.js / Express │      │  Python / FastAPI       │
                 │  SQLite: songs.db  │      │  SQLite: playlist.db    │
                 └─────────┬──────────┘      └────────────┬────────────┘
                           │      pubblica eventi         │ consuma eventi
                           │      (song.created/          │ (aggiorna cache
                           │       updated/deleted)       │  locale canzoni)
                           └───────────►  RabbitMQ  ◄─────┘
                                     (message broker)

   Servizi di supporto (non nel flusso applicativo):
   - registry:2      → registry Docker locale (push/pull immagini)
   - portainer-ce    → monitoraggio/deploy dello stack
```

**Perché due linguaggi diversi?** `songs-service` è in Node.js/Express
(continuità con il codice originale), `playlist-service` è stato riscritto
in Python/FastAPI: dimostra che i microservizi comunicano solo tramite
API HTTP ed eventi asincroni, senza dipendere dal linguaggio con cui sono
implementati.

**Perché un message broker?** Nel monolite originale, cancellare una
canzone eliminava automaticamente le sue associazioni nelle playlist
grazie a una `FOREIGN KEY ... ON DELETE CASCADE` **nello stesso database**.
In un'architettura a microservizi ogni servizio ha il proprio database
(`songs.db` e `playlist.db` sono separati), quindi questa integrità va
gestita in modo asincrono:

- `songs-service` pubblica su RabbitMQ (exchange `songs.events`, tipo
  `topic`) gli eventi `song.created`, `song.updated`, `song.deleted`;
- `playlist-service` mantiene una **cache locale** delle canzoni
  (tabella `canzoni_cache`) aggiornata consumando questi eventi, e
  rimuove le associazioni playlist↔canzone quando una canzone viene
  cancellata.

Questo disaccoppia i due servizi (uno può essere giù/lento senza bloccare
l'altro) ed è anche il meccanismo di **scalabilità**: se scali
`playlist-service` su più repliche, tutte le istanze si mettono in
ascolto sulla stessa coda (`playlist_songs_sync`) e RabbitMQ distribuisce
i messaggi tra loro (pattern *competing consumers*).

### 1.1 Catalogo reale precaricato + streaming audio

Al primo avvio (database vuoto), `songs-service` carica il catalogo da
`db/catalogo.csv` — **2180 brani reali** (colonne `Titolo, Artista,
Album, Genere, Anno, Durata`), ottenuti unendo un export Exportify da
Spotify a un catalogo di base e deduplicando su chiave Titolo+Artista —
e pubblica un evento `song.created` per ciascuno, così `playlist-service`
sincronizza subito la propria cache: l'app è quindi già utilizzabile,
con canzoni pronte da inserire nelle playlist, senza inserimenti manuali
necessari.

Ogni canzone ha un campo `file_audio` e può essere riprodotta dal
frontend (pulsante ▶ nella tabella canzoni e nel dettaglio playlist,
player fisso in basso) tramite:

```
GET /api/canzoni/{id}/audio
```

**Nota sui file audio**: per ora sono presenti solo due file audio per le prime due canzoni del file csv dal quale vengono caricate le canzoni

---

## 2. Prerequisiti

- Docker Engine ≥ 24
- Docker Compose v2 (comando `docker compose`, non il vecchio `docker-compose`)
- Circa 2 GB di spazio libero per le immagini

Verifica:

```bash
docker --version
docker compose version
```

---

## 3. Setup da zero

### 3.1 Configurazione

```bash
cd musiclab-microservices
cp .env.example .env
```

Il file `.env` contiene le credenziali di RabbitMQ e l'host del registry.
Per un uso puramente locale i valori di default vanno già bene.

### 3.2 Build delle immagini

```bash
docker compose build
```

Verranno costruite 4 immagini: `songs-service`, `playlist-service`,
`api-gateway`, `frontend`.

### 3.3 Avvio dello stack

```bash
docker compose up -d
```

Verifica lo stato dei container:

```bash
docker compose ps
```

Tutti i servizi con healthcheck devono risultare `healthy` dopo circa
15-30 secondi (i database SQLite e le tabelle vengono creati
automaticamente al primo avvio).

### 3.4 Accesso ai servizi

| Servizio                  | URL                              | Note                                   |
|---------------------------|-----------------------------------|----------------------------------------|
| Applicazione web          | http://localhost:8080            | Frontend MusicLab                      |
| RabbitMQ management UI    | http://localhost:15672           | utente/password da `.env`              |
| Registry Docker           | http://localhost:5000/v2/_catalog| elenco immagini nel registry           |
| Portainer                 | https://localhost:9443           | creare l'utente admin al primo accesso |

### 3.5 Arresto

```bash
docker compose down          # ferma e rimuove i container (i dati restano nei volumi)
docker compose down -v       # ferma e cancella anche i volumi (reset completo)
```

---

## 4. Registry Docker locale (push / pull)

Il registry (`registry:2`) è già incluso nello stack e parte insieme
agli altri servizi, sulla porta `5000`.

Le immagini nel `docker-compose.yml` sono già taggate con il prefisso
del registry (`${REGISTRY_HOST}/musiclab/<servizio>:1.0.0`), quindi
build/push/pull funzionano direttamente con i comandi di Compose:

```bash
# 1. build locale delle immagini
docker compose build

# 2. push delle immagini nel registry locale
docker compose push

# 3. verifica che le immagini siano nel registry
curl http://localhost:5000/v2/_catalog
# → {"repositories":["musiclab/api-gateway","musiclab/frontend","musiclab/playlist-service","musiclab/songs-service"]}

# 4. pull (es. su un'altra macchina/ambiente collegata allo stesso registry)
docker compose pull
```

Per simulare un deploy "da zero" scaricando solo dal registry (senza
ricompilare):

```bash
docker compose down
docker compose pull
docker compose up -d --no-build
```

> Nota: questo registry non ha autenticazione (uso didattico/locale).
> In produzione andrebbe protetto con TLS e credenziali
> (`registry:2` supporta `htpasswd` e certificati out-of-the-box).

---

## 5. Scalabilità con il message broker

Scalare i microservizi che consumano eventi da RabbitMQ:

```bash
docker compose up -d --scale playlist-service=3 --scale songs-service=2
```

- Le richieste HTTP verso `songs-service`/`playlist-service` vengono
  distribuite dall'`api-gateway`, che risolve il nome del servizio via
  DNS interno di Docker ad ogni richiesta (round-robin tra le repliche).
- Gli eventi RabbitMQ pubblicati da `songs-service` vengono consumati
  in modalità *competing consumers*: se `playlist-service` ha 3
  repliche, ciascun messaggio viene elaborato da **una sola** di esse,
  distribuendo il carico di sincronizzazione.

Verifica le repliche attive:

```bash
docker compose ps playlist-service
```

> Nota tecnica: SQLite non è pensato per scritture concorrenti da più
> processi su larga scala. Qui è usato in modalità WAL per gestire più
> repliche in lettura/scrittura a basso volume; per uno scenario di
> produzione con scaling reale si sostituirebbe con PostgreSQL/MySQL
> (il codice applicativo cambierebbe solo nel layer di accesso ai dati).

---

## 6. Monitoraggio (e deploy opzionale) con Portainer

1. Apri **https://localhost:9443** (certificato self-signed: accetta
   l'avviso del browser).
2. Al primo accesso crea l'utente amministratore.
3. Seleziona l'ambiente **"local"** (il socket Docker è già montato nel
   container Portainer tramite `docker-compose.yml`).
4. In **Containers** trovi tutti i container dello stack `musiclab`,
   con stato, log, statistiche CPU/RAM in tempo reale.
5. In **Images** puoi vedere le immagini pull-ate/pushate verso il
   registry locale.

### Deploy dello stack direttamente da Portainer (opzionale)

Invece di usare `docker compose up` da riga di comando, lo stesso file
`docker-compose.yml` può essere usato per creare uno **Stack** in
Portainer:

1. Menu laterale → **Stacks** → **Add stack**.
2. Nome: `musiclab`.
3. Build method: **Upload** (carica `docker-compose.yml`) oppure
   **Web editor** (incolla il contenuto del file).
4. In **Environment variables** aggiungi le stesse chiavi presenti in
   `.env` (`REGISTRY_HOST`, `RABBITMQ_DEFAULT_USER`,
   `RABBITMQ_DEFAULT_PASS`, `RABBITMQ_URL`), oppure carica direttamente
   il file `.env`.
5. **Deploy the stack**.

Portainer richiama internamente lo stesso motore di Docker Compose, per
cui il file non richiede modifiche: è già "Portainer-ready" (nomi dei
servizi, reti e volumi espliciti, nessun path relativo all'host tranne
il socket Docker per Portainer stesso).

---

## 7. Struttura del progetto

```
musiclab-microservices/
├── docker-compose.yml
├── docker-compose.override.yml.example   # espone porte di debug (Swagger/FastAPI docs)
├── .env.example
├── README.md
├── frontend/                # Nginx + index.html statico
│   ├── Dockerfile
│   ├── nginx.conf
│   └── index.html
├── api-gateway/              # Nginx reverse proxy
│   ├── Dockerfile
│   └── nginx.conf
├── songs-service/            # Node.js / Express / SQLite
│   ├── Dockerfile
│   ├── package.json
│   ├── server.js
│   ├── db/
│   │   ├── schema.js
│   │   ├── catalogo.csv      # catalogo reale: 2180 brani (Titolo, Artista, Album, Genere, Anno, Durata)
│   │   └── seed.js           # popola il DB al primo avvio dal csv (idempotente)
│   ├── tracce-audio/         # contiene le canzoni in formato musicale, da collegare al tasto play in front end
│   ├── routes/canzoniRouter.js
│   ├── events/publisher.js
│   └── doc/swagger.json
└── playlist-service/         # Python / FastAPI / SQLite
    ├── Dockerfile
    ├── requirements.txt
    ├── main.py
    ├── db.py
    ├── routers/playlist.py
    └── events/consumer.py
```

---

## 8. Differenze rispetto al monolite originale (e miglioramenti applicati)

- **Frontend**: l'URL delle API era hardcoded (`http://localhost:3000/api`),
  reso relativo (`/api`) così il frontend funziona con qualsiasi host/porta
  di deploy, proxato dallo stesso Nginx che serve i file statici (niente CORS).
- **Bug fix**: in `openPlaylistModal()` il codice cercava l'elemento
  `PlaylistModal` (con la P maiuscola) invece di `playlistModal`,
  impedendo l'apertura del modal di creazione/modifica playlist.
- **Separazione dei dati**: `canzoni` e `playlist` non condividono più lo
  stesso database; l'integrità referenziale (cascata alla cancellazione
  di una canzone) è ora garantita in modo asincrono via eventi RabbitMQ
  invece che da una `FOREIGN KEY` SQL nello stesso DB.
- **Documentazione API**: `songs-service` espone Swagger UI su
  `/api-docs`, `playlist-service` espone i docs automatici di FastAPI su
  `/docs` (entrambi raggiungibili solo abilitando
  `docker-compose.override.yml.example`, per non esporre i servizi
  interni in condizioni normali).
- **Catalogo dati**:catalogo reale di 2180 brani, ottenuto unendo un
  export Exportify (Spotify) al catalogo di base e deduplicando su
  Titolo+Artista.

---

## 9. Troubleshooting rapido

| Sintomo | Causa probabile | Soluzione |
|---|---|---|
| `playlist-service` non mostra titolo/artista nelle playlist appena create | la cache locale non è stata ancora sincronizzata | attendere qualche secondo dopo aver creato la canzone, oppure verificare i log: `docker compose logs -f playlist-service` |
| Container in stato `unhealthy` | RabbitMQ non ancora pronto | attendere, `depends_on: condition: service_healthy` gestisce l'ordine di avvio |
| `docker compose push` fallisce | registry non raggiungibile | verificare che il container `registry` sia `Up`: `docker compose ps registry` |
| Porta 8080/5672/15672/5000/9443 già in uso | conflitto con altri servizi locali | modificare il mapping delle porte nel `docker-compose.yml` |