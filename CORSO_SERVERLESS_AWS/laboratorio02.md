# Laboratorio 02 - Green IT, Economia Circolare e Intro Serverless

Lavoro di gruppo (Gruppo 2: Matteo Ninotti / Riccardo Gouthier / Ivan Cioffi).

## Step 1 - Classificazione RAEE

Normativa: Direttiva UE 2012/19/UE (RAEE), economia circolare.

| Dispositivo | Quantita | Categoria RAEE | Azione consigliata | Normativa applicabile |
|---|---|---|---|---|
| Laptop (funzionanti) | 50 | R3 - IT e Telecomunicazioni | Refurbishment / Donazione | Art. 3(1)(a), All. III - Cat. 3 |
| Monitor LCD (non funzionanti) | 30 | R3 - IT e Telecomunicazioni | Riciclo certificato | Art. 3(1)(a), All. III - Cat. 3 |
| Server rack (obsoleti ma funzionanti) | 20 | R3 - IT e Telecomunicazioni | Refurbishment | Art. 3(1)(a), All. III - Cat. 3 |
| Stampanti laser (miste) | 30 | R3 - Apparecchiature IT (grandi e piccole) | Riciclo certificato | Art. 3(1)(a), All. III - Cat. 3/5 |
| Smartphone aziendali (funzionanti) | 20 | R4 - Piccoli apparecchi elettronici | Donazione / Refurbishment | Art. 3(1)(a), All. III - Cat. 4 |
| **Totale** | **150** | | | |

Legenda azioni:

- **Refurbishment / Donazione**: dispositivi funzionanti ricondizionati e ceduti a enti no-profit, scuole o rivenditori.
- **Riciclo certificato**: dispositivi non funzionanti o non ricondizionabili avviati a impianti RAEE autorizzati per il recupero di materie prime seconde.
- **Cat. R3 / R4**: R3 = IT e Telecomunicazioni; R4 = piccoli apparecchi elettronici (All. III, Dir. 2012/19/UE).

## Step 2 - POC: elaborazione CSV con Lambda, S3, DynamoDB e SNS

Scenario: un utente carica un CSV su S3; l'evento avvia una pipeline serverless che elabora, trasforma e salva i dati su DynamoDB e notifica via SNS. Paradigma: Event-Driven Architecture, nessun server da gestire.

### Flusso dati

```
Utente --(upload CSV)--> S3 --(PUT event)--> S3 Event Notification --(invoca)--> Lambda
                                                                                   |
                                                           +----(write)------------+----(publish)----+
                                                           v                                          v
                                                      DynamoDB                                       SNS
```

### Classificazione dei componenti

| Componente | Ruolo | Serverless? | Motivazione |
|---|---|---|---|
| Amazon S3 | Archivia il CSV; evento iniziale della pipeline | Si | Object storage gestito, scaling automatico, si paga per GB usato |
| S3 Event Notification | Trigger automatico all'upload, senza polling | Si | Funzionalita nativa di S3, nessuna infrastruttura aggiuntiva |
| AWS Lambda | Legge il CSV, trasforma (parsing, validazione, mapping), scrive su DynamoDB, pubblica su SNS | Si | FaaS, esecuzione on-demand, billing al millisecondo, scala da 0 a migliaia di esecuzioni |
| Amazon DynamoDB | Database NoSQL dei dati trasformati | Si | Gestito, on-demand, nessun cluster, patching automatico |
| Amazon SNS | Notifica publish/subscribe a fine elaborazione (email, Lambda, SQS, HTTP) | Si | Messaggistica gestita, multi-AZ nativa, si paga per messaggio |
| **Totale** | | **5 / 5** | Architettura 100% serverless |

### Flusso di esecuzione

1. **Caricamento**: l'utente carica il CSV sul bucket S3.
2. **Trigger**: S3 emette `s3:ObjectCreated` e attiva la Lambda.
3. **Elaborazione**: la Lambda scarica il CSV, ne fa il parsing e applica le trasformazioni.
4. **Persistenza**: scrittura su DynamoDB, in batch o singola voce.
5. **Notifica**: la Lambda pubblica un messaggio su SNS per i sistemi a valle.

### Vantaggi

- Costo zero a riposo.
- Scalabilita automatica.
- Overhead operativo ridotto (niente patching, niente cluster).
- Time-to-market rapido (deploy via AWS SAM o CDK).

## Step 3 - EC2 t3.medium always-on vs Lambda + principi Green IT

Ipotesi: us-east-1, EC2 t3.medium on-demand, Lambda 256 MB, 100.000 invocazioni/mese, durata media 500 ms, prezzi AWS 2025.

### Costi

| Scenario | Calcolo | Costo mensile | Costo annuo |
|---|---|---|---|
| EC2 t3.medium (always-on) | $0.0416/h x 24 h x 365 gg = 8.760 h/anno, fatturati anche a idle | $30.37 | $364.42 |
| AWS Lambda (pay-per-use) | 100.000 inv. x 0,5 s x 0,25 GB = 12.500 GB-s | $0.21 | $2.52 |
| **Risparmio annuale** | $364.42 - $2.52 | | **$361.90 (-99,3%)** |

### Dettaglio Lambda

| Parametro | Valore | Note |
|---|---|---|
| Invocazioni mensili | 100.000 | Carico stimato POC EcoTech |
| Durata per invocazione | 500 ms | Lettura CSV + trasformazione + write DynamoDB |
| Memoria | 256 MB (0,25 GB) | Sufficiente per CSV standard |
| GB-secondi mensili | 12.500 | 100.000 x 0,5 s x 0,25 GB |
| Free tier Lambda | 400.000 GB-s/mese (+ 1.000.000 richieste) | Carico POC coperto quasi interamente |
| Costo eccedenza | $0.00001667 per GB-s | Pricing us-east-1 (2025) |
| Costo mensile effettivo | ~$0.21 | Richieste + compute |
| Costo annuo | $2.52 | $0.21 x 12 |

### Collegamento ai principi Green IT

| Principio | Applicazione al serverless | Beneficio per EcoTech |
|---|---|---|
| Efficienza energetica | Lambda esegue codice solo quando serve; EC2 always-on consuma anche con CPU allo 0% | ~350 kWh/anno di consumo idle evitati per singolo t3.medium |
| Pay-as-you-go | Risorse allocate e fatturate solo per i millisecondi di esecuzione | Costo da $364.42 a $2.52/anno (-99,3%) |
| Riduzione hardware fisico | Nessun server fisico dedicato da acquistare o dismettere | Meno RAEE (coerente con Step 1) |
| Scalabilita sostenibile | Scala da 0 al picco richiesto | Zero over-provisioning |
| Carbon footprint ridotta | Infrastruttura condivisa tra molti clienti, piu efficiente di un server dedicato | Programmi AWS di energia rinnovabile |

## Sintesi esecutiva

- Risparmio annuo per pipeline CSV: $364.42 - $2.52 = **$361.90**.
- Risparmio percentuale: **99,3%**.
- Break-even serverless: immediato per questo carico.
- Su 10 pipeline: EC2 ~$3.644/anno vs Lambda ~$25/anno, risparmio ~$3.619/anno (crescita lineare).
- Raccomandazione per EcoTech: approccio **serverless-first** per i nuovi workload event-driven, in linea con economia circolare e dismissione responsabile degli asset IT (Step 1).
