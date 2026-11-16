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
| ~181 $ | ~124 $ | ~0 $ |

## Tabella confronti

| Componente | Monolite | Microservizi | Serverless |
|---|---|---|---|
| Compute | ~23 $ (x2 EC2) | 0 $ (x4 task Fargate) | 0 $ (x4 Lambda) |
| Database | ~135 $ | ~31 $ (x4 db) | 0 $ (x2 DB) |
| API Gateway | - | - | ~0.02 $ |
| **Prezzo mensile** | **~181 $** | **~124 $** | **~0 $** |

Fonte dei prezzi: AWS Pricing Calculator (una stima per architettura).

## Considerazioni finali

**Raccomandazione: architettura serverless per QuickOrder.**

Il traffico e spiky (500 ordini/giorno in media, fino a 3.000 ordini/ora nel weekend), pattern ideale per serverless:

- **Costo variabile**: si pagano solo le ~15k richieste effettive/mese, non i server inattivi di notte.
- **Scaling automatico**: Lambda gestisce i picchi senza configurazione, da 0 a migliaia di esecuzioni parallele in millisecondi.
- **Time-to-market**: una startup paga ~$0/mese e si concentra sul prodotto, non sull'infrastruttura.

**Limite**: cold start Lambda (~200-500 ms) per richieste rare. Mitigabile con **Provisioned Concurrency** (pre-inizializza un numero definito di ambienti di esecuzione, eliminando i cold start).

Procedura di esecuzione in CLI Cloudshell:

Il laboratorio confronta tre architetture con AWS Pricing Calculator (nessuna risorsa da creare). In CloudShell si riproduce il calcolo del carico Lambda e il confronto con le cifre del Calculator.

```bash
awk 'BEGIN {
  # Richieste mensili per servizio (256 MB, 200 ms)
  utenti=5000; catalogo=30000; ordini=15000; pagamenti=15000
  req = utenti + catalogo + ordini + pagamenti
  gbs = req * 0.2 * 0.25
  free_gbs = 400000; free_req = 1000000
  printf "Richieste Lambda/mese: %d (free tier %d)\n", req, free_req
  printf "GB-s/mese: %.0f (free tier %d) -> compute a pagamento: %.0f GB-s\n", gbs, free_gbs, (gbs>free_gbs)?gbs-free_gbs:0
  api = 0.02                                  # stima Calculator del deliverable
  printf "API Gateway: ~%.2f $/mese (stima Calculator)\n", api

  # Cifre dal Pricing Calculator (stime del deliverable)
  mono=181; micro=124; sless=0
  printf "Monolitica %d $ | Microservizi %d $ | Serverless ~%d $\n", mono, micro, sless
  printf "Risparmio serverless vs monolite: ~%d $/mese\n", mono - sless
}'
```

Il costo serverless e ~0 $ perche il carico resta nel free tier di Lambda e DynamoDB on-demand; API Gateway pesa pochi centesimi.
