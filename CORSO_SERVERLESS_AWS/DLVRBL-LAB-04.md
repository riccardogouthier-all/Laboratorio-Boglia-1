# Laboratorio 04 - Casi d'Uso Serverless e Analisi Economica

Lavoro di gruppo (Gruppo 2: Matteo Ninotti / Riccardo Gouthier / Ivan Cioffi).

Regione: `us-east-1`. Stime fatte con AWS Pricing Calculator (stima EC2 e stima serverless per ogni scenario). Le cifre "Calculator" sono quelle delle stime del gruppo (gli screenshot non sono allegati a questo documento); le cifre "Sintesi" sono quelle arrotondate delle tabelle di conclusione. Nelle conclusioni si usa la serie indicata di volta in volta.

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

**Risultato**: risparmio ~$21,73/mese, ~$261/anno, **~94%**. Serverless è ~15x più economico con le cifre Sintesi ($23,23 contro $1,50) e ~19x con quelle Calculator ($23,67 contro $1,27).

**Conclusione**: il costo fisso EC2 si paga a prescindere dalle visite (10.000 o zero); con serverless si paga il consumo. La maggiore complessità di configurazione (Lambda, API Gateway, DynamoDB) è ripagata già nel primo mese.

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

**Conclusione**: scenario ribaltato rispetto al blog. API Gateway e Lambda fatturano ogni invocazione; con carico alto e prevedibile il canone fisso di EC2 è un vantaggio enorme.

## Step 3 - Scenario C: applicazione stagionale

Traffico: estate (4 mesi) 50.000 richieste/ora = 36M richieste/mese (144M a stagione); inverno (8 mesi) 500 richieste/ora = 360k richieste/mese (2,88M a stagione).

Nota: per ottenere i totali annui, il costo mensile della stima va moltiplicato x4 (estate) e x8 (inverno). Con EC2 il costo non cambia tra stagioni (capacità sempre accesa).

| Voce | EC2 | Serverless |
|---|---|---|
| Estate, mensile (Calculator) | $270,47 (EC2 $248,20 + ELB $22,27) | $96,33 (API Gateway $36,00 + Lambda $60,33) |
| Inverno, mensile (Calculator) | $270,47 (stessa stima) | $0,36 (API Gateway $0,36 + Lambda $0,00, free tier) |
| Estate (4 mesi), Sintesi | 4x EC2 c5.large $992 + ALB $80 | API Gateway HTTP $144 + Lambda (200 ms, 512 MB) $268 |
| Inverno (8 mesi), Sintesi | 4x EC2 c5.large $1.984 + ALB $160 | API Gateway HTTP ~$3 + Lambda (free tier) ~$0 |
| **Totale annuo (Sintesi)** | **~$3.216** | **~$415** |

Totale annuo dalle stime Calculator: EC2 $270,47 x 12 = ~$3.245; serverless $96,33 x 4 + $0,36 x 8 = ~$388. La serie Sintesi ($3.216 e ~$415) arrotonda le stesse voci; il risparmio resta ~87-88% con entrambe.

**Risultato**: risparmio ~$2.801/anno, **~87%** (serverless ~7x più economico).

**Conclusione**: con EC2 la capacità dimensionata per l'estate si paga tutto l'anno, anche a gennaio con 500 richieste/ora. Con serverless i costi seguono il traffico: in estate Lambda scala sui 50.000 req/ora, in inverno il volume rientra nel free tier permanente.

## Break-even point

Confronto Lambda (200 ms, 256 MB) + HTTP API + DynamoDB vs EC2 t3.medium 24/7, tutti con prezzi on-demand **us-east-1** (la stessa regione degli scenari A-C).

Prezzi usati:
- Lambda: $0,20 per milione di richieste (primo milione gratuito) e $0,0000166667 per GB-s (primi 400.000 GB-s gratuiti).
- HTTP API: $1,00 per milione di richieste.
- DynamoDB on-demand: $0,125 per milione di letture, ipotizzando 1 lettura per richiesta (le scritture non sono incluse).
- EC2 t3.medium: $0,0416/h x 730 h = ~$30,37/mese.

Compute per invocazione: 256 MB x 0,2 s = 0,05 GB-s (51,2 MB-s).

Scomposizione a 17M richieste/mese:

| Voce | Calcolo | Costo mensile |
|---|---|---|
| Richieste Lambda | (17M - 1M gratuito) x $0,20/M | $3,20 |
| Compute Lambda | (17M x 0,05 GB-s - 400.000 GB-s gratuiti) x $0,0000166667 | $7,50 |
| HTTP API | 17M x $1/M | $17,00 |
| DynamoDB (letture) | 17M x $0,125/M | $2,12 |
| **Totale serverless** | | **~$29,82** |
| EC2 t3.medium 24/7 | | ~$30,37 |

**Break-even: circa 17M richieste/mese.** Sopra questa soglia EC2 diventa più economico. Senza DynamoDB (solo API Gateway e Lambda) la soglia sale a ~18M: l'ordine di grandezza non cambia, ma il database sposta il punto di pareggio verso il basso.

## Conclusioni generali

| Scenario | Profilo traffico | Scelta consigliata |
|---|---|---|
| A - Blog | Basso, variabile | Serverless (-94%) |
| B - E-commerce | Alto, costante (720M req/mese) | EC2 (serverless ~3x più caro) |
| C - Stagionale | Picchi estivi, inverno quasi nullo | Serverless (-87%) |

Regola pratica: serverless conviene con traffico basso, irregolare o stagionale; EC2 conviene con carico alto, costante e prevedibile (sopra ~17M richieste/mese a parità di profilo Lambda).

Procedura di esecuzione in CLI Cloudshell:

Le stime ufficiali vengono dall'AWS Pricing Calculator. In CloudShell si riproducono i calcoli principali con `awk`.

```bash
# Scenario A - blog (900.000 richieste/mese), cifre Calculator
awk 'BEGIN {
  ec2 = 8.23 + 15.44                          # EC2 t3.micro + RDS db.t3.micro
  sl  = 0.00 + 0.37 + 0.90                    # Lambda + DynamoDB + HTTP API
  printf "A) EC2 %.2f $/mese (%.2f/anno) | Serverless %.2f $/mese (%.2f/anno) | risparmio %.0f%%\n", ec2, ec2*12, sl, sl*12, (ec2-sl)/ec2*100
}'

# Scenario B - e-commerce 720M richieste/mese
awk 'BEGIN {
  ec2 = 626.90 + 22.27                        # 10x c5.large + ALB
  sl  = 1337.14 + 678.00                      # Lambda + HTTP API
  printf "B) EC2 %.2f | Serverless %.2f | serverless = %.1fx\n", ec2, sl, sl/ec2
}'

# Scenario C - stagionale: 4 mesi estate, 8 mesi inverno
awk 'BEGIN {
  ec2 = 270.47 * 12
  sl  = 96.33*4 + 0.36*8
  printf "C) EC2 %.0f $/anno | Serverless %.0f $/anno | risparmio %.0f%%\n", ec2, sl, (ec2-sl)/ec2*100
}'

# Break-even Lambda (200 ms, 256 MB) + HTTP API + DynamoDB (1 lettura/richiesta) vs EC2 t3.medium 24/7, us-east-1
awk 'BEGIN {
  ec2 = 0.0416 * 730                            # 30,37 $/mese
  for (n = 1; n <= 40; n += 0.1) {              # n = milioni di richieste/mese
    req  = (n-1) * 0.20                         # Lambda: richieste oltre il primo milione gratuito
    gbs  = n * 1000000 * 0.2 * 0.25             # GB-s mensili
    comp = ((gbs > 400000) ? gbs - 400000 : 0) * 0.0000166667
    api  = n * 1.00                             # HTTP API: 1 $ per milione
    ddb  = n * 0.125                            # DynamoDB on-demand: letture
    tot  = req + comp + api + ddb
    if (tot >= ec2) { printf "Break-even ~%.1f M richieste/mese (serverless %.2f $ vs EC2 %.2f $)\n", n, tot, ec2; break }
  }
}'
```

Il break-even calcolato (~17,3 M richieste/mese) coincide con quello del deliverable (~17 M).
