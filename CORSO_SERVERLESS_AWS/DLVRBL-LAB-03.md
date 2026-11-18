# Laboratorio 03 - Fondamenti Serverless e Confronto Architetturale

Lavoro di gruppo (Gruppo 2: Matteo Ninotti / Riccardo Gouthier / Ivan Cioffi).

## Scenario

QuickOrder: startup di ordini online. Traffico spiky: ~500 ordini/giorno in media, fino a 3.000 ordini/ora nel weekend. Confronto tra tre architetture con stesso carico (utenti, catalogo, ordini, pagamenti).

## Architetture a confronto

### 1. Monolitica

```
Internet / Utenti
      |
Application Load Balancer
      |
      +--> EC2 t3.medium #1 (moduli Utenti, Catalogo, Ordini, Pagamenti) --+
      +--> EC2 t3.medium #2 (moduli Utenti, Catalogo, Ordini, Pagamenti) --+
                                                                           v
                                                  RDS MySQL db.t3.small (database condiviso)
```

### 2. Microservizi

```
Internet / Utenti
      |
API Gateway (entry point + routing)
      |
ECS Fargate (2 task / servizio, 0.25 vCPU, 0.5 GB RAM ciascuno)
  +-- Utenti    --> DynamoDB (tabella utenti)
  +-- Catalogo  --> DynamoDB (tabella catalogo)
  +-- Ordini    --> RDS MySQL (DB ordini)
  +-- Pagamenti --> RDS MySQL (DB pagamenti)
```

### 3. Serverless

```
Internet / Utenti
      |
API Gateway (routing per path)
  +-- Lambda Utenti     (256 MB / 200 ms, ~5k req/mese)  --+
  +-- Lambda Catalogo   (256 MB / 200 ms, ~30k req/mese) --+--> DynamoDB on-demand (4 tabelle)
  +-- Lambda Ordini     (256 MB / 200 ms, ~15k req/mese) --> SNS Topic (notifiche ordine) --+
  +-- Lambda Pagamenti  (256 MB / 200 ms, ~15k req/mese) --+--> DynamoDB on-demand (tabelle ordini / pagamenti)
```

## Tabella consumi (costo mensile)

| Monolitica | Microservizi | Serverless |
|---|---|---|
| ~142 $ | ~106 $ | < 1 $ |

## Tabella confronti

Stima manuale con i prezzi pubblici on-demand di us-east-1 (730 h/mese, carico medio di ~500 ordini/giorno, ~65.000 richieste/mese in totale). I picchi da 3.000 ordini/ora (< 1 richiesta/s) non cambiano il costo: i 2 EC2 e i task Fargate li reggono, Lambda scala da sola.

| Componente | Monolite | Microservizi | Serverless |
|---|---|---|---|
| Compute | ~61 $ (2 x t3.medium a 0,0416 $/h) | ~72 $ (8 task Fargate da 0,25 vCPU / 0,5 GB: 4 servizi x 2 task, ~9 $ ciascuno) | 0 $ (4 Lambda, 65.000 richieste e ~3.250 GB-s dentro il free tier) |
| Bilanciamento / entry point | ~22 $ (ALB: 16,43 $ fissi + LCU) | ~0,23 $ (API Gateway REST, 3,50 $ per milione) | ~0,23 $ (API Gateway REST) |
| Database | ~59 $ (RDS MySQL db.t3.small Multi-AZ + 20 GB) | ~34 $ (2 RDS db.t3.micro single-AZ per Ordini e Pagamenti + 2 tabelle DynamoDB on-demand) | < 1 $ (4 tabelle DynamoDB on-demand) |
| **Prezzo mensile** | **~142 $** | **~106 $** | **< 1 $** |

Fonte: prezzi pubblici AWS ricalcolati a mano. Gli screenshot dell'AWS Pricing Calculator non sono allegati: le cifre del Calculator vanno confrontate con questa tabella e, se diverse, vanno motivate (per esempio storage, traffico di rete o tariffe di un'altra Region).

## Considerazioni finali

**Raccomandazione: architettura serverless per QuickOrder.**

Il traffico è spiky (500 ordini/giorno in media, fino a 3.000 ordini/ora nel weekend), pattern ideale per serverless:

- **Costo variabile**: si pagano solo le ~15k richieste effettive/mese, non i server inattivi di notte.
- **Scaling automatico**: Lambda gestisce i picchi senza configurazione, da 0 a migliaia di esecuzioni parallele in millisecondi.
- **Time-to-market**: una startup paga meno di 1 $/mese e si concentra sul prodotto, non sull'infrastruttura.

**Limite**: cold start Lambda (~200-500 ms) per richieste rare. Mitigabile con **Provisioned Concurrency** (pre-inizializza un numero definito di ambienti di esecuzione, eliminando i cold start).

Procedura di esecuzione in CLI Cloudshell:

Il laboratorio confronta tre architetture (nessuna risorsa da creare). In CloudShell si riproduce il calcolo del carico Lambda e dei costi mensili delle tre architetture.

```bash
awk 'BEGIN {
  # Richieste mensili per servizio (256 MB, 200 ms)
  utenti=5000; catalogo=30000; ordini=15000; pagamenti=15000
  req = utenti + catalogo + ordini + pagamenti
  gbs = req * 0.2 * 0.25
  free_gbs = 400000; free_req = 1000000
  printf "Richieste Lambda/mese: %d (free tier %d)\n", req, free_req
  printf "GB-s/mese: %.0f (free tier %d) -> compute a pagamento: %.0f GB-s\n", gbs, free_gbs, (gbs>free_gbs)?gbs-free_gbs:0
  api = req * 3.50 / 1000000                   # API Gateway REST: 3,50 $ per milione di richieste
  printf "API Gateway: ~%.2f $/mese\n", api

  # Costi mensili calcolati con i prezzi us-east-1 (730 h/mese)
  mono  = 2*0.0416*730 + (16.43+5.5) + (0.068*730 + 2*0.23*20)
  micro = 8*(0.25*0.04048 + 0.5*0.004445)*730 + 2*(0.017*730 + 0.23*20) + api
  sless = api + 0.5                            # 0,5 $ = stima prudente DynamoDB on-demand
  printf "Monolitica %.0f $ | Microservizi %.0f $ | Serverless %.2f $\n", mono, micro, sless
  printf "Risparmio serverless vs monolite: ~%.0f $/mese\n", mono - sless
}'
```

Il costo serverless è inferiore a 1 $ perché il carico resta nel free tier di Lambda; restano API Gateway (circa 0,23 $) e DynamoDB on-demand (stima prudente 0,5 $).
