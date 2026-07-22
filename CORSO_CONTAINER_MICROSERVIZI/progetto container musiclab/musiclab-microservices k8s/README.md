# MusicLab – Deploy su Kubernetes

Migrazione dello stack MusicLab (canzoni + playlist) da **Docker Compose**
a **Kubernetes**: stessi microservizi, stesso message broker, ma
orchestrazione, self-healing, scalabilità e networking gestiti dal
cluster invece che dal Docker Engine.

Scenario:       Gestione canzoni + playlist.
Microservizi:   Deployment/Service/Ingress k8s, PersistentVolumeClaim, Secret/ConfigMap, message broker.

---

## 1. Architettura

```
                         ┌──────────────────────────────┐
   Browser  ───────────► │  Ingress (musiclab.local)    │
                         └──────────────┬───────────────┘
                                        │
                         ┌──────────────▼───────────────┐
                         │  Service "frontend" (Nginx)   │
                         │  serve index.html             │
                         │  + proxy /api/* ─────────┐    │
                         └──────────────────────────┼────┘
                                                    │
                         ┌──────────────────────────▼────┐
                         │  Service "api-gateway" (Nginx)│
                         │  /api/canzoni  /api/playlist  │
                         └──┬───────────────────────┬────┘
                            │                       │
                 ┌──────────▼─────────┐      ┌──────▼──────────────────┐
                 │ Service            │      │ Service                 │
                 │ "songs-service"    │      │ "playlist-service"      │
                 │ Node/Express :8000 │      │ Python/FastAPI :8001    │
                 │ PVC: songs-data    │      │ PVC: playlist-data      │
                 └─────────┬──────────┘      └──────────────┬──────────┘
                           │      pubblica eventi           │ consuma eventi
                           │      (song.created/            │ (aggiorna cache
                           │       updated/deleted)         │  locale canzoni)
                           └───────────►  Service   ◄───────┘
                                     "rabbitmq" (broker)
                                     PVC: rabbitmq-data

   Namespace: musiclab (tutte le risorse sopra vivono qui)
```

| Componente | Risorse k8s | Porta Service | Storage |
|---|---|---|---|
| frontend | Deployment + Service + Ingress | 80 | - |
| api-gateway | Deployment + Service | 80 | - |
| songs-service | Deployment + Service | 8000 | PVC `songs-data` |
| playlist-service | Deployment + Service | 8001 | PVC `playlist-data` |
| rabbitmq | Deployment + Service | 5672 / 15672 | PVC `rabbitmq-data` |
| musiclab-secret | Secret | - | credenziali RabbitMQ |
| musiclab-config | ConfigMap | - | path DB, registry |

**Perché Deployment invece di Pod singoli?** Un Deployment garantisce
self-healing (Pod ricreato se crasha) e permette di scalare le repliche
con un solo comando, sostituendo `restart: unless-stopped` e
`docker compose up -d --scale` di Compose.

**Perché Secret e ConfigMap separati?** Le credenziali RabbitMQ (Secret)
non devono mai finire in chiaro nei manifest versionati; i path dei DB
e altre variabili non sensibili (ConfigMap) restano invece leggibili e
modificabili senza toccare il codice, stesso principio del file `.env`
di Compose ma con la sensibilità dei dati separata a livello di risorsa.

**Perché un initContainer che attende RabbitMQ?** Kubernetes non ha un
equivalente diretto di `depends_on: condition: service_healthy`;
l'initContainer (`wait-for-rabbitmq`) rimanda l'avvio dei container
applicativi finché la porta 5672 non risponde, riproducendo lo stesso
ordinamento di avvio del compose originale.

---

## 2. Struttura progetto

```
musiclab-microservices/
├── k8s/
│   ├── kustomization.yaml
│   ├── 00-namespace.yaml
│   ├── 01-secret.yaml
│   ├── 02-configmap.yaml
│   ├── 03-pvc.yaml
│   ├── 10-rabbitmq.yaml
│   ├── 11-songs-service.yaml
│   ├── 12-playlist-service.yaml
│   ├── 13-api-gateway.yaml
│   ├── 14-frontend.yaml
│   └── 20-ingress.yaml
├── frontend/                # stesso Dockerfile/nginx.conf di Compose
├── api-gateway/              # stesso Dockerfile/nginx.conf di Compose
├── songs-service/            # stesso codice Node.js/Express/SQLite
└── playlist-service/         # stesso codice Python/FastAPI/SQLite
```

Nessun file applicativo è stato modificato: la migrazione riguarda solo
il layer di orchestrazione (`k8s/*.yaml` sostituisce `docker-compose.yml`).

---

## 3. Accesso ai servizi

| Servizio | URL | Note |
|---|---|---|
| App web | http://musiclab.local | via Ingress, aggiungi `127.0.0.1 musiclab.local` a `/etc/hosts` |
| RabbitMQ management | `kubectl port-forward -n musiclab svc/rabbitmq 15672:15672` poi http://localhost:15672 | user/pass da Secret `musiclab-secret` |
| Dashboard cluster | `kubectl proxy` + Kubernetes Dashboard, oppure Lens/K9s | sostituisce Portainer |

Senza Ingress Controller installato, per test rapidi:

```bash
kubectl -n musiclab port-forward svc/frontend 8080:80
```

---

## 4. Immagini e registry

Stesso schema di tag di Compose (`${REGISTRY_HOST}/musiclab/<servizio>:1.0.0`),
ma il cluster deve poter *raggiungere* il registry: se è quello locale
(`registry:2` di `services-compose.yml`), va reso raggiungibile dai nodi
(es. Minikube: `minikube image load`, kind: `kind load docker-image`) o
sostituito con un registry esterno (Docker Hub, GHCR, ECR...).

```bash
docker compose build
docker tag localhost:5000/musiclab/songs-service:1.0.0 <tuo-registry>/musiclab/songs-service:1.0.0
docker push <tuo-registry>/musiclab/songs-service:1.0.0
# ripeti per playlist-service, api-gateway, frontend
```

Poi aggiorna il campo `image:` nei manifest in `k8s/1x-*.yaml` con il
nuovo registry, o usa `kustomize edit set image`.

> Senza autenticazione sul registry serve anche un `imagePullSecret` se il registry è privato.

---

## 5. Scalabilità

```bash
kubectl -n musiclab scale deployment/playlist-service --replicas=3
kubectl -n musiclab scale deployment/songs-service --replicas=2
```

- HTTP verso i servizi: distribuito dal Service k8s (load balancing L4 nativo, round-robin)
- Eventi RabbitMQ: competing consumers, ogni messaggio elaborato da 1 sola replica (invariato rispetto a Compose)

Verifica:

```bash
kubectl -n musiclab get pods -l app=playlist-service
```

Per scalare in automatico in base al carico:

```bash
kubectl -n musiclab autoscale deployment/playlist-service --min=1 --max=5 --cpu-percent=70
```

> **Attenzione SQLite + repliche:** i PVC `songs-data`/`playlist-data` sono `ReadWriteOnce`: con più repliche dello stesso Deployment, solo un Pod alla volta può montarli in scrittura (a differenza del volume Docker locale, condivisibile tra repliche su singolo nodo). Per scalare davvero servono uno storage `ReadWriteMany` (es. NFS) oppure la migrazione a PostgreSQL/MySQL, esattamente come già indicato nel README originale per Compose.

---

## 6. Dashboard del cluster (sostituisce Portainer)

1. `kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.7.0/aio/deploy/recommended.yaml`
2. `kubectl proxy`
3. Apri http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/
4. Login con token di un ServiceAccount con i permessi opportuni

In alternativa, per uso locale/didattico: **Lens** o **K9s** (nessun
deploy aggiuntivo nel cluster, si connettono al kubeconfig esistente).

### Deploy da manifest (equivalente a "Add stack" di Portainer)

```bash
kubectl apply -k k8s/
```

---

## 7. Differenze rispetto allo stack Docker Compose

- Networking: le reti Docker (`public-net`, `backend-net`) diventano Service k8s risolti via DNS interno del cluster (`<nome-service>.<namespace>.svc.cluster.local`)
- Health/restart: `restart: unless-stopped` + `depends_on: condition: service_healthy` → readiness/liveness probe + initContainer
- Esposizione esterna: porta pubblicata `8080:80` → risorsa Ingress (o port-forward/NodePort in locale)
- Persistenza: volumi Docker nominati → PersistentVolumeClaim
- Credenziali: variabili in `.env` → risorsa Secret dedicata
- Portainer/registry locale (`services-compose.yml`) → Dashboard k8s/Lens per il monitoraggio, registry esterno o reso raggiungibile dal cluster

---

## 8. Troubleshooting

|                              Sintomo                                 |                Causa                          |                              Soluzione                                          |
|------------------------------------------------------------------------|-----------------------------------------------|----------------------------------------------------------------------------------|
| playlist-service non mostra titolo/artista in playlist appena create   | cache locale non ancora sincronizzata          | attendere qualche secondo, o `kubectl -n musiclab logs -f deploy/playlist-service` |
| Pod resta in `Init:0/1`                                                | RabbitMQ non ancora pronto                     | normale, l'initContainer `wait-for-rabbitmq` attende; verifica con `kubectl -n musiclab get pods` |
| Pod in `CrashLoopBackOff`                                              | probe `/health` fallisce o immagine non trovata| `kubectl -n musiclab describe pod <nome>` e `kubectl -n musiclab logs <nome>`     |
| `ImagePullBackOff`                                                     | registry non raggiungibile dal cluster         | verifica `image:` nel manifest e presenza di un `imagePullSecret` se privato      |
| Ingress non risponde                                                   | Ingress Controller non installato               | installa Traefik o ingress-nginx nel cluster, oppure usa `kubectl port-forward`   |

---

## 9. Procedura di installazione da zero

### 9.1 Prerequisiti

- Un cluster Kubernetes funzionante (Minikube, kind, k3s o un cluster gestito)
- `kubectl` ≥ 1.28 configurato sul cluster target
- Immagini `musiclab/*` già buildate e pubblicate su un registry raggiungibile dal cluster (vedi sezione 4)

```bash
kubectl version --client
kubectl cluster-info
```

### 9.2 Configurazione

```bash
cd musiclab-microservices
```

Le credenziali di default sono già in `k8s/01-secret.yaml`; per un
ambiente diverso da quello locale, modificale prima di applicare i
manifest (o gestiscile con un secret manager esterno).

### 9.3 Creazione delle risorse

```bash
kubectl apply -k k8s/
```

Crea nell'ordine: namespace, Secret, ConfigMap, PVC, poi i Deployment/Service di rabbitmq, songs-service, playlist-service, api-gateway, frontend, infine l'Ingress.

### 9.4 Avvio e verifica

```bash
kubectl -n musiclab get pods -w
```

Attendi che tutti i Pod risultino `Running` e `1/1 Ready` (RabbitMQ
richiede qualche secondo in più per il proprio readiness probe).

### 9.5 Verifica finale

- App: http://musiclab.local (con Ingress) oppure `kubectl -n musiclab port-forward svc/frontend 8080:80`
- RabbitMQ UI: `kubectl -n musiclab port-forward svc/rabbitmq 15672:15672` → http://localhost:15672
- Stato risorse: `kubectl -n musiclab get all`

### 9.6 Arresto

```bash
kubectl delete -k k8s/                 # rimuove tutte le risorse, i PVC restano (dati preservati)
kubectl delete namespace musiclab      # reset completo, cancella anche i dati nei PVC
```