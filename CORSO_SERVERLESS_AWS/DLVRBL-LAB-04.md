# Laboratorio 04 - Casi d'Uso Serverless e Analisi Economica

Lavoro di gruppo (Gruppo 2: Matteo Ninotti / Riccardo Gouthier / Ivan Cioffi).

Regione: `us-east-1`. Stime fatte con AWS Pricing Calculator (stima EC2 e stima serverless per ogni scenario). Le cifre "Calculator" vengono dagli screenshot delle stime; le cifre "Sintesi" dalle tabelle di conclusione.

## Step 1 - Scenario A: blog con traffico scarso

Traffico: 10.000 visite/giorno, 3 API call/visita, 30.000 richieste/giorno, 900.000 richieste/mese.

| Voce | EC2 | Serverless |
|---|---|---|
| Compute | EC2 t3.micro (Linux, 730 h): $8,23 | Lambda (900k req, 50 ms, 128 MB): $0,00 (Calculator) / ~$0,10 (Sintesi) |
| Database | RDS db.t3.micro (Single-AZ, 20 GB): $15,44 | DynamoDB on-demand: $0,37 (Calculator) / ~$0,50 (Sintesi) |
| API | - | API Gateway HTTP API: $0,90 |
| Totale mensile (Calculator) | $23,67 | $1,27 |
| Totale 12 mesi (Calculator) | $284,04 | $15,24 |
| Totale mensile (Sintesi) | $23,23 | $1,50 |

**Risultato**: risparmio ~$21,73/mese, ~$261/anno, **~94%** (serverless ~15x piu economico).

**Conclusione**: il costo fisso EC2 si paga a prescindere dalle visite (10.000 o zero); con serverless si paga il consumo. La maggiore complessita di configurazione (Lambda, API Gateway, DynamoDB) e ripagata gia nel primo mese.

## Step 2 - Scenario B: e-commerce ad alto traffico costante

Traffico: 1.000.000 richieste/ora, 24/7, 720M richieste/mese, traffico costante.

| Voce | EC2 | Serverless |
|---|---|---|
| Compute | 10x EC2 c5.large (Linux, on-demand): ~$620 (Sintesi) / $626,90 (Calculator) | Lambda (720M req, 200 ms, 512 MB): ~$1.200 (Sintesi) / $1.337,14 (Calculator) |
| Load balancer | ALB: ~$20 (Sintesi) / $22,27 (Calculator) | - |
| API | - | API Gateway HTTP API (720M req): ~$720 (Sintesi) / $678,00 (Calculator) |
| Totale mensile (Calculator) | $649,17 | $2.015,14 |
| Totale 12 mesi (Calculator) | $7.790,04 | $24.181,68 |
| Totale mensile (Sintesi) | ~$640 | ~$1.920 |

**Risultato**: serverless costa **~3x** EC2 (+$1.280/mese, ~$15.360/anno). **EC2 conviene.**

**Conclusione**: scenario ribaltato rispetto al blog. API Gateway e Lambda fatturano ogni invocazione; con carico alto e prevedibile il canone fisso EC2 e un vantaggio enorme.

## Step 3 - Scenario C: applicazione stagionale

Traffico: estate (4 mesi) 50.000 richieste/ora = 36M richieste/mese (144M a stagione); inverno (8 mesi) 500 richieste/ora = 360k richieste/mese (2,88M a stagione).

Nota: per ottenere i totali annui, il costo mensile della stima va moltiplicato x4 (estate) e x8 (inverno). Con EC2 il costo non cambia tra stagioni (capacita sempre accesa).

| Voce | EC2 | Serverless |
|---|---|---|
| Estate, mensile (Calculator) | $270,47 (EC2 $248,20 + ELB $22,27) | $96,33 (API Gateway $36,00 + Lambda $60,33) |
| Inverno, mensile (Calculator) | $270,47 (stessa stima) | $0,36 (API Gateway $0,36 + Lambda $0,00, free tier) |
| Estate (4 mesi), Sintesi | 4x EC2 c5.large $992 + ALB $80 | API Gateway HTTP $144 + Lambda (200 ms, 512 MB) $268 |
| Inverno (8 mesi), Sintesi | 4x EC2 c5.large $1.984 + ALB $160 | API Gateway HTTP ~$3 + Lambda (free tier) ~$0 |
| **Totale annuo (Sintesi)** | **~$3.216** | **~$415** |

Totale annuo serverless dalle stime Calculator: $96,33 x 4 + $0,36 x 8 = ~$388 (calcolato).

**Risultato**: risparmio ~$2.801/anno, **~87%** (serverless ~7x piu economico).

**Conclusione**: con EC2 la capacita dimensionata per l'estate si paga tutto l'anno, anche a gennaio con 500 richieste/ora. Con serverless i costi seguono il traffico: in estate Lambda scala sui 50.000 req/ora, in inverno il volume rientra nel free tier permanente.

## Break-even point

Confronto Lambda (200 ms, 256 MB) vs EC2 t3.medium 24/7.

- Compute per invocazione: 256 MB x 0,2 s = 51,2 MB-s.
- Costo oltre il free tier (regione eu-south-1): $0.00000023 per richiesta + $0.0000195172 per GB-s oltre i 400.000 GB-s.
- Ipotesi: 19M richieste/mese (18M a pagamento, 1M in free tier).

| Voce | Costo mensile |
|---|---|
| Richieste Lambda: $0,23 x 18 | ~$4,14 |
| Compute Lambda | ~$10 |
| Subtotale Lambda | ~$14,14 |
| HTTP API: 19M richieste x $1/1M | $19 |
| **Totale serverless** | **~$33,14** |
| EC2 t3.medium 24/7 | ~$33 |

**Break-even: circa 19M richieste Lambda/mese.** Sopra questa soglia EC2 diventa piu economico.

## Conclusioni generali

| Scenario | Profilo traffico | Scelta consigliata |
|---|---|---|
| A - Blog | Basso, variabile | Serverless (-94%) |
| B - E-commerce | Alto, costante (720M req/mese) | EC2 (serverless ~3x piu caro) |
| C - Stagionale | Picchi estivi, inverno quasi nullo | Serverless (-87%) |

Regola pratica: serverless conviene con traffico basso, irregolare o stagionale; EC2 conviene con carico alto, costante e prevedibile (sopra ~19M richieste/mese a parita di profilo Lambda).
