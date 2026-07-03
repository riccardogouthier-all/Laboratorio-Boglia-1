# MusicLab – Catalogo Musicale a Microservizi

Applicazione di gestione di un catalogo musicale (canzoni + playlist),
riorganizzata da monolite a **architettura a microservizi** con Docker
Compose, registry Docker locale, message broker e monitoraggio via
Portainer.

Scenario:       Gestione canzoni + playlist. 
Microservizi:   Docker Compose, registry locale, message broker, monitoraggio Portainer.

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
                         ┌─────────────────────────▼────┐
                         │  api-gateway (Nginx)         │
                         │  /api/canzoni  /api/playlist │
                         └──┬───────────────────────┬───┘
                            │ rete "backend-net"    │
                 ┌──────────▼─────────┐      ┌──────▼──────────────────┐
                 │   songs-service    │      │    playlist-service     │
                 │ Node/Express :4001 │      │  Python/FastAPI :4002   │
                 │  SQLite: songs.db  │      │  SQLite: playlist.db    │
                 └─────────┬──────────┘      └──────────────┬──────────┘
                           │      pubblica eventi           │ consuma eventi
                           │      (song.created/            │ (aggiorna cache
                           │       updated/deleted)         │  locale canzoni)
                           └───────────►  RabbitMQ  ◄───────┘
                                     (message broker)

   Servizi di supporto (non nel flusso applicativo):
   - registry:2      → registry Docker locale (push/pull immagini)
   - portainer-ce    → monitoraggio/deploy dello stack
```

| Componente | Stack | Porta interna | DB |
|---|---|---|---|
| frontend | Nginx statico + proxy `/api/*` | 80 (esposta 8080) | - |
| api-gateway | Nginx reverse proxy | 80 | - |
| songs-service | Node.js/Express, SQLite | 4001 | `songs.db` |
| playlist-service | Python/FastAPI, SQLite | 4002 | `playlist.db` |
| rabbitmq | RabbitMQ 3.13 management | 5672 / 15672 | - |
| registry | registry:2 | 5000 | - |
| portainer | portainer-ce:2.21.4 | 9443 | - |


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

---

## 2. Struttura progetto

```
musiclab-microservices/
├── docker-compose.yml
├── docker-compose.override.yml.example   # espone porte debug (Swagger/FastAPI docs)
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
│   ├── db/schema.js
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

## 3. Accesso ai servizi

| Servizio | URL | Note |
|---|---|---|
| App web | http://localhost:8080 | Frontend MusicLab |
| RabbitMQ management | http://localhost:15672 | user/pass da `.env` |
| Registry | http://localhost:5000/v2/_catalog | elenco immagini |
| Portainer | https://localhost:9443 | crea admin al primo accesso |

Con `docker-compose.override.yml.example` rinominato in `.override.yml`: Swagger songs-service su `:4001/api-docs`, docs FastAPI playlist-service su `:4002/docs`.

---

## 4. Registry Docker locale

Immagini già taggate `${REGISTRY_HOST}/musiclab/<servizio>:1.0.0`.

```bash
docker compose build
docker compose push
curl http://localhost:5000/v2/_catalog
# → {"repositories":["musiclab/api-gateway","musiclab/frontend","musiclab/playlist-service","musiclab/songs-service"]}
docker compose pull
```

Deploy "da zero" solo da registry, senza build:

```bash
docker compose down
docker compose pull
docker compose up -d --no-build
```

> Registry senza auth (uso didattico). In produzione: TLS + htpasswd.

---

## 5. Scalabilità

```bash
docker compose up -d --scale playlist-service=3 --scale songs-service=2
```

- HTTP verso i servizi: distribuito da api-gateway via DNS interno Docker (round-robin)
- Eventi RabbitMQ: competing consumers, ogni messaggio elaborato da 1 sola replica

Verifica:

```bash
docker compose ps playlist-service
```

> SQLite in WAL regge repliche a basso volume. Scaling reale in produzione → PostgreSQL/MySQL (cambia solo il layer di accesso dati).

---

## 6. Portainer

1. https://localhost:9443 (certificato self-signed, accetta l'avviso)
2. Crea utente admin al primo accesso
3. Seleziona ambiente **local** (socket Docker già montato)
4. **Containers**: stato, log, CPU/RAM dello stack `musiclab`
5. **Images**: immagini pull/push verso registry locale

### Deploy da Portainer (opzionale)

1. Stacks → Add stack, nome `musiclab`
2. Upload `docker-compose.yml` o Web editor
3. Environment variables: stesse chiavi di `.env` (`REGISTRY_HOST`, `RABBITMQ_DEFAULT_USER`, `RABBITMQ_DEFAULT_PASS`, `RABBITMQ_URL`), o carica `.env` direttamente
4. Deploy the stack

File già "Portainer-ready": nomi servizi/reti/volumi espliciti, nessun path host tranne socket Docker per Portainer stesso.

---

## 7. Differenze dal monolite originale

- Frontend: URL API hardcoded (`http://localhost:3000/api`) → relativo (`/api`), proxato dallo stesso Nginx (niente CORS)
- Bug fix: `openPlaylistModal()` cercava `PlaylistModal` invece di `playlistModal` (modal non si apriva)
- DB separati per servizio, cascata gestita via eventi RabbitMQ invece che FOREIGN KEY SQL
- Swagger UI (songs-service, `/api-docs`) e docs FastAPI (playlist-service, `/docs`) raggiungibili solo con override

---

## 8. Troubleshooting

| Sintomo | Causa | Soluzione |
|---|---|---|
| playlist-service non mostra titolo/artista in playlist appena create | cache locale non ancora sincronizzata | attendere qualche secondo, o `docker compose logs -f playlist-service` |
| Container `unhealthy` | RabbitMQ non pronto | attendere, `depends_on: condition: service_healthy` gestisce l'ordine |
| `docker compose push` fallisce | registry non raggiungibile | `docker compose ps registry` |
| Porta 8080/5672/15672/5000/9443 occupata | conflitto locale | modifica mapping porte in `docker-compose.yml` |

---

## 9. Procedura di installazione da zero

### 9.1 Prerequisiti

- Docker Engine ≥ 24
- Docker Compose v2 (`docker compose`, non il vecchio `docker-compose`)
- ~2 GB spazio libero

```bash
docker --version
docker compose version
```

### 9.2 Configurazione

```bash
cd musiclab-microservices
cp .env.example .env
```

Valori di default in `.env` già sufficienti per uso locale.

### 9.3 Build immagini

```bash
docker compose build
```

Costruisce 4 immagini: `songs-service`, `playlist-service`, `api-gateway`, `frontend`.

### 9.4 Avvio stack

```bash
docker compose up -d
docker compose ps
```

Tutti i servizi con healthcheck devono risultare `healthy` dopo 15-30s (DB SQLite e tabelle creati automaticamente al primo avvio).

### 9.5 Verifica

- App: http://localhost:8080
- RabbitMQ UI: http://localhost:15672 (credenziali da `.env`)
- Registry: `curl http://localhost:5000/v2/_catalog`
- Portainer: https://localhost:9443

### 9.6 Arresto

```bash
docker compose down          # ferma/rimuove container, dati restano nei volumi
docker compose down -v       # ferma + cancella volumi (reset completo)
```